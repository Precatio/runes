# Palms jordar: P0–P3 och robustheten enligt analysplaner/2026-11-08-palm-jordarna.md (sha 85a70fa3). Läser
# rutor_2000.csv (och rutor_1000/5000.csv om de finns), skriver resultat.json.
#   Rscript utdata/palm_jordarna/analys.R
suppressMessages({library(MASS); library(sandwich); library(jsonlite)})
HERE <- "utdata/palm_jordarna"
MALAR <- c("attundaland", "tiundaland", "fjadrundaland", "roden", "U", "Sö", "Vs")
GOTA <- c("Vg", "Sm", "aspeland", "finnveden", "handbord", "kinda", "mo", "more", "njudung", "sevede", "tjust", "tveta",
          "varend", "vedbo", "vista")
read_cells <- function(m) {
  f <- file.path(HERE, sprintf("rutor_%d.csv", m))
  if (!file.exists(f)) return(NULL)
  d <- read.csv(f)
  d$region <- relevel(factor(d$region), ref = "Sö")  # a land with many stones as reference
  d$lgrave <- log1p(d$gravefields)
  d$ldist <- log(d$dist_water_km + 0.5)
  d
}
fit <- function(d, form) glm.nb(form, data = d, control = glm.control(maxit = 100))
coef_test <- function(m, d, name, side) {
  V <- vcovCL(m, cluster = d$block)
  est <- unname(coef(m)[name]); se <- sqrt(V[name, name]); z <- est / se
  p <- if (side == "greater") 1 - pnorm(z) else pnorm(z)
  list(estimate = est, se = se, z = z, p_one_sided = p, rate_ratio = exp(est))
}
# The contrast between two groups of lands: the log of the ratio of their cell-weighted mean rates (at the same soil,
# grave fields and water), with a delta-method cluster-robust SE. Taken on the rate scale, not as a mean of the lands'
# effects on the log scale: a land without a single stone in its settled cells has an effect towards minus infinity,
# and on the rate scale it rightly counts as (almost) zero density.
contrast <- function(m, d, A, B) {
  cf <- coef(m); cf[is.na(cf)] <- 0; V <- vcovCL(m, cluster = d$block)
  lv <- levels(d$region); n <- table(d$region)
  grp <- function(G) {
    L <- intersect(G, lv); w <- as.numeric(n[L]) / sum(n[L])
    b <- vapply(L, function(l) { nm <- paste0("region", l); if (nm %in% names(cf)) unname(cf[nm]) else 0 }, 0)
    e <- w * exp(b)
    g <- setNames(numeric(length(cf)), names(cf))
    for (k in seq_along(L)) { nm <- paste0("region", L[k]); if (nm %in% names(g)) g[nm] <- e[k] / sum(e) }
    list(val = log(sum(e)), grad = g)
  }
  a <- grp(A); b <- grp(B)
  est <- a$val - b$val; gr <- a$grad - b$grad
  se <- sqrt(drop(t(gr) %*% V[names(gr), names(gr)] %*% gr))
  list(estimate = est, se = se, p_one_sided = 1 - pnorm(est / se), ratio = exp(est))
}

d <- read_cells(2000)
full <- stones ~ clay + lgrave + ldist + region + offset(log(land_km2))
m <- fit(d, full)
m0 <- fit(d, stones ~ clay + ldist + region + offset(log(land_km2)))
mu <- fit(d, stones ~ region + offset(log(land_km2)))
P0 <- coef_test(m0, d, "clay", "greater")
P1 <- coef_test(m, d, "clay", "greater")
P3 <- coef_test(m, d, "ldist", "less")
c_adj <- contrast(m, d, MALAR, GOTA); c_un <- contrast(mu, d, MALAR, GOTA)
P2 <- list(adjusted = c_adj, unadjusted = c_un, explained_share = 1 - c_adj$estimate / c_un$estimate)
P1$holds <- P1$p_one_sided < 0.05 && P1$estimate > 0
P2$holds <- c_adj$p_one_sided < 0.05 && c_adj$estimate > 0
P3$holds <- P3$p_one_sided < 0.05 && P3$estimate < 0

rob <- list()
for (cs in c(1000, 5000)) {
  dd <- read_cells(cs)
  if (!is.null(dd)) rob[[sprintf("cells_%d_m", cs)]] <- coef_test(fit(dd, full), dd, "clay", "greater")
}
dm <- droplevels(d[d$region %in% MALAR, ]); dg <- droplevels(d[d$region %in% GOTA, ])
dg$region <- relevel(dg$region, ref = "Vg")
rob$malar_only <- coef_test(fit(dm, full), dm, "clay", "greater")
rob$gotaland_only <- coef_test(fit(dg, full), dg, "clay", "greater")
rob$without_water <- coef_test(fit(d, stones ~ clay + lgrave + region + offset(log(land_km2))), d, "clay", "greater")

desc <- do.call(rbind, lapply(split(d, d$region), function(x) data.frame(
  region = as.character(x$region[1]), cells = nrow(x), stones = sum(x$stones), gravefields = sum(x$gravefields),
  land_km2 = sum(x$land_km2), clay = sum(x$lera_silt) / sum(x$land_px), stones_per_100km2 = 100 * sum(x$stones) / sum(x$land_km2),
  stones_per_gravefield = sum(x$stones) / sum(x$gravefields))))
desc <- desc[order(-desc$stones), ]
# plain-words effect: stones per cell at the 25th and 75th percentile of clay, other things as in the data
q <- quantile(d$clay, c(0.25, 0.75))
eff <- unname(exp(coef(m)["clay"] * (q[2] - q[1])))
out <- list(plan = "analysplaner/2026-11-08-palm-jordarna.md", plan_sha = "85a70fa3",
            cells = nrow(d), stones = sum(d$stones), gravefields = sum(d$gravefields), lands = nlevels(d$region),
            theta = m$theta, clay_quartiles = unname(q), ratio_q75_vs_q25 = eff,
            P0 = P0, P1 = P1, P2 = P2, P3 = P3, robustness = rob, per_land = desc)
write_json(out, file.path(HERE, "resultat.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
cat(sprintf("%d rutor, %d stenar, %d land\nP0 lera utan gravfält: RR %.2f p %.3g\nP1 lera inom bygden: RR %.2f p %.3g (%s)\nP2 Mälar−Göta: ojusterad %.2f×, justerad %.2f× p %.3g, förklarat %.0f %% (%s)\nP3 avstånd vatten: RR %.2f p %.3g (%s)\n",
            nrow(d), sum(d$stones), nlevels(d$region), P0$rate_ratio, P0$p_one_sided, P1$rate_ratio, P1$p_one_sided,
            ifelse(P1$holds, "håller", "håller inte"), c_un$ratio, c_adj$ratio, c_adj$p_one_sided,
            100 * P2$explained_share, ifelse(P2$holds, "håller", "håller inte"), P3$rate_ratio, P3$p_one_sided,
            ifelse(P3$holds, "håller", "håller inte")))
