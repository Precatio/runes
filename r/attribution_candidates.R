# Attribueringsmodellens förslag för runstenar utan säker ristare, med full sannolikhetsfördelning, omkalibrerad som
# provningen visade (analysplaner/2026-11-04-attribuering-provad.md, fråga 5: p^a omnormerat, a = 1,7) och med spärren
# ”någon annan” (förstavalets okalibrerade sannolikhet under 0,33, grupperade sannolikheter).
#   Rscript r/attribution_candidates.R KORPUSMAPP UTFIL.csv
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(tidymodels); library(ranger) })
.a <- commandArgs(trailingOnly = TRUE); cdir <- .a[1]; out <- .a[2]
A_CAL <- 1.7; THR <- 0.33; NEAR_KM <- 25

M <- readRDS(file.path(cdir, "attribution_model.rds"))
d <- read_corpus(file.path(cdir, "corpus.csv"))
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
full <- d %>% left_join(geo %>% select(signum, x, y, water_km), by = "signum") %>% left_join(txt, by = "signum") %>%
  mutate(x_km = x / 1000, y_km = y / 1000)
v2_path <- file.path(cdir, "attribution_v2.csv")  # korsformen (src/attribution_features.py), om modellen har den
if (file.exists(v2_path)) {
  v2 <- read.csv(v2_path, encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE, na.strings = "")
  full <- full %>% left_join(v2[, c("signum", grep("^kors_", names(v2), value = TRUE))], by = "signum")
}
if (!is.null(M$cal_a)) A_CAL <- M$cal_a
if (!is.null(M$threshold)) THR <- M$threshold
prep_frame <- function(df, cols) {
  df <- df[, cols, drop = FALSE]
  for (col in intersect(M$nominal, cols)) {
    v <- as.character(df[[col]]); v[is.na(v) | !(v %in% M$train_levels[[col]])] <- "okänd"
    df[[col]] <- factor(v, levels = M$train_levels[[col]])
  }
  df
}
cand <- full %>% filter(is.na(carver), !is.na(x))
cand$near_km <- vapply(seq_len(nrow(cand)), function(i) min(sqrt((M$train_xy[, 1] - cand$x[i])^2 + (M$train_xy[, 2] - cand$y[i])^2)) / 1000, 0)
cand <- cand[cand$near_km <= NEAR_KM, ]
P <- as.matrix(predict(M$final, prep_frame(cand, M$cols), type = "prob"))
colnames(P) <- sub("^\\.pred_", "", colnames(P))
Q <- P^A_CAL; Q <- Q / rowSums(Q)
o1 <- max.col(Q, ties.method = "first")
o2 <- apply(Q, 1, function(r) order(-r)[2])
res <- data.frame(signum = cand$signum, province = cand$province, place = cand$place, parish = cand$parish,
                  lat = cand$lat, lon = cand$lon,
                  style = cand$style, near_km = round(cand$near_km, 1), n_words = cand$n_words,
                  rundata_uncertain = ifelse(is.na(cand$carvers_all), "", cand$carvers_all),
                  top = colnames(Q)[o1], p_cal = round(Q[cbind(seq_len(nrow(Q)), o1)], 3),
                  p_raw = round(P[cbind(seq_len(nrow(P)), o1)], 3),
                  second = colnames(Q)[o2], p2_cal = round(Q[cbind(seq_len(nrow(Q)), o2)], 3),
                  someone_else = apply(P, 1, max) < THR, stringsAsFactors = FALSE)
write.csv(res, out, row.names = FALSE, fileEncoding = "UTF-8")
cat(nrow(res), "stenar;", sum(!res$someone_else), "utan spärr;", sum(res$p_cal >= 0.7 & !res$someone_else), "med minst 70 %\n")
print(head(res[order(-res$p_cal), c("signum", "top", "p_cal", "p_raw", "second", "someone_else")], 15))
