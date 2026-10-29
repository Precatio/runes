# Mästarmodellen, steg 3 (analysplaner/2026-10-29-en-och-samma-mastare.md, del 3): sannolikheten att en grupp är en hand
# (renhet = 1) eller en mästare med enstaka avvikare (renhet >= 0,75), kalibrerad på grupper bildade som i r/anonymous.R
# på kända ristare i hållet-utanför-läge.
#   Rscript utdata/okanda_ristare/mastare_modell.R
suppressPackageStartupMessages(library(jsonlite))
OUT <- "utdata/okanda_ristare"
set.seed(2026)
g <- merge(read.csv(file.path(OUT, "mastare_grupper.csv")), read.csv(file.path(OUT, "mastare_drag.csv")), by = "group")
cal <- g[g$kind == "kalibrering", ]
span_med <- median(cal$span, na.rm = TRUE)
prep <- function(x) {
  x$log_n <- log(x$n)
  x$span_f <- ifelse(is.na(x$span), span_med, x$span)
  for (k in c("pct_rock", "pct_names", "pct_rare")) x[[k]] <- ifelse(is.na(x[[k]]), 0.5, x[[k]])
  x
}
g <- prep(g); cal <- prep(cal); cand <- g[g$kind == "kandidat", ]
cal$pure <- as.integer(cal$purity >= 1 - 1e-9)
cal$dom <- as.integer(cal$purity >= 0.75)
F_FULL <- ~ log_n + g_mean + gnt_mean + spread_km + span_f + pct_rock + pct_names + pct_rare
F_HAND <- ~ log_n + g_mean + gnt_mean + spread_km
fit <- function(y, f, d) suppressWarnings(glm(update(f, paste(y, "~ .")), data = d, family = binomial))
auc <- function(p, y) { r <- rank(p); n1 <- sum(y == 1); n0 <- sum(y == 0); (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0) }
calib <- function(p, y) {
  b <- cut(p, unique(quantile(p, seq(0, 1, 0.1))), include.lowest = TRUE)
  data.frame(predicted = tapply(p, b, mean), observed = tapply(y, b, mean), n = as.vector(table(b)))
}

validation <- list()
for (y in c("pure", "dom")) for (nm in c("full", "hand")) {
  f <- if (nm == "full") F_FULL else F_HAND
  tr <- cal[cal$rep <= 25, ]; te <- cal[cal$rep > 25, ]
  p <- predict(fit(y, f, tr), te, type = "response")
  validation[[paste(y, nm, sep = "_")]] <- list(auc = auc(p, te[[y]]), brier = mean((p - te[[y]])^2),
                                                brier_base = mean((mean(tr[[y]]) - te[[y]])^2),
                                                calibration = calib(p, te[[y]]))
}

reps <- unique(cal$rep)
est <- list()
for (y in c("pure", "dom")) {
  m <- fit(y, F_FULL, cal)
  p_hat <- predict(m, cand, type = "response")
  boot <- replicate(1000, {
    rs <- sample(reps, replace = TRUE)
    d <- do.call(rbind, lapply(rs, function(r) cal[cal$rep == r, ]))
    predict(fit(y, F_FULL, d), cand, type = "response")
  })
  hand <- predict(fit(y, F_HAND, cal), cand, type = "response")
  est[[y]] <- list(base_rate = mean(cal[[y]]), coef = as.list(coef(m)),
                   candidates = lapply(seq_len(nrow(cand)), function(i) list(
                     candidate = cand$candidate[i], p = unname(p_hat[i]),
                     ci = unname(quantile(boot[i, ], c(0.025, 0.975))), p_hand_only = unname(hand[i]))))
}
vars <- c("log_n", "g_mean", "gnt_mean", "spread_km", "span_f", "pct_rock", "pct_names", "pct_rare")
outside <- lapply(seq_len(nrow(cand)), function(i) {
  o <- vars[vapply(vars, function(v) {
    q <- quantile(cal[[v]], c(0.01, 0.99)); cand[[v]][i] < q[1] || cand[[v]][i] > q[2] }, TRUE)]
  list(candidate = cand$candidate[i], outside = o)
})
features <- cand[, c("candidate", "n", vars)]
write_json(list(n_calibration = nrow(cal), n_reps = length(reps), validation = validation, estimates = est,
                outside = outside, candidate_features = features),
           file.path(OUT, "mastare_modell.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
for (y in c("pure", "dom")) {
  cat(y, "grundfrekvens", round(est[[y]]$base_rate, 3), "\n")
  for (c in est[[y]]$candidates) cat("  ", c$candidate, round(c$p, 3), round(c$ci, 3), "hand:", round(c$p_hand_only, 3), "\n")
}
for (k in names(validation)) cat(k, "AUC", round(validation[[k]]$auc, 3), "Brier", round(validation[[k]]$brier, 3),
                                 "bas", round(validation[[k]]$brier_base, 3), "\n")
