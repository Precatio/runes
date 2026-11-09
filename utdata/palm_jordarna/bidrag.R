# Palms jordar, efter provet (beskrivande, inte i den låsta planen 85a70fa3): är det leran, vattnet eller bygden?
# Samma rutor och samma modell som analys.R. (1) Effekten av varje faktor i den fulla modellen, från den 25:e till den
# 75:e percentilen (jämförbara steg), med klusterrobusta 95 %-intervall; (2) hur mycket varje faktor ensam ändrar den
# andra faktorns effekt (lera med och utan vatten, vatten med och utan lera); (3) hur mycket av skillnaden mellan
# Mälardalen och Götalands inland som varje faktor förklarar, fördelat rättvist över alla ordningar (Shapley), eftersom
# faktorerna hänger ihop. Skriver bidrag.json.
#   Rscript utdata/palm_jordarna/bidrag.R
suppressMessages({library(MASS); library(sandwich); library(jsonlite)})
HERE <- "utdata/palm_jordarna"
MALAR <- c("attundaland", "tiundaland", "fjadrundaland", "roden", "U", "Sö", "Vs")
GOTA <- c("Vg", "Sm", "aspeland", "finnveden", "handbord", "kinda", "mo", "more", "njudung", "sevede", "tjust", "tveta",
          "varend", "vedbo", "vista")
d <- read.csv(file.path(HERE, "rutor_2000.csv"))
d$region <- relevel(factor(d$region), ref = "Sö")
d$lgrave <- log1p(d$gravefields)
d$ldist <- log(d$dist_water_km + 0.5)
fit <- function(form) glm.nb(form, data = d, control = glm.control(maxit = 100))
contrast <- function(m) {  # as analys.R: log ratio of cell-weighted mean rates, Mälar lands vs Götaland inland
  cf <- coef(m); cf[is.na(cf)] <- 0
  lv <- levels(d$region); n <- table(d$region)
  grp <- function(G) {
    L <- intersect(G, lv); w <- as.numeric(n[L]) / sum(n[L])
    b <- vapply(L, function(l) { nm <- paste0("region", l); if (nm %in% names(cf)) unname(cf[nm]) else 0 }, 0)
    log(sum(w * exp(b)))
  }
  grp(MALAR) - grp(GOTA)
}

# (1) comparable steps: 25th → 75th percentile of each factor (for the distance: far → near, so all ratios read "more")
m <- fit(stones ~ clay + lgrave + ldist + region + offset(log(land_km2)))
V <- vcovCL(m, cluster = d$block)
step <- function(name, lo, hi) {
  b <- coef(m)[[name]]; se <- sqrt(V[name, name]); delta <- unname(hi - lo)
  ci <- sort(exp(c(b - 1.96 * se, b + 1.96 * se) * delta))
  list(ratio = exp(b * delta), lo95 = ci[1], hi95 = ci[2])
}
qc <- quantile(d$clay, c(.25, .75)); qg <- quantile(d$gravefields, c(.25, .75)); qd <- quantile(d$dist_water_km, c(.25, .75))
steps <- list(
  clay = c(step("clay", qc[[1]], qc[[2]]), from = qc[[1]], to = qc[[2]]),
  gravefields = c(step("lgrave", log1p(qg[[1]]), log1p(qg[[2]])), from = qg[[1]], to = qg[[2]]),
  water_near = c(step("ldist", log(qd[[2]] + .5), log(qd[[1]] + .5)), from_km = qd[[2]], to_km = qd[[1]]))

# (2) does one stand in for the other?
b_clay_with <- coef(m)[["clay"]]
b_clay_without <- coef(fit(stones ~ clay + lgrave + region + offset(log(land_km2))))[["clay"]]
b_dist_with <- coef(m)[["ldist"]]
b_dist_without <- coef(fit(stones ~ lgrave + ldist + region + offset(log(land_km2))))[["ldist"]]
overlap <- list(cor_clay_logdist = cor(d$clay, d$ldist),
                clay_all_or_nothing_with_water = exp(b_clay_with), clay_all_or_nothing_without_water = exp(b_clay_without),
                water_per_doubling_with_clay = 2^b_dist_with, water_per_doubling_without_clay = 2^b_dist_without)

# (3) Shapley shares of the Mälar–Götaland gap (log scale)
F <- c("clay", "lgrave", "ldist")
key <- function(S) if (length(S)) paste(sort(S), collapse = "+") else "ingen"
val <- list()
for (k in 0:3) for (S in combn(F, k, simplify = FALSE)) {
  form <- as.formula(paste("stones ~", paste(c(S, "region", "offset(log(land_km2))"), collapse = " + ")))
  val[[key(S)]] <- contrast(fit(form))
}
total <- val[[key(character(0))]]
shap <- setNames(numeric(3), F)
for (f in F) {
  others <- setdiff(F, f)
  for (k in 0:2) for (S in combn(others, k, simplify = FALSE)) {
    w <- factorial(length(S)) * factorial(length(F) - length(S) - 1) / factorial(length(F))
    shap[f] <- shap[f] + w * (val[[key(S)]] - val[[key(c(S, f))]])
  }
}
gap <- list(unadjusted_ratio = exp(total), adjusted_ratio = exp(val[[key(F)]]),
            explained_share_total = 1 - val[[key(F)]] / total,
            shapley_share = as.list(shap / total), models = lapply(val, exp))
out <- list(note = "Efter provet, beskrivande (inte i den låsta planen 85a70fa3); samma rutor och modell som analys.R",
            cells = nrow(d), steps = steps, overlap = overlap, gap = gap)
write_json(out, file.path(HERE, "bidrag.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
cat(sprintf("Steg 25→75 %%: lera %.2f [%.2f–%.2f] (%.0f→%.0f %%), gravfält %.2f [%.2f–%.2f] (%g→%g), nära vatten %.2f [%.2f–%.2f] (%.1f→%.1f km)\n",
            steps$clay$ratio, steps$clay$lo95, steps$clay$hi95, 100 * qc[1], 100 * qc[2],
            steps$gravefields$ratio, steps$gravefields$lo95, steps$gravefields$hi95, qg[1], qg[2],
            steps$water_near$ratio, steps$water_near$lo95, steps$water_near$hi95, qd[2], qd[1]))
cat(sprintf("Överlapp: r(lera, log avstånd) %.2f; lera ingen→bara med vatten %.2f, utan %.2f; vatten per fördubbling med lera %.2f, utan %.2f\n",
            overlap$cor_clay_logdist, overlap$clay_all_or_nothing_with_water, overlap$clay_all_or_nothing_without_water,
            overlap$water_per_doubling_with_clay, overlap$water_per_doubling_without_clay))
cat(sprintf("Mälar–Göta: %.2f× → %.2f×, förklarat %.0f %%; Shapley: lera %.0f %%, gravfält %.0f %%, vatten %.0f %%\n",
            gap$unadjusted_ratio, gap$adjusted_ratio, 100 * gap$explained_share_total,
            100 * shap[["clay"]] / total, 100 * shap[["lgrave"]] / total, 100 * shap[["ldist"]] / total))
