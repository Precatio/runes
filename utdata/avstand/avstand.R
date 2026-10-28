# Avståndet mellan runstenarna (spatstat), enligt den låsta planen analysplaner/2026-10-28-avstand-mellan-stenar.md.
#   Rscript utdata/avstand/avstand.R KORPUS.csv NATURALEARTH_DIR LAMNINGAR.csv UTMAPP
# Skriver avstand.json, figurer och en logg i UTMAPP.
.args <- commandArgs(trailingOnly = TRUE)
source(file.path(dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]))),
                 "..", "..", "r", "common.R"))
suppressPackageStartupMessages({ library(sf); library(spatstat.geom); library(spatstat.explore); library(spatstat.model);
  library(jsonlite) })
sf_use_s2(FALSE)
set.seed(2026)
corpus_path <- .args[1]; ne_dir <- .args[2]; remains_path <- .args[3]; out <- .args[4]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
NSIM <- as.integer(Sys.getenv("NSIM", "999")); MERGE_M <- 25; BUFFER_M <- 5000; SIGMA <- 2000; RINT <- c(100, 1000)

d <- read_corpus(corpus_path)
d <- d[!is.na(d$lat) & !is.na(d$lon), ]
pts_all <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), SWEREF)
water <- read_water(ne_dir)
graves <- read.csv(remains_path, stringsAsFactors = FALSE)
graves <- graves[graves$type == "gravfält" & !is.na(graves$lat), ]
graves <- st_transform(st_as_sf(graves, coords = c("lon", "lat"), crs = 4326), SWEREF)

# Platser: stenar inom MERGE_M m slås ihop (enkel länkning), mittpunkten blir platsen
sites <- function(xy, merge = TRUE) {
  if (!merge || nrow(xy) < 2) return(xy)
  h <- hclust(dist(xy), method = "single")
  g <- cutree(h, h = MERGE_M)
  t(sapply(split(seq_len(nrow(xy)), g), function(i) colMeans(xy[i, , drop = FALSE])))
}

pattern <- function(prov, merge = TRUE) {
  inp <- d$province == prov & d$moved == 0 & d$lost == 0
  xy <- st_coordinates(pts_all[inp, ])
  xy <- sites(xy, merge)
  win_sf <- st_union(st_buffer(pts_all[d$province == prov, ], BUFFER_M))
  if (!is.null(water$land)) win_sf <- st_intersection(win_sf, water$land)
  W <- as.owin(st_geometry(win_sf))
  X <- ppp(xy[, 1], xy[, 2], window = W, check = FALSE)
  X <- X[inside.owin(X$x, X$y, W)]
  list(X = X, win_sf = win_sf, n_stones = sum(inp))
}

# DCLF-testet på L(r) − r mot inhomogen Poisson med kärnskattad täthet; tätheten skattas om för varje simulering
dclf_kernel <- function(X, sigma = SIGMA, rint = RINT) {
  lam <- density(X, sigma = sigma, edge = TRUE, positive = TRUE)
  sim <- lapply(seq_len(NSIM), function(i) rpoispp(lam))  # simulated in advance: spatstat evaluates expressions elsewhere
  t <- dclf.test(X, Linhom, sigma = sigma, positive = TRUE, simulate = sim, nsim = NSIM, rinterval = rint, verbose = FALSE,
                 savefuns = TRUE, alternative = "two.sided", correction = "translate")
  direction(t, X, rint)
}
direction <- function(t, X, rint) {
  f <- attr(t, "envelope")
  sims <- attr(f, "simfuns")
  r <- f$r; keep <- r >= rint[1] & r <= rint[2]
  obs <- f$obs[keep]; mu <- rowMeans(as.matrix(as.data.frame(sims))[keep, -1, drop = FALSE])
  list(p = unname(t$p.value), statistic = unname(t$statistic), n = X$n, mean_dev_m = mean(obs - mu),
       direction = if (mean(obs - mu) < 0) "regelbundet" else "klumpat")
}
# Kovariatmodellen: avstånd till vatten och till närmaste gravfält (robusthet 2)
dclf_covariate <- function(X, win_sf) {
  W <- Window(X)
  grid <- as.mask(W, dimyx = 256)
  cen <- st_as_sf(as.data.frame(rasterxy.mask(grid, drop = TRUE)), coords = c("x", "y"), crs = SWEREF)
  wd <- as.numeric(st_distance(cen, water$lines)) / 1000
  gd <- apply(st_distance(cen, graves[st_intersects(graves, st_buffer(win_sf, 20000), sparse = FALSE)[, 1], ]), 1, min) / 1000
  im_of <- function(v) { m <- as.im(grid); m[grid] <- v; m }
  covs <- list(water = im_of(wd), grave = im_of(as.numeric(gd)))
  fit <- ppm(X ~ water + grave, covariates = covs)
  lam <- predict(fit)
  sim <- lapply(seq_len(NSIM), function(i) rpoispp(lam))
  t <- dclf.test(X, Linhom, lambda = fit, simulate = sim, nsim = NSIM, rinterval = RINT,
                 verbose = FALSE, savefuns = TRUE, correction = "translate")
  direction(t, X, RINT)
}
halves <- function(X, sigma = SIGMA) {
  mx <- median(X$x)
  lapply(list(vast = X[X$x <= mx], ost = X[X$x > mx]), function(Y) {
    Y <- ppp(Y$x, Y$y, window = convexhull(Y), check = FALSE)  # varje halva i sitt eget område
    dclf_kernel(Y, sigma)
  })
}

res <- list(plan = "analysplaner/2026-10-28-avstand-mellan-stenar.md", nsim = NSIM, merge_m = MERGE_M, sigma_m = SIGMA,
            rinterval_m = RINT, provinces = list())
for (prov in c("U", "Sö")) {
  P <- pattern(prov)
  X <- P$X
  cat(prov, "stenar på plats", P$n_stones, "platser", X$n, "\n")
  main <- dclf_kernel(X)
  nn <- nndist(X)
  r <- list(n_stones = P$n_stones, n_sites = X$n, main = main,
            halves = halves(X),
            robustness = list(sigma_1km = dclf_kernel(X, 1000), sigma_4km = dclf_kernel(X, 4000),
                              covariates = tryCatch(dclf_covariate(X, P$win_sf), error = function(e) list(error = conditionMessage(e))),
                              no_merge = dclf_kernel(pattern(prov, merge = FALSE)$X),
                              r_100_500 = dclf_kernel(X, SIGMA, c(100, 500))),
            nearest_m = as.list(quantile(nn, c(0.1, 0.25, 0.5, 0.75, 0.9))))
  # Figur: global envelopp för g(r)
  lam0 <- density(X, sigma = SIGMA, positive = TRUE)
  env <- envelope(X, pcfinhom, sigma = SIGMA, positive = TRUE, simulate = lapply(seq_len(2 * NSIM), function(i) rpoispp(lam0)),
                  nsim = NSIM, global = TRUE, r = seq(0, 3000, by = 25), verbose = FALSE)
  png(file.path(out, paste0("g_", prov, ".png")), width = 1400, height = 900, res = 200)
  plot(env, main = paste(prov, "– parkorrelation g(r) mot inhomogen Poisson"), xlab = "r (m)", legend = FALSE)
  dev.off()
  res$provinces[[prov]] <- r
  cat(sprintf("%s: p %.4f, medelavvikelse %.1f m (%s)\n", prov, main$p, main$mean_dev_m, main$direction))
}
ps <- sapply(res$provinces, function(r) r$main$p)
ph <- p.adjust(ps, "holm")
for (k in names(res$provinces)) {
  r <- res$provinces[[k]]; r$main$p_holm <- ph[[k]]
  same <- function(h) !is.null(h$p) && h$p < 0.05 && h$direction == r$main$direction
  both <- same(r$halves$vast) && same(r$halves$ost)
  r$status <- if (ph[[k]] < 0.05 && both) r$main$direction else if (ph[[k]] < 0.05) "mönster att pröva" else
    "ingen avvikelse från slumpen påvisad"
  res$provinces[[k]] <- r
  cat(k, "→", r$status, "(Holm", signif(ph[[k]], 3), ")\n")
}
write_json(res, file.path(out, "avstand.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE, null = "null")
