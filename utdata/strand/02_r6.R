# Steg 2 (robusthet R6), ett landskap per process:  Rscript --vanilla utdata/strand/02_r6.R <landskap>
# Oberoende höjdmodell: Copernicus GLO-30. Vatten omkring år 1050 = mark på höjd högst landskapets landhöjning
# (r/common.R) + δ (δ = −1, 0, +1 m) som hänger samman med havet år 1949 (SGU), plus SGU:s hav och sjöar år 1949.
# Sammanhanget avgörs på ett 90 m-rutnät för hela landskapet (lägsta höjden i varje cell, så att smala sund finns kvar);
# avstånden räknas i rutor om 30 m.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "config.R"))
pv <- commandArgs(trailingOnly = TRUE)[1]
stopifnot(pv %in% PROVS)
key <- pv_key(pv)
CORE <- 40000; BUF <- 15000; R30 <- 30; R90 <- 90
DELTAS <- c(-1, 0, 1)
up <- UPLIFT[[pv]]
A <- readRDS(file.path(WORK, paste0(key, "_avstand.rds")))
S <- load_stones()
g_all <- S$all6[S$all6$province == pv, ]
cop <- vrt(list.files(COP_DIR, pattern = "_DEM\\.tif$", full.names = TRUE))
dem_for <- function(e, res, method) {
  t <- rast(ext(e), resolution = res, crs = "EPSG:3006")
  bb <- st_bbox(st_transform(st_as_sfc(st_bbox(c(xmin = e[1], ymin = e[3], xmax = e[2], ymax = e[4]), crs = st_crs(SWEREF))), 4326))
  project(crop(cop, ext(bb[["xmin"]] - 0.05, bb[["xmax"]] + 0.05, bb[["ymin"]] - 0.03, bb[["ymax"]] + 0.03)), t, method = method)
}
t90 <- prov_template(g_all, R90)
E <- unname(as.vector(ext(t90)))
dem90 <- dem_for(E, R90, "min")
sea90 <- { w <- read_slice(NOW, E, 1); rasterize(vect(w), t90, field = 1, touches = TRUE) }
conn <- list()
for (dl in DELTAS) {
  low <- ifel(!is.na(dem90) & dem90 <= up + dl, 1, NA)
  pt <- patches(cover(low, sea90), directions = 8)   # SGU's sea of 1949 joins the low ground it touches
  ids <- unique(values(mask(pt, sea90))[, 1]); ids <- ids[!is.na(ids)]
  conn[[as.character(dl)]] <- ifel(pt %in% ids, 1, NA, filename = file.path(WORK, paste0(key, "_conn", dl, ".tif")),
                                   overwrite = TRUE, datatype = "INT1U")
  rm(low, pt); gc(verbose = FALSE)
}
rm(dem90); gc(verbose = FALSE)
say(pv, ": sammanhang på 90 m klart (nivå ", up, " m ± 1)")

sets <- c(list(stones = data.frame(x = g_all$x, y = g_all$y)), list(main = A$rnd$main[, c("x", "y")]))
tile_of <- function(df) paste(floor((df$x - E[1]) / CORE), floor((df$y - E[3]) / CORE))
tiles <- unique(unlist(lapply(sets, tile_of)))
res <- lapply(sets, function(s) as.data.frame(matrix(NA_real_, nrow(s), length(DELTAS),
                                                    dimnames = list(NULL, paste0("d", DELTAS)))))
for (tl in tiles) {
  ij <- as.numeric(strsplit(tl, " ")[[1]])
  x0 <- E[1] + ij[1] * CORE; y0 <- E[3] + ij[2] * CORE
  te <- c(x0 - BUF, x0 + CORE + BUF, y0 - BUF, y0 + CORE + BUF)
  te <- c(floor(te[1] / R30) * R30, ceiling(te[2] / R30) * R30, floor(te[3] / R30) * R30, ceiling(te[4] / R30) * R30)
  tt <- rast(ext(te), resolution = R30, crs = "EPSG:3006")
  dem <- dem_for(te, R30, "bilinear")
  w49 <- read_slice(NOW, te, c(1, 4))
  m49 <- if (nrow(w49)) rasterize(vect(w49), tt, field = 1, touches = FALSE) else init(tt, NA)
  for (dl in DELTAS) {
    cn <- resample(crop(conn[[as.character(dl)]], ext(tt), snap = "out"), tt, method = "near")
    w <- cover(ifel(!is.na(dem) & dem <= up + dl & !is.na(cn), 1, NA), m49)
    dr <- distance(w)
    for (k in names(sets)) {
      i <- which(tile_of(sets[[k]]) == tl)
      if (length(i)) res[[k]][i, paste0("d", dl)] <- at(dr, sets[[k]]$x[i], sets[[k]]$y[i])
    }
    rm(cn, w, dr)
  }
  rm(dem, m49); gc(verbose = FALSE)
  say("ruta ", tl)
}
saveRDS(list(province = pv, level_m = up, stones = cbind(data.frame(signum = g_all$signum), res$stones),
             main = res$main), file.path(WORK, paste0(key, "_r6.rds")))
unlink(file.path(WORK, paste0(key, "_conn", DELTAS, ".tif")))
say("klart R6 ", pv)
