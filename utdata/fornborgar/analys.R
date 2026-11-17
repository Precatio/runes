# Fornborgarna: vatten år 450, bygd och de gamla landens gränser (låst plan analysplaner/2026-11-17-fornborgarna.md,
# sha256 e0bd5ea5). Läser borgarna ur /Volumes/2TB/Antigrvity/Runes/downloads/fornborgar/fornborgar.csv.
#   Rscript utdata/fornborgar/analys.R
suppressPackageStartupMessages({library(sf); library(terra); library(jsonlite); library(dplyr)})
sf_use_s2(FALSE)
here <- local({f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)); dirname(normalizePath(f[1]))})
repo <- normalizePath(file.path(here, "..", ".."))
plan <- file.path(repo, "analysplaner", "2026-11-17-fornborgarna.md")
sha <- sub(" .*", "", system2("shasum", c("-a", "256", shQuote(plan)), stdout = TRUE))
stopifnot(startsWith(sha, "e0bd5ea5"))
SEED <- strtoi(substr(sha, 1, 7), 16L)
set.seed(SEED)
SW <- "EPSG:3006"
GPKG <- "/Volumes/2TB/cache/strand/sgu/strandforskjutning_1000_1900.gpkg"
NNULL <- 10; RMIN <- 200; RMAX <- 5000; WATER_WIN <- 15000; GRAVE_R <- 2000
T0 <- Sys.time(); say <- function(...) message(round(as.numeric(difftime(Sys.time(), T0, units = "secs"))), " s  ", ...)

# ---- the forts
f <- read.csv("/Volumes/2TB/Antigrvity/Runes/downloads/fornborgar/fornborgar.csv", fileEncoding = "UTF-8")
f <- f[!is.na(f$lat), ]
if (nzchar(Sys.getenv("LIMIT"))) f <- head(f, as.integer(Sys.getenv("LIMIT")))  # trial run: timing only
xy <- st_coordinates(st_transform(st_as_sf(f, coords = c("lon", "lat"), crs = 4326), SW))
f$x <- xy[, 1]; f$y <- xy[, 2]
say(nrow(f), " borgar med läge")

# ---- the soil raster (100 m; PIL-written, so georeference set from its json)
meta <- fromJSON(file.path(repo, "utdata", "palm_jordarna", "jordart_100m.json"))
soil <- rast(file.path(repo, "utdata", "palm_jordarna", "jordart_100m.tif"))
ext(soil) <- c(meta$xmin, meta$xmax, meta$ymin, meta$ymax); crs(soil) <- SW

# ---- grave fields and the old lands' shared borders
rem <- read.csv(file.path(repo, "data", "raa", "lamningar.csv"), fileEncoding = "UTF-8")
gr <- rem[rem$type == "gravfält", ]
gxy <- st_coordinates(st_transform(st_as_sf(gr, coords = c("lon", "lat"), crs = 4326), SW))
land <- st_transform(st_read(file.path(repo, "web", "public", "geo", "land.geojson"), quiet = TRUE), SW)
land <- st_make_valid(land)
pairs <- list()
for (i in seq_len(nrow(land))) for (j in seq_len(nrow(land))) if (i < j) {
  s <- suppressWarnings(st_intersection(st_boundary(land[i, ]), st_boundary(land[j, ])))
  if (nrow(s)) pairs[[length(pairs) + 1]] <- st_geometry(s)
}
border <- st_union(do.call(c, pairs))
say("gränser mellan landen: ", length(pairs), " par")

water_near <- function(x, y, r = WATER_WIN) {
  bb <- st_as_sfc(st_bbox(c(xmin = x - r, ymin = y - r, xmax = x + r, ymax = y + r), crs = st_crs(SW)))
  w <- st_read(GPKG, "issjohav_1500", wkt_filter = st_as_text(bb), quiet = TRUE)
  w <- w[w$code %in% c(1, 4), ]
  if (!nrow(w)) return(NULL)
  st_crs(w) <- SW
  st_union(st_geometry(w))
}

rank_u <- function(v_fort, v_null) mean((v_null < v_fort) + 0.5 * (v_null == v_fort))

rows <- vector("list", nrow(f))
for (k in seq_len(nrow(f))) {
  x <- f$x[k]; y <- f$y[k]
  W <- water_near(x, y)
  # candidate cells within the annulus
  win <- crop(soil, ext(x - RMAX, x + RMAX, y - RMAX, y + RMAX))
  cc <- as.data.frame(win, xy = TRUE, na.rm = TRUE)
  names(cc)[3] <- "cls"
  d <- sqrt((cc$x - x)^2 + (cc$y - y)^2)
  cc <- cc[d >= RMIN & d <= RMAX, ]
  pick <- function(pool) {
    if (!nrow(pool)) return(pool[0, ])
    pool <- pool[sample.int(nrow(pool)), ]
    if (!is.null(W)) {
      inw <- lengths(st_intersects(st_as_sf(pool, coords = c("x", "y"), crs = SW), W)) > 0
      pool <- pool[!inw, ]
    }
    head(pool, NNULL)
  }
  rock <- pick(cc[cc$cls == 5, ])
  # all land: soil cells of any land class, or (outside the raster) random points in the annulus
  anyl <- if (nrow(cc)) cc[cc$cls %in% c(1, 2, 3, 4, 5, 7), ] else cc
  if (nrow(anyl) < 50) {
    th <- runif(400, 0, 2 * pi); rr <- sqrt(runif(400, RMIN^2, RMAX^2))
    anyl <- data.frame(x = x + rr * cos(th), y = y + rr * sin(th), cls = NA)
  }
  allp <- pick(anyl)
  pts <- rbind(data.frame(x = x, y = y, kind = "borg"),
               if (nrow(rock)) data.frame(x = rock$x, y = rock$y, kind = "berg") else NULL,
               if (nrow(allp)) data.frame(x = allp$x, y = allp$y, kind = "mark") else NULL)
  ps <- st_as_sf(pts, coords = c("x", "y"), crs = SW)
  pts$water <- if (is.null(W)) WATER_WIN else pmin(as.numeric(st_distance(ps, W)), WATER_WIN)
  pts$graves <- sapply(seq_len(nrow(pts)), function(i) {
    dd <- sqrt((gxy[, 1] - pts$x[i])^2 + (gxy[, 2] - pts$y[i])^2); sum(dd >= RMIN & dd <= GRAVE_R)
  })
  inside <- lengths(st_intersects(ps[1, ], land)) > 0
  pts$border <- if (inside) as.numeric(st_distance(ps, border)) else NA
  pts$id <- f$uuid[k]
  rows[[k]] <- pts
  if (k %% 100 == 0) say(k, " borgar")
}
P <- bind_rows(rows)
write.csv(P, file.path(here, "punkter.csv"), row.names = FALSE)
say("punkter klara")

info <- f %>% select(uuid, lan, socken) %>% arrange(lan, socken)
info$half <- NA
for (l in unique(info$lan)) {
  s <- sort(unique(info$socken[info$lan == l]))
  h <- setNames(ifelse(seq_along(s) %% 2 == 1, "A", "B"), s)
  info$half[info$lan == l] <- h[info$socken[info$lan == l]]
}

u_table <- function(measure, nullkind) {
  out <- list()
  for (id in unique(P$id)) {
    p <- P[P$id == id, ]
    b <- p[p$kind == "borg", ]
    n <- p[p$kind == nullkind, ]
    if (nrow(n) < NNULL || is.na(b[[measure]])) next
    vals <- c(b[[measure]], n[[measure]])
    out[[id]] <- vals
  }
  out
}
test <- function(tab, reps = 10000) {
  if (!length(tab)) return(list(n = 0, u = NA_real_, p = NA_real_))
  u <- sapply(tab, function(v) rank_u(v[1], v[-1]))
  obs <- mean(u)
  null <- replicate(reps, mean(sapply(tab, function(v) {i <- sample.int(length(v), 1); rank_u(v[i], v[-i])})))
  p <- (sum(abs(null - 0.5) >= abs(obs - 0.5) - 1e-12) + 1) / (reps + 1)
  list(n = length(tab), u = obs, p = p)
}
share_within <- function(tab, lim = 500) {
  list(borgar = mean(sapply(tab, function(v) v[1] <= lim)), jamforelse = mean(unlist(lapply(tab, function(v) v[-1] <= lim))))
}
res <- list(sha = substr(sha, 1, 8), borgar_med_lage = nrow(f))
for (m in c("water", "graves", "border")) {
  main <- u_table(m, "berg")
  halves <- lapply(c("A", "B"), function(h) test(main[names(main) %in% info$uuid[info$half == h]], 4000))
  names(halves) <- c("A", "B")
  res[[m]] <- list(huvud = test(main), halvor = halves, all_mark = test(u_table(m, "mark"), 4000))
  if (m == "water") res[[m]]$inom_500m <- share_within(main)
  say(m, ": u = ", round(res[[m]]$huvud$u, 3), " p = ", signif(res[[m]]$huvud$p, 3), " n = ", res[[m]]$huvud$n)
}
ps <- sapply(c("water", "graves", "border"), function(m) res[[m]]$huvud$p)
ph <- p.adjust(ps, "holm")
dir_ok <- function(m) {
  d0 <- sign(res[[m]]$huvud$u - 0.5)
  ok_h <- all(sapply(res[[m]]$halvor, function(h) isTRUE(sign(h$u - 0.5) == d0 && (h$p < 0.05 || h$n < 30))))
  ok_a <- isTRUE(sign(res[[m]]$all_mark$u - 0.5) == d0)
  list(halvor = ok_h, all_mark = ok_a)
}
for (i in seq_along(ps)) {
  m <- names(ps)[i]
  res[[m]]$p_holm <- unname(ph[i])
  dd <- dir_ok(m)
  res[[m]]$haller <- isTRUE(ph[i] < 0.05) && dd$halvor && dd$all_mark
  res[[m]]$kontroller <- dd
}
if (nzchar(Sys.getenv("LIMIT"))) quit(save = "no")
write_json(res, file.path(here, "resultat.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
say("klart")
print(toJSON(res, auto_unbox = TRUE, digits = 4, pretty = TRUE))
