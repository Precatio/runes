# Hot spots och kluster: var klustrar mönstren på kartan mer än slumpen ger?
#
# För varje mönster på mönsterkartan (pm_*, src/pattern_map.py) och de stenar där mönstret kan avgöras (flyttade stenar
# räknas inte):
#  * Morans I (spdep) – klustrar mönstret alls geografiskt? Grannar är de åtta närmaste stenarna (SWEREF 99 TM).
#  * Getis-Ord Gi* (spdep) – vilka stenar ligger i ett hett område (mönstret vanligare bland grannarna än i landet) eller
#    ett kallt? De lokala p-värdena justeras med Benjamini–Hochberg över stenarna.
#  * Kulldorffs rumsliga scanstatistik (smerc, Poisson med landets andel som förväntat värde) – alla cirklar runt varje sten med högst en tiondel av stenarna
#    prövas; de kluster där mönstret är ovanligt vanligt redovisas med p-värde från Monte Carlo-simuleringar. Varje
#    kluster prövas också i korpusens två halvor (uppdelade per socken som i change.R): är mönstret vanligare inne i
#    klustret än utanför i båda halvorna?
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(sf); library(spdep); library(smerc) })
sf_use_s2(FALSE)

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
K <- 8           # neighbours
UBPOP <- 0.1     # largest cluster: a tenth of the stones
NSIM <- 999
MIN_CASES <- 15

d <- read_corpus(P$corpus) %>% filter(!is.na(lat), !is.na(lon))
if ("moved" %in% names(d)) d <- d %>% filter(is.na(moved) | moved == 0)
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
pts <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326, remove = FALSE), SWEREF)
xy <- st_coordinates(pts) / 1000          # km
d$x <- xy[, 1]; d$y <- xy[, 2]

# Halves, as in change.R: whole parishes alternating within each province by mean dating
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]

inside_test <- function(y, inside) {
  t <- table(factor(inside, c(TRUE, FALSE)), factor(y, c(1, 0)))
  if (any(rowSums(t) == 0)) return(NULL)
  ft <- fisher.test(t)
  list(rate_in = r3(t[1, 1] / sum(t[1, ])), rate_out = r3(t[2, 1] / sum(t[2, ])), or = r3(unname(ft$estimate)),
       p = signif(ft$p.value, 3))
}

analyse <- function(fe) {
  ok <- !is.na(d[[fe]])
  dd <- d[ok, ]
  y <- as.integer(dd[[fe]])
  if (sum(y) < MIN_CASES || sum(1 - y) < MIN_CASES) return(NULL)
  coords <- cbind(dd$x, dd$y)
  # Duplicate coordinates (several stones at one place) would make zero distances; jitter them by a few metres
  dup <- duplicated(coords) | duplicated(coords, fromLast = TRUE)
  coords[dup, ] <- coords[dup, ] + matrix(runif(sum(dup) * 2, -0.01, 0.01), ncol = 2)
  nb <- knn2nb(knearneigh(coords, k = K))
  nb <- make.sym.nb(nb)
  mi <- moran.test(y, nb2listw(nb, style = "W"), alternative = "greater")
  g <- as.numeric(localG(y, nb2listw(include.self(nb), style = "B")))
  gp <- 2 * pnorm(-abs(g))
  gq <- p.adjust(gp, "BH")
  hot <- which(gq < 0.05 & g > 0); cold <- which(gq < 0.05 & g < 0)
  stones <- data.frame(signum = dd$signum, z = round(g, 2), q = signif(gq, 3))
  stones <- stones[gq < 0.05, ]

  # Poisson with the national share as the expected count per stone (the binomial form fails with one stone per place)
  sc <- tryCatch(suppressWarnings(scan.test(coords, cases = y, pop = rep(1, length(y)), ex = rep(mean(y), length(y)),
                                            nsim = NSIM, alpha = 0.05, ubpop = UBPOP, longlat = FALSE, type = "poisson",
                                            min.cases = 3)),
                 error = function(e) { message("scan ", fe, ": ", conditionMessage(e)); NULL })
  best_p <- if (!is.null(sc) && length(sc$clusters)) signif(sc$clusters[[1]]$pvalue, 3) else NA
  clusters <- list()
  if (!is.null(sc) && length(sc$clusters)) for (cl in sc$clusters) {
    if (cl$pvalue >= 0.05) next          # smerc returns the most likely cluster also when it is not significant
    ids <- cl$locids
    inside <- seq_along(y) %in% ids
    ctr <- ids[1]
    radius <- cl$r
    halves <- lapply(c(A = "A", B = "B"), function(h) {
      s <- !is.na(dd$half) & dd$half == h
      if (sum(inside & s) < 3) return(NULL)
      inside_test(y[s], inside[s])
    })
    same <- function(r) !is.null(r) && r$p < 0.05 && r$or > 1
    ll <- st_coordinates(st_transform(st_sfc(st_point(as.numeric(cl$centroid) * 1000), crs = SWEREF), 4326))
    clusters[[length(clusters) + 1]] <- list(
      center = dd$signum[ctr], lat = round(ll[2], 4), lon = round(ll[1], 4), radius_km = round(radius, 1),
      n = length(ids), cases = sum(y[ids]), rate_in = r3(mean(y[ids])), rate_out = r3(mean(y[-ids])),
      rr = r3(mean(y[ids]) / mean(y[-ids])), p = signif(cl$pvalue, 3),
      provinces = as.list(table(dd$province[ids])), stones = dd$signum[ids],
      halves = list(A = halves$A, B = halves$B, replicated = same(halves$A) && same(halves$B)))
  }
  list(key = sub("^pm_", "", fe), n = length(y), cases = sum(y), share = r3(mean(y)),
       moran = list(i = r3(unname(mi$estimate[1])), p = signif(mi$p.value, 3)),
       n_hot = length(hot), n_cold = length(cold), stones = stones, clusters = clusters, best_cluster_p = best_p)
}

res <- lapply(grep("^pm_", names(d), value = TRUE), function(fe) {
  tryCatch(analyse(fe), error = function(e) { message(fe, ": ", conditionMessage(e)); NULL })
})
res <- Filter(Negate(is.null), res)
# Moran's I adjusted over the patterns, and the most likely cluster of each pattern adjusted over the patterns
mq <- p.adjust(sapply(res, function(r) r$moran$p), "BH")
for (i in seq_along(res)) res[[i]]$moran$q_bh <- signif(mq[i], 3)
# The clusters adjusted over the patterns: each pattern's clusters, and for patterns without a significant cluster the
# most likely one, enter one Benjamini–Hochberg family
pv <- unlist(lapply(res, function(r) if (length(r$clusters)) sapply(r$clusters, `[[`, "p") else r$best_cluster_p))
cq <- p.adjust(pv[!is.na(pv)], "BH")
j <- 0
for (i in seq_along(res)) {
  if (length(res[[i]]$clusters)) {
    for (c in seq_along(res[[i]]$clusters)) { j <- j + 1; res[[i]]$clusters[[c]]$q_bh <- signif(cq[j], 3) }
  } else if (!is.na(res[[i]]$best_cluster_p)) j <- j + 1
}

write_result(list(
  n_stones = nrow(d), k = K, ubpop = UBPOP, nsim = NSIM, patterns = res,
  method = paste(
    "För varje mönster på mönsterkartan och de stenar där det kan avgöras (flyttade stenar räknas inte): Morans I med de",
    K, "närmaste stenarna som grannar (spdep), Benjamini–Hochberg över mönstren; Getis-Ord Gi* för varje sten, med de",
    "lokala p-värdena justerade med Benjamini–Hochberg; och Kulldorffs rumsliga scanstatistik (smerc, Poisson med",
    "landets andel som förväntat värde per sten) med",
    "cirklar som rymmer högst", UBPOP * 100, "% av stenarna och", NSIM, "Monte Carlo-simuleringar. Varje kluster prövas",
    "också i korpusens två halvor, uppdelade per socken: är mönstret vanligare inne i klustret än utanför i båda",
    "(Fishers exakta test)? Klustrens p-värden justeras med Benjamini–Hochberg över mönstren."
  )
), out, "hotspots")
