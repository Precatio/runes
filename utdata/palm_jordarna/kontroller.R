# Lerkantens kontroller K2 och K3 enligt den låsta planen analysplaner/2026-11-10-lerkanten-kontroller.md: varje sten mot
# sina 50 slumpvisa platser i samma 2 km-ruta, villkorad logistisk regression med stenen som stratum (survival::clogit).
# K2: kanten (inom 200 m från lera och silt, inte på den) + inom 200 m från sand och grus. K3: + inom 200 m från torv och
# gyttja. Håller om kantens koefficient > 0, ensidigt p < 0,05. Läser kontroller_punkter.csv (kontroller.py).
suppressMessages({library(survival); library(jsonlite)})
here <- "utdata/palm_jordarna"
d <- read.csv(file.path(here, "kontroller_punkter.csv"))
fit <- function(f) {
  m <- clogit(f, data = d)
  s <- summary(m)$coefficients
  lapply(setNames(rownames(s), rownames(s)), function(v) list(
    coef = s[v, "coef"], or = s[v, "exp(coef)"], se = s[v, "se(coef)"], z = s[v, "z"],
    p_one_sided_pos = pnorm(s[v, "z"], lower.tail = FALSE)))
}
k0 <- fit(obs ~ edge + strata(stone))
k2 <- fit(obs ~ edge + sand200 + strata(stone))
k3 <- fit(obs ~ edge + sand200 + peat200 + strata(stone))
res <- list(
  K0_bara_kanten = k0,
  K2_med_sand_och_grus = k2, K2_holds = k2$edge$coef > 0 && k2$edge$p_one_sided_pos < 0.05,
  K3_med_torv_och_gyttja = k3, K3_holds = k3$edge$coef > 0 && k3$edge$p_one_sided_pos < 0.05,
  andelar = list(stenar = colMeans(d[d$obs == 1, c("edge", "sand200", "peat200", "on_clay")]),
                 slump = colMeans(d[d$obs == 0, c("edge", "sand200", "peat200", "on_clay")])),
  n_stenar = sum(d$obs), n_platser = nrow(d))
write_json(res, file.path(here, "kontroller_R.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
str(res[c("K2_holds", "K3_holds")]); print(round(sapply(k3, function(x) c(OR = x$or, p = x$p_one_sided_pos)), 4)); print(res$andelar)
