# Samlad datering v3 enligt utdata/datering/analysplan_v3.md (låst 2026-10-27, SHA-256 45df1d5c…): sannolikheter per
# tidsskikt med en sannolikhetsskog, prövad med femfaldig korsvalidering grupperad per socken (3 upprepningar).
#   Rscript utdata/datering/datering_v3.R
suppressPackageStartupMessages({ library(ranger); library(sf); library(jsonlite) })
set.seed(2026)
FP <- "data/cache/r/corpus/76c2c44abc5d823a"
d <- read.csv(file.path(FP, "corpus.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
ch <- read.csv(file.path(FP, "chronology_stones.csv"), stringsAsFactors = FALSE)
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
ok <- !is.na(d$lat) & !is.na(d$lon)
xy <- matrix(NA, nrow(d), 2)
xy[ok, ] <- st_coordinates(st_transform(st_as_sf(d[ok, ], coords = c("lon", "lat"), crs = 4326), 3006)) / 1000
d$east <- ifelse(is.na(xy[, 1]), median(xy[, 1], na.rm = TRUE), xy[, 1])
d$north <- ifelse(is.na(xy[, 2]), median(xy[, 2], na.rm = TRUE), xy[, 2])
d$ser <- ch$score[match(d$signum, ch$signum)]
d$ser_has <- as.integer(!is.na(d$ser)); d$ser[is.na(d$ser)] <- 0
d$parish_g <- ifelse(is.na(d$parish), d$signum, paste(d$province, d$parish))
feat <- c(grep("^(trait_|cat_)", names(d), value = TRUE), "cross", "short_twig", "pagan", "signed", "n_words",
          "province", "east", "north", "ser", "ser_has")
for (f in feat) if (is.character(d[[f]]) || f == "province") d[[f]] <- factor(ifelse(is.na(d[[f]]), "saknas", d[[f]]))
for (f in feat) if (is.numeric(d[[f]])) d[[f]][is.na(d[[f]])] <- 0
dd <- d[!is.na(d$year), ]
LEV <- sort(unique(dd$year)); dd$cls <- factor(dd$year, levels = LEV)
mid <- as.numeric(LEV)

ece <- function(p, y) {  # expected calibration error of the top class probability, 10 equal bins
  top <- apply(p, 1, max); hit <- (max.col(p, ties.method = "first") == as.integer(y))
  bin <- cut(top, seq(0, 1, 0.1), include.lowest = TRUE)
  sum(tapply(seq_along(top), bin, function(i) length(i) * abs(mean(hit[i]) - mean(top[i]))), na.rm = TRUE) / length(top)
}
set80 <- function(p, y) {  # the most likely classes until they sum to 0.8: does the set hold the true class?
  sapply(seq_len(nrow(p)), function(i) { o <- order(-p[i, ]); k <- which(cumsum(p[i, o]) >= 0.8)[1]; as.integer(y[i]) %in% o[1:k] })
}
res_rep <- list(); P <- NULL
for (r in 1:3) {
  g <- unique(dd$parish_g); fold <- sample(rep(1:5, length.out = length(g))); names(fold) <- g
  f <- fold[dd$parish_g]
  prob <- matrix(NA, nrow(dd), length(LEV)); b1 <- rep(NA, nrow(dd))
  for (k in 1:5) {
    tr <- dd[f != k, ]; te <- f == k
    fit <- ranger(reformulate(feat, "cls"), tr, num.trees = 500, probability = TRUE, seed = 2026 + r * 10 + k)
    prob[te, ] <- predict(fit, dd[te, ])$predictions[, as.character(LEV)]
    pm <- tapply(tr$year, as.character(tr$province), median)
    b1[te] <- ifelse(as.character(dd$province[te]) %in% names(pm), pm[as.character(dd$province[te])], median(tr$year))
  }
  ey <- as.vector(prob %*% mid)
  res_rep[[r]] <- data.frame(signum = dd$signum, province = as.character(dd$province), year = dd$year, ey = ey, b1 = b1,
                             top = apply(prob, 1, max), hit = max.col(prob, ties.method = "first") == as.integer(dd$cls),
                             inset = set80(prob, dd$cls), rep = r)
  P <- rbind(P, prob)
}
cvd <- do.call(rbind, res_rep)
yy <- factor(rep(dd$year, 3), levels = LEV)
mae <- mean(abs(cvd$ey - cvd$year)); mae_b1 <- mean(abs(cvd$b1 - cvd$year))
E <- ece(P, yy)
up <- cvd[cvd$province == "U", ]
up$ser <- ch$est[match(up$signum, ch$signum)]
upr <- up[!is.na(up$ser), ]
U <- list(n = nrow(upr) / 3, mae_model = mean(abs(upr$ey - upr$year)), mae_seriation = mean(abs(upr$ser - upr$year)))
pass <- c(p1 = mae <= 0.85 * mae_b1, p2 = E <= 0.05, p3 = U$mae_model <= U$mae_seriation + 2)
res <- list(plan_sha256 = "45df1d5cbf2d7106", n = nrow(dd), mae = mae, mae_b1 = mae_b1, ece = E,
            top_accuracy = mean(cvd$hit), set80_coverage = mean(cvd$inset), uppland = U, pass = as.list(pass), passed = all(pass),
            reliability = lapply(split(cvd, cut(cvd$top, seq(0, 1, 0.1), include.lowest = TRUE)), function(x)
              list(n = nrow(x), mean_p = mean(x$top), accuracy = mean(x$hit))))
write_json(res, "utdata/datering/validering_v3.json", auto_unbox = TRUE, digits = 4, pretty = TRUE)
print(str(res[c("mae", "mae_b1", "ece", "top_accuracy", "set80_coverage", "uppland", "pass", "passed")]))

if (all(pass)) {
  fit <- ranger(reformulate(feat, "cls"), dd, num.trees = 500, probability = TRUE, seed = 2026)
  un <- d[is.na(d$year), ]
  p <- predict(fit, un)$predictions[, as.character(LEV)]
  out <- data.frame(signum = un$signum, province = un$province, expected = round(as.vector(p %*% mid)),
                    top = LEV[max.col(p, ties.method = "first")], p_top = round(apply(p, 1, max), 3))
  for (j in seq_along(LEV)) out[[paste0("p_", LEV[j])]] <- round(p[, j], 3)
  write.csv(out, "utdata/datering/dateringar.csv", row.names = FALSE)
  cat("Daterade", nrow(un), "stenar utan stilgrupp\n")
}
