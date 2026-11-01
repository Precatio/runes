# Steg 1b, ett landskap per process:  Rscript --vanilla utdata/strand/01b_marginal.R <landskap>
# Avstånd som i steg 1 nådde rutornas marginal (≥ 95 % av 15 km; i praktiken bara R2, bara havet, långt inne i landet)
# ersätts med avståndet på en raster om 100 m över hela landskapet. Övriga avstånd behåller 25 m-värdet.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "config.R"))
pv <- commandArgs(trailingOnly = TRUE)[1]
key <- pv_key(pv)
f <- file.path(WORK, paste0(key, "_avstand.rds"))
a <- readRDS(f)
LIM <- a$buffer * 0.95
slices <- list(then = list(MAIN, c(1, 4)), now = list(NOW, c(1, 4)), sea = list(MAIN, 1))
for (bp in c(R1, R1X)) slices[[paste0("s", bp)]] <- list(bp, c(1, 4))
S <- load_stones()
g_all <- S$all6[S$all6$province == pv, ]
xy <- list(stones = g_all[match(a$stones$signum, g_all$signum), c("x", "y")])
for (k in names(a$rnd)) xy[[k]] <- a$rnd[[k]][, c("x", "y")]
get <- function(k) if (k == "stones") a$stones else a$rnd[[k]]
replaced <- list()
for (nm in names(slices)) {
  need <- sapply(names(xy), function(k) any(get(k)[[nm]] >= LIM, na.rm = TRUE))
  if (!any(need)) next
  t100 <- prov_template(g_all, 100)
  # A wider frame for the coarse raster, so that the far points also find their nearest water
  e <- unname(as.vector(ext(t100))) + c(-30000, 30000, -30000, 30000)
  t100 <- rast(ext(e), resolution = 100, crs = "EPSG:3006")
  dr <- distance(water_mask(slices[[nm]][[1]], t100, slices[[nm]][[2]]))
  n <- 0
  for (k in names(xy)) {
    v <- get(k)[[nm]]; i <- which(v >= LIM)
    if (!length(i)) next
    v[i] <- at(dr, xy[[k]]$x[i], xy[[k]]$y[i]); n <- n + length(i)
    if (k == "stones") a$stones[[nm]] <- v else a$rnd[[k]][[nm]] <- v
  }
  replaced[[nm]] <- n
  rm(dr); gc(verbose = FALSE)
  say(pv, " ", nm, ": ", n, " avstånd ersatta med 100 m-värden")
}
a$replaced_100m <- replaced
saveRDS(a, f)
say("klart 1b ", pv)
