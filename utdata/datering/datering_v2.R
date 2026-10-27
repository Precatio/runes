# Samlad datering v2 enligt utdata/datering/analysplan_v2.md (låst 2026-10-27, SHA-256 84256b0f…): som v1 men med
# konform kvantilregression för intervallen. v1: utdata/datering/datering.R
# (v1-rubrik:) Samlad datering enligt utdata/datering/analysplan.md (låst 2026-10-27, SHA-256 bb06d292…): kvantilregressionsskog,
# femfaldig korsvalidering grupperad per socken, upprepad 3 gånger; jämförd med landskapets median (B1) och seriationen
# i Uppland (B2). M2 (med sannolikhetsmodellens språkdatering) redovisas bara.
#   Rscript utdata/datering/datering.R
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

# M2: the text model's out-of-fold epoch likelihoods as shares (dated inscriptions only)
rl <- fromJSON("utdata/Malt/runlm_datering.json")$rows
ll <- as.matrix(rl$ll[, c("800", "900", "1000", "1100")])
post <- exp(ll - apply(ll, 1, max)); post <- post / rowSums(post)
m2 <- data.frame(signum = rl$sig, lm800 = post[, 1], lm900 = post[, 2], lm1000 = post[, 3], lm1100 = post[, 4])
d <- merge(d, m2, by = "signum", all.x = TRUE)
d$lm_has <- as.integer(!is.na(d$lm1000))
for (f in c("lm800", "lm900", "lm1000", "lm1100")) d[[f]][is.na(d[[f]])] <- 0
feat2 <- c(feat, "lm800", "lm900", "lm1000", "lm1100", "lm_has")

dd <- d[!is.na(d$year), ]
cat("Daterade stenar:", nrow(dd), " odaterade:", sum(is.na(d$year)), "\n")
# Conformalized quantile regression: train on 70 % of the parishes, the 80th percentile of max(q10 - y, y - q90) on the
# other 30 % widens or narrows the interval
conformal <- function(tr, features, seed) {
  set.seed(seed)
  g <- unique(tr$parish_g); cal <- sample(g, round(0.3 * length(g)))
  a <- tr[!tr$parish_g %in% cal, ]; b <- tr[tr$parish_g %in% cal, ]
  fit <- ranger(reformulate(features, "year"), a, num.trees = 500, quantreg = TRUE, seed = seed)
  q <- predict(fit, b, type = "quantiles", quantiles = c(0.1, 0.9))$predictions
  E <- pmax(q[, 1] - b$year, b$year - q[, 2])
  unname(quantile(E, 0.8 * (1 + 1 / nrow(b)), type = 1))
}
cv <- function(features, reps = 3) {
  out <- list()
  for (r in seq_len(reps)) {
    g <- unique(dd$parish_g); fold <- sample(rep(1:5, length.out = length(g))); names(fold) <- g
    f <- fold[dd$parish_g]
    pred <- data.frame(signum = dd$signum, year = dd$year, province = as.character(dd$province), med = NA, lo = NA, hi = NA, b1 = NA, rep = r, Q = NA)
    for (k in 1:5) {
      tr <- dd[f != k, ]; te <- f == k
      fit <- ranger(reformulate(features, "year"), tr, num.trees = 500, quantreg = TRUE, seed = 2026 + r * 10 + k)
      q <- predict(fit, dd[te, ], type = "quantiles", quantiles = c(0.1, 0.5, 0.9))$predictions
      Q <- conformal(tr, features, 2026 + r * 10 + k)
      pred$lo[te] <- q[, 1] - Q; pred$med[te] <- q[, 2]; pred$hi[te] <- q[, 3] + Q; pred$Q[te] <- Q
      pm <- tapply(tr$year, as.character(tr$province), median)
      pred$b1[te] <- ifelse(as.character(dd$province[te]) %in% names(pm), pm[as.character(dd$province[te])], median(tr$year))
    }
    out[[r]] <- pred
  }
  do.call(rbind, out)
}
summ <- function(p) list(mae = mean(abs(p$med - p$year)), mae_b1 = mean(abs(p$b1 - p$year)),
                         coverage = mean(p$year >= p$lo & p$year <= p$hi), width = mean(p$hi - p$lo), n = nrow(p) / 3)
p1 <- cv(feat); p2 <- cv(feat2)
s1 <- summ(p1); s2 <- summ(p2)
up <- p1[p1$province == "U", ]
chU <- ch[ch$signum %in% up$signum, ]
up$ser <- chU$est[match(up$signum, chU$signum)]
upr <- up[!is.na(up$ser), ]
uppland <- list(n = nrow(upr) / 3, mae_model = mean(abs(upr$med - upr$year)), mae_seriation = mean(abs(upr$ser - upr$year)))
pass <- c(p1 = s1$mae <= 0.85 * s1$mae_b1, p2 = s1$coverage >= 0.75 && s1$coverage <= 0.88,
          p3 = uppland$mae_model <= uppland$mae_seriation + 2)
res <- list(plan_sha256 = "84256b0fe76d8626", Q_mean = mean(p1$Q), M1 = s1, M2 = s2, uppland = uppland, pass = as.list(pass), passed = all(pass),
            by_province = lapply(split(p1, p1$province), function(x) list(n = nrow(x) / 3, mae = mean(abs(x$med - x$year)),
                                                                          mae_b1 = mean(abs(x$b1 - x$year)),
                                                                          coverage = mean(x$year >= x$lo & x$year <= x$hi))))
write_json(res, "utdata/datering/validering_v2.json", auto_unbox = TRUE, digits = 4, pretty = TRUE)
print(str(res[c("M1", "M2", "uppland", "pass", "passed")]))

if (all(pass)) {  # the plan's step after a pass: train on all dated stones and date the undated ones
  fit <- ranger(reformulate(feat, "year"), dd, num.trees = 500, quantreg = TRUE, seed = 2026)
  Q <- conformal(dd, feat, 2026)
  un <- d[is.na(d$year), ]
  q <- predict(fit, un, type = "quantiles", quantiles = c(0.1, 0.5, 0.9))$predictions
  write.csv(data.frame(signum = un$signum, province = un$province, lo = round(q[, 1] - Q), med = round(q[, 2]), hi = round(q[, 3] + Q)),
            "utdata/datering/dateringar.csv", row.names = FALSE)
  cat("Daterade", nrow(un), "stenar utan stilgrupp\n")
}
