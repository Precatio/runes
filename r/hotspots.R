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
    for (ci in seq_along(res[[i]]$clusters)) { j <- j + 1; res[[i]]$clusters[[ci]]$q_bh <- signif(cq[j], 3) }
  } else if (!is.na(res[[i]]$best_cluster_p)) j <- j + 1
}

# ---- figures: where each pattern gathers ----------------------------------------------------------------------------
# For the patterns that cluster (Moran's I, q < 0.05) and have hot or cold areas or a cluster: the share of stones with
# the pattern per hexagon of 25 km (at least 5 stones), the hot and cold stones (Gi*) and the clusters (Kulldorff), on the
# land of Natural Earth – the same picture as the map tool's "Kluster", for reports and the blog.
HEX_M <- 25000
MIN_HEX <- 5
labels <- P$pattern_labels %||% list()
wat <- tryCatch(read_water(P$water_dir), error = function(e) { message("vatten: ", conditionMessage(e)); NULL })
outline <- if (!is.null(wat$land)) st_boundary(wat$land) else NULL
wrap <- function(x, w = 105) paste(strwrap(x, w), collapse = "\n")
qtxt <- function(q) if (q < 0.001) tr("< 0,001", "< 0.001") else format(signif(q, 2), decimal.mark = tr(",", "."))
figures <- list()
for (i in seq_along(res)) {
  r <- res[[i]]
  if (is.null(r$moran$q_bh) || r$moran$q_bh >= 0.05 || (r$n_hot + r$n_cold == 0 && !length(r$clusters))) next
  fig <- tryCatch({
    fe <- paste0("pm_", r$key)
    sub <- pts[!is.na(d[[fe]]), ]
    sub$y <- as.integer(d[[fe]][!is.na(d[[fe]])])
    grid <- st_sf(geometry = st_make_grid(st_as_sfc(st_bbox(sub)), cellsize = HEX_M, square = FALSE))
    hits <- st_intersects(grid, sub)
    grid$n <- lengths(hits)
    grid$k <- vapply(hits, function(ix) sum(sub$y[ix]), numeric(1))
    grid <- grid[grid$n > 0, ]
    grid$share <- ifelse(grid$n >= MIN_HEX, grid$k / grid$n, NA_real_)
    st <- if (nrow(r$stones)) merge(data.frame(signum = sub$signum, st_coordinates(sub)), r$stones, by = "signum") else NULL
    circ <- if (length(r$clusters)) do.call(rbind, lapply(r$clusters, function(c)
      st_sf(geometry = st_buffer(st_transform(st_sfc(st_point(c(c$lon, c$lat)), crs = 4326), SWEREF), c$radius_km * 1000))))
      else NULL
    # The view: where nearly all the stones are (a few far to the north would otherwise shrink the map)
    xy_sub <- st_coordinates(sub)
    xl <- quantile(xy_sub[, 1], c(0.01, 0.99)) + c(-30000, 30000)
    yl <- quantile(xy_sub[, 2], c(0.01, 0.99)) + c(-30000, 30000)
    lab <- labels[[r$key]] %||% r$key
    p <- ggplot() + geom_sf(data = grid, aes(fill = share), colour = "white", linewidth = 0.15)
    if (!is.null(outline)) p <- p + geom_sf(data = outline, colour = MUTED, linewidth = 0.2, inherit.aes = FALSE)
    if (!is.null(st)) p <- p + geom_point(data = st, aes(X, Y, colour = ifelse(z > 0, "hot", "cold")), size = 1.1)
    if (!is.null(circ)) p <- p + geom_sf(data = circ, fill = NA, colour = ACCENT, linewidth = 0.7, linetype = "22")
    p <- p +
      scale_fill_gradientn(colours = SEQ, limits = c(0, 1), na.value = "#eef0f2",
                           labels = function(x) paste0(round(100 * x), " %"),
                           name = tr("Andel med mönstret", "Share with the pattern")) +
      scale_colour_manual(values = c(hot = ACCENT, cold = SERIES[1]),
                          labels = c(hot = tr("hett område (Gi*)", "hot area (Gi*)"), cold = tr("kallt område (Gi*)", "cold area (Gi*)")),
                          name = NULL, drop = TRUE) +
      coord_sf(crs = SWEREF, xlim = xl, ylim = yl, expand = FALSE, datum = NA) +
      labs(title = tr(sprintf("%s – var mönstret samlas", lab), sprintf("%s – where the pattern gathers", lab)),
           subtitle = wrap(tr(sprintf("Andel per sexkant om 25 km (minst %d stenar; grått: färre). Punkter: heta och kalla områden (Getis-Ord Gi*). Ringar: kluster (Kulldorff).", MIN_HEX),
                              sprintf("Share per 25 km hexagon (at least %d stones; grey: fewer). Points: hot and cold areas (Getis-Ord Gi*). Rings: clusters (Kulldorff).", MIN_HEX))),
           caption = wrap(tr(sprintf("Morans I %s (q %s), %d stenar i heta och %d i kalla områden. Flyttade stenar räknas inte. Källa: Vitki, r/hotspots.R; Rundata (ODbL).",
                                     format(r$moran$i, decimal.mark = ","), qtxt(r$moran$q_bh), r$n_hot, r$n_cold),
                             sprintf("Moran's I %s (q %s), %d stones in hot and %d in cold areas. Moved stones are left out. Source: Vitki, r/hotspots.R; Rundata (ODbL).",
                                     r$moran$i, qtxt(r$moran$q_bh), r$n_hot, r$n_cold)))) +
      theme_map(9) + theme(legend.key.width = unit(1.1, "cm"), legend.box = "vertical")
    save_fig(p, out, sprintf("hotspot_%s.png", r$key), 7, 7.5)
  }, error = function(e) { message("figur ", r$key, ": ", conditionMessage(e)); NULL })
  if (!is.null(fig)) { res[[i]]$figure <- fig; figures[[paste0("hotspot_", r$key)]] <- fig }
}

write_result(list(
  n_stones = nrow(d), k = K, ubpop = UBPOP, nsim = NSIM, patterns = res, figures = figures,
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
