# Rak study: do independent groove measurements on Kitzler Åhfeldt's open scans reproduce her carving-technique groups?
# Analysis plan fixed 2026-10-05, before any of the new measurements were looked at.
#   Rscript --vanilla utdata/Rak/rak_analysis.R utdata/Rak/referenser_g7 utdata/Rak/out
#
# 1. Primary: her twelve Rak stones of granite or gneiss. Statistic = mean distance within Rak 1 and within Rak 2 divided by
#    mean distance between them (core members only, 5 + 4 stones); exact permutation over all 126 ways to split the nine
#    stones 5/4. Variables after her v, D, w, k: V-angle, depth, width, bottom radius; stone means, standardised.
# 2. Single-linkage clustering of the twelve stones, cut at five groups (her five variants among them); adjusted Rand index
#    against her grouping, null from 10,000 random relabellings.
# 3. Database carvers with at least two stones in the dataset: within-carver against other distances, permutation.
#    Material (sandstone or not) is tested the same way, since it may confound technique.
# Sensitivity: all seven measures; slice medians instead of means.
.here <- normalizePath("r")
source(file.path(.here, "common.R"))
suppressPackageStartupMessages(library(jsonlite))
adjustedRandIndex <- function(x, y) {  # Hubert & Arabie 1985
  t <- table(x, y); c2 <- function(n) n * (n - 1) / 2
  a <- sum(c2(t)); b <- sum(c2(rowSums(t))); c <- sum(c2(colSums(t))); e <- b * c / c2(sum(t))
  (a - e) / ((b + c) / 2 - e)
}
a <- commandArgs(trailingOnly = TRUE); dir <- a[1]; out <- a[2]; dir.create(out, showWarnings = FALSE, recursive = TRUE)
set.seed(20261005)

KA <- c("Sö 131" = "Rak 1", "Sö 137" = "Rak 1", "Sö 166" = "Rak 1", "Sö 367" = "Rak 1", "Sö Fv1973;189" = "Rak 1",
        "Sö 165" = "Rak 2", "Sö 307" = "Rak 2", "Sö 360" = "Rak 2", "Sö Fv1954;20" = "Rak 2",
        "Sö 113" = "Rak 3", "Sö 319" = "Rak 4", "Sö 164" = "Rak 6")
KA_POSSIBLE <- c("Sö 134" = "Rak 1?", "Sö 161" = "Rak 1?", "Sö 370" = "Rak 2?", "Sö 162" = "Rak 5")
CARVER <- c("Sö 45" = "Traen", "Sö 112" = "Traen", "Sö 129" = "Traen", "Sö 164" = "Traen", "Sö 143" = "Tore 1", "Sö 149" = "Tore 1",
            "Sö 206" = "Äsbjörn", "Sö 208" = "Äsbjörn", "Sö 211" = "Äskil 1", "Sö 333" = "Äskil 1",
            "Sö 160" = "Gunnlev 2 & Sigmund", "Sö 162" = "Gunnlev 2 & Sigmund")
SAND <- c("Sö 128", "Sö 134", "Sö 160", "Sö 161", "Sö 162", "Sö 163", "Sö 207", "Sö 370", "Sö Fv1948;282", "Sö Fv1954;19")
CORE4 <- c("apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm", "bottenradie_mm")
ALL7 <- c(CORE4, "asymmetri_deg", "djup_bredd_kvot", "ytråhet_mm")

# ---- stone values from the slices (Sö 137A and B pooled as Sö 137) ----------------------------------------------------------
files <- list.files(dir, "\\.json$", full.names = TRUE)
sl <- bind_rows(lapply(files, function(f) {
  d <- fromJSON(f); s <- as.data.frame(d$slices)
  s$signum <- sub("^(Sö \\d+)[AB]$", "\\1", d$signum); s
}))
stone <- function(fun) sl %>% group_by(signum) %>% summarise(across(all_of(ALL7), ~ fun(.x, na.rm = TRUE)), n = n(), .groups = "drop")
M <- stone(mean); MED <- stone(median)
M$material <- ifelse(M$signum %in% SAND, "sandstone", "granite/gneiss")

zdist <- function(tab, ids, vars) {
  X <- as.matrix(tab[match(ids, tab$signum), vars]); rownames(X) <- ids
  as.matrix(dist(scale(X)))
}

# ---- 1. primary test ---------------------------------------------------------------------------------------------------------
core <- names(KA)[KA %in% c("Rak 1", "Rak 2")]
ratio <- function(D, g) {
  w <- c(); b <- c()
  for (i in seq_along(g)) for (j in seq_along(g)) if (i < j) if (g[i] == g[j]) w <- c(w, D[i, j]) else b <- c(b, D[i, j])
  mean(w) / mean(b)
}
primary <- function(tab, vars) {
  ids <- core[core %in% tab$signum]
  D <- zdist(tab, intersect(names(KA), tab$signum), vars)[ids, ids]
  g <- unname(KA[ids]); obs <- ratio(D, g)
  n1 <- sum(g == "Rak 1"); splits <- combn(length(ids), n1)
  null <- apply(splits, 2, function(s) { h <- rep("b", length(ids)); h[s] <- "a"; ratio(D, h) })
  list(stones = ids, missing = setdiff(core, ids), ratio = r3(obs), p_exact = signif(mean(null <= obs + 1e-12), 3),
       n_partitions = length(null))
}
P <- list(core4_means = primary(M, CORE4), all7_means = primary(M, ALL7), core4_medians = primary(MED, CORE4))

# ---- 2. clustering against her grouping ---------------------------------------------------------------------------------------
ids12 <- intersect(names(KA), M$signum)
D12 <- zdist(M, ids12, CORE4)
hc <- hclust(as.dist(D12), method = "single")
cl <- cutree(hc, k = 5)
ari <- adjustedRandIndex(cl, KA[ids12])
ari_null <- replicate(10000, adjustedRandIndex(cl, sample(KA[ids12])))
CL <- list(stones = ids12, clusters = as.list(cl), ari = r3(ari), p = signif(mean(ari_null >= ari), 3))

# ---- 3. database carvers and material over all stones -------------------------------------------------------------------------
label_test <- function(lab, ids, vars, B = 9999) {
  D <- zdist(M, M$signum, vars)[ids, ids]; g <- lab[ids]
  stat <- function(g) { same <- outer(g, g, "==") & upper.tri(D); mean(D[same]) / mean(D[upper.tri(D) & !same]) }
  obs <- stat(g); null <- replicate(B, stat(sample(g)))
  list(n = length(ids), ratio = r3(obs), p = signif((sum(null <= obs) + 1) / (B + 1), 3))
}
cids <- intersect(names(CARVER), M$signum)
mat_lab <- setNames(M$material, M$signum)
C3 <- list(carvers = label_test(CARVER, cids, CORE4), material_all = label_test(mat_lab, M$signum, CORE4))

# ---- position of the possible members and the two Grinda stones ----------------------------------------------------------------
Dall <- zdist(M, M$signum, CORE4)
centroid_rank <- function(s) {
  sapply(c("Rak 1", "Rak 2"), function(G) {
    m <- intersect(names(KA)[KA == G], M$signum); m <- setdiff(m, s)
    r3(mean(Dall[s, m]))
  })
}
poss <- lapply(intersect(names(KA_POSSIBLE), M$signum), function(s) c(signum = s, ka = KA_POSSIBLE[[s]], as.list(centroid_rank(s))))
grinda <- if (all(c("Sö 165", "Sö 166") %in% M$signum))
  list(distance = r3(Dall["Sö 165", "Sö 166"]), share_pairs_closer = r3(mean(Dall[upper.tri(Dall)] < Dall["Sö 165", "Sö 166"]))) else NULL

# ---- figures ------------------------------------------------------------------------------------------------------------------
mds <- cmdscale(as.dist(Dall), k = 2)
pd <- data.frame(signum = rownames(mds), x = mds[, 1], y = mds[, 2])
pd$group <- ifelse(pd$signum %in% names(KA), KA[pd$signum], ifelse(pd$signum %in% names(KA_POSSIBLE), KA_POSSIBLE[pd$signum], "Other stones"))
pd$group[pd$group %in% c("Rak 3", "Rak 4", "Rak 5", "Rak 6")] <- "Rak 3–6"
pd$group[pd$group == "Rak 1?"] <- "Rak 1"; pd$group[pd$group == "Rak 2?"] <- "Rak 2"
pd$material <- M$material[match(pd$signum, M$signum)]
p <- ggplot(pd, aes(x, y)) +
  geom_point(aes(fill = group, shape = material), size = 3, colour = INK, stroke = 0.3) +
  geom_text(aes(label = sub("Sö ", "", signum)), size = 2.5, vjust = -1.1, colour = INK) +
  scale_fill_manual(values = c("Rak 1" = SERIES[1], "Rak 2" = SERIES[2], "Rak 3–6" = SERIES[3], "Other stones" = "white"), name = NULL) +
  scale_shape_manual(values = c("granite/gneiss" = 21, "sandstone" = 24), name = NULL) +
  guides(fill = guide_legend(override.aes = list(shape = 21))) +
  labs(x = "MDS 1", y = "MDS 2") + theme_runor()
save_fig(p, out, "mds.png", 7.5, 6)
png(file.path(out, "dendrogram.png"), width = 7, height = 4.5, units = "in", res = 300)
plot(hc, main = "", sub = "", xlab = "", ylab = "Distance (standardised)", labels = paste0(ids12, " (", KA[ids12], ")"), cex = 0.7)
dev.off()

write.csv(M, file.path(out, "stone_means.csv"), row.names = FALSE)
write_result(list(primary = P, clustering = CL, labels = C3, possible = poss, grinda = grinda,
                  n_stones = nrow(M), slices = as.list(setNames(M$n, M$signum))), out, "rak")
