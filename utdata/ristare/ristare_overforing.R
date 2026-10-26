# Överföringstest: gränsen tas fram på ristare från ett landskap och prövas på ristare i ett annat. Kandidatgrupperna ligger
# i landskap (Ög, Sm, Vg, M) där nästan inga stenar har ristare i Rundata; här prövas om gränsen från Uppland/Södermanland
# fungerar någon annanstans. Samma förfarande som r/anonymous.R och ristare_heldout.R.
.proj <- local({f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)); if (length(f)) normalizePath(file.path(dirname(f[1]), "../..")) else normalizePath(".")})  # projektmappen (Rscript), annars arbetsmappen
.here <- file.path(.proj, "r")
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(cluster); library(igraph) })
a <- cli_args(); P <- a$params; out <- a$out; cdir <- P$corpus_dir
set.seed(2026); MIN_GROUP <- 4; MIN_CARVER <- 3; MIN_WORDS <- 5; LINK_KM <- 30; LR_MIN <- 12; REP <- 30
d <- read_corpus(P$corpus)
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
full <- d %>% left_join(geo %>% select(signum, x, y), by = "signum") %>% left_join(txt, by = "signum") %>%
  filter(!is.na(x), n_words >= MIN_WORDS)
full$style_short <- ifelse(is.na(full$style), NA, sub("[ ?].*", "", full$style))
tc <- trait_cols(d); fcols <- grep("^formula_", names(txt), value = TRUE); bcols <- grep("^bg_", names(txt), value = TRUE)
HAND <- c("style_short", "cross", "short_twig", tc, fcols, bcols)
X <- full[, HAND]; for (col in c("style_short", "cross", "short_twig", tc, fcols)) X[[col]] <- factor(X[[col]])
G <- as.matrix(daisy(X, metric = "gower")); K <- as.matrix(dist(cbind(full$x, full$y))) / 1000
cn <- table(full$carver); known <- which(!is.na(full$carver) & full$carver %in% names(cn[cn >= MIN_CARVER]))
home <- vapply(unique(full$carver[known]), function(cv) names(sort(table(full$province[full$carver == cv]), decreasing = TRUE))[1], "")
cat("ristare per hemlandskap:", paste(names(table(home)), table(home), collapse = ", "), "\n")
spread <- function(idx) { cx <- mean(full$x[idx]); cy <- mean(full$y[idx]); median(sqrt((full$x[idx] - cx)^2 + (full$y[idx] - cy)^2)) / 1000 }
purity <- function(grp) max(table(full$carver[grp])) / length(grp)
test_on <- function(train_prov, test_prov) {
  tr <- known[home[full$carver[known]] %in% train_prov]; te <- known[home[full$carver[known]] %in% test_prov]
  ut <- upper.tri(diag(length(tr))); near <- K[tr, tr] <= LINK_KM & ut
  same <- outer(full$carver[tr], full$carver[tr], "=="); gk <- G[tr, tr]; ds <- gk[near & same]; dd <- gk[near & !same]
  grid <- sort(unique(quantile(c(ds, dd), seq(0.005, 0.5, by = 0.005), na.rm = TRUE)))
  lr <- vapply(grid, function(t) mean(ds <= t) / pmax(mean(dd <= t), 1e-9), 0)
  ok <- lr >= LR_MIN & vapply(grid, function(t) mean(ds <= t), 0) > 0
  thr <- if (any(ok)) max(grid[ok]) else min(grid)
  ct <- table(full$carver[tr]); big <- names(ct[ct >= 5])
  ms <- unname(quantile(vapply(big, function(cv) spread(which(full$carver == cv)), 0), 0.9))
  A <- (G[te, te] <= thr) & (K[te, te] <= LINK_KM); diag(A) <- FALSE
  W <- ifelse(A, 1 - G[te, te] / (thr + 1e-9) + 0.05, 0)
  res <- NULL
  for (i in seq_len(REP)) {
    m <- as.integer(membership(cluster_louvain(graph_from_adjacency_matrix(W, mode = "undirected", weighted = TRUE, diag = FALSE))))
    sz <- table(m)
    for (k in as.integer(names(sz[sz >= MIN_GROUP]))) {
      grp <- te[m == k]; if (spread(grp) > ms) next
      centre <- grp[which.min(rowSums(G[grp, grp]))]; nn <- te[order(K[centre, te])][seq_along(grp)]
      res <- rbind(res, data.frame(rep = i, n = length(grp), pure = purity(grp), geo = purity(nn)))
    }
  }
  if (is.null(res)) return(list(train = paste(train_prov, collapse = "+"), test = paste(test_prov, collapse = "+"), n_test_stenar = length(te), n_grupper = 0))
  pr <- vapply(split(res, res$rep), function(r) if (nrow(r) < 5 || all(r$pure == r$geo)) NA_real_ else
    suppressWarnings(wilcox.test(r$pure, r$geo, paired = TRUE, alternative = "greater")$p.value), 0)
  w <- function(x) weighted.mean(x, res$n)
  r <- list(train = paste(train_prov, collapse = "+"), test = paste(test_prov, collapse = "+"), n_test_stenar = length(te),
            n_test_ristare = length(unique(full$carver[te])), n_train_stenar = length(tr), tröskel = round(thr, 3),
            grupper_per_körning = round(nrow(res) / REP, 1), renhet = round(w(res$pure), 3), geografi = round(w(res$geo), 3),
            skillnad = round(w(res$pure) - w(res$geo), 3), andel_rena_75 = round(mean(res$pure >= .75), 3),
            andel_rena_75_geo = round(mean(res$geo >= .75), 3), median_p_per_körning = signif(median(pr, na.rm = TRUE), 3),
            körningar_p05 = sum(pr < 0.05, na.rm = TRUE), körningar = sum(!is.na(pr)))
  cat(sprintf("träna %s (%d st) -> pröva %s (%d st, %d ristare): %.1f grupper/körning, renhet %.3f mot geografi %.3f, median p %.3g, p<0,05 i %d av %d\n",
              r$train, r$n_train_stenar, r$test, r$n_test_stenar, r$n_test_ristare, r$grupper_per_körning, r$renhet, r$geografi,
              r$median_p_per_körning, r$körningar_p05, r$körningar))
  r
}
ut <- list(per_landskap = as.list(table(home)),
           U_till_Sö = test_on("U", "Sö"), Sö_till_U = test_on("Sö", "U"), USö_till_övriga = test_on(c("U", "Sö"), setdiff(unique(home), c("U", "Sö"))))
write(jsonlite::toJSON(ut, auto_unbox = TRUE, pretty = TRUE, digits = NA), file.path(out, "ristare_overforing.json"))
