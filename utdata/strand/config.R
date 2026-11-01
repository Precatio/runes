# Gemensamma inställningar för stegen i utdata/strand/ (planen analysplaner/2026-10-23-strand-och-gravfalt.md).
# Varje steg körs som en egen R-process (kör.sh), så att höjd- och vattenrastrar för ett landskap i taget hålls i minnet.
.proj <- local({f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)); if (length(f)) normalizePath(file.path(dirname(f[1]), "../..")) else normalizePath(".")})  # projektmappen (Rscript), annars arbetsmappen
REPO <- .proj
source(file.path(REPO, "r", "common.R"))
suppressPackageStartupMessages({ library(sf); library(terra) })
sf_use_s2(FALSE)
CACHE <- "/Volumes/2TB/cache/strand"
WORK <- file.path(CACHE, "work")
dir.create(file.path(CACHE, "tmp"), showWarnings = FALSE)
dir.create(WORK, showWarnings = FALSE)
terraOptions(tempdir = file.path(CACHE, "tmp"), progress = 0, memfrac = 0.25)
OUT <- file.path(REPO, "utdata", "strand")
T0 <- Sys.time()
say <- function(...) message(format(round(as.numeric(difftime(Sys.time(), T0, units = "secs")))), " s  ", ...)

CORPUS <- file.path(REPO, "data/cache/r/corpus/d6cffd1578418f74/corpus.csv")
REMAINS <- file.path(REPO, "data/raa/lamningar.csv")
GPKG_A <- file.path(CACHE, "sgu/strandforskjutning_1_900.gpkg")
GPKG_B <- file.path(CACHE, "sgu/strandforskjutning_1000_1900.gpkg")
COP_DIR <- file.path(CACHE, "copernicus")
SEED <- 2026
PROVS <- c("U", "Sö", "Ög", "Sm", "Vg", "Öl")
PROV_NAME <- c(U = "Uppland", "Sö" = "Södermanland", "Ög" = "Östergötland", Sm = "Småland", Vg = "Västergötland",
               "Öl" = "Öland")
RES <- 25            # m, raster for SGU:s water
MARGIN <- 20000      # m around the province's stones
LOCAL <- 5000        # m, the null model's radius
NPER <- 10           # random points per stone
MAIN <- "900"        # BP = AD 1050
NOW <- "1"           # BP = AD 1949
R1 <- c("1200", "1000", "800", "700")
R1X <- c("1400", "400")
B_BOOT <- 2000
SITE_M <- 200
bp_year <- function(bp) 1950 - as.integer(bp)
pv_key <- function(pv) c(U = "U", "Sö" = "So", "Ög" = "Og", Sm = "Sm", Vg = "Vg", "Öl" = "Ol")[[pv]]

load_stones <- function() {
  all <- read_corpus(CORPUS) %>% filter(!is.na(lat), !is.na(lon))
  all$moved[is.na(all$moved)] <- 0
  all$year <- ifelse(!is.na(all$style_from), (all$style_from + all$style_to) / 2, NA)
  all$t50 <- (all$year - 1050) / 50
  all$christian <- as.integer(all$cross == 1 | all$cat_kristen == 1)
  all6 <- all %>% filter(province %in% PROVS)
  xy <- st_coordinates(st_transform(st_as_sf(all6, coords = c("lon", "lat"), crs = 4326), SWEREF))
  all6$x <- xy[, 1]; all6$y <- xy[, 2]
  list(all = all, all6 = all6)
}

prov_template <- function(g, res = RES) {
  e <- c(floor((min(g$x) - MARGIN) / res) * res, ceiling((max(g$x) + MARGIN) / res) * res,
         floor((min(g$y) - MARGIN) / res) * res, ceiling((max(g$y) + MARGIN) / res) * res)
  rast(ext(e), resolution = res, crs = "EPSG:3006")
}

read_slice <- function(bp, e, codes = c(1, 4)) {
  f <- if (as.integer(bp) < 1000) GPKG_A else GPKG_B
  bb <- st_as_sfc(st_bbox(c(xmin = e[1], ymin = e[3], xmax = e[2], ymax = e[4]), crs = st_crs(SWEREF)))
  w <- st_read(f, paste0("issjohav_", bp), wkt_filter = st_as_text(bb), quiet = TRUE)
  w <- w[w$code %in% codes, ]
  st_crs(w) <- SWEREF
  w
}
# 1 in water (cell centre inside a polygon of the chosen codes), NA elsewhere
water_mask <- function(bp, tmpl, codes = c(1, 4), filename = "") {
  e <- unname(as.vector(ext(tmpl)))
  w <- read_slice(bp, e, codes)
  if (!nrow(w)) return(init(tmpl, NA))
  rasterize(vect(w), tmpl, field = 1, touches = FALSE, datatype = "INT1U", filename = filename, overwrite = TRUE)
}
at <- function(r, x, y) terra::extract(r, cbind(x, y))[, 1]
