# Huggteknik sten för sten: liknar en sten en ristares stenar mer än andra ristares stenar gör?
#
# Indata (params$stones): [{signum, group, role, means: {mått: värde}, slices: [{mått: värde}]}], där role är
# "reference" (stenar av ristaren som prövas), "contrast" (andra ristare) eller "query" (stenarna som prövas).
# Varje sten beskrivs med medelvärden per mått (tvärsnitt längs samma spår är inte oberoende), standardiserade
# över alla stenar. Avståndet till referensgruppens tyngdpunkt jämförs med referensstenarnas egna avstånd
# (lämna-en-ute) och med kontrollstenarnas avstånd. Per mått prövas skillnaden mellan frågestenens tvärsnitt
# och referensstenarnas tvärsnitt med ett permutationstest på stennivå.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
METRICS <- c("apex_vinkel_deg", "asymmetri_deg", "spårdjup_mm", "spårbredd_mm", "djup_bredd_kvot", "bottenradie_mm", "ytråhet_mm")
LABELS <- if (identical(LANG, "en")) c("V-angle (°)", "Asymmetry (°)", "Depth (mm)", "Width (mm)", "Depth/width", "Bottom radius (mm)", "Roughness (mm)") else
  c("V-vinkel (°)", "Asymmetri (°)", "Djup (mm)", "Bredd (mm)", "Djup/bredd", "Bottenradie (mm)", "Ytråhet (mm)")
names(LABELS) <- METRICS
ref_name <- P$reference_carver

st <- P$stones
S <- data.frame(signum = st$signum, group = st$group, role = st$role, stringsAsFactors = FALSE)
X <- as.matrix(st$means[, METRICS])
rownames(X) <- S$signum
Z <- scale(X)
ref <- S$role == "reference"
ctr <- S$role == "contrast"
qry <- S$role == "query"

dist_to <- function(z, idx) sqrt(sum((z - colMeans(Z[idx, , drop = FALSE]))^2))
ref_loo <- sapply(which(ref), function(i) dist_to(Z[i, ], setdiff(which(ref), i)))
ctr_d <- sapply(which(ctr), function(i) dist_to(Z[i, ], which(ref)))
qry_d <- sapply(which(qry), function(i) dist_to(Z[i, ], which(ref)))
names(ref_loo) <- S$signum[ref]; names(ctr_d) <- S$signum[ctr]; names(qry_d) <- S$signum[qry]

# Rank of each query stone among the contrast stones: how many other carvers' stones are closer to the reference?
query_rows <- lapply(which(qry), function(i) {
  d <- qry_d[[S$signum[i]]]
  list(signum = S$signum[i], distance = r3(d),
       within_reference_range = d <= max(ref_loo),
       share_contrast_closer = r3(mean(ctr_d < d)),
       share_reference_farther = r3(mean(ref_loo >= d)))
})

# Does the distance separate the carvers at all? Reference (leave-one-out) vs contrast distances
sep <- if (length(ref_loo) >= 2 && length(ctr_d) >= 2) wilcox.test(ref_loo, ctr_d, alternative = "less", exact = FALSE)$p.value else NA
auc <- if (length(ref_loo) && length(ctr_d)) mean(outer(ref_loo, ctr_d, "<") + 0.5 * outer(ref_loo, ctr_d, "==")) else NA

# Per metric: query stone vs the reference stones (stone-level permutation of the slice means)
slices <- st$slices
metric_rows <- list()
for (i in which(qry)) {
  qs <- slices[[i]]
  for (m in METRICS) {
    rv <- X[ref, m]
    obs <- X[i, m] - mean(rv)
    pool <- c(X[i, m], rv)
    perm <- replicate(4999, { s <- sample(pool); s[1] - mean(s[-1]) })
    p <- (1 + sum(abs(perm) >= abs(obs))) / 5000
    metric_rows[[length(metric_rows) + 1]] <- list(
      signum = S$signum[i], metric = m, label = LABELS[[m]], value = r3(X[i, m]), sd = r3(sd(qs[[m]], na.rm = TRUE)),
      reference_mean = r3(mean(rv)), reference_min = r3(min(rv)), reference_max = r3(max(rv)),
      inside_reference_range = X[i, m] >= min(rv) && X[i, m] <= max(rv), p = signif(p, 3))
  }
}

# ---- figures ----------------------------------------------------------------------------------------------------
pc <- prcomp(Z)
ve <- 100 * pc$sdev^2 / sum(pc$sdev^2)
pd <- data.frame(S, pc1 = pc$x[, 1], pc2 = pc$x[, 2])
role_lab <- c(reference = tr(paste("Säkra stenar av", ref_name), paste("Stones attributed to", ref_name)),
              contrast = tr("Andra ristare", "Other carvers"), query = tr("Stenar som prövas", "Stones tested"))
pd$role_l <- factor(role_lab[pd$role], levels = role_lab)
p <- ggplot(pd, aes(pc1, pc2)) +
  geom_point(aes(colour = role_l, shape = role_l), size = 3.4) +
  geom_text(aes(label = signum), vjust = -1.1, size = 3, colour = INK) +
  scale_colour_manual(values = setNames(c(SERIES[1], MUTED, ACCENT), role_lab), name = NULL) +
  scale_shape_manual(values = setNames(c(16, 17, 18), role_lab), name = NULL) +
  labs(title = tr("Huggteknik: stenarnas medelmått", "Carving technique: mean groove measures per stone"),
       subtitle = sprintf(tr("Principalkomponenter av sju standardiserade spårmått (%.0f %% och %.0f %% av variansen)",
                              "Principal components of seven standardised groove measures (%.0f %% and %.0f %% of variance)"), ve[1], ve[2]),
       x = "PC1", y = "PC2",
       caption = tr("Skanningar: Kitzler Åhfeldt 2024 (Zenodo, CC BY 4.0). Mått: Bifrost, automatisk spåranalys.",
                    "Scans: Kitzler Åhfeldt 2024 (Zenodo, CC BY 4.0). Measures: Bifrost automatic groove analysis.")) +
  theme_runor()
fig_pca <- save_fig(p, out, "teknik_pca.png", 7.5, 5.5)

dd <- bind_rows(
  data.frame(signum = names(ref_loo), d = ref_loo, role = "reference"),
  data.frame(signum = names(ctr_d), d = ctr_d, role = "contrast"),
  data.frame(signum = names(qry_d), d = qry_d, role = "query"))
dd$role_l <- factor(role_lab[dd$role], levels = role_lab)
dd$signum <- factor(dd$signum, levels = dd$signum[order(dd$d)])
p <- ggplot(dd, aes(d, signum, colour = role_l, shape = role_l)) +
  geom_segment(aes(x = 0, xend = d, yend = signum), linewidth = 0.4, colour = GRID) +
  geom_point(size = 3.2) +
  scale_colour_manual(values = setNames(c(SERIES[1], MUTED, ACCENT), role_lab), name = NULL) +
  scale_shape_manual(values = setNames(c(16, 17, 18), role_lab), name = NULL) +
  labs(title = sprintf(tr("Avstånd till %ss tyngdpunkt", "Distance to the %s centroid"), ref_name),
       subtitle = tr("Standardiserade medelmått; referensstenarna mäts mot de övriga referensstenarna (lämna-en-ute)",
                     "Standardised mean measures; reference stones measured against the other reference stones (leave-one-out)"),
       x = tr("Avstånd (standardavvikelser)", "Distance (standard deviations)"), y = NULL) +
  theme_runor() + theme(panel.grid.major.y = element_blank())
fig_dist <- save_fig(p, out, "teknik_avstand.png", 7, 4.5)

long <- bind_rows(lapply(seq_len(nrow(S)), function(i) {
  sl <- slices[[i]]
  if (is.null(sl) || !nrow(sl)) return(NULL)
  data.frame(signum = S$signum[i], role = S$role[i], apex = sl$apex_vinkel_deg, depth = sl$`spårdjup_mm`)
}))
long$role_l <- factor(role_lab[long$role], levels = role_lab)
long$signum <- factor(long$signum, levels = S$signum[order(S$role != "query", S$role != "reference", S$signum)])
p <- ggplot(long, aes(apex, signum, fill = role_l)) +
  geom_boxplot(outlier.size = 0.3, outlier.colour = MUTED, linewidth = 0.3, width = 0.6) +
  scale_fill_manual(values = setNames(c("#cfe0f6", "#e2e8f0", "#f3c9b4"), role_lab), name = NULL) +
  labs(title = tr("V-vinkel per sten", "V-angle per stone"), x = tr("V-vinkel (°)", "V-angle (°)"), y = NULL,
       subtitle = tr("Alla godkända tvärsnitt", "All accepted cross-sections")) +
  theme_runor() + theme(panel.grid.major.y = element_blank())
fig_box <- save_fig(p, out, "teknik_vinkel.png", 7, 5)

result <- list(
  reference_carver = ref_name, n_reference = sum(ref), n_contrast = sum(ctr),
  stones = lapply(seq_len(nrow(S)), function(i) list(signum = S$signum[i], group = S$group[i], role = S$role[i],
                                                     means = as.list(round(X[i, ], 3)), n_slices = if (is.null(slices[[i]])) 0 else nrow(slices[[i]]))),
  reference_loo = as.list(round(ref_loo, 3)), contrast = as.list(round(ctr_d, 3)), queries = query_rows,
  separation = list(p = signif(sep, 3), auc = r3(auc)),
  metrics = metric_rows, pca_variance = r1(ve[1:3]),
  figures = list(pca = fig_pca, distance = fig_dist, angle = fig_box),
  method = tr(
    paste("Varje sten beskrivs med medelvärdet av sju spårmått över alla godkända tvärsnitt, standardiserade över",
          "stenarna. Avståndet (euklidiskt) till referensristarens tyngdpunkt jämförs med referensstenarnas egna avstånd",
          "(lämna-en-ute) och med andra ristares stenar; om referensstenarna ligger närmare än kontrollstenarna prövas med",
          "Wilcoxons test och sammanfattas som AUC. Per mått prövas frågestenen mot referensstenarna med ett",
          "permutationstest på stennivå (4 999 permutationer)."),
    paste("Each stone is described by the mean of seven groove measures over all accepted cross-sections, standardised",
          "across stones. The Euclidean distance to the reference carver's centroid is compared with the reference stones'",
          "own distances (leave-one-out) and with other carvers' stones; whether reference stones lie closer than contrast",
          "stones is tested with Wilcoxon's test and summarised as AUC. Per measure, the query stone is tested against the",
          "reference stones with a stone-level permutation test (4,999 permutations).")),
  caveat = tr(
    "Få stenar per ristare, olika vittring och bergart och en annan mätmetod än Kitzler Åhfeldts Groove Measure; resultatet är en indikation, inte en attribuering.",
    "Few stones per carver, differing weathering and rock, and a measurement method other than Kitzler Åhfeldt's Groove Measure; the result is an indication, not an attribution.")
)
write_result(result, out, "technique")
