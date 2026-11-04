# Attribueringsmodellen version 3 enligt analysplaner/2026-11-04-attribuering-v3.md: kalibrerad ”samma hand”, ristarens
# bygd och tid, och en blandning – allt som väljs väljs på sockenhalva 1, besluten fattas på halva 2.
#   Rscript r/attribution_v3.R KORPUSMAPP DRAG_V2.csv UTMAPP     (läser utdata/attribuering_v2/oof_samma_hand.rds)
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
V2_LIB_ONLY <- TRUE
source(file.path(.here, "attribution_v2.R"))
V2DIR <- file.path(dirname(out), "attribuering_v2")

h1rows <- function(R) R$parish %in% HALF1
calib <- function(R, grid = seq(0.5, 15, 0.05)) {       # potens vald på halva 1 (log-förlust), använd på allt
  h <- h1rows(R)
  ll <- vapply(grid, function(a) llf(powcal(R$P[h], a), R$carver[h]), 0)
  a <- grid[which.min(ll)]
  R$P <- I(powcal(R$P, a)); attr(R, "a") <- a; attr(R, "ll_h1") <- min(ll); R
}
priors <- lapply(seq_along(SPL), function(k) {
  tr <- train[SPL[[k]]$tr, ]; te <- train[SPL[[k]]$te, ]
  dens <- sapply(lv, function(cn) {
    s <- tr[tr$carver == cn & !is.na(tr$x_km), ]
    vapply(seq_len(nrow(te)), function(i) {
      if (is.na(te$x_km[i]) || !nrow(s)) return(1)
      mean(exp(-((s$x_km - te$x_km[i])^2 + (s$y_km - te$y_km[i])^2) / (2 * BW_KM^2))) / (2 * pi * BW_KM^2) + 1e-9
    }, 0)
  })
  tid <- sapply(lv, function(cn) {
    s <- tr[tr$carver == cn & !is.na(tr$style_from), ]
    vapply(seq_len(nrow(te)), function(i) {
      if (is.na(te$style_from[i]) || !nrow(s)) return(1)
      (sum(s$style_to >= te$style_from[i] & s$style_from <= te$style_to[i]) + 0.5) / (nrow(s) + 1)
    }, 0)
  })
  list(dens = matrix(dens, nrow = nrow(te), dimnames = list(NULL, lv)), tid = matrix(tid, nrow = nrow(te), dimnames = list(NULL, lv)))
})
mats <- function(R) lapply(seq_along(SPL), function(k) { r <- R[R$fold == k, ]; r <- r[order(match(r$.row, SPL[[k]]$te)), ]
  M <- do.call(rbind, lapply(r$P, function(p) p[lv])); colnames(M) <- lv; M })
with_prior <- function(Ms, w) lapply(seq_along(Ms), function(k) {
  Q <- Ms[[k]] * priors[[k]]$dens^w * priors[[k]]$tid^w; Q <- Q / pmax(rowSums(Q), 1e-300); colnames(Q) <- lv; Q })
best_w <- function(Ms, grid = seq(0, 2, 0.25)) {
  fits <- lapply(grid, function(w) calib(rows_from(with_prior(Ms, w))))
  i <- which.min(vapply(fits, function(R) attr(R, "ll_h1"), 0))
  R <- fits[[i]]; attr(R, "w") <- grid[i]; R
}

log_("K0 A+1")
K0 <- calib(run_rf(c(BASE, KORS), "A+1"))
R4 <- readRDS(file.path(V2DIR, "oof_samma_hand.rds"))$R4
log_("K1 samma hand, kalibrerad")
K1 <- calib(R4)
log_("K2 samma hand × bygd och tid")
K2 <- best_w(mats(R4))
log_("K3 skog utan koordinater × bygd och tid")
R3rf <- run_rf(setdiff(c(BASE, KORS), GEOC), "A+1 utan koordinater")
K3 <- best_w(mats(R3rf))
log_("K4 blandning K0 + K1")
M0 <- mats(K0); M1 <- mats(K1)
mix <- function(v) rows_from(lapply(seq_along(M0), function(k) (1 - v) * M0[[k]] + v * M1[[k]]))
vs <- seq(0, 1, 0.25)
vl <- vapply(vs, function(v) { R <- mix(v); h <- h1rows(R); llf(R$P[h], R$carver[h]) }, 0)
K4 <- mix(vs[which.min(vl)]); attr(K4, "v") <- vs[which.min(vl)]

h2 <- function(R) R[!h1rows(R), ]
evalv <- function(R, name) {
  a <- per_stone(h2(R)); b <- per_stone(h2(K0)); s <- a[a$signed == 1, ]; sb <- b[b$signed == 1, ]
  d1 <- boot_diff(a, b, f_top1); d2 <- boot_diff(a, b, f_macro)
  full <- per_stone(R)
  list(name = name, a = attr(R, "a"), w = attr(R, "w"), v = attr(R, "v"),
       half2 = list(n_signed = nrow(s), top1 = round(mean(s$ok), 4), macro = round(f_macro(s), 4), log_loss = round(mean(s$ll), 4),
                    d_top1 = round(d1, 4), d_macro = round(d2, 4), log_loss_not_worse = mean(s$ll) <= mean(sb$ll) + 1e-9),
       all = list(top1_signed = round(mean(full$ok[full$signed == 1]), 4), macro_signed = round(f_macro(full[full$signed == 1, ]), 4),
                  top1_attributed = round(mean(full$ok[full$signed == 0]), 4)),
       per_carver = full[full$signed == 1, ] %>% group_by(carver) %>% summarise(n = n(), top1 = round(mean(ok), 3), .groups = "drop"))
}
V <- list(K0 = evalv(K0, "K0 A+1"), K1 = evalv(K1, "K1 samma hand"), K2 = evalv(K2, "K2 samma hand × bygd och tid"),
          K3 = evalv(K3, "K3 skog × bygd och tid"), K4 = evalv(K4, "K4 blandning"))
ok <- names(V)[-1][vapply(names(V)[-1], function(k) { h <- V[[k]]$half2; h$d_top1[["est"]] > 0 && h$d_macro[["est"]] > 0 && h$log_loss_not_worse }, TRUE)]
chosen <- if (length(ok)) ok[which.min(vapply(ok, function(k) V[[k]]$half2$log_loss, 0))] else "K0"
proven <- chosen != "K0" && V[[chosen]]$half2$d_top1[["lo"]] > 0
for (k in names(V)) { h <- V[[k]]$half2; log_(V[[k]]$name, sprintf("halva 2: top1 %.3f (%+.3f [%.3f, %.3f]) macro %.3f (%+.3f) ll %.3f | hela: top1 %.3f macro %.3f attribuerade %.3f",
  h$top1, h$d_top1[["est"]], h$d_top1[["lo"]], h$d_top1[["hi"]], h$macro, h$d_macro[["est"]], h$log_loss, V[[k]]$all$top1_signed, V[[k]]$all$macro_signed, V[[k]]$all$top1_attributed)) }
log_("godtagna:", paste(ok, collapse = ", "), "· vald:", chosen, "· påvisad:", proven)
saveRDS(list(K0 = K0, K1 = K1, K2 = K2, K3 = K3, K4 = K4), file.path(out, "oof_v3.rds"))
write_json(list(plan = "analysplaner/2026-11-04-attribuering-v3.md", varianter = V, godtagna = ok, vald = chosen, pavisad = proven),
           file.path(out, "resultat.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
