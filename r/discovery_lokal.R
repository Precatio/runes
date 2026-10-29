# Upptäcktsmotorn, version 2, del 2 och 3 enligt den låsta planen analysplaner/2026-10-29-upptacktsmotorn-v2.md.
# Del 2: bygder där ett drag är vanligare än landskap, tid och textlängd förklarar. Kulldorffs scanstatistik med
# förväntat = summan av varje stens sannolikhet ur glm(drag ~ landskap + tidsskikt + log ord); upptäcks i halva A
# (999 simuleringar), kandidaterna fryses (SHA-256) och prövas i samma cirkel i halva B (9 999 simuleringar), Holm.
# Del 3: udda stenar – överraskning mot samma modeller skattade på alla stenar (beskrivning).
#   Rscript r/discovery_lokal.R drag.csv drag_familjer.json UTMAPP
.args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({ library(jsonlite); library(dplyr); library(sf) })
sf_use_s2(FALSE)
feat_path <- .args[1]; fam_path <- .args[2]; out <- .args[3]
set.seed(2026)
MIN_N <- 30; KMIN <- 10; UB <- 0.05; RMAX <- 30000; NSIM_A <- 999; NSIM_B <- 9999; Q <- 0.05; MIN_RATIO <- 1.5

d <- read.csv(feat_path, stringsAsFactors = FALSE, na.strings = "")
fam <- fromJSON(fam_path)
meta <- c("signum", "province", "parish", "carver", "style_from", "style_to", "n_words", "lat", "lon", "pa_plats", "lokal")
famof <- function(f) if (!is.null(fam[[f]])) fam[[f]] else f
feats <- setdiff(names(d), meta)
feats <- feats[!vapply(feats, famof, "") %in% c("landskap", "material")]
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
d$lw <- log1p(d$n_words)
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
xy <- st_coordinates(st_transform(st_as_sf(d[!is.na(d$lat), ], coords = c("lon", "lat"), crs = 4326), 3006))
d$x <- NA; d$y <- NA; d$x[!is.na(d$lat)] <- xy[, 1]; d$y[!is.na(d$lat)] <- xy[, 2]

expected <- function(x, f) {
  m <- suppressWarnings(glm(reformulate(c(if (length(unique(x$province)) > 1) "province", "period", "lw"), f),
                            family = binomial, data = droplevels(x)))
  fitted(m)
}
llr <- function(O, E, N) {
  r <- O * log(O / E) + (N - O) * log((N - O) / (N - E))
  r[!is.finite(r) | O <= E] <- 0
  r
}
scan_feature <- function(x, f) {
  x <- x[!is.na(x[[f]]), ]
  yv <- x[[f]]
  if (sum(yv == 1) < MIN_N || sum(yv == 0) < MIN_N) return(NULL)
  p <- expected(x, f)
  n <- nrow(x); kmax <- max(KMIN, floor(UB * n))
  D <- as.matrix(dist(cbind(x$x, x$y)))
  nb <- t(apply(D, 1, order))[, 1:kmax, drop = FALSE]
  rad <- t(sapply(seq_len(n), function(i) D[i, nb[i, ]]))
  ok <- rad <= RMAX; ok[, seq_len(KMIN - 1)] <- FALSE
  stat <- function(yy) {
    N <- sum(yy)
    O <- t(apply(matrix(yy[nb], n), 1, cumsum)); E <- t(apply(matrix(p[nb], n), 1, cumsum))
    L <- llr(O, E, N); L[!ok] <- 0
    list(L = L, O = O, E = E)
  }
  s <- stat(yv)
  best <- which(s$L == max(s$L), arr.ind = TRUE)[1, ]
  sims <- replicate(NSIM_A, max(stat(rbinom(n, 1, p))$L))
  i <- best[1]; k <- best[2]
  list(feature = f, n = n, cases = sum(yv), center = x$signum[i], cx = x$x[i], cy = x$y[i], radius = rad[i, k],
       k = k, O = s$O[i, k], E = s$E[i, k], ratio = s$O[i, k] / s$E[i, k], llr = s$L[i, k],
       p = (1 + sum(sims >= s$L[i, k])) / (NSIM_A + 1), stones = x$signum[nb[i, 1:k]])
}
confirm <- function(c, x) {
  f <- c$feature
  x <- x[!is.na(x[[f]]), ]
  if (sum(x[[f]] == 1) < 5) return(list(nB = nrow(x)))
  p <- expected(x, f)
  inside <- sqrt((x$x - c$cx)^2 + (x$y - c$cy)^2) <= c$radius
  O <- sum(x[[f]][inside]); E <- sum(p[inside])
  sims <- replicate(NSIM_B, sum(rbinom(sum(inside), 1, p[inside])))
  list(nB = sum(inside), OB = O, EB = E, ratioB = O / E, pB = (1 + sum(sims >= O)) / (NSIM_B + 1),
       stonesB = x$signum[inside])
}

loc <- d[d$lokal == 1 & !is.na(d$x), ]
A <- loc[loc$half == "A", ]; B <- loc[loc$half == "B", ]
t0 <- Sys.time()
scans <- Filter(Negate(is.null), lapply(feats, function(f) scan_feature(A, f)))
cat("skannade drag:", length(scans), " tid", round(as.numeric(Sys.time() - t0, units = "mins"), 1), "min\n")
tab <- data.frame(feature = sapply(scans, `[[`, "feature"), p = sapply(scans, `[[`, "p"),
                  ratio = sapply(scans, `[[`, "ratio"), O = sapply(scans, `[[`, "O"), E = sapply(scans, `[[`, "E"))
tab$q <- p.adjust(tab$p, "BH")
cand <- scans[tab$q < Q & tab$ratio >= MIN_RATIO]
cf <- file.path(out, "lokala_kandidater.json")
write_json(lapply(cand, function(c) c[c("feature", "center", "cx", "cy", "radius", "k", "O", "E", "ratio", "p")]), cf,
           auto_unbox = TRUE, digits = NA, pretty = TRUE)
sha <- system2("shasum", c("-a", "256", shQuote(cf)), stdout = TRUE)
writeLines(sha, file.path(out, "lokala_kandidater.sha256"))
cat("kandidater", length(cand), " frysta:", sub(" .*", "", sha), "\n")
conf <- lapply(cand, function(c) c(c, confirm(c, B)))
pB <- sapply(conf, function(c) if (is.null(c$pB)) NA else c$pB)
holm <- p.adjust(pB, "holm")
for (i in seq_along(conf)) {
  conf[[i]]$holm <- holm[i]
  conf[[i]]$utslag <- if (!is.na(holm[i]) && holm[i] < 0.05) "bekräftad" else
    if (!is.na(pB[i]) && pB[i] < 0.05) "mönster att pröva" else "höll inte"
  inside <- d$signum %in% c(conf[[i]]$stones, conf[[i]]$stonesB)
  cv <- d$carver[inside & !is.na(d$carver) & d$carver != ""]
  conf[[i]]$carvers <- as.list(sort(table(cv), decreasing = TRUE))
  conf[[i]]$parishes <- as.list(sort(table(d$parish[inside]), decreasing = TRUE))
}

# ---- Del 3: udda stenar -------------------------------------------------------------------------------------------
H <- function(p) -(p * log2(p) + (1 - p) * log2(1 - p))
contrib <- matrix(NA_real_, nrow(d), length(feats), dimnames = list(d$signum, feats))
for (f in feats) {
  k <- !is.na(d[[f]])
  if (sum(d[[f]][k] == 1) < MIN_N || sum(d[[f]][k] == 0) < MIN_N) next
  p <- pmin(pmax(expected(d[k, ], f), 1e-6), 1 - 1e-6)
  yv <- d[[f]][k]
  contrib[k, f] <- -log2(ifelse(yv == 1, p, 1 - p)) - H(p)
}
known <- rowSums(!is.na(contrib))
surprise <- rowSums(contrib, na.rm = TRUE)
odd <- order(-ifelse(known >= 10, surprise, -Inf))[1:25]
odd_list <- lapply(odd, function(i) {
  cc <- sort(contrib[i, !is.na(contrib[i, ])], decreasing = TRUE)[1:3]
  list(signum = d$signum[i], province = d$province[i], surprise = surprise[i], known = known[i],
       top = lapply(names(cc), function(f) list(feature = f, value = d[[f]][i], bits = unname(cc[f]))))
})

write_json(list(plan = "analysplaner/2026-10-29-upptacktsmotorn-v2.md", n_A = nrow(A), n_B = nrow(B),
                scanned = tab, candidates_sha256 = sub(" .*", "", sha), confirmed = conf, odd = odd_list),
           file.path(out, "lokala.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
print(tab[order(tab$p), ][1:15, ], row.names = FALSE, digits = 3)
for (c in conf) cat(sprintf("%-18s %s r=%.1f km  A: %d/%.1f (%.1f×) p %.3f | B: %s/%s (%s×) p %s holm %s  %s | %s\n",
  c$feature, c$center, c$radius / 1000, c$O, c$E, c$ratio, c$p, c$OB, format(c$EB, digits = 3),
  format(c$ratioB, digits = 2), format(c$pB, digits = 2), format(c$holm, digits = 2), c$utslag,
  paste(names(c$carvers)[1:min(3, length(c$carvers))], collapse = ", ")))
cat("\nUdda stenar:\n")
for (o in odd_list) cat(sprintf("%-12s %5.1f bitar (%d drag): %s\n", o$signum, o$surprise, o$known,
  paste(sapply(o$top, function(t) sprintf("%s=%s", t$feature, t$value)), collapse = ", ")))
