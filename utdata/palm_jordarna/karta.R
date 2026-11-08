# Karta till artikeln: Mälardalen med lera och silt (SGU), vattnet omkring år 1050 (SGU:s strandförskjutningsmodell) och
# runstenarna som står kvar på sin plats. Ingen text i bilden (bildtexten står i artikeln, på svenska och engelska).
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
plot(code, col = cols, type = "classes", legend = FALSE, axes = FALSE, box = FALSE, maxcell = 4e6, mar = c(0, 0, 0, 0))
points(p[, 1], p[, 2], pch = 21, bg = "#b7410e", col = "#3b1a08", cex = 0.55, lwd = 0.4)
dev.off()
cat(nrow(p), "stenar på kartan\n")
