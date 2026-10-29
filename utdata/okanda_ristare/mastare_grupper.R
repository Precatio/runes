# Mästarmodellen, steg 1 (analysplaner/2026-10-29-en-och-samma-mastare.md, del 3): kalibreringsgrupper bildade som i
# r/anonymous.R:s hållet-utanför-test (ristarna i tre delar, gränsen på två, grupperna på den tredje; 50 upprepningar),
# och handens drag för dem och för de fem kandidaterna.
#   Rscript utdata/okanda_ristare/mastare_grupper.R
# Uppsättningen (Gower, gränsen, spridningen) är densamma som i r/anonymous.R; den är kopierad hit, eftersom modulen inte
# går att läsa in utan att den körs.
suppressPackageStartupMessages({ library(dplyr); library(cluster); library(igraph); library(jsonlite) })
source("r/common.R")
cdir <- "data/cache/r/corpus/3f58e9339191761e"
OUT <- "utdata/okanda_ristare"
LINK_KM <- 30; LR_MIN <- 12; MIN_GROUP <- 4; MIN_CARVER <- 3; MIN_WORDS <- 5
REP <- 50; FOLDS <- 3; SEED <- 2026
CANDIDATES <- c(2, 5, 6, 12, 13)

d <- read_corpus(file.path(cdir, "corpus.csv"))
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
full <- d %>% left_join(geo %>% select(signum, x, y), by = "signum") %>% left_join(txt, by = "signum") %>%
  filter(!is.na(x), n_words >= MIN_WORDS)
full$style_short <- ifelse(is.na(full$style), NA, sub("[ ?].*", "", full$style))
tc <- trait_cols(d)
fcols <- grep("^formula_", names(txt), value = TRUE)
bcols <- grep("^bg_", names(txt), value = TRUE)
HAND <- c("style_short", "cross", "short_twig", tc, fcols, bcols)
X <- full[, HAND]
for (col in c("style_short", "cross", "short_twig", tc, fcols)) X[[col]] <- factor(X[[col]])
G <- as.matrix(daisy(X, metric = "gower"))
TIME_DEP <- intersect(c("style_short", "cross", "trait_stungna", "trait_stungen_e", "trait_stungen_y", "trait_stungen_g",
                        "trait_bon", "trait_sjal", "trait_o_runa", "trait_signatur", "formula_bon"), HAND)
G_nt <- as.matrix(daisy(X[, setdiff(HAND, TIME_DEP), drop = FALSE], metric = "gower"))
K <- as.matrix(dist(cbind(full$x, full$y))) / 1000
spread <- function(idx) {
  cx <- mean(full$x[idx]); cy <- mean(full$y[idx])
  median(sqrt((full$x[idx] - cx)^2 + (full$y[idx] - cy)^2)) / 1000
}
carver_n <- table(full$carver)
known <- which(!is.na(full$carver) & full$carver %in% names(carver_n[carver_n >= MIN_CARVER]))
purity <- function(grp) max(table(full$carver[grp])) / length(grp)
mean_in <- function(M, grp) { m <- M[grp, grp]; mean(m[upper.tri(m)]) }

rows <- list(); members <- list(); gid <- 0
add <- function(kind, grp, rep = NA, fold = NA, cand = NA) {
  gid <<- gid + 1
  rows[[gid]] <<- data.frame(group = gid, kind = kind, rep = rep, fold = fold, candidate = cand, n = length(grp),
                             purity = if (kind == "kalibrering") purity(grp) else NA,
                             g_mean = mean_in(G, grp), gnt_mean = mean_in(G_nt, grp), spread_km = spread(grp))
  members[[gid]] <<- data.frame(group = gid, signum = full$signum[grp], carver = full$carver[grp])
}

set.seed(SEED)
carvers <- unique(full$carver[known])
for (r in seq_len(REP)) {
  fold <- sample(rep(seq_len(FOLDS), length.out = length(carvers))); names(fold) <- carvers
  for (f in seq_len(FOLDS)) {
    te <- known[fold[full$carver[known]] == f]; tr <- known[fold[full$carver[known]] != f]
    nr <- K[tr, tr] <= LINK_KM & upper.tri(diag(length(tr)))
    sm <- outer(full$carver[tr], full$carver[tr], "=="); gk <- G[tr, tr]; ds <- gk[nr & sm]; dd <- gk[nr & !sm]
    if (length(ds) < 20) next
    gr <- sort(unique(quantile(c(ds, dd), seq(0.005, 0.5, by = 0.005), na.rm = TRUE)))
    lr <- vapply(gr, function(t) mean(ds <= t) / pmax(mean(dd <= t), 1e-9), 0)
    ok <- lr >= LR_MIN & vapply(gr, function(t) mean(ds <= t), 0) > 0
    thr <- if (any(ok)) max(gr[ok]) else min(gr)
    ct <- table(full$carver[tr]); big <- names(ct[ct >= 5])
    ms <- if (length(big) >= 3) unname(quantile(vapply(big, function(cv) spread(which(full$carver == cv)), 0), 0.9)) else Inf
    A <- (G[te, te] <= thr) & (K[te, te] <= LINK_KM); diag(A) <- FALSE
    W <- ifelse(A, 1 - G[te, te] / (thr + 1e-9) + 0.05, 0)
    m <- as.integer(membership(cluster_louvain(graph_from_adjacency_matrix(W, mode = "undirected", weighted = TRUE, diag = FALSE))))
    sz <- table(m)
    for (k in as.integer(names(sz[sz >= MIN_GROUP]))) {
      grp <- te[m == k]
      if (spread(grp) > ms) next
      add("kalibrering", grp, r, f)
    }
  }
}
anon <- fromJSON(file.path(cdir, "anonymous.json"), simplifyVector = FALSE)
for (g in anon$groups) {
  if (!(g$id %in% CANDIDATES)) next
  st <- vapply(g$stones, function(s) if (is.character(s)) s else s$signum, "")
  add("kandidat", which(full$signum %in% st), cand = g$id)
}
write.csv(do.call(rbind, rows), file.path(OUT, "mastare_grupper.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write.csv(do.call(rbind, members), file.path(OUT, "mastare_medlemmar.csv"), row.names = FALSE, fileEncoding = "UTF-8")
cat(sum(vapply(rows, function(x) x$kind == "kalibrering", TRUE)), "kalibreringsgrupper,",
    sum(vapply(rows, function(x) x$kind == "kandidat", TRUE)), "kandidater\n")
