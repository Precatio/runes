# Geografi: ristarnas områden, tyngdpunkter och spridning, prövat mot slumpvisa urval i samma landskap,
# samt runstenarnas avstånd till vatten jämfört med slumpvisa punkter på land.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages(library(sf))
sf_use_s2(FALSE)

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
MIN_N <- 5
B <- 499

d <- read_corpus(P$corpus) %>% filter(!is.na(lat), !is.na(lon))
pts <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326, remove = FALSE), SWEREF)
xy <- st_coordinates(pts)
d$x <- xy[, 1]; d$y <- xy[, 2]

to_latlon <- function(x, y) {
  p <- st_coordinates(st_transform(st_sfc(st_point(c(x, y)), crs = SWEREF), 4326))
  list(lat = r3(p[2]), lon = r3(p[1]))
}

spread <- function(x, y) {
  cx <- mean(x); cy <- mean(y)
  median(sqrt((x - cx)^2 + (y - cy)^2)) / 1000
}

# ---- carvers ---------------------------------------------------------------------------------
cv <- d %>% filter(!is.na(carver)) %>% group_by(carver) %>% filter(n() >= MIN_N) %>% ungroup()
by_prov <- split(seq_len(nrow(d)), d$province)
carver_rows <- list(); hulls <- list()
for (name in names(sort(table(cv$carver), decreasing = TRUE))) {
  g <- cv %>% filter(carver == name)
  cx <- mean(g$x); cy <- mean(g$y)
  dd <- sqrt((g$x - cx)^2 + (g$y - cy)^2) / 1000
  m <- as.matrix(dist(cbind(g$x, g$y))) / 1000
  diag(m) <- NA
  nn <- apply(m, 1, min, na.rm = TRUE)
  # Is the carver's area more compact than random runestones from the same provinces?
  pool <- unlist(by_prov[unique(g$province)])
  obs <- median(dd)
  rand <- replicate(B, {
    s <- sample(pool, nrow(g))
    spread(d$x[s], d$y[s])
  })
  hull <- st_convex_hull(st_union(st_geometry(pts)[d$carver %in% name & !is.na(d$carver)]))
  area <- if (st_is(hull, "POLYGON")) as.numeric(st_area(hull)) / 1e6 else 0
  hc <- if (st_is(hull, "POLYGON")) st_coordinates(st_transform(hull, 4326))[, 1:2] else matrix(numeric(0), ncol = 2)
  provs <- sort(table(g$province), decreasing = TRUE)
  carver_rows[[name]] <- list(
    carver = name, n = nrow(g), centroid = to_latlon(cx, cy), cx = cx, cy = cy,
    sd_km = r1(sqrt(mean(dd^2))), median_km = r1(obs), p90_km = r1(unname(quantile(dd, 0.9))),
    max_km = r1(max(dd)), nn_km = r1(mean(nn)), hull_area_km2 = round(area),
    hull = lapply(seq_len(nrow(hc)), function(i) c(r3(hc[i, 2]), r3(hc[i, 1]))),
    provinces = paste0(names(provs), " (", as.integer(provs), ")", collapse = ", "),
    random_median_km = r1(mean(rand)), compact_ratio = r3(obs / mean(rand)),
    compact_p = r3((1 + sum(rand <= obs)) / (1 + B))
  )
  hulls[[name]] <- hull
}
cp <- sapply(carver_rows, function(r) r$compact_p)
cq <- p.adjust(cp, "BH")
for (i in seq_along(carver_rows)) carver_rows[[i]]$compact_q <- r3(cq[i])
n_compact <- sum(cq < 0.05)

# ---- water -----------------------------------------------------------------------------------
W <- read_water(P$water_dir)
water <- list(available = FALSE, note = "Vattenlagren (Natural Earth) kunde inte läsas; avstånd till vatten beräknades inte.")
d$water_km <- NA_real_
if (!is.null(W)) {
  d$water_km <- as.numeric(st_distance(pts, W$lines)) / 1000
  # Random points on land (not in lakes) within each province's runestone area
  prov_n <- table(d$province)
  provs <- names(prov_n[prov_n >= 20])
  rnd <- list()
  for (pv in provs) {
    area <- st_buffer(st_convex_hull(st_union(st_geometry(pts)[d$province == pv])), 2000)
    if (!is.null(W$land)) area <- suppressWarnings(suppressMessages(st_intersection(area, W$land)))
    if (!length(area) || all(st_is_empty(area))) next
    s <- st_sample(area, size = as.integer(prov_n[pv]) * 2, type = "random")
    if (!is.null(W$lakes)) s <- s[!lengths(st_intersects(s, W$lakes))]
    s <- s[seq_len(min(length(s), as.integer(prov_n[pv])))]
    if (length(s)) rnd[[pv]] <- data.frame(province = pv, water_km = as.numeric(st_distance(s, W$lines)) / 1000)
  }
  rnd <- bind_rows(rnd)
  stones <- d %>% filter(province %in% provs)
  overall <- wilcox.test(stones$water_km, rnd$water_km, alternative = "less")
  prov_rows <- lapply(provs, function(pv) {
    s <- stones$water_km[stones$province == pv]; r <- rnd$water_km[rnd$province == pv]
    if (length(r) < 10) return(NULL)
    list(province = pv, n = length(s), median_stones_km = r3(median(s)), median_random_km = r3(median(r)),
         p = wilcox.test(s, r, alternative = "less")$p.value)
  })
  prov_rows <- Filter(Negate(is.null), prov_rows)
  pq <- p.adjust(sapply(prov_rows, `[[`, "p"), "BH")
  for (i in seq_along(prov_rows)) { prov_rows[[i]]$p <- signif(prov_rows[[i]]$p, 3); prov_rows[[i]]$q <- signif(pq[i], 3) }
  wc <- d %>% filter(!is.na(carver)) %>% group_by(carver) %>% filter(n() >= 8) %>% ungroup()
  kw <- kruskal.test(water_km ~ factor(carver), data = wc)
  carver_water <- wc %>% group_by(carver) %>% summarise(n = n(), median_km = r3(median(water_km))) %>% arrange(median_km)
  bro <- d$water_km[d$cat_bro_vag == 1]; other <- d$water_km[d$cat_bro_vag == 0]
  bt <- wilcox.test(bro, other, alternative = "less")
  water <- list(
    available = TRUE, note = WATER_NOTE,
    overall = list(n_stones = nrow(stones), n_random = nrow(rnd), median_stones_km = r3(median(stones$water_km)),
                   median_random_km = r3(median(rnd$water_km)), p = signif(overall$p.value, 3)),
    provinces = prov_rows,
    carvers = list(kruskal_p = signif(kw$p.value, 3), df = unname(kw$parameter), rows = carver_water),
    bridges = list(n = length(bro), median_bridge_km = r3(median(bro)), median_other_km = r3(median(other)),
                   p = signif(bt$p.value, 3))
  )
  # Figure: distance to water, runestones vs random points on land
  long <- bind_rows(data.frame(group = tr("Runstenar", "Runestones"), water_km = stones$water_km),
                    data.frame(group = tr("Slumpvisa punkter på land", "Random points on land"), water_km = rnd$water_km))
  p <- ggplot(long, aes(water_km, colour = group, linetype = group)) +
    stat_ecdf(linewidth = 0.7) +
    scale_colour_manual(values = SERIES[1:2], name = NULL) +
    scale_linetype_manual(values = c("solid", "22"), name = NULL) +
    scale_x_sqrt(breaks = c(0, 0.5, 1, 2, 5, 10, 20)) +
    labs(title = "Avstånd till vatten", x = tr("km till närmaste strand, sjö eller vattendrag (rotskala)",
                                               "km to the nearest shore, lake or river (square-root scale)"),
         y = tr("Kumulativ andel", "Cumulative share"),
         subtitle = sprintf("Median: runstenar %.2f km, slumpvisa punkter %.2f km (Wilcoxon, ensidigt p = %s)",
                            median(stones$water_km), median(rnd$water_km), format.pval(overall$p.value, digits = 2)),
         caption = "Vattnet enligt Natural Earth 1:10 milj. (dagens strandlinjer). Slumpvisa punkter på land inom varje landskaps runstensområde.") +
    theme_runor()
  water$figure <- save_fig(p, out, "geografi_vatten.png", 7, 4.5)
}

# ---- map figure: small multiples, one carver per panel ----------------------------------------
top <- head(names(carver_rows), 12)
bg <- d %>% select(x, y)
pal <- d %>% filter(carver %in% top) %>% mutate(carver = factor(carver, levels = top))
cent <- bind_rows(lapply(top, function(n) data.frame(carver = n, x = carver_rows[[n]]$cx, y = carver_rows[[n]]$cy))) %>%
  mutate(carver = factor(carver, levels = top))
hull_df <- bind_rows(lapply(top, function(n) {
  h <- hulls[[n]]
  if (!st_is(h, "POLYGON")) return(NULL)
  cc <- st_coordinates(h)
  data.frame(carver = n, x = cc[, 1], y = cc[, 2])
})) %>% mutate(carver = factor(carver, levels = top))
lim <- pal %>% summarise(x0 = min(x) - 30000, x1 = max(x) + 30000, y0 = min(y) - 30000, y1 = max(y) + 30000)
p <- ggplot()
if (!is.null(W) && !is.null(W$coast)) {
  p <- p + geom_sf(data = W$coast, colour = WATER, linewidth = 0.2)
}
if (!is.null(W) && !is.null(W$lakes)) p <- p + geom_sf(data = W$lakes, fill = "#e6eef8", colour = WATER, linewidth = 0.1)
p <- p +
  geom_point(data = bg, aes(x, y), colour = FAINT, size = 0.25) +
  geom_polygon(data = hull_df, aes(x, y), fill = NA, colour = SERIES[1], linewidth = 0.3) +
  geom_point(data = pal, aes(x, y), colour = SERIES[1], size = 0.8) +
  geom_point(data = cent, aes(x, y), shape = 3, colour = INK, size = 2, stroke = 0.6) +
  facet_wrap(~carver, ncol = 4) +
  coord_sf(xlim = c(lim$x0, lim$x1), ylim = c(lim$y0, lim$y1), crs = SWEREF, datum = NA) +
  labs(title = "Ristarnas områden", subtitle = "Säkra stenar (blå), konvext hölje och tyngdpunkt (+). Grått: alla svenska vikingatida runstenar.",
       caption = "Källa: Samnordisk runtextdatabas. Ristare med minst fem säkra stenar; de tolv med flest stenar visas.") +
  theme_map()
fig_map <- save_fig(p, out, "geografi_ristare.png", 9, 9)

# ---- interactive map for the reproducibility package (leaflet) ---------------------------------
html_map <- NULL
tryCatch({
  suppressPackageStartupMessages({ library(leaflet); library(htmlwidgets) })
  lp <- d %>% filter(carver %in% top)
  m <- leaflet(lp) %>% addProviderTiles("CartoDB.Positron") %>%
    addCircleMarkers(~lon, ~lat, radius = 3, stroke = FALSE, fillOpacity = 0.8, color = SERIES[1],
                     label = ~paste0(signum, " – ", carver), group = ~carver) %>%
    addLayersControl(overlayGroups = top, options = layersControlOptions(collapsed = FALSE))
  saveWidget(m, file.path(out, "ristare_karta.html"), selfcontained = nzchar(Sys.which("pandoc")), title = "Ristarnas stenar")
  html_map <- "ristare_karta.html"
}, error = function(e) message("leaflet: ", conditionMessage(e)))

# ---- per stone (used by stone.R) ---------------------------------------------------------------
pct <- if (!all(is.na(d$water_km))) ecdf(d$water_km)(d$water_km) else NA
write.csv(data.frame(signum = d$signum, x = d$x, y = d$y, water_km = d$water_km, water_pct = pct),
          file.path(out, "geography_stones.csv"), row.names = FALSE, fileEncoding = "UTF-8")
saveRDS(list(hulls = hulls), file.path(out, "geography_model.rds"))

result <- list(
  n_stones = nrow(d), min_inscriptions = MIN_N, permutations = B,
  carvers = unname(lapply(carver_rows, function(r) r[setdiff(names(r), c("cx", "cy"))])),
  n_compact = n_compact,
  water = water,
  figures = list(map = fig_map, water = water$figure),
  html_map = html_map,
  method = paste(
    "Koordinaterna (WGS 84 i Rundata) projicerades till SWEREF 99 TM. För varje ristare med minst", MIN_N,
    "säkra stenar beräknades tyngdpunkten (medelkoordinaten), standardavståndet, medianavståndet till tyngdpunkten,",
    "medelavståndet till närmaste egna sten och det konvexa höljets yta. Att ristaren arbetade inom ett avgränsat område",
    "prövades genom att jämföra medianavståndet med", B, "slumpvisa urval av lika många runstenar ur samma landskap",
    "(permutationstest, p justerat med Benjamini–Hochberg). Avstånd till vatten jämfördes med slumpvisa punkter på land",
    "inom varje landskaps runstensområde (Wilcoxons rangsummetest)."
  )
)
write_result(result, out, "geography")
