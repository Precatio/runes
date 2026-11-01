# Steg 1, ett landskap per process:  Rscript --vanilla utdata/strand/01_avstand.R <landskap>
# Slumppunkter (huvudnollmodellen, R7 2 och 10 km, D1 med flyttade stenar) och avståndet till SGU:s vatten i alla
# tidssnitt för stenar och punkter. Avstånden räknas i rutor (40 km kärna + 15 km marginal, 25 m celler) så att bara en
# liten raster i taget finns i minnet; ett avstånd som når marginalen flaggas.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "config.R"))
pv <- commandArgs(trailingOnly = TRUE)[1]
stopifnot(pv %in% PROVS)
key <- pv_key(pv)
CORE <- 40000; BUF <- 15000
S <- load_stones()
g_all <- S$all6[S$all6$province == pv, ]
g_pop <- g_all[g_all$moved == 0, ]
tmpl <- prov_template(g_all)
E <- unname(as.vector(ext(tmpl)))
say(pv, ": ", nrow(g_pop), " icke flyttade, ", nrow(g_all), " alla")

# ---- random points: uniform in the union of buffers, rejected if in water in AD 1050 or 1949 (point in polygon) -----
w900 <- st_geometry(read_slice(MAIN, E)); w1 <- st_geometry(read_slice(NOW, E))
in_water <- function(p) lengths(st_intersects(p, w900)) > 0 | lengths(st_intersects(p, w1)) > 0
sample_points <- function(g, radius, n) {
  area <- st_union(st_buffer(st_as_sf(g, coords = c("x", "y"), crs = SWEREF), radius))
  got <- NULL
  while (is.null(got) || nrow(got) < n) {
    s <- st_sample(area, size = ceiling(n * 1.5), type = "random")
    s <- s[!in_water(s)]
    got <- rbind(got, st_coordinates(s))
  }
  got <- got[seq_len(n), , drop = FALSE]
  data.frame(province = pv, x = got[, 1], y = got[, 2])
}
set.seed(SEED)
rnd <- list(main = sample_points(g_pop, LOCAL, NPER * nrow(g_pop)),
            r2 = sample_points(g_pop, 2000, NPER * nrow(g_pop)),
            r10 = sample_points(g_pop, 10000, NPER * nrow(g_pop)),
            d1 = sample_points(g_all, LOCAL, NPER * nrow(g_all)))
rm(w900, w1); gc(verbose = FALSE)
say("slumppunkter ", paste(sapply(rnd, nrow), collapse = "/"))

# ---- distances, tile by tile -------------------------------------------------------------------------------------
sets <- c(list(stones = data.frame(x = g_all$x, y = g_all$y)), lapply(rnd, function(r) r[, c("x", "y")]))
tile_of <- function(df) paste(floor((df$x - E[1]) / CORE), floor((df$y - E[3]) / CORE))
tiles <- unique(unlist(lapply(sets, tile_of)))
slices <- list(then = list(MAIN, c(1, 4)), now = list(NOW, c(1, 4)), sea = list(MAIN, 1))
for (bp in c(R1, R1X)) slices[[paste0("s", bp)]] <- list(bp, c(1, 4))
res <- lapply(sets, function(s) as.data.frame(matrix(NA_real_, nrow(s), length(slices), dimnames = list(NULL, names(slices)))))
flag <- 0L
for (tl in tiles) {
  ij <- as.numeric(strsplit(tl, " ")[[1]])
  x0 <- E[1] + ij[1] * CORE; y0 <- E[3] + ij[2] * CORE
  te <- c(x0 - BUF, x0 + CORE + BUF, y0 - BUF, y0 + CORE + BUF)
  tr_ <- rast(ext(te), resolution = RES, crs = "EPSG:3006")
  for (nm in names(slices)) {
    w <- read_slice(slices[[nm]][[1]], te, slices[[nm]][[2]])
    m <- if (nrow(w)) rasterize(vect(w), tr_, field = 1, touches = FALSE) else init(tr_, NA)
    dr <- if (global(m, "notNA")[1, 1] > 0) distance(m) else init(tr_, Inf)
    for (k in names(sets)) {
      i <- which(tile_of(sets[[k]]) == tl)
      if (length(i)) res[[k]][i, nm] <- at(dr, sets[[k]]$x[i], sets[[k]]$y[i])
    }
    rm(w, m, dr)
  }
  gc(verbose = FALSE)
  say("ruta ", tl)
}
for (k in names(res)) {
  big <- as.matrix(res[[k]]) >= BUF * 0.95
  flag <- flag + sum(big, na.rm = TRUE)
}
stones <- cbind(data.frame(signum = g_all$signum), res$stones)
for (k in names(rnd)) rnd[[k]] <- cbind(rnd[[k]], res[[k]])
saveRDS(list(province = pv, stones = stones, rnd = rnd, flagged = flag, core = CORE, buffer = BUF),
        file.path(WORK, paste0(key, "_avstand.rds")))
say("klart ", pv, "; avstånd vid marginalen: ", flag)
