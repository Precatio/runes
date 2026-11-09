# Kartor till artikeln: Mälardalen med lera och silt (SGU), vattnet omkring år 1050 (SGU:s strandförskjutningsmodell) och
# runstenarna som står kvar på sin plats, med inzoomningens ram; och inzoomningen (Täby–Vallentuna, jordarterna i 10 m ur
# zoom_jord.py) med gravfälten. Ingen text i bilderna (bildtexterna står i artikeln, på svenska och engelska).
#   Rscript utdata/palm_jordarna/karta.R
suppressMessages({library(terra); library(sf); library(jsonlite)})
HERE <- "utdata/palm_jordarna"
meta <- fromJSON(file.path(HERE, "jordart_100m.json"))
r <- rast(file.path(HERE, "jordart_100m.tif")); ext(r) <- c(meta$xmin, meta$xmax, meta$ymin, meta$ymax); crs(r) <- "EPSG:3006"
wr <- rast("/Volumes/2TB/cache/terra/vatten1050_100m.tif")
E <- ext(530000, 720000, 6530000, 6700000)
r <- crop(r, E); wr <- crop(wr, E)
code <- ifel(wr == 1, 3, ifel(r == 1, 2, ifel(r >= 2 & r <= 7 & r != 6, 1, ifel(r == 6, 3, 0))))
cols <- c("#ffffff", "#e7e2d8", "#c9a227", "#9cc3e6")   # unmapped, other soils, clay and silt, water around 1050
corp <- read.csv("data/cache/r/corpus/510ebfb3acc9a229/corpus.csv")
st <- corp[corp$moved == 0 & corp$lost == 0 & !is.na(corp$lat), ]
p <- st_coordinates(st_transform(st_as_sf(st, coords = c("lon", "lat"), crs = 4326), 3006))
p <- p[p[, 1] > E[1] & p[, 1] < E[2] & p[, 2] > E[3] & p[, 2] < E[4], ]
png(file.path(HERE, "karta_malardalen.png"), width = 1600, height = round(1600 * 170 / 190), res = 150)
par(mar = c(0, 0, 0, 0))
plot(code, col = data.frame(value = 0:3, color = cols), type = "classes", legend = FALSE, axes = FALSE, box = FALSE, maxcell = 4e6, mar = c(0, 0, 0, 0))
points(p[, 1], p[, 2], pch = 21, bg = "#b7410e", col = "#3b1a08", cex = 0.55, lwd = 0.4)
zm <- fromJSON(file.path(HERE, "jordart_zoom.json"))
rect(zm$xmin, zm$ymin, zm$xmax, zm$ymax, border = "#1f2937", lwd = 2.2)
dev.off()
cat(nrow(p), "stenar på kartan\n")

# --- the zoom: soils at 10 m, water around 1050, grave fields and runestones; a 2 km bar at the bottom left
z <- rast(file.path(HERE, "jordart_zoom.tif")); ext(z) <- c(zm$xmin, zm$xmax, zm$ymin, zm$ymax); crs(z) <- "EPSG:3006"
w <- st_read("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/sgu/strandforskjutning_1_900.gpkg", layer = "issjohav_900", quiet = TRUE)
w <- st_transform(st_make_valid(w), 3006)
w <- suppressWarnings(st_crop(w, st_bbox(c(xmin = zm$xmin, ymin = zm$ymin, xmax = zm$xmax, ymax = zm$ymax), crs = st_crs(3006))))
wz <- rasterize(vect(w), z, field = 1, background = 0)
cz <- ifel(wz == 1, 3, ifel(z == 1, 2, ifel(z >= 2 & z <= 7 & z != 6, 1, ifel(z == 6, 3, 0))))
inz <- function(m) m[m[, 1] > zm$xmin & m[, 1] < zm$xmax & m[, 2] > zm$ymin & m[, 2] < zm$ymax, , drop = FALSE]
gfz <- inz(as.matrix(read.csv("/Volumes/2TB/cache/terra/gravfalt_xy.csv")))
pz <- inz(p)
png(file.path(HERE, "karta_zoom.png"), width = 1600, height = 1600, res = 150)
par(mar = c(0, 0, 0, 0))
plot(cz, col = data.frame(value = 0:3, color = cols), type = "classes", legend = FALSE, axes = FALSE, box = FALSE, maxcell = 5e6, mar = c(0, 0, 0, 0))
points(gfz[, 1], gfz[, 2], pch = 17, col = "#374151", cex = 0.55)
points(pz[, 1], pz[, 2], pch = 21, bg = "#b7410e", col = "#3b1a08", cex = 1.25, lwd = 0.8)
bx <- zm$xmin + 800; by <- zm$ymin + 700
rect(bx - 250, by - 300, bx + 2000 + 250, by + 300, col = "#ffffffcc", border = NA)
segments(bx, by, bx + 2000, by, lwd = 4, col = "#1f2937", lend = 1)
dev.off()
cat(nrow(pz), "stenar och", nrow(gfz), "gravfält i inzoomningen\n")
