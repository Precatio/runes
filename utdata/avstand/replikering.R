# Replikering av steg 1 (avståndet mellan runstenarna) i Östergötland, Västergötland och Småland, enligt den låsta
# planen analysplaner/2026-10-31-avstand-replikering.md. Metoden är exakt avstand.R med tillägget (10 km, golv 5 %);
# den enda skillnaden är att ett mönster kan omfatta flera landskap (fönstret = unionen av landskapens fönster).
#   Rscript utdata/avstand/replikering.R KORPUS.csv NATURALEARTH_DIR UTMAPP
.args <- commandArgs(trailingOnly = TRUE)
source(file.path(dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]))),
                 "..", "..", "r", "common.R"))
suppressPackageStartupMessages({ library(sf); library(spatstat.geom); library(spatstat.explore); library(spatstat.model);
  library(jsonlite) })
sf_use_s2(FALSE)
set.seed(2026)
corpus_path <- .args[1]; ne_dir <- .args[2]; out <- .args[3]
NSIM <- as.integer(Sys.getenv("NSIM", "999")); MERGE_M <- 25; BUFFER_M <- 5000; SIGMA <- 10000; FLOOR <- 0.05; RINT <- c(100, 1000)
PROVS <- c("Ög", "Vg", "Sm")

d <- read_corpus(corpus_path)
d <- d[!is.na(d$lat) & !is.na(d$lon), ]
pts_all <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), SWEREF)
water <- read_water(ne_dir)

sites <- function(xy, merge = TRUE) {
  if (!merge || nrow(xy) < 2) return(xy)
  h <- hclust(dist(xy), method = "single")
  g <- cutree(h, h = MERGE_M)
  t(sapply(split(seq_len(nrow(xy)), g), function(i) colMeans(xy[i, , drop = FALSE])))
}
pattern <- function(provs, merge = TRUE) {
  inp <- d$province %in% provs & d$moved == 0 & d$lost == 0
  xy <- sites(st_coordinates(pts_all[inp, ]), merge)
  win_sf <- st_union(st_buffer(pts_all[d$province %in% provs, ], BUFFER_M))
  if (!is.null(water$land)) win_sf <- st_intersection(win_sf, water$land)
  W <- as.owin(st_geometry(win_sf))
  X <- ppp(xy[, 1], xy[, 2], window = W, check = FALSE)
  X <- X[inside.owin(X$x, X$y, W)]
  list(X = X, n_stones = sum(inp))
}
lam_points <- function(Y, sigma, floor) {
  m <- Y$n / area(Window(Y))
  pmax(as.numeric(density(Y, sigma = sigma, at = "points", leaveoneout = TRUE, positive = TRUE)), floor * m)
}
Lfloor <- function(Y, ..., sigma, floor) Linhom(Y, lambda = lam_points(Y, sigma, floor), ...)
lam_image <- function(X, sigma, floor) {
  lam <- density(X, sigma = sigma, edge = TRUE, positive = TRUE)
  m <- X$n / area(Window(X))
  eval.im(pmax(lam, floor * m))
}
direction <- function(t, X, rint) {
  f <- attr(t, "envelope")
  sims <- attr(f, "simfuns")
  r <- f$r; keep <- r >= rint[1] & r <= rint[2]
  obs <- f$obs[keep]; mu <- rowMeans(as.matrix(as.data.frame(sims))[keep, -1, drop = FALSE])
  list(p = unname(t$p.value), statistic = unname(t$statistic), n = X$n, mean_dev_m = mean(obs - mu),
       direction = if (mean(obs - mu) < 0) "regelbundet" else "klumpat")
}
dclf_kernel <- function(X, sigma = SIGMA, rint = RINT, floor = FLOOR) {
  lam <- lam_image(X, sigma, floor)
  sim <- lapply(seq_len(NSIM), function(i) rpoispp(lam))
  t <- dclf.test(X, Lfloor, sigma = sigma, floor = floor, simulate = sim, nsim = NSIM, rinterval = rint, verbose = FALSE,
                 savefuns = TRUE, alternative = "two.sided", correction = "translate")
  direction(t, X, rint)
}
halves <- function(X, sigma = SIGMA) {
  mx <- median(X$x)
  lapply(list(vast = X[X$x <= mx], ost = X[X$x > mx]), function(Y) {
    Y <- ppp(Y$x, Y$y, window = convexhull(Y), check = FALSE)
    dclf_kernel(Y, sigma)
  })
}

res <- list(plan = "analysplaner/2026-10-31-avstand-replikering.md", nsim = NSIM, merge_m = MERGE_M, sigma_m = SIGMA,
            floor = FLOOR, rinterval_m = RINT)
P <- pattern(PROVS)
cat("huvudtest", paste(PROVS, collapse = "+"), "stenar på plats", P$n_stones, "platser", P$X$n, "\n")
res$main <- c(dclf_kernel(P$X), list(n_stones = P$n_stones))
res$halves <- halves(P$X)
res$nearest_m <- as.list(quantile(nndist(P$X), c(0.1, 0.25, 0.5, 0.75, 0.9)))
res$provinces <- lapply(setNames(PROVS, PROVS), function(p) { Q <- pattern(p); c(dclf_kernel(Q$X), list(n_stones = Q$n_stones)) })
h <- res$halves
res$status <- if (res$main$p < 0.05 && res$main$direction == "klumpat") {
  if (all(sapply(h, function(x) x$p < 0.05 && x$direction == "klumpat"))) "replikerat" else "delvis replikerat"
} else "inte replikerat"
dir.create(out, showWarnings = FALSE, recursive = TRUE)
write_json(res, file.path(out, if (NSIM < 999) "replikering_prov.json" else "replikering.json"), auto_unbox = TRUE, digits = 8, pretty = TRUE)
cat(sprintf("HUVUDTEST p %.3f %s (medelavvikelse %.1f m)\n", res$main$p, res$main$direction, res$main$mean_dev_m))
for (k in names(h)) cat(sprintf("  halva %-4s p %.3f %s (n %d)\n", k, h[[k]]$p, h[[k]]$direction, h[[k]]$n))
for (p in PROVS) cat(sprintf("  %-3s p %.3f %s (n %d platser, %d stenar)\n", p, res$provinces[[p]]$p, res$provinces[[p]]$direction, res$provinces[[p]]$n, res$provinces[[p]]$n_stones))
cat("UTFALL:", res$status, "\n")
