# Fornborgarnas strandkurva: avståndet till vatten vid 19 tider (SGU:s strandförskjutningsmodell) för borgarna och samma
# jämförelsepunkter som i förra körningen (punkter.csv). Låst plan analysplaner/2026-11-18-fornborgarnas-strandkurva.md
# (sha256 ba363a4b).
#   Rscript utdata/fornborgar/strandkurva.R            (STEG=avstand hoppar över analysen; STEG=analys återanvänder csv:n)
suppressPackageStartupMessages({library(sf); library(jsonlite); library(dplyr)})
sf_use_s2(FALSE)
here <- local({f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)); dirname(normalizePath(f[1]))})
repo <- normalizePath(file.path(here, "..", ".."))
plan <- file.path(repo, "analysplaner", "2026-11-18-fornborgarnas-strandkurva.md")
sha <- sub(" .*", "", system2("shasum", c("-a", "256", shQuote(plan)), stdout = TRUE))
stopifnot(startsWith(sha, "ba363a4b"))
SEED <- strtoi(substr(sha, 1, 7), 16L)
SW <- "EPSG:3006"; CAP <- 15000; TILE <- 40000
DIR <- "/Volumes/2TB/cache/strand/sgu"
BP <- c(1900, 1800, 1700, 1600, 1500, 1400, 1300, 1200, 1000, 900, 800, 700, 600, 500, 400, 300, 200, 100, 1)
YEAR <- 1950 - BP; YEAR[BP == 1] <- 2000  # "i dag"
gpkg <- function(bp) file.path(DIR, if (bp >= 1000) "strandforskjutning_1000_1900.gpkg" else "strandforskjutning_1_900.gpkg")
T0 <- Sys.time(); say <- function(...) message(round(as.numeric(difftime(Sys.time(), T0, units = "secs"))), " s  ", ...)
STEG <- Sys.getenv("STEG")
OUT <- file.path(here, "strandavstand.csv")

P <- read.csv(file.path(here, "punkter.csv"))
P <- P[P$kind %in% c("borg", "berg", "mark"), c("x", "y", "kind", "id")]

if (STEG != "analys") {
  P$tile <- paste(floor(P$x / TILE), floor(P$y / TILE))
  D <- matrix(NA_real_, nrow(P), length(BP), dimnames = list(NULL, paste0("bp", BP)))
  tiles <- unique(P$tile)
  for (j in seq_along(BP)) {
    for (tl in tiles) {
      i <- which(P$tile == tl)
      bb <- c(xmin = min(P$x[i]) - CAP, ymin = min(P$y[i]) - CAP, xmax = max(P$x[i]) + CAP, ymax = max(P$y[i]) + CAP)
      w <- st_read(gpkg(BP[j]), paste0("issjohav_", BP[j]),
                   wkt_filter = st_as_text(st_as_sfc(st_bbox(bb, crs = st_crs(SW)))), quiet = TRUE)
      w <- w[w$code %in% c(1, 4), ]
      if (!nrow(w)) { D[i, j] <- CAP; next }
      st_crs(w) <- SW
      pts <- st_as_sf(P[i, ], coords = c("x", "y"), crs = SW)
      dm <- st_distance(pts, st_geometry(w))
      D[i, j] <- pmin(apply(matrix(as.numeric(dm), nrow = length(i)), 1, min), CAP)
    }
    say("BP ", BP[j], " (år ", YEAR[j], ") klart")
  }
  write.csv(cbind(P[, c("x", "y", "kind", "id")], D), OUT, row.names = FALSE)
  if (STEG == "avstand") quit(save = "no")
}

# ---- analysis
A <- read.csv(OUT)
cols <- paste0("bp", BP)
f <- read.csv("/Volumes/2TB/Antigrvity/Runes/downloads/fornborgar/fornborgar.csv", fileEncoding = "UTF-8")
f <- f[!is.na(f$lat), ]
# halves: within each county, parishes alternately A/B in name order (as in plan e0bd5ea5)
f$half <- NA
for (l in unique(f$lan)) {
  s <- sort(unique(f$socken[f$lan == l]))
  h <- setNames(ifelse(seq_along(s) %% 2 == 1, "A", "B"), s)
  f$half[f$lan == l] <- h[f$socken[f$lan == l]]
}
# province: nearest ISOF parish centroid
prov <- fromJSON("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/provinces.json")
par <- fromJSON("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/parishes.json")
par <- par[!is.na(par$latitude), ]
pxy <- st_coordinates(st_transform(st_as_sf(par, coords = c("longitude", "latitude"), crs = 4326), SW))
par$land <- prov$name[match(par$province_id, prov$id)]

ids <- unique(A$id)
nb <- length(ids)
U <- matrix(NA_real_, nb, length(BP), dimnames = list(ids, cols))
Um <- U
under <- matrix(FALSE, nb, length(BP), dimnames = list(ids, cols))
sens <- setNames(rep(FALSE, nb), ids)
land <- setNames(rep(NA_character_, nb), ids)
uval <- function(db, dn) {
  dn <- dn[dn > 0]
  if (db <= 0 || length(dn) < 5) return(NA_real_)
  mean((dn < db) + 0.5 * (dn == db))
}
for (k in seq_along(ids)) {
  a <- A[A$id == ids[k], ]
  b <- a[a$kind == "borg", ][1, ]
  n <- a[a$kind == "berg", ]
  m <- a[a$kind == "mark", ]
  land[k] <- par$land[which.min((pxy[, 1] - b$x)^2 + (pxy[, 2] - b$y)^2)]
  for (j in seq_along(cols)) {
    under[k, j] <- b[[cols[j]]] <= 0
    if (nrow(n) >= 5) U[k, j] <- uval(b[[cols[j]]], n[[cols[j]]])
    if (nrow(m) >= 5) Um[k, j] <- uval(b[[cols[j]]], m[[cols[j]]])
  }
  if (nrow(n) == 10) sens[k] <- sum(abs(n$bp1900 - n$bp1) >= 100) >= 3
}
say(sum(sens), " strandkänsliga borgar av ", nb)

j450 <- which(BP == 1500); j1050 <- which(BP == 900); jnow <- which(BP == 1)
curve <- function(M, rows) lapply(seq_along(BP), function(j) {
  v <- M[rows, j]; list(ar = YEAR[j], bp = BP[j], n = sum(!is.na(v)), u = if (any(!is.na(v))) mean(v, na.rm = TRUE) else NA)
})
set.seed(SEED)
signflip <- function(d, reps = 10000) {
  obs <- mean(d)
  null <- replicate(reps, mean(d * sample(c(-1, 1), length(d), replace = TRUE)))
  list(n = length(d), medel_d = obs, p = (sum(abs(null) >= abs(obs) - 1e-12) + 1) / (reps + 1))
}
S <- ids[sens & !under[, j450]]
half <- setNames(f$half[match(ids, f$uuid)], ids)
res <- list(sha = substr(sha, 1, 8), borgar = nb, strandkansliga = sum(sens), prov = list())
for (nm in c("K1_idag", "K2_vikingatid")) {
  jj <- if (nm == "K1_idag") jnow else j1050
  ok <- S[!is.na(U[S, j450]) & !is.na(U[S, jj])]
  d <- U[ok, j450] - U[ok, jj]
  r <- signflip(d)
  r$halvor <- lapply(c(A = "A", B = "B"), function(h) signflip(d[half[ok] == h], 4000))
  res$prov[[nm]] <- r
}
ph <- p.adjust(sapply(res$prov, `[[`, "p"), "holm")
for (nm in names(res$prov)) {
  r <- res$prov[[nm]]
  d0 <- sign(r$medel_d)
  okh <- all(sapply(r$halvor, function(h) isTRUE(sign(h$medel_d) == d0 && (h$p < 0.05 || h$n < 30))))
  res$prov[[nm]]$p_holm <- unname(ph[nm])
  res$prov[[nm]]$haller <- isTRUE(ph[nm] < 0.05) && okh && d0 < 0
}
sidx <- which(sens)
res$kurva_kansliga <- curve(U, sidx)
res$kurva_alla <- curve(U, seq_len(nb))
res$kurva_kansliga_all_mark <- curve(Um, sidx)
res$kurva_ovriga <- curve(U, which(!sens))
# the bottom of the curve and a bootstrap interval
bottom <- function(rows) {
  m <- colMeans(U[rows, , drop = FALSE], na.rm = TRUE)
  YEAR[which.min(m)]
}
res$botten <- bottom(sidx)
bs <- replicate(2000, bottom(sample(sidx, replace = TRUE)))
res$botten_intervall <- unname(quantile(bs, c(0.025, 0.975), type = 1))
res$botten_fordelning <- as.list(table(bs))
# under water
res$under_vatten <- lapply(seq_along(BP), function(j) list(ar = YEAR[j], n = sum(under[, j])))
uw <- ids[under[, 1]]
res$under_vatten_ar50_exempel <- head(lapply(uw, function(i) {
  r <- f[f$uuid == i, ][1, ]
  list(raa = r$raa_nummer, namn = r$lamningsnamn, socken = r$socken, forst_torr = YEAR[which(!under[i, ])[1]])
}), 40)
# per province (≥ 30 sensitive forts)
tl <- table(land[sidx])
res$per_landskap <- lapply(setNames(names(tl[tl >= 30]), names(tl[tl >= 30])), function(l) {
  rows <- sidx[land[sidx] == l]
  list(n = length(rows), botten = bottom(rows), kurva = sapply(curve(U, rows), `[[`, "u"))
})
res$ar <- YEAR
write_json(res, file.path(here, "resultat_strandkurva.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
say("klart")
print(toJSON(res[c("borgar", "strandkansliga", "prov", "botten", "botten_intervall")], auto_unbox = TRUE, digits = 4, pretty = TRUE))
cat(sprintf("%5d  n=%4d  u=%.3f\n", YEAR, sapply(res$kurva_kansliga, `[[`, "n"), sapply(res$kurva_kansliga, `[[`, "u")), sep = "")
