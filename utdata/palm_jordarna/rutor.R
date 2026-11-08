# Palms jordar (analysplaner/2026-11-08-palm-jordarna.md, sha 85a70fa3): bygderutorna. Per ruta (2 km, eller argumentet
# i meter): landyta år 1050, andelen lera och silt och övriga klasser av marken, gravfält, avståndet till vattnet år
# 1050 och det vikingatida landet; runstenar (inte flyttade eller försvunna). Skriver rutor_<m>.csv.
#   Rscript utdata/palm_jordarna/rutor.R 2000
suppressMessages({library(sf); library(terra); library(jsonlite)})
args <- commandArgs(trailingOnly = TRUE)
CELL <- if (length(args)) as.numeric(args[1]) else 2000
HERE <- "utdata/palm_jordarna"
GEO <- "/Volumes/2TB/Antigrvity/Runes/geografi_kallor"
terraOptions(memfrac = 0.4, tempdir = "/Volumes/2TB/cache/terra")
dir.create("/Volumes/2TB/cache/terra", showWarnings = FALSE, recursive = TRUE)

meta <- fromJSON(file.path(HERE, "jordart_100m.json"))
r <- rast(file.path(HERE, "jordart_100m.tif"))
ext(r) <- c(meta$xmin, meta$xmax, meta$ymin, meta$ymax); crs(r) <- "EPSG:3006"

# water around 1050 (SGU shoreline model, 900 years before present), on the 100 m grid; cached
wfile <- "/Volumes/2TB/cache/terra/vatten1050_100m.tif"
if (!file.exists(wfile)) {
  w <- st_read(file.path(GEO, "sgu/strandforskjutning_1_900.gpkg"), layer = "issjohav_900", quiet = TRUE)
  w <- st_transform(st_make_valid(w), 3006)
  wr <- rasterize(vect(w), r, field = 1, background = 0, filename = wfile, overwrite = TRUE, datatype = "INT1U")
}
wr <- rast(wfile)
mapped <- (r >= 1) & (r <= 7) & (r != 6)        # soil-mapped land (not water, not unmapped)
land <- mapped & (wr == 0)                        # and above the water of 1050
fact <- CELL / 100
agg <- function(x) aggregate(x, fact, sum, na.rm = TRUE)
landc <- agg(land)
cls <- lapply(1:7, function(k) agg(land & (r == k)))
names(cls) <- c("lera_silt", "sand_grus", "moran", "torv_gyttja", "berg", "vatten", "ovrigt")

# distance from every 500 m cell to the water of 1050
dfile <- "/Volumes/2TB/cache/terra/avstand_vatten1050_500m.tif"
if (!file.exists(dfile)) {
  w5 <- aggregate(wr, 5, max)
  w5 <- classify(w5, cbind(0, NA))
  distance(w5, filename = dfile, overwrite = TRUE)
}
dw <- rast(dfile)

# grave fields (KMR points and polygons, type Gravfält), with their parish
kmr <- file.path(GEO, "raa/lamningar_sverige.gpkg")
gp <- st_read(kmr, query = "SELECT socken, geometri FROM \"lämningar_sverige_point\" WHERE lamningstyp = 'Gravfält'", quiet = TRUE)
gq <- st_read(kmr, query = "SELECT socken, geometri FROM \"lämningar_sverige_polygon\" WHERE lamningstyp = 'Gravfält'", quiet = TRUE)
gq <- st_point_on_surface(gq)
gf <- rbind(gp, gq)
gf <- st_transform(gf, 3006)

# the grave field's Viking-age land: folkland, small land or treding by polygon; otherwise its parish's province
lands <- st_transform(st_read("web/public/geo/land.geojson", quiet = TRUE), 3006)
gf$land <- lands$id[st_intersects(gf, lands) |> vapply(function(i) if (length(i)) i[1] else NA_integer_, 1L)]
isof <- fromJSON(file.path(GEO, "isof/parishes.json"))
prov <- fromJSON(file.path(GEO, "isof/provinces.json"))
CODE <- c(Uppland = "U", "Södermanland" = "Sö", "Östergötland" = "Ög", "Västergötland" = "Vg", "Småland" = "Sm",
          "Öland" = "Öl", Gotland = "G", "Västmanland" = "Vs", "Närke" = "Nä", "Värmland" = "Vr", Dalarna = "D",
          "Gästrikland" = "Gs", "Hälsingland" = "Hs", Medelpad = "M", "Ångermanland" = "Ån", Dalsland = "Dsl",
          "Bohuslän" = "Bo", Halland = "Hl", "Skåne" = "Sk", Blekinge = "Bl", "Jämtland" = "J", "Härjedalen" = "Hr")
isof$prov <- CODE[prov$name[match(isof$province_id, prov$id)]]
isof <- isof[!is.na(isof$latitude) & !is.na(isof$prov), ]
ip <- st_transform(st_as_sf(isof, coords = c("longitude", "latitude"), crs = 4326), 3006)
ip$key <- tolower(sub(" sn$", "", ip$name))
gf$key <- tolower(trimws(gf$socken))
gf$prov <- NA_character_
for (k in unique(gf$key)) {
  i <- which(gf$key == k)
  cand <- which(ip$key == k | ip$key == paste0(k, "s"))
  if (!length(cand)) cand <- seq_len(nrow(ip))       # no name match: the nearest parish
  j <- cand[st_nearest_feature(gf[i, ], ip[cand, ])]
  gf$prov[i] <- ip$prov[j]
}
gf$region <- ifelse(is.na(gf$land), gf$prov, gf$land)

# runestones: not moved, not lost, with coordinates
corp <- read.csv("data/cache/r/corpus/510ebfb3acc9a229/corpus.csv")
st <- corp[corp$moved == 0 & corp$lost == 0 & !is.na(corp$lat) & !(corp$province %in% c("Sk", "Hl", "Bl", "Bo")), ]
sx <- st_coordinates(st_transform(st_as_sf(st, coords = c("lon", "lat"), crs = 4326), 3006))

# the cells
xy <- xyFromCell(landc, 1:ncell(landc))
cid_st <- cellFromXY(landc, sx)
cid_gf <- cellFromXY(landc, st_coordinates(gf))
n_st <- tabulate(cid_st[!is.na(cid_st)], ncell(landc))
n_gf <- tabulate(cid_gf[!is.na(cid_gf)], ncell(landc))
reg <- tapply(gf$region, cid_gf, function(v) names(sort(table(v), decreasing = TRUE))[1])
d <- data.frame(cell = 1:ncell(landc), x = xy[, 1], y = xy[, 2], stones = n_st, gravefields = n_gf,
                land_px = values(landc)[, 1])
for (k in names(cls)) d[[k]] <- values(cls[[k]])[, 1]
d$region <- NA_character_
d$region[as.integer(names(reg))] <- unname(reg)
d <- d[!is.na(d$land_px) & d$gravefields >= 1 & d$land_px / fact^2 >= 0.25 & !is.na(d$region) &
       !(d$region %in% c("Sk", "Hl", "Bl", "Bo")), ]
d$land_km2 <- d$land_px * 0.01
d$clay <- d$lera_silt / d$land_px
d$dist_water_km <- extract(dw, d[, c("x", "y")])[, 2] / 1000
d$dist_water_km[is.na(d$dist_water_km)] <- 0           # the cell's centre is in the water of 1050
d$block <- paste(floor(d$x / 20000), floor(d$y / 20000))
write.csv(d, file.path(HERE, sprintf("rutor_%d.csv", CELL)), row.names = FALSE)
cat(sprintf("%d m: %d bygderutor, %d runstenar i dem (av %d), %d gravfält; %d land\n", CELL, nrow(d), sum(d$stones),
            nrow(st), sum(d$gravefields), length(unique(d$region))))
