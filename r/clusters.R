# Klustring och multipel korrespondensanalys (MCA) av runstenarnas stil, språkdrag och innehåll.
# Geografi och ristare ingår inte i klustringen; de används efteråt för att tolka grupperna.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({
  library(cluster)
  library(FactoMineR)
  library(factoextra)
})

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
K_RANGE <- 2:10
B <- 20
MIN_FEATURES <- 5

d <- read_corpus(P$corpus)
tc <- trait_cols(d); cc <- cat_cols(d)
informative <- rowSums(!is.na(d[, c("style", tc)]))
keep <- informative >= MIN_FEATURES
dd <- d[keep, ]

# Gower distance: style and language traits nominal, cross and short-twig runes symmetric binary,
# content categories asymmetric binary (shared absence of e.g. a bridge says little)
X <- dd[, c("style", tc, "cross", "short_twig", cc)]
for (col in c("style", tc)) X[[col]] <- factor(X[[col]])
D <- daisy(X, metric = "gower", type = list(symm = c("cross", "short_twig"), asymm = cc))
Dm <- as.matrix(D)

sil <- sapply(K_RANGE, function(k) pam(D, k, diss = TRUE)$silinfo$avg.width)
k <- K_RANGE[which.max(sil)]
fit <- pam(D, k, diss = TRUE)
dd$cluster <- fit$clustering
sw <- silhouette(fit)[, "sil_width"]

# Stability (Hennig 2007): Jaccard similarity of each cluster with its best match in B subsamples of 80 %
jac <- matrix(NA_real_, B, k)
for (b in seq_len(B)) {
  idx <- sort(sample(nrow(dd), floor(0.8 * nrow(dd))))
  fb <- pam(as.dist(Dm[idx, idx]), k, diss = TRUE)$clustering
  for (c0 in seq_len(k)) {
    A <- which(dd$cluster[idx] == c0)
    if (!length(A)) next
    jac[b, c0] <- max(sapply(seq_len(k), function(c1) {
      Bset <- which(fb == c1)
      length(intersect(A, Bset)) / length(union(A, Bset))
    }))
  }
}
stability <- colMeans(jac, na.rm = TRUE)

# MCA on the same variables (missing trait = its own level "ej bestämbart")
M <- dd[, c("style", tc, "cross", "short_twig", cc)]
M$style[is.na(M$style)] <- "okänd"
for (col in tc) M[[col]][is.na(M[[col]])] <- "ej bestämbart"
M$cross <- ifelse(M$cross == 1, "kors", "inget kors")
M$short_twig <- ifelse(M$short_twig == 1, "kortkvist", "ej kortkvist")
for (col in cc) M[[col]] <- ifelse(M[[col]] == 1, CAT_LABELS[[col]], paste("ej", tolower(CAT_LABELS[[col]])))
names(M) <- c("Stil", unname(TRAIT_LABELS[tc]), "Kors", "Kortkvistrunor", unname(CAT_LABELS[cc]))
M[] <- lapply(M, factor)
mca <- MCA(M, ncp = 5, graph = FALSE)
eig <- mca$eig[, 2]
coords <- mca$ind$coord[, 1:2]
dd$dim1 <- coords[, 1]; dd$dim2 <- coords[, 2]

# Cluster profiles: over-represented levels (v-test, catdes)
cd <- NULL
invisible(capture.output(cd <- catdes(cbind(M, Kluster = factor(dd$cluster)), num.var = ncol(M) + 1, proba = 0.01)))
profiles <- lapply(seq_len(k), function(c0) {
  t <- cd$category[[as.character(c0)]]
  top <- if (!is.null(t) && nrow(t)) {
    t <- t[t[, "v.test"] > 0, , drop = FALSE]
    t <- head(t[order(-t[, "v.test"]), , drop = FALSE], 6)
    lapply(seq_len(nrow(t)), function(i) list(level = rownames(t)[i], share_in_cluster = r3(t[i, "Mod/Cla"] / 100),
                                              share_overall = r3(t[i, "Global"] / 100), v_test = r1(t[i, "v.test"])))
  } else list()
  g <- dd[dd$cluster == c0, ]
  carv <- sort(table(g$carver), decreasing = TRUE)
  prov <- sort(table(g$province), decreasing = TRUE)
  sty <- sort(table(g$style), decreasing = TRUE)
  list(cluster = c0, n = nrow(g), silhouette = r3(mean(sw[dd$cluster == c0])), stability = r3(stability[c0]),
       medoid = dd$signum[fit$id.med[c0]], features = top,
       carvers = head(lapply(names(carv), function(n) list(carver = n, n = as.integer(carv[n]))), 6),
       provinces = head(lapply(names(prov), function(n) list(province = n, n = as.integer(prov[n]))), 5),
       styles = head(lapply(names(sty), function(n) list(style = n, n = as.integer(sty[n]))), 4),
       n_with_carver = sum(!is.na(g$carver)))
})

# Clusters against carvers (stones with one certain carver; carvers with at least 5 stones here)
kc <- dd %>% filter(!is.na(carver)) %>% group_by(carver) %>% filter(n() >= 5) %>% ungroup()
ari <- if (nrow(kc) > 10) adjusted_rand(kc$cluster, kc$carver) else NA
carver_rows <- kc %>% count(carver, cluster) %>% group_by(carver) %>%
  summarise(n = sum(n), modal_cluster = cluster[which.max(n)], purity = r3(max(n) / sum(n))) %>% arrange(desc(n))
ari_province <- adjusted_rand(dd$cluster, dd$province)
style_known <- dd %>% filter(!is.na(style))
ari_style <- adjusted_rand(style_known$cluster, style_known$style)

# ---- figures ----------------------------------------------------------------------------------
pf <- data.frame(k = K_RANGE, sil = sil)
p <- ggplot(pf, aes(k, sil)) +
  geom_hline(yintercept = 0.25, colour = MUTED, linetype = "dashed", linewidth = 0.4) +
  geom_line(colour = SERIES[1], linewidth = 0.7) + geom_point(colour = SERIES[1], size = 2.4) +
  geom_point(data = pf[pf$k == k, ], colour = INK, size = 3.4, shape = 21, stroke = 1) +
  annotate("text", x = max(K_RANGE), y = 0.25, label = tr("0,25: svag struktur under", "0.25: weak structure below"), hjust = 1, vjust = -0.6,
           colour = MUTED, size = 3) +
  scale_x_continuous(breaks = K_RANGE) +
  labs(title = "Antal grupper", subtitle = sprintf("Genomsnittlig silhuettbredd för PAM med k = 2–10; högst vid k = %d", k),
       x = tr("Antal grupper (k)", "Number of groups (k)"), y = tr("Silhuettbredd", "Silhouette width")) +
  theme_runor()
fig_sil <- save_fig(p, out, "kluster_silhuett.png", 6.5, 4)

hl <- bind_rows(lapply(seq_len(k), function(c0) data.frame(panel = sprintf(tr("Grupp %d (n = %d)", "Group %d (n = %d)"), c0, sum(dd$cluster == c0)),
                                                       dim1 = dd$dim1, dim2 = dd$dim2, member = dd$cluster == c0)))
hl$panel <- factor(hl$panel, levels = unique(hl$panel))
p <- ggplot(hl, aes(dim1, dim2)) +
  geom_point(data = hl[!hl$member, ], colour = FAINT, size = 0.4) +
  geom_point(data = hl[hl$member, ], colour = SERIES[1], size = 0.6) +
  facet_wrap(~panel) +
  labs(title = "Runstenarna i MCA-rummet", x = sprintf("Dimension 1 (%.1f %%)", eig[1]),
       y = sprintf("Dimension 2 (%.1f %%)", eig[2]),
       subtitle = "Varje panel visar en grupp (blå) mot alla klustrade stenar (grått)",
       caption = "Andelarna förklarad inerti är lägre i MCA än i PCA och underskattar hur mycket dimensionerna fångar.") +
  theme_runor()
fig_mca <- save_fig(p, out, "kluster_mca.png", 8, 6)

p <- fviz_mca_var(mca, choice = "var.cat", select.var = list(contrib = 25), repel = TRUE, col.var = INK,
                  labelsize = 3, pointsize = 1.4, title = "Kategorier som bidrar mest till dimension 1–2") +
  theme_runor()
fig_var <- save_fig(p, out, "kluster_variabler.png", 8, 6.5)

if (nrow(kc)) {
  hm <- kc %>% count(carver, cluster) %>% group_by(carver) %>% mutate(share = n / sum(n)) %>% ungroup() %>%
    complete(carver, cluster = seq_len(k), fill = list(n = 0, share = 0))
  order_c <- carver_rows$carver
  hm$carver <- factor(hm$carver, levels = rev(order_c))
  p <- ggplot(hm, aes(factor(cluster), carver, fill = share)) +
    geom_tile(colour = "white", linewidth = 0.6) +
    geom_text(aes(label = ifelse(n > 0, n, "")), size = 2.6, colour = ifelse(hm$share > 0.55, "white", INK)) +
    scale_fill_gradient(low = SEQ[1], high = SEQ[3], name = tr("Andel av ristarens stenar", "Share of the carver's stones"), labels = scales::percent) +
    labs(title = "Ristarnas stenar fördelade på grupperna", x = tr("Grupp", "Group"), y = NULL,
         subtitle = sprintf("Justerat Rand-index mellan grupp och ristare: %.2f (0 = slump, 1 = full överensstämmelse)", ari)) +
    theme_runor() + theme(panel.grid.major = element_blank())
  fig_carv <- save_fig(p, out, "kluster_ristare.png", 7, max(4, 0.28 * length(order_c) + 1.8))
} else fig_carv <- NULL

write.csv(data.frame(signum = dd$signum, cluster = dd$cluster, sil_width = sw, dim1 = dd$dim1, dim2 = dd$dim2),
          file.path(out, "clusters_stones.csv"), row.names = FALSE, fileEncoding = "UTF-8")
saveRDS(list(X = X, signum = dd$signum, cluster = dd$cluster, carver = dd$carver, k = k,
             types = list(symm = c("cross", "short_twig"), asymm = cc)),
        file.path(out, "clusters_model.rds"))

strength <- if (max(sil) >= 0.5) "tydlig" else if (max(sil) >= 0.25) "svag men verklig" else "ingen tydlig"
result <- list(
  n_stones = nrow(dd), n_excluded = sum(!keep), min_features = MIN_FEATURES, k = k,
  silhouette = lapply(seq_along(K_RANGE), function(i) list(k = K_RANGE[i], width = r3(sil[i]))),
  best_silhouette = r3(max(sil)), structure = strength,
  clusters = profiles,
  mca = list(dims = lapply(1:5, function(i) list(dim = i, inertia_pct = r1(eig[i])))),
  carvers = list(ari = r3(ari), n = nrow(kc), rows = carver_rows),
  ari_province = r3(ari_province), ari_style = r3(ari_style),
  figures = list(silhouette = fig_sil, mca = fig_mca, variables = fig_var, carvers = fig_carv),
  method = paste(
    "Stenar med minst", MIN_FEATURES, "bestämbara drag (stilgrupp och språkdrag) klustrades på stilgrupp, elva språkdrag,",
    "kors, kortkvistrunor och nio innehållskategorier. Avståndet var Gowers (nominala drag; kategorierna som asymmetriskt",
    "binära), klustringen PAM (Kaufman & Rousseeuw 1990) med det antal grupper k = 2–10 som gav högst silhuettbredd.",
    "Gruppernas stabilitet mättes som Jaccard-likhet med bästa motsvarighet i", B, "delurval om 80 % (Hennig 2007);",
    "över 0,75 räknas som stabil, under 0,5 som upplöst. Samma variabler sammanfattades med multipel korrespondensanalys",
    "(FactoMineR). Ristare och landskap ingick inte i klustringen utan jämfördes efteråt med justerat Rand-index."
  )
)
write_result(result, out, "clusters")
