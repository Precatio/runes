# Lerkanten med stenarna i grupp som enhet (analysplaner/2026-11-26-lerkanten-grupper.md): K2 och K3 med klusterrobust
# standardfel över 1 km-grupperna, och beskrivande en slumpvis sten per grupp (1 000 dragningar, frö 20261126).
suppressMessages({library(survival); library(jsonlite)})
here <- "utdata/palm_jordarna"
d <- read.csv(file.path(here, "kontroller_punkter.csv"))
g <- read.csv(file.path(here, "grupper_lerkant.csv"))
d$grupp <- g$grupp[match(d$stone, g$stone)]
stopifnot(!any(is.na(d$grupp)))
robust <- function(f) {
  m <- clogit(f, data = d, method = "efron")
  s <- summary(m)$coefficients
  z <- s["edge", "coef"] / s["edge", "robust se"]
  list(coef = s["edge", "coef"], or = exp(s["edge", "coef"]), robust_se = s["edge", "robust se"],
       naiv_se = s["edge", "se(coef)"], p_one_sided_pos = pnorm(z, lower.tail = FALSE))
}
gk2 <- robust(obs ~ edge + sand200 + strata(stone) + cluster(grupp))
gk3 <- robust(obs ~ edge + sand200 + peat200 + strata(stone) + cluster(grupp))
set.seed(20261126)
stones_by_group <- split(unique(d$stone), g$grupp[match(unique(d$stone), g$stone)])
draws <- function(f) {
  r <- t(sapply(1:1000, function(i) {
    pick <- vapply(stones_by_group, function(v) if (length(v) == 1) v else sample(v, 1), "")
    m <- clogit(f, data = d[d$stone %in% pick, ])
    s <- summary(m)$coefficients
    c(s["edge", "coef"], pnorm(s["edge", "coef"] / s["edge", "se(coef)"], lower.tail = FALSE))
  }))
  list(median_coef = median(r[, 1]), median_or = exp(median(r[, 1])), andel_p_under_005 = mean(r[, 2] < 0.05))
}
res <- list(
  plan = "2026-11-26-lerkanten-grupper.md", stenar = length(unique(d$stone)), grupper = length(stones_by_group),
  G_K2 = gk2, G_K2_holds = gk2$coef > 0 && gk2$p_one_sided_pos < 0.05,
  G_K3 = gk3, G_K3_holds = gk3$coef > 0 && gk3$p_one_sided_pos < 0.05,
  en_sten_per_grupp_K2 = draws(obs ~ edge + sand200 + strata(stone)),
  en_sten_per_grupp_K3 = draws(obs ~ edge + sand200 + peat200 + strata(stone))
)
write_json(res, file.path(here, "grupper.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
print(toJSON(res, auto_unbox = TRUE, pretty = TRUE, digits = 4))
