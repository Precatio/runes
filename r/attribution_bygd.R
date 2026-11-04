# Bygdsmodellen – en andra bedömning för de små ristarna. Skogen utan koordinater (med korsformen) gånger ristarens
# bygd (Gauss 15 km kring hans säkra stenar) och tid (överlapp i stildatering), vikt w = 1,25 och kalibrering p^1,5 –
# variant K3 i analysplaner/2026-11-04-attribuering-v3.md, vald på sockenhalva 1. Den klarade INTE den låsta regeln
# (sämre log-förlust på halva 2) och används därför inte som appens modell, bara som en tydligt märkt andra bedömning:
# på halva 2 höjde den medel per ristare från 50 till 62 %.
#   Rscript r/attribution_bygd.R KORPUSMAPP UTFIL.csv
.args0 <- commandArgs(trailingOnly = TRUE)
cdir0 <- .args0[1]; out_csv <- .args0[2]
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
V2_LIB_ONLY <- TRUE
# attribution_v2.R läser KORPUSMAPP, DRAG_V2.csv och UTMAPP ur kommandoraden
commandArgs <- function(trailingOnly = FALSE) if (trailingOnly) c(cdir0, file.path(cdir0, "attribution_v2.csv"), tempdir()) else base::commandArgs(FALSE)
source(file.path(.here, "attribution_v2.R"))
rm(commandArgs)
W <- 1.25; A <- 1.5; NEAR_KM <- 25

cols <- setdiff(c(BASE, KORS), GEOC)
m <- fit_rf(train, cols)
cand <- full %>% filter(is.na(carver), !is.na(x_km))
for (col in nominal_all) cand[[col]] <- as.character(cand[[col]])
tx <- train[!is.na(train$x_km), ]
cand$near_km <- vapply(seq_len(nrow(cand)), function(i) min(sqrt((tx$x_km - cand$x_km[i])^2 + (tx$y_km - cand$y_km[i])^2)), 0)
cand <- cand[cand$near_km <= NEAR_KM, ]
P <- probs_for(m, cand, cols, lv)
dens <- sapply(lv, function(cn) {
  s <- tx[tx$carver == cn, ]
  vapply(seq_len(nrow(cand)), function(i) mean(exp(-((s$x_km - cand$x_km[i])^2 + (s$y_km - cand$y_km[i])^2) / (2 * BW_KM^2))) / (2 * pi * BW_KM^2) + 1e-9, 0)
})
tid <- sapply(lv, function(cn) {
  s <- train[train$carver == cn & !is.na(train$style_from), ]
  vapply(seq_len(nrow(cand)), function(i) {
    if (is.na(cand$style_from[i]) || !nrow(s)) return(1)
    (sum(s$style_to >= cand$style_from[i] & s$style_from <= cand$style_to[i]) + 0.5) / (nrow(s) + 1)
  }, 0)
})
Q <- P * dens^W * tid^W; Q <- Q / pmax(rowSums(Q), 1e-300)
Q <- Q^A; Q <- Q / rowSums(Q)
o1 <- max.col(Q, ties.method = "first"); o2 <- apply(Q, 1, function(r) order(-r)[2])
res <- data.frame(signum = cand$signum, place = cand$place, parish = cand$parish, lat = cand$lat, lon = cand$lon,
                  style = cand$style, near_km = round(cand$near_km, 1),
                  rundata_uncertain = ifelse(is.na(cand$carvers_all), "", cand$carvers_all),
                  top = lv[o1], p_cal = round(Q[cbind(seq_len(nrow(Q)), o1)], 3), second = lv[o2],
                  p2_cal = round(Q[cbind(seq_len(nrow(Q)), o2)], 3), stringsAsFactors = FALSE)
write.csv(res, out_csv, row.names = FALSE, fileEncoding = "UTF-8")
cat(nrow(res), "stenar; förstaval per ristare:\n"); print(sort(table(res$top), decreasing = TRUE))
