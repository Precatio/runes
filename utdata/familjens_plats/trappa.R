# Robusthetstrappan för test A (gravfält inom 500 m, grupp mot ensam) enligt den låsta tilläggsplanen
# analysplaner/2026-10-31-familjens-plats-trappan.md. Samma data och modell som analys.R (planen 2026-10-29).
#   Rscript utdata/familjens_plats/trappa.R
suppressMessages({library(dplyr); library(jsonlite); library(lme4); library(mgcv); library(sf)})
sf_use_s2(FALSE)
dir <- "utdata/familjens_plats"
d <- read.csv(file.path(dir, "stenar.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
corp <- read.csv("data/cache/r/corpus/3f58e9339191761e/corpus.csv", encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d <- merge(d, corp[, c("signum", "lat", "lon", "carvers_uncertain")], by = "signum", all.x = TRUE)
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
d$pkey <- pkey
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
# the carver group: a secure carver, otherwise the parish (as in the ladder, METHODS 1v)
d$cg <- ifelse(!is.na(d$carver) & d$carver != "" & (is.na(d$carvers_uncertain) | d$carvers_uncertain == 0),
               paste0("R:", d$carver), paste0("S:", d$pkey))
# Runor 2020: stones not at their original place
runor <- fromJSON("data/raa/runor_2020.json", simplifyVector = TRUE)
rr <- if (is.data.frame(runor)) runor else runor$inscriptions
moved_runor <- rr$signum[!is.na(rr$original) & rr$original == FALSE]
d$moved_runor <- d$signum %in% moved_runor
# SWEREF 99 TM, km
ok <- !is.na(d$lat) & !is.na(d$lon)
xy <- st_coordinates(st_transform(st_as_sf(d[ok, ], coords = c("lon", "lat"), crs = 4326), 3006)) / 1000
d$x <- NA; d$y <- NA; d$x[ok] <- xy[, 1]; d$y[ok] <- xy[, 2]

Y <- "y1_gravfalt"
d <- d[!is.na(d$grupp) & !is.na(d[[Y]]), ]
prep <- function(dd) {
  small <- names(which(table(dd$province) < 10))
  dd$prov <- factor(ifelse(dd$province %in% small, "övriga", dd$province))
  droplevels(dd)
}
rhs_of <- function(dd) c("grupp", if (nlevels(dd$prov) > 1) "prov", if (nlevels(dd$period) > 1) "period", "lt")
coef_row <- function(b, se, p, n, extra = list()) c(list(or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se), p = p, n = n), extra)
glm_fit <- function(dd, rhs = NULL) {
  dd <- prep(dd); rhs <- if (is.null(rhs)) rhs_of(dd) else rhs
  m <- suppressWarnings(glm(reformulate(rhs, Y), family = binomial, data = dd))
  s <- summary(m)$coefficients
  coef_row(s["grupp", 1], s["grupp", 2], s["grupp", 4], nrow(dd))
}
glmer_fit <- function(dd, grp) {
  dd <- prep(dd)
  f <- as.formula(paste(Y, "~", paste(rhs_of(dd), collapse = " + "), "+ (1 |", grp, ")"))
  m <- tryCatch(suppressWarnings(glmer(f, family = binomial, data = dd, control = glmerControl(optimizer = "bobyqa"))), error = function(e) NULL)
  if (is.null(m)) return(list(error = "konvergerade inte", n = nrow(dd)))
  s <- summary(m)$coefficients
  coef_row(s["grupp", 1], s["grupp", 2], s["grupp", 4], nrow(dd), list(groups = length(unique(dd[[grp]])), singular = isSingular(m)))
}
gam_fit <- function(dd) {
  dd <- prep(dd[!is.na(dd$x), ])
  f <- as.formula(paste(Y, "~", paste(rhs_of(dd), collapse = " + "), "+ s(x, y, k = 30)"))
  m <- gam(f, family = binomial, data = dd, method = "REML")
  s <- summary(m)$p.table
  coef_row(s["grupp", 1], s["grupp", 2], s["grupp", 4], nrow(dd))
}
holds <- function(r) !is.null(r$or) && is.finite(r$or) && r$or > 1 && r$p < 0.05 && !isTRUE(r$singular)

out <- list(plan = "analysplaner/2026-10-31-familjens-plats-trappan.md", test = "A: gravfält inom 500 m, grupp mot ensam", rungs = list())
out$rungs$raw <- glm_fit(d, "grupp")
out$rungs$adjusted <- glm_fit(d)
out$rungs$carver <- glmer_fit(d, "cg")
out$rungs$parish <- glmer_fit(d, "pkey")
out$rungs$place <- gam_fit(d)
out$rungs$half_A <- glm_fit(d[d$half == "A", ])
out$rungs$half_B <- glm_fit(d[d$half == "B", ])
provs <- names(which(table(d$province) >= 30))
lopo <- lapply(provs, function(p) { r <- glm_fit(d[d$province != p, ]); r$without <- p; r$share_left <- r$n / nrow(d); r })
names(lopo) <- provs
out$lopo <- lopo
worst <- lopo[[which.max(sapply(lopo, function(r) r$p))]]
lopo_ok <- all(sapply(lopo, function(r) r$or > 1)) && all(sapply(lopo, function(r) r$share_left < 2/3 || r$p < 0.05))
out$rungs$lopo <- c(worst, list(all_direction = all(sapply(lopo, function(r) r$or > 1)), provinces = provs, holds_rule = lopo_ok))
out$rungs$moved_runor <- glm_fit(d[!d$moved_runor, ])
for (k in names(out$rungs)) {
  r <- out$rungs[[k]]
  out$rungs[[k]]$holds <- if (k == "lopo") lopo_ok else if (!is.null(r$error)) NA else holds(r)
}
out$n <- nrow(d); out$n_grupp <- sum(d$grupp == 1); out$n_ensam <- sum(d$grupp == 0); out$n_moved_runor <- sum(d$moved_runor)
write_json(out, file.path(dir, "trappan.json"), auto_unbox = TRUE, digits = 8, pretty = TRUE)
for (k in names(out$rungs)) { r <- out$rungs[[k]]
  cat(sprintf("%-12s OR %s [%s, %s] p %s n %s %s %s\n", k, signif(r$or, 3), signif(r$lo, 3), signif(r$hi, 3), signif(r$p, 2), r$n,
              if (!is.null(r$groups)) paste("grupper", r$groups) else if (!is.null(r$without)) paste("utan", r$without) else "",
              if (isTRUE(r$holds)) "HÅLLER" else if (is.na(r$holds)) "EJ PRÖVAT" else "HÅLLER INTE")) }
for (p in provs) cat(sprintf("   utan %-3s OR %.2f p %.3g andel kvar %.2f\n", p, lopo[[p]]$or, lopo[[p]]$p, lopo[[p]]$share_left))
