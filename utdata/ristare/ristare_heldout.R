# Hållet-utanför-test av metoden för okända ristare (r/anonymous.R).
# Ristarna delas slumpmässigt i tre omgångar. Gränsen för att länka två stenar (och största tillåtna spridning) tas fram
# på två omgångar och prövas på den tredje: stenar vars ristare metoden aldrig sett. Gruppernas renhet (andel av gruppen
# som är samma ristare) jämförs med lika stora grupper av närliggande stenar i samma provmängd (bara geografi).
# Upprepas REP gånger med nya indelningar. Körs med samma params som anonymous.R.
#   Rscript utdata/ristare/ristare_heldout.R <params.json> utdata/ristare/ut
.here <- "/Volumes/2TB/Antigrvity/Runes/aagaard-research/r"
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(cluster); library(igraph) })
a <- cli_args(); P <- a$params; out <- a$out; cdir <- P$corpus_dir
set.seed(2026)
MIN_GROUP <- 4; MIN_CARVER <- 3; MIN_WORDS <- 5; REP <- 30; FOLDS <- as.integer(Sys.getenv("FOLDS", "3"))

d <- read_corpus(P$corpus)
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
full <- d %>% left_join(geo %>% select(signum, x, y), by = "signum") %>% left_join(txt, by = "signum") %>%
  filter(!is.na(x), n_words >= MIN_WORDS)
full$style_short <- ifelse(is.na(full$style), NA, sub("[ ?].*", "", full$style))
tc <- trait_cols(d); fcols <- grep("^formula_", names(txt), value = TRUE); bcols <- grep("^bg_", names(txt), value = TRUE)
HAND <- c("style_short", "cross", "short_twig", tc, fcols, bcols)
TIME_DEP <- intersect(c("style_short", "cross", "trait_stungna", "trait_stungen_e", "trait_stungen_y", "trait_stungen_g",
                        "trait_bon", "trait_sjal", "trait_o_runa", "trait_signatur", "formula_bon"), HAND)
gower <- function(cols) {
  X <- full[, cols, drop = FALSE]
  for (col in intersect(c("style_short", "cross", "short_twig", tc, fcols), cols)) X[[col]] <- factor(X[[col]])
  as.matrix(daisy(X, metric = "gower"))
}
K <- as.matrix(dist(cbind(full$x, full$y))) / 1000
cn <- table(full$carver)
known <- which(!is.na(full$carver) & full$carver %in% names(cn[cn >= MIN_CARVER]))
carvers <- unique(full$carver[known])

spread <- function(idx) {
  cx <- mean(full$x[idx]); cy <- mean(full$y[idx])
  median(sqrt((full$x[idx] - cx)^2 + (full$y[idx] - cy)^2)) / 1000
}
purity <- function(grp) max(table(full$carver[grp])) / length(grp)

one_run <- function(G, link_km, lr_min) {
  res <- list()
  fold <- sample(rep(seq_len(FOLDS), length.out = length(carvers))); names(fold) <- carvers
  for (f in seq_len(FOLDS)) {
    test <- known[fold[full$carver[known]] == f]
    train <- known[fold[full$carver[known]] != f]
    ut <- upper.tri(diag(length(train)))
    near <- K[train, train] <= link_km & ut
    same <- outer(full$carver[train], full$carver[train], "==")
    gk <- G[train, train]; ds <- gk[near & same]; dd <- gk[near & !same]
    if (length(ds) < 20) next
    grid <- sort(unique(quantile(c(ds, dd), seq(0.005, 0.5, by = 0.005), na.rm = TRUE)))
    lr <- vapply(grid, function(t) mean(ds <= t) / pmax(mean(dd <= t), 1e-9), 0)
    ok <- lr >= lr_min & vapply(grid, function(t) mean(ds <= t), 0) > 0
    thr <- if (any(ok)) max(grid[ok]) else min(grid)
    ct <- table(full$carver[train]); big <- names(ct[ct >= 5])
    ms <- if (length(big) >= 3) unname(quantile(vapply(big, function(cv) spread(which(full$carver == cv)), 0), 0.9)) else Inf
    A <- (G[test, test] <= thr) & (K[test, test] <= link_km); diag(A) <- FALSE
    W <- ifelse(A, 1 - G[test, test] / (thr + 1e-9) + 0.05, 0)
    m <- as.integer(membership(cluster_louvain(graph_from_adjacency_matrix(W, mode = "undirected", weighted = TRUE, diag = FALSE))))
    sz <- table(m)
    for (k in as.integer(names(sz[sz >= MIN_GROUP]))) {
      grp <- test[m == k]
      if (spread(grp) > ms) next
      centre <- grp[which.min(rowSums(G[grp, grp]))]
      nn <- test[order(K[centre, test])][seq_along(grp)]
      res[[length(res) + 1]] <- data.frame(n = length(grp), pure = purity(grp), geo = purity(nn))
    }
  }
  if (length(res)) do.call(rbind, res) else NULL
}

kor <- function(G, link_km, lr_min, namn) {
  runs <- lapply(seq_len(REP), function(i) one_run(G, link_km, lr_min))
  allg <- do.call(rbind, Map(function(r, i) if (is.null(r)) NULL else cbind(rep = i, r), runs, seq_along(runs)))
  diff_rep <- vapply(seq_len(REP), function(i) {
    r <- allg[allg$rep == i, ]; if (!nrow(r)) NA_real_ else weighted.mean(r$pure, r$n) - weighted.mean(r$geo, r$n)
  }, 0)
  w <- function(x) weighted.mean(x, allg$n)
  wt <- suppressWarnings(wilcox.test(allg$pure, allg$geo, paired = TRUE, alternative = "greater"))
  # sign test excluding ties
  dlt <- allg$pure - allg$geo
  bt <- binom.test(sum(dlt > 0), sum(dlt != 0), 0.5, alternative = "greater")
  # a repeat is the unit that is not shared: how many repeats have purity above geography, and bootstrap over repeats
  pr <- vapply(seq_len(REP), function(i) {
    r <- allg[allg$rep == i, ]; if (nrow(r) < 5 || all(r$pure == r$geo)) NA_real_ else
      suppressWarnings(wilcox.test(r$pure, r$geo, paired = TRUE, alternative = "greater")$p.value)
  }, 0)
  rr <- diff_rep[!is.na(diff_rep)]
  boot <- replicate(5000, mean(sample(rr, replace = TRUE)))
  cat(sprintf("  per omgång (grupperna delas inte mellan omgångar): median p=%.3g, p<0,05 i %d av %d omgångar, grupper/omgång %.1f\n",
              median(pr, na.rm = TRUE), sum(pr < 0.05, na.rm = TRUE), sum(!is.na(pr)), nrow(allg) / REP))
  cat(sprintf("%s: %d grupper över %d omgångar | renhet %.3f mot geografi %.3f | wilcoxon p=%.2g | tecken %d/%d p=%.2g | omgångar där renhet>geografi %d/%d | skillnad %.3f (95 %% %.3f–%.3f)\n",
              namn, nrow(allg), length(rr), w(allg$pure), w(allg$geo), wt$p.value, sum(dlt > 0), sum(dlt != 0), bt$p.value,
              sum(rr > 0), length(rr), mean(rr), quantile(boot, .025), quantile(boot, .975)))
  list(namn = namn, link_km = link_km, lr_min = lr_min, n_grupper = nrow(allg), n_omgangar = length(rr),
       renhet = round(w(allg$pure), 3), geografi = round(w(allg$geo), 3), p_wilcoxon = signif(wt$p.value, 3),
       positiva = sum(dlt > 0), icke_lika = sum(dlt != 0), p_tecken = signif(bt$p.value, 3),
       omgangar_over_geografi = sum(rr > 0), p_per_omgang_median = signif(median(pr, na.rm = TRUE), 3), omgangar_p05 = sum(pr < 0.05, na.rm = TRUE), skillnad = round(mean(rr), 3),
       skillnad_ci = round(unname(quantile(boot, c(.025, .975))), 3),
       andel_rena_75 = round(mean(allg$pure >= .75), 3), andel_rena_75_geo = round(mean(allg$geo >= .75), 3))
}

G_all <- gower(HAND); G_nt <- gower(setdiff(HAND, TIME_DEP))
ut <- list(n_kanda_ristare = length(carvers), n_kanda_stenar = length(known), omgangar = REP, delar = FOLDS)
ut$huvud <- kor(G_all, 30, 12, "alla drag, 30 km, kvot 12")
ut$utan_tid <- kor(G_nt, 30, 12, "utan tidsberoende drag, 30 km, kvot 12")
ut$kanslighet <- list(kor(G_all, 20, 12, "alla drag, 20 km, kvot 12"), kor(G_all, 30, 4, "alla drag, 30 km, kvot 4"),
                      kor(G_all, 15, 8, "alla drag, 15 km, kvot 8"))
write(jsonlite::toJSON(ut, auto_unbox = TRUE, pretty = TRUE, digits = NA), file.path(out, paste0("ristare_heldout_", FOLDS, "delar.json")))
