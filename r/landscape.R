# Landskap kring en sten: höjdmodell, läge i terrängen, modellerad strandlinje vid vikingatiden, sikt (viewshed)
# och bästa vägar i terrängen (least-cost paths) mellan grannstenarna.
#
# Höjddata: Tilezen/Mapzen Terrain Tiles (terrarium, AWS Open Data), zoomnivå 12 (ca 20 m i Mellansverige).
# Strandlinjen: dagens höjd minus landhöjningen sedan omkring år 1000 (grov skattning per landskap, kan ändras).
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({
  library(sf)
  library(terra)
})
sf_use_s2(FALSE)

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
RADIUS_KM <- if (is.null(P$radius_km)) 12 else P$radius_km
SITE_KM <- 1 # stones closer than this are the same site
VIEW_KM <- 5
ZOOM <- 12
RES <- 40 # m, for cost surfaces
N_NEIGH <- 8
N_RANDOM <- 300
tile_dir <- if (is.null(P$tile_dir)) file.path(out, "tiles") else P$tile_dir

# Approximate land uplift since c. AD 1000 (m), coarse values per province. Mälardalen about 5 m is the
# commonly cited figure; elsewhere the values follow today's uplift pattern (high in the north, near zero in Skåne).
UPLIFT <- c(U = 5.5, "Sö" = 5, Vs = 5, Gs = 6.5, "Nä" = 4, "Ög" = 3, "Öl" = 1.5, G = 2, Sm = 1.5, Vg = 2.5, Bo = 1.5,
            Hs = 8, M = 8.5, D = 5, J = 7, "Ån" = 8.5, Vr = 3.5, DR = 0, "Hr" = 7)

d <- read_corpus(P$corpus) %>% filter(!is.na(lat))
row <- d[d$signum == P$signum, ]
if (!nrow(row)) stop("Stenen saknar koordinater eller finns inte i korpusen: ", P$signum)
uplift <- if (!is.null(P$uplift_m)) P$uplift_m else if (row$province %in% names(UPLIFT)) UPLIFT[[row$province]] else 3

pt <- st_transform(st_as_sf(row, coords = c("lon", "lat"), crs = 4326), SWEREF)
sx <- st_coordinates(pt)[1]; sy <- st_coordinates(pt)[2]
win <- ext(sx - RADIUS_KM * 1000, sx + RADIUS_KM * 1000, sy - RADIUS_KM * 1000, sy + RADIUS_KM * 1000)

# ---- terrain tiles ---------------------------------------------------------------------------------------------
lonlat_box <- st_bbox(st_transform(st_as_sfc(st_bbox(c(xmin = win$xmin[[1]], ymin = win$ymin[[1]], xmax = win$xmax[[1]],
                                                       ymax = win$ymax[[1]]), crs = st_crs(SWEREF))), 4326))
tile_xy <- function(lon, lat, z) {
  n <- 2^z
  x <- floor((lon + 180) / 360 * n)
  y <- floor((1 - log(tan(lat * pi / 180) + 1 / cos(lat * pi / 180)) / pi) / 2 * n)
  c(x, y)
}
merc_bounds <- function(x, y, z) {
  n <- 2^z; R <- 6378137; size <- 2 * pi * R / n; o <- pi * R
  c(xmin = x * size - o, xmax = (x + 1) * size - o, ymax = o - y * size, ymin = o - (y + 1) * size)
}
t0 <- tile_xy(lonlat_box[["xmin"]], lonlat_box[["ymax"]], ZOOM)
t1 <- tile_xy(lonlat_box[["xmax"]], lonlat_box[["ymin"]], ZOOM)
tiles <- list()
for (tx in t0[1]:t1[1]) for (ty in t0[2]:t1[2]) {
  f <- file.path(tile_dir, ZOOM, tx, paste0(ty, ".png"))
  if (!file.exists(f)) {
    dir.create(dirname(f), recursive = TRUE, showWarnings = FALSE)
    url <- sprintf("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/%d/%d/%d.png", ZOOM, tx, ty)
    ok <- tryCatch(download.file(url, f, mode = "wb", quiet = TRUE) == 0, error = function(e) FALSE)
    if (!ok) { unlink(f); next }
  }
  img <- png::readPNG(f) * 255
  elev <- img[, , 1] * 256 + img[, , 2] + img[, , 3] / 256 - 32768
  b <- merc_bounds(tx, ty, ZOOM)
  tiles[[length(tiles) + 1]] <- rast(elev, extent = ext(b[["xmin"]], b[["xmax"]], b[["ymin"]], b[["ymax"]]), crs = "EPSG:3857")
}
if (!length(tiles)) stop("Höjddata kunde inte hämtas (Terrain Tiles).")
dem_m <- if (length(tiles) == 1) tiles[[1]] else merge(sprc(tiles))
template <- rast(win, resolution = 20, crs = "EPSG:3006")
dem <- project(dem_m, template, method = "bilinear")
names(dem) <- "elev"

# ---- water: today's lakes and the modelled shoreline ----------------------------------------------------------------
W <- read_water(P$water_dir)
lake_r <- if (!is.null(W) && !is.null(W$lakes)) rasterize(vect(st_sf(geometry = W$lakes)), dem, touches = TRUE) else dem * NA
water_now <- (dem <= 0.5) | !is.na(lake_r)
water_then <- (dem <= uplift) | !is.na(lake_r)
names(water_now) <- "water"; names(water_then) <- "water"

# ---- position in the terrain ---------------------------------------------------------------------------------------
elev_s <- extract(dem, cbind(sx, sy))[1, 1]
slope <- terrain(dem, "slope", unit = "degrees")
slope_s <- extract(slope, cbind(sx, sy))[1, 1]
tpi <- function(rad) {
  w <- focalMat(dem, rad, "circle")
  m <- focal(dem, w, fun = sum, na.rm = TRUE)
  extract(dem - m, cbind(sx, sy))[1, 1]
}
tpi300 <- tpi(300)
# Share of the surroundings (2 km) lower than the stone
around <- crop(dem, ext(sx - 2000, sx + 2000, sy - 2000, sy + 2000))
lower_share <- mean(values(around) < elev_s, na.rm = TRUE)
dist_to <- function(wr) {
  wv <- wr; wv[wv == 0] <- NA
  if (all(is.na(values(wv)))) return(NA_real_)
  extract(distance(wv), cbind(sx, sy))[1, 1] / 1000
}
shore_now_km <- dist_to(water_now)
shore_then_km <- dist_to(water_then)

# ---- viewshed: where the stone (top 2 m) can be seen by a person (1.6 m) ---------------------------------------------
vwin <- crop(dem, ext(sx - VIEW_KM * 1000, sx + VIEW_KM * 1000, sy - VIEW_KM * 1000, sy + VIEW_KM * 1000))
vs <- viewshed(vwin, c(sx, sy), observer = 2, target = 1.6, curvcoef = 6/7)
cell_km2 <- prod(res(vwin)) / 1e6
dxy <- crds(vwin)
dd_ <- sqrt((dxy[, 1] - sx)^2 + (dxy[, 2] - sy)^2)
vv <- values(vs)[, 1]
within <- function(km) dd_ <= km * 1000
wt <- values(crop(water_then, vwin))[, 1]
view <- list(
  visible_km2_2km = r3(sum(vv[within(2)] == 1, na.rm = TRUE) * cell_km2),
  share_2km = r3(mean(vv[within(2)] == 1, na.rm = TRUE)),
  visible_km2_5km = r3(sum(vv[within(5)] == 1, na.rm = TRUE) * cell_km2),
  share_5km = r3(mean(vv[within(5)] == 1, na.rm = TRUE)),
  water_visible_km2 = r3(sum(vv == 1 & wt == 1, na.rm = TRUE) * cell_km2),
  water_visible = any(vv == 1 & wt == 1, na.rm = TRUE)
)

# Compare with random land points: how visible is the stone's position compared with its surroundings?
land_pts <- spatSample(crop(water_then, ext(sx - 3000, sx + 3000, sy - 3000, sy + 3000)) == 0, 60, method = "random",
                       xy = TRUE, na.rm = TRUE, values = TRUE)
land_pts <- land_pts[land_pts[, 3] == 1, 1:2, drop = FALSE]
rand_view <- if (nrow(land_pts)) sapply(seq_len(min(40, nrow(land_pts))), function(i) {
  v <- viewshed(vwin, unlist(land_pts[i, ]), observer = 2, target = 1.6, curvcoef = 6/7)
  c2 <- crds(v); d2 <- sqrt((c2[, 1] - land_pts[i, 1])^2 + (c2[, 2] - land_pts[i, 2])^2)
  mean(values(v)[d2 <= 2000, 1] == 1, na.rm = TRUE)
}) else numeric(0)
view$random_share_2km_median <- if (length(rand_view)) r3(median(rand_view)) else NA
view$percentile <- if (length(rand_view)) r3(mean(rand_view <= view$share_2km)) else NA

# ---- least-cost paths between the neighbouring runestones -------------------------------------------------------------
dx <- d %>% filter(signum != P$signum)
dp <- st_coordinates(st_transform(st_as_sf(dx, coords = c("lon", "lat"), crs = 4326), SWEREF))
dx$x <- dp[, 1]; dx$y <- dp[, 2]
dx$dist <- sqrt((dx$x - sx)^2 + (dx$y - sy)^2)
# Other sites only: stones at the stone's own site would make the test circular, and stones at the same
# neighbouring site count once
cand_n <- dx %>% filter(dist >= SITE_KM * 1000, dist <= RADIUS_KM * 900) %>% arrange(dist)
same_site <- dx %>% filter(dist < SITE_KM * 1000)
keep_i <- c()
for (i in seq_len(nrow(cand_n))) {
  if (length(keep_i) >= N_NEIGH) break
  if (!length(keep_i) || all(sqrt((cand_n$x[keep_i] - cand_n$x[i])^2 + (cand_n$y[keep_i] - cand_n$y[i])^2) >= SITE_KM * 1000))
    keep_i <- c(keep_i, i)
}
neigh <- cand_n[keep_i, ]
routes <- NULL
paths_sf <- NULL
if (nrow(neigh) >= 3) {
  suppressPackageStartupMessages({ library(raster); library(gdistance) })
  coarse <- aggregate(dem, fact = RES / 20, fun = "mean")
  wcoarse <- aggregate(water_then, fact = RES / 20, fun = "max")
  R <- raster(coarse)
  hd <- function(x) x[2] - x[1]
  tr <- transition(R, hd, directions = 8, symm = FALSE)
  slope_tr <- geoCorrection(tr, scl = FALSE)
  adj <- adjacent(R, cells = 1:ncell(R), pairs = TRUE, directions = 8)
  speed <- slope_tr
  speed[adj] <- 6 * exp(-3.5 * abs(slope_tr[adj] + 0.05)) # Tobler's hiking function, km/h
  # Water (at the modelled Viking Age shoreline) is slow to cross on foot: one tenth of flat-ground speed
  wv <- values(wcoarse)[, 1]
  wet <- which(wv == 1)
  if (length(wet)) {
    wadj <- adj[adj[, 2] %in% wet, , drop = FALSE]
    speed[wadj] <- 0.6
  }
  cond <- geoCorrection(speed, scl = FALSE)
  coords <- as.matrix(neigh[, c("x", "y")])
  lines <- list()
  for (i in 1:(nrow(coords) - 1)) for (j in (i + 1):nrow(coords)) {
    l <- tryCatch(shortestPath(cond, coords[i, ], coords[j, ], output = "SpatialLines"), error = function(e) NULL)
    if (!is.null(l)) lines[[length(lines) + 1]] <- st_geometry(st_as_sf(l))
  }
  if (length(lines)) {
    paths_sf <- st_set_crs(do.call(c, lines), SWEREF)
    net <- st_union(paths_sf)
    stone_d <- as.numeric(st_distance(pt, net)) / 1000
    # Random land points in the same window
    rp <- spatSample(water_then == 0, N_RANDOM * 2, method = "random", xy = TRUE, values = TRUE, na.rm = TRUE)
    rp <- rp[rp[, 3] == 1, 1:2, drop = FALSE]
    rp <- head(rp, N_RANDOM)
    rd <- as.numeric(st_distance(st_as_sf(as.data.frame(rp), coords = c("x", "y"), crs = SWEREF), net)) / 1000
    routes <- list(n_neighbours = nrow(neigh), n_paths = length(lines), same_site = same_site$signum, stone_to_route_km = r3(stone_d),
                   random_median_km = r3(median(rd)), percentile = r3(mean(rd <= stone_d)),
                   neighbours = lapply(seq_len(nrow(neigh)), function(i) list(signum = neigh$signum[i],
                                                                               km = r1(neigh$dist[i] / 1000))))
  }
}

# ---- figures -------------------------------------------------------------------------------------------------------------
hs <- shade(terrain(dem, "slope", unit = "radians"), terrain(dem, "aspect", unit = "radians"), angle = 40, direction = 315)
hs_df <- as.data.frame(hs, xy = TRUE); names(hs_df)[3] <- "hs"
q <- quantile(hs_df$hs, c(0.02, 0.98), na.rm = TRUE)
hs_df$hs <- pmin(pmax((hs_df$hs - q[1]) / max(1e-9, q[2] - q[1]), 0), 1) # stretch contrast in flat terrain
wt_df <- as.data.frame(water_then, xy = TRUE); names(wt_df)[3] <- "w"; wt_df <- wt_df[wt_df$w == 1, ]
wn_df <- as.data.frame(water_now, xy = TRUE); names(wn_df)[3] <- "w"; wn_df <- wn_df[wn_df$w == 1, ]
p <- ggplot() +
  geom_raster(data = hs_df, aes(x, y, fill = hs), show.legend = FALSE) +
  scale_fill_gradient(low = "#475569", high = "#f8fafc") +
  geom_raster(data = wt_df, aes(x, y), fill = "#bcd3ee", alpha = 0.85) +
  geom_raster(data = wn_df, aes(x, y), fill = "#7aa6d8", alpha = 0.9)
if (!is.null(paths_sf)) p <- p + geom_sf(data = paths_sf, colour = SERIES[1], linewidth = 0.6, inherit.aes = FALSE)
p <- p +
  geom_point(data = neigh, aes(x, y), shape = 21, fill = "white", colour = INK, size = 1.8) +
  geom_point(aes(x = sx, y = sy), shape = 23, size = 4, fill = ACCENT, colour = "white", stroke = 0.8) +
  annotate("text", x = sx, y = sy, label = P$signum, vjust = -1.3, size = 3.2, fontface = "bold", colour = INK) +
  coord_sf(xlim = c(win$xmin[[1]], win$xmax[[1]]), ylim = c(win$ymin[[1]], win$ymax[[1]]), crs = SWEREF, datum = NA, expand = FALSE) +
  labs(title = sprintf("%s i landskapet", P$signum),
       subtitle = sprintf("Mörkblått: dagens vatten. Ljusblått: under %s m, ungefär stranden vid vikingatiden. Blå linjer: bästa vägar mellan andra runstensplatser i närheten.",
                          format(uplift)),
       caption = "Höjddata: Terrain Tiles (Tilezen/Mapzen, AWS Open Data). Strandlinjen är en grov modell utan hänsyn till sediment och dämning.") +
  theme_map()
fig_land <- save_fig(p, out, "landskap_karta.png", 7.5, 7.5)

vs_df <- as.data.frame(vs, xy = TRUE); names(vs_df)[3] <- "v"; vs_df <- vs_df[vs_df$v == 1, ]
hs2 <- hs_df[hs_df$x >= sx - VIEW_KM * 1000 & hs_df$x <= sx + VIEW_KM * 1000 & hs_df$y >= sy - VIEW_KM * 1000 & hs_df$y <= sy + VIEW_KM * 1000, ]
p <- ggplot() +
  geom_raster(data = hs2, aes(x, y, fill = hs), show.legend = FALSE) +
  scale_fill_gradient(low = "#475569", high = "#f8fafc") +
  geom_raster(data = wt_df[wt_df$x %in% hs2$x & wt_df$y %in% hs2$y, ], aes(x, y), fill = "#bcd3ee", alpha = 0.7) +
  geom_raster(data = vs_df, aes(x, y), fill = "#f59e0b", alpha = 0.55) +
  geom_point(aes(x = sx, y = sy), shape = 23, size = 4, fill = ACCENT, colour = "white", stroke = 0.8) +
  coord_sf(xlim = c(sx - VIEW_KM * 1000, sx + VIEW_KM * 1000), ylim = c(sy - VIEW_KM * 1000, sy + VIEW_KM * 1000),
           crs = SWEREF, datum = NA, expand = FALSE) +
  labs(title = sprintf("Var %s syns", P$signum),
       subtitle = sprintf("Gult: platser där en person (1,6 m) ser stenens topp (2 m) inom %d km. Synligt inom 2 km: %.0f %% av ytan.",
                          VIEW_KM, 100 * view$share_2km),
       caption = "Höjdmodellen saknar skog och byggnader i vikingatida form; sikten är en övre gräns i öppet landskap.") +
  theme_map()
fig_view <- save_fig(p, out, "landskap_sikt.png", 7, 7)

result <- list(
  signum = P$signum, uplift_m = uplift, radius_km = RADIUS_KM, resolution_m = 20,
  terrain = list(elevation_m = r1(elev_s), slope_deg = r1(slope_s), tpi300_m = r1(tpi300), lower_share_2km = r3(lower_share)),
  shore = list(today_km = r3(shore_now_km), viking_age_km = r3(shore_then_km)),
  view = view, routes = routes,
  figures = list(map = fig_land, view = fig_view),
  method = paste(
    "Höjdmodellen är Terrain Tiles (zoomnivå 12, ca 20 m) omprojicerad till SWEREF 99 TM. Stenens läge beskrivs med",
    "höjd, lutning, topografiskt positionsindex (höjd minus medelhöjden inom 300 m) och andelen av omgivningen inom 2 km",
    "som ligger lägre. Stranden vid vikingatiden modellerades som dagens höjd minus landhöjningen sedan omkring år 1000",
    sprintf("(%s m för %s, en grov skattning). Sikten beräknades med terra::viewshed (stenens topp 2 m, betraktare 1,6 m,", format(uplift), row$province),
    "jordens krökning och ljusbrytning) och jämfördes med slumpvisa punkter på land inom 3 km. Bästa vägar mellan",
    "runstensplatser inom", RADIUS_KM, "km (andra platser än stenens egen, minst", SITE_KM, "km isär) beräknades med gdistance på en kostnadsyta efter Toblers vandringsfunktion (vatten tio gånger långsammare),",
    "och stenens avstånd till vägnätet jämfördes med slumpvisa punkter på land i samma område."
  ),
  caveat = paste(
    "Höjddata är en sammanställning av flera källor och visar dagens markyta; vägar är simulerade bästa vägar i terrängen,",
    "inte belagda vikingatida vägar. Grannstenarna kan själva stå vid vägar, så vägnätet är inte oberoende av stenarnas lägen."
  )
)
write_result(result, out, "landscape")
