# Kultplatsernas landskap: upptäckt i A, bekräftelse i B (låst plan analysplaner/2026-11-17-kultplatsernas-landskap.md,
# sha256 55a61e0d). Läser landskap_drag.csv (landskap.py), skriver kandidater_A.json (+ .sha256) innan B räknas, och
# resultat_landskap.json.
#   Rscript utdata/asatro/landskap.R
suppressPackageStartupMessages(library(jsonlite))
here <- local({f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)); dirname(normalizePath(f[1]))})
plan <- file.path(here, "..", "..", "analysplaner", "2026-11-17-kultplatsernas-landskap.md")
sha <- system2("shasum", c("-a", "256", shQuote(plan)), stdout = TRUE)
stopifnot(startsWith(sha, "55a61e0d"))
d <- read.csv(file.path(here, "landskap_drag.csv"), fileEncoding = "UTF-8")
d$lnn <- log(d$nn_km)
for (v in c("gravfalt", "hog", "fardvag")) d[[v]] <- log1p(d[[v]])
FEATURES <- c("gravfalt", "hog", "fornborg", "hamn", "fardvag", "bro", "kyrka", "central", "ting",
              "lera", "sand", "moran", "berg")

fit <- function(dd, v, y = "cult") {
  dd <- dd[!is.na(dd[[v]]), ]
  dd <- dd[dd$land %in% names(which(tapply(dd[[y]], dd$land, sum) > 0)), ]  # provinces with at least one case
  if (length(unique(dd[[v]])) < 2) return(list(b = NA, p = NA, n = nrow(dd)))
  f <- as.formula(paste(y, "~", v, "+ factor(land) + lnn"))
  m <- suppressWarnings(glm(f, data = dd, family = binomial))
  s <- summary(m)$coefficients
  if (!v %in% rownames(s)) return(list(b = NA, p = NA, n = nrow(dd)))
  list(b = unname(s[v, 1]), se = unname(s[v, 2]), p = unname(s[v, 4]), n = nrow(dd), cases = sum(dd[[y]]))
}

run <- function(disc, conf, tag) {
  A <- d[d$half == disc, ]
  B <- d[d$half == conf, ]
  scan <- lapply(FEATURES, function(v) c(feature = v, fit(A, v)))
  cand <- Filter(function(x) !is.na(x$p) && x$p < 0.05, scan)
  frozen <- toJSON(lapply(cand, function(x) list(feature = x$feature, b = x$b)), auto_unbox = TRUE, digits = NA)
  f <- file.path(here, paste0("kandidater_", tag, ".json"))
  writeLines(frozen, f)
  writeLines(system2("shasum", c("-a", "256", shQuote(f)), stdout = TRUE), paste0(f, ".sha256"))
  conf_res <- lapply(cand, function(x) {
    r <- fit(B, x$feature)
    p1 <- if (is.na(r$b)) NA else if (sign(r$b) == sign(x$b)) r$p / 2 else 1 - r$p / 2
    sure <- fit(d, x$feature, "cult_saker")
    list(feature = x$feature, b_A = x$b, p_A = x$p, b_B = r$b, p_B_ensidig = p1, n_B = r$n,
      b_saker = sure$b, saker_samma_riktning = !is.na(sure$b) && sign(sure$b) == sign(x$b))
  })
  if (length(conf_res)) {
    ph <- p.adjust(sapply(conf_res, function(x) x$p_B_ensidig), "holm")
    for (i in seq_along(conf_res)) {
      conf_res[[i]]$p_holm <- ph[i]
      conf_res[[i]]$bekraftat <- !is.na(ph[i]) && ph[i] < 0.05 && isTRUE(conf_res[[i]]$saker_samma_riktning)
    }
  }
  list(upptackt = disc, bekraftelse = conf, skanning = scan, kandidater = conf_res)
}

res <- list(sha = substr(sha, 1, 8), socknar = nrow(d), kultsocknar = sum(d$cult),
            huvud = run("A", "B", "A"), bytta = run("B", "A", "B"))
write_json(res, file.path(here, "resultat_landskap.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
show <- function(r) {
  cat("\n== upptäckt", r$upptackt, "\n")
  for (x in r$skanning) cat(sprintf("  %-9s b=%7.3f p=%.4f\n", x$feature, ifelse(is.na(x$b), NA, x$b), ifelse(is.na(x$p), NA, x$p)))
  for (x in r$kandidater) cat(sprintf("  KANDIDAT %-9s B: b=%.3f p1=%.4f holm=%.4f säker=%s bekräftat=%s\n",
                                      x$feature, x$b_B, x$p_B_ensidig, x$p_holm, x$saker_samma_riktning, x$bekraftat))
}
show(res$huvud); show(res$bytta)
