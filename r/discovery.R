# Upptäcktsmotorn, version 1: parskanning i två steg enligt den låsta planen analysplaner/2026-10-28-upptacktsmotorn.md.
#   Rscript r/discovery.R drag.csv drag_familjer.json UTMAPP
# Steg 1 (halva A): varje par av drag ur olika familjer, b ~ a + landskap + tidsskikt + log(1 + ord) (glm); kandidater
# med BH-q < 0,05 och oddskvot minst 1,5 åt något håll, högst 50. Listan fryses (SHA-256) innan halva B läses.
# Steg 2 (halva B): samma modell plus ristaren som slumpeffekt (mgcv), ensidigt i steg 1:s riktning; Holm och BH.
# Sekundärt: halvorna bytta.
.args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({ library(mgcv); library(jsonlite); library(dplyr) })
feat_path <- .args[1]; fam_path <- .args[2]; out <- .args[3]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
MIN_N <- 20; MIN_OR <- 1.5; MAX_CAND <- 50; Q <- 0.05

d <- read.csv(feat_path, stringsAsFactors = FALSE, na.strings = "")
fam <- fromJSON(fam_path)
meta <- c("signum", "province", "parish", "carver", "style_from", "style_to", "n_words")
feats <- setdiff(names(d), meta)
famof <- function(f) if (!is.null(fam[[f]])) fam[[f]] else f
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
d$lw <- log1p(d$n_words)
d$carver_f <- factor(ifelse(!is.na(d$carver) & d$carver != "", d$carver,
                            paste0("_", d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish))))
# Halvorna som i change.R: socken för socken, växelvis inom varje landskap i sockenmedeldateringens ordning
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]

pairs <- do.call(rbind, lapply(seq_along(feats), function(i) if (i < length(feats))
  data.frame(a = feats[i], b = feats[(i + 1):length(feats)], stringsAsFactors = FALSE)))
pairs <- pairs[mapply(function(a, b) famof(a) != famof(b), pairs$a, pairs$b), ]

usable <- function(x, f) { v <- x[[f]][!is.na(x[[f]])]; sum(v == 1) >= MIN_N && sum(v == 0) >= MIN_N }

stage1 <- function(H) {
  x <- d[d$half == H, ]
  res <- lapply(seq_len(nrow(pairs)), function(i) {
    a <- pairs$a[i]; b <- pairs$b[i]
    y <- x[!is.na(x[[a]]) & !is.na(x[[b]]), ]
    if (!usable(y, a) || !usable(y, b)) return(NULL)
    f <- as.formula(paste(b, "~", a, "+ province + period + lw"))
    fit <- tryCatch(suppressWarnings(glm(f, family = binomial, data = droplevels(y))), error = function(e) NULL)
    if (is.null(fit)) return(NULL)
    s <- summary(fit)$coefficients
    if (!a %in% rownames(s)) return(NULL)
    data.frame(a = a, b = b, n = nrow(y), k_ab = sum(y[[a]] == 1 & y[[b]] == 1), or = exp(s[a, 1]), p = s[a, 4])
  })
  res <- do.call(rbind, res)
  res$q <- p.adjust(res$p, "BH")
  res
}
stage2 <- function(cand, H) {
  x <- d[d$half == H, ]
  out <- lapply(seq_len(nrow(cand)), function(i) {
    a <- cand$a[i]; b <- cand$b[i]
    y <- x[!is.na(x[[a]]) & !is.na(x[[b]]), ]
    f <- as.formula(paste(b, "~", a, "+ province + period + lw + s(carver_f, bs = \"re\")"))
    fit <- tryCatch(suppressWarnings(gam(f, family = binomial, data = droplevels(y), method = "REML")), error = function(e) NULL)
    if (is.null(fit)) return(data.frame(n = nrow(y), or2 = NA, p1 = NA))
    s <- summary(fit)$p.table
    if (!a %in% rownames(s)) return(data.frame(n = nrow(y), or2 = NA, p1 = NA))
    z <- s[a, 3]
    p1 <- if (cand$or[i] > 1) pnorm(z, lower.tail = FALSE) else pnorm(z)  # ensidigt i steg 1:s riktning
    data.frame(n2 = nrow(y), k_ab2 = sum(y[[a]] == 1 & y[[b]] == 1), or2 = exp(s[a, 1]), p1 = p1)
  })
  r <- cbind(cand, do.call(rbind, out))
  r$holm <- p.adjust(r$p1, "holm"); r$q2 <- p.adjust(r$p1, "BH")
  r$utslag <- ifelse(!is.na(r$holm) & r$holm < 0.05, "bekräftad",
                     ifelse(!is.na(r$q2) & r$q2 < Q, "mönster att pröva", "höll inte"))
  r
}
run <- function(disc, conf, tag) {
  s1 <- stage1(disc)
  cand <- s1[s1$q < Q & (s1$or >= MIN_OR | s1$or <= 1 / MIN_OR), ]
  cand <- head(cand[order(cand$q), ], MAX_CAND)
  cf <- file.path(out, paste0("kandidater_", tag, ".json"))
  write_json(cand, cf, digits = NA, pretty = TRUE)
  sha <- system2("shasum", c("-a", "256", shQuote(cf)), stdout = TRUE)
  writeLines(sha, file.path(out, paste0("kandidater_", tag, ".sha256")))
  cat(tag, ": prövade par", nrow(s1), " kandidater", nrow(cand), " frysta:", sub(" .*", "", sha), "\n")
  s2 <- stage2(cand, conf)
  list(tested = nrow(s1), n_cand = nrow(cand), sha256 = sub(" .*", "", sha), results = s2)
}
set.seed(2026)
main <- run("A", "B", "A_till_B")
swap <- run("B", "A", "B_till_A")
key <- function(r) paste(r$a, r$b)
both <- intersect(key(main$results[main$results$utslag == "bekräftad", ]), key(swap$results[swap$results$utslag == "bekräftad", ]))
write_json(list(plan = "analysplaner/2026-10-28-upptacktsmotorn.md", n_stones = nrow(d), n_features = length(feats),
                halves = as.list(table(d$half)), main = main, swap = swap, stable_both_ways = both),
           file.path(out, "upptackt.json"), digits = NA, pretty = TRUE, auto_unbox = TRUE)
show <- main$results[order(main$results$holm), c("a", "b", "or", "q", "or2", "p1", "holm", "utslag")]
print(show, row.names = FALSE, digits = 3)
cat("bekräftade åt båda håll:", paste(both, collapse = "; "), "\n")
