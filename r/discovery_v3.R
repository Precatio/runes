# Upptäcktsmotorn, version 3: samspel mellan tre drag (y; a × b) enligt den låsta planen
# analysplaner/2026-11-01-upptacktsmotorn-v3-samspel.md (sha a641368c).
#   Rscript r/discovery_v3.R utdata/upptackt_v3 data/cache/r/corpus/<fp>/corpus.csv
# Steg 1 (halva A): ranger + hstats (Friedmans H² bland de tio viktigaste dragen) och pre (RuleFit, regler med två villkor)
# föreslår (y; a, b); kandidat om tre familjer, ≥ 15 stenar per cell och glm-samspel p < 0,01; högst 30, fryses (SHA-256).
# Steg 2 (halva B): gam med ristaren som slumpeffekt, ensidigt, Holm. Sekundärt: halvorna bytta. Steg 3: andelar,
# utan ett landskap i taget, utan flyttade stenar.
.args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({
  library(mgcv); library(jsonlite); library(dplyr); library(ranger); library(hstats); library(pre); library(digest)
})
dir <- .args[1]; corpus_csv <- .args[2]
MIN_Y <- 40; MIN_CELL <- 15; P1 <- 0.01; MAX_CAND <- 30; SEED <- 2026

d <- read.csv(file.path(dir, "drag.csv"), stringsAsFactors = FALSE, na.strings = "")
fam <- fromJSON(file.path(dir, "drag_familjer.json"))
meta <- c("signum", "province", "parish", "carver", "style_from", "style_to", "n_words", "lat", "lon", "pa_plats", "lokal")
feats <- setdiff(names(d), meta)
feats <- feats[vapply(feats, function(f) all(d[[f]] %in% c(0, 1, NA)), TRUE)]
famof <- function(f) if (!is.null(fam[[f]])) fam[[f]] else f
forbid <- vapply(fromJSON(file.path(dir, "drag_forbjudna.json"), simplifyVector = FALSE),
                 function(p) paste(sort(unlist(p)), collapse = "|"), "")
okpair <- function(a, b) famof(a) != famof(b) && !(paste(sort(c(famof(a), famof(b))), collapse = "|") %in% forbid)
oktriple <- function(y, a, b) okpair(y, a) && okpair(y, b) && okpair(a, b)

# --- as in r/discovery_v2.R: period, words, carver, parish halves ---
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
d$lw <- log1p(d$n_words)
d$carver_f <- factor(ifelse(!is.na(d$carver) & d$carver != "", d$carver,
                            paste0("_", d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish))))
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
cc <- read.csv(corpus_csv, stringsAsFactors = FALSE)[, c("signum", "moved")]
d$moved <- cc$moved[match(d$signum, cc$signum)]

glm_inter <- function(x, y, a, b) {
  z <- x[!is.na(x[[y]]) & !is.na(x[[a]]) & !is.na(x[[b]]), ]
  cells <- table(factor(z[[a]], 0:1), factor(z[[b]], 0:1))
  if (any(cells < MIN_CELL)) return(NULL)
  fit <- tryCatch(suppressWarnings(glm(as.formula(paste(y, "~", a, "*", b, "+ province + period + lw")),
                                       family = binomial, data = droplevels(z))), error = function(e) NULL)
  if (is.null(fit)) return(NULL)
  s <- summary(fit)$coefficients; term <- paste0(a, ":", b)
  if (!term %in% rownames(s)) return(NULL)
  data.frame(y = y, a = a, b = b, n = nrow(z), min_cell = min(cells), beta = s[term, 1], p = s[term, 4])
}

propose <- function(H) {
  x <- d[d$half == H, ]
  ys <- feats[vapply(feats, function(f) sum(x[[f]] == 1, na.rm = TRUE) >= MIN_Y, TRUE)]
  props <- list()
  for (y in ys) {
    preds <- feats[vapply(feats, function(f) f != y && okpair(y, f), TRUE)]
    z <- x[!is.na(x[[y]]), c(y, preds, "province", "period", "lw")]
    for (f in preds) z[[f]][is.na(z[[f]])] <- -1             # 'not measurable' kept apart for the forest
    z$province <- factor(z$province); z$yf <- factor(z[[y]])
    set.seed(SEED)
    rf <- ranger(dependent.variable.name = "yf", data = z[, c("yf", preds, "province", "period", "lw")],
                 num.trees = 500, probability = TRUE, importance = "permutation", seed = SEED)
    imp <- sort(rf$variable.importance[preds], decreasing = TRUE)
    top <- names(imp)[seq_len(min(10, length(imp)))]
    X <- z[, c(preds, "province", "period", "lw")]
    hs <- tryCatch(hstats(rf, X = X, v = top, pairwise_m = 10, threeway_m = 0, n_max = 400, verbose = FALSE,
                          pred_fun = function(m, X) predict(m, X)$predictions[, 2]), error = function(e) NULL)
    if (!is.null(hs)) {
      h2 <- tryCatch(h2_pairwise(hs, normalize = TRUE, squared = TRUE, zero = FALSE), error = function(e) NULL)
      if (!is.null(h2) && length(h2$M)) {
        v <- sort(h2$M[, 1], decreasing = TRUE)[seq_len(min(3, nrow(h2$M)))]
        for (nm in names(v)) {
          ab <- strsplit(nm, ":")[[1]]
          props[[length(props) + 1]] <- data.frame(y = y, a = ab[1], b = ab[2], tool = "hstats", strength = v[[nm]])
        }
      }
    }
    zp <- x[!is.na(x[[y]]), c(y, preds)]
    for (f in preds) zp[[f]][is.na(zp[[f]])] <- 0
    zp[[y]] <- factor(zp[[y]])
    set.seed(SEED)
    pf <- tryCatch(pre(as.formula(paste(y, "~ .")), data = zp, family = "binomial", maxdepth = 2L, ntrees = 200,
                       verbose = FALSE), error = function(e) NULL)
    if (!is.null(pf)) {
      co <- coef(pf); co <- co[co$coefficient != 0 & grepl("&", co$description), ]
      for (i in seq_len(nrow(co))) {
        vars <- trimws(sub("\\s*(<=|>|<|>=|==|%in%).*$", "", strsplit(co$description[i], "&")[[1]]))
        if (length(vars) == 2 && all(vars %in% feats) && vars[1] != vars[2])
          props[[length(props) + 1]] <- data.frame(y = y, a = vars[1], b = vars[2], tool = "pre", strength = abs(co$coefficient[i]))
      }
    }
    cat(H, y, "klar\n")
  }
  do.call(rbind, props)
}

stage1 <- function(H) {
  pr <- propose(H)
  pr <- pr[pr$a %in% feats & pr$b %in% feats & mapply(oktriple, pr$y, pr$a, pr$b), ]
  pr$key <- mapply(function(y, a, b) paste(y, paste(sort(c(a, b)), collapse = "×")), pr$y, pr$a, pr$b)
  tools <- tapply(pr$tool, pr$key, function(t) paste(sort(unique(t)), collapse = "+"))
  pr <- pr[!duplicated(pr$key), ]
  x <- d[d$half == H, ]
  g <- do.call(rbind, lapply(seq_len(nrow(pr)), function(i) glm_inter(x, pr$y[i], pr$a[i], pr$b[i])))
  if (is.null(g)) return(list(proposals = pr, cand = NULL))
  g$key <- mapply(function(y, a, b) paste(y, paste(sort(c(a, b)), collapse = "×")), g$y, g$a, g$b)
  g$tools <- as.character(tools[g$key])
  cand <- g[g$p < P1, ]; cand <- cand[order(cand$p), ]; cand <- head(cand, MAX_CAND)
  list(proposals = pr, tested = g, cand = cand)
}

stage2 <- function(cand, H) {
  x <- d[d$half == H, ]
  out <- lapply(seq_len(nrow(cand)), function(i) {
    y <- cand$y[i]; a <- cand$a[i]; b <- cand$b[i]
    z <- x[!is.na(x[[y]]) & !is.na(x[[a]]) & !is.na(x[[b]]), ]
    f <- as.formula(paste(y, "~", a, "*", b, "+ province + period + lw + s(carver_f, bs = \"re\")"))
    fit <- tryCatch(suppressWarnings(gam(f, family = binomial, data = droplevels(z), method = "REML")), error = function(e) NULL)
    term <- paste0(a, ":", b)
    if (is.null(fit) || !term %in% rownames(summary(fit)$p.table)) return(data.frame(n2 = nrow(z), beta2 = NA, p1 = NA))
    s <- summary(fit)$p.table; zv <- s[term, 3]
    data.frame(n2 = nrow(z), beta2 = s[term, 1], p1 = if (cand$beta[i] > 0) pnorm(zv, lower.tail = FALSE) else pnorm(zv))
  })
  r <- cbind(cand, do.call(rbind, out))
  r$holm <- p.adjust(r$p1, "holm")
  r$utslag <- ifelse(!is.na(r$holm) & r$holm < 0.05, "bekräftad", "höll inte")
  r
}

cells <- function(y, a, b, x = d) {
  z <- x[!is.na(x[[y]]) & !is.na(x[[a]]) & !is.na(x[[b]]), ]
  fit <- suppressWarnings(glm(as.formula(paste(y, "~", a, "*", b, "+ province + period + lw")), family = binomial, data = droplevels(z)))
  sapply(list(c(0, 0), c(1, 0), c(0, 1), c(1, 1)), function(v) { zz <- z; zz[[a]] <- v[1]; zz[[b]] <- v[2]; mean(predict(fit, zz, type = "response")) })
}

stage3 <- function(r) {
  conf <- r[r$utslag == "bekräftad", ]
  if (!nrow(conf)) return(NULL)
  provs <- names(which(table(d$province) >= 100))
  do.call(rbind, lapply(seq_len(nrow(conf)), function(i) {
    y <- conf$y[i]; a <- conf$a[i]; b <- conf$b[i]
    sh <- cells(y, a, b)
    lopo <- vapply(provs, function(p) { g <- glm_inter(d[d$province != p, ], y, a, b); if (is.null(g)) NA else sign(g$beta) == sign(conf$beta[i]) }, NA)
    mv <- glm_inter(d[is.na(d$moved) | d$moved == 0, ], y, a, b)
    data.frame(y = y, a = a, b = b, p00 = sh[1], p10 = sh[2], p01 = sh[3], p11 = sh[4],
               lopo_holds = all(lopo, na.rm = TRUE), lopo_flips = paste(provs[!is.na(lopo) & !lopo], collapse = ","),
               unmoved_beta = if (is.null(mv)) NA else mv$beta, unmoved_p = if (is.null(mv)) NA else mv$p)
  }))
}

# --- run: A finds, B tests (main); B finds, A tests (secondary) ---
s1 <- stage1("A")
saveRDS(s1, file.path(dir, "steg1_A.rds"))
write_json(s1$cand, file.path(dir, "kandidater.json"), digits = NA, pretty = TRUE, dataframe = "rows")
writeLines(paste(digest(file = file.path(dir, "kandidater.json"), algo = "sha256"), " kandidater.json"), file.path(dir, "kandidater.sha256"))
cat("kandidater fryst:", nrow(s1$cand), "\n")
r <- if (!is.null(s1$cand) && nrow(s1$cand)) stage2(s1$cand, "B") else NULL
s3 <- if (!is.null(r)) stage3(r) else NULL
s1b <- stage1("B")
saveRDS(s1b, file.path(dir, "steg1_B.rds"))
rb <- if (!is.null(s1b$cand) && nrow(s1b$cand)) stage2(s1b$cand, "A") else NULL
res <- list(plan = "analysplaner/2026-11-01-upptacktsmotorn-v3-samspel.md", n_stones = nrow(d),
            n_proposals = nrow(s1$proposals), n_tested = if (is.null(s1$tested)) 0 else nrow(s1$tested),
            proposals_by_tool = as.list(table(s1$proposals$tool)), main = r, confirmed_details = s3,
            swapped = rb, n_proposals_swapped = nrow(s1b$proposals))
write_json(res, file.path(dir, "resultat.json"), digits = NA, pretty = TRUE, auto_unbox = TRUE, na = "null")
print(r[, intersect(c("y", "a", "b", "n", "beta", "p", "tools", "beta2", "p1", "holm", "utslag"), names(r))])
print(s3)
print(rb[, intersect(c("y", "a", "b", "beta", "p", "beta2", "holm", "utslag"), names(rb))])
