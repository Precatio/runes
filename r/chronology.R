# Seriation och relativ datering med korrespondensanalys (ca).
#
# Korrespondensanalysen görs på språkdrag, formler, kors, kortkvistrunor och innehåll – utan stilgruppen.
# Ordningen längs första dimensionen prövas sedan mot Gräslunds stilkronologi, som är oberoende av de
# variablerna. Bara om ordningen följer stilkronologin används den för att skatta en tidpunkt för stenar utan
# stilgrupp, och då med ett prediktionsintervall.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages(library(ca))

a <- cli_args(); P <- a$params; out <- a$out; cdir <- P$corpus_dir
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
MIN_ATTR <- 15
MIN_PER_STONE <- 4

d <- read_corpus(P$corpus)
tc <- trait_cols(d); cc <- cat_cols(d)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", check.names = FALSE)
fcols <- grep("^formula_", names(txt), value = TRUE)
d <- d %>% left_join(txt[, c("signum", fcols)], by = "signum")
d0 <- d
# Gräslund's chronology was built on Uppland's runestones; elsewhere language and formulas also vary by region,
# which swamps the time signal (first CA dimension uncorrelated with style dates in the whole corpus).
REGION <- "U"
d <- d %>% filter(province %in% REGION)

all_d <- d0
# Incidence matrix: stones x attribute levels (presence/absence)
levels_of <- function(col, labels, d) {
  v <- d[[col]]
  ok <- !is.na(v) & !(v %in% c("ingen", "ej bestämbar"))
  out <- matrix(0L, nrow(d), 0)
  for (lv in sort(unique(v[ok]))) {
    m <- matrix(as.integer(ok & v == lv), ncol = 1, dimnames = list(NULL, paste0(labels[[col]], ": ", trv(lv))))
    out <- cbind(out, m)
  }
  out
}
FL <- if (identical(LANG, "en")) FORMULA_LABELS_EN else
  c(formula_raising = "Resarformel", formula_monument = "Monument", formula_order = "Ordföljd",
    formula_signature = "Ristarsignatur", formula_prayer = "Bön")
TL <- if (identical(LANG, "en")) TRAIT_LABELS_EN else TRAIT_LABELS
CL <- if (identical(LANG, "en")) CAT_LABELS_EN else CAT_LABELS
incidence <- function(d) {
  I <- do.call(cbind, c(lapply(tc, levels_of, labels = TL, d = d), lapply(fcols, levels_of, labels = FL, d = d)))
  extra <- cbind(d$cross, d$short_twig); colnames(extra) <- c(tr("Kors", "Cross"), tr("Kortkvistrunor", "Short-twig runes"))
  I <- cbind(I, extra)
  CI <- as.matrix(d[, cc]); colnames(CI) <- unname(CL[cc])
  I <- cbind(I, CI)
  I <- I[, colSums(I) >= MIN_ATTR, drop = FALSE]
  keep <- rowSums(I) >= MIN_PER_STONE
  I <- I[keep, , drop = FALSE]
  list(I = I[, colSums(I) > 0, drop = FALSE], keep = keep)
}
inc <- incidence(d)
I <- inc$I
dd <- d[inc$keep, ]

fit <- ca(I, nd = 3)
score <- fit$rowcoord[, 1]
attr_score <- fit$colcoord[, 1]
inertia <- 100 * fit$sv^2 / sum(fit$sv^2)

# Validation against Gräslund (midpoint of the style group's span); orient so that later = higher
dd$mid <- ifelse(!is.na(dd$style_from), (dd$style_from + dd$style_to) / 2, NA)
dated <- !is.na(dd$mid)
rho0 <- suppressWarnings(cor(score[dated], dd$mid[dated], method = "spearman"))
if (!is.na(rho0) && rho0 < 0) { score <- -score; attr_score <- -attr_score }
ct <- suppressWarnings(cor.test(score[dated], dd$mid[dated], method = "spearman", exact = FALSE))
rho <- unname(ct$estimate)
# Is the axis geography rather than time? Correlation with latitude, and partial correlation with time
lat_rho <- suppressWarnings(cor(score, dd$lat, method = "spearman", use = "complete.obs"))
partial <- {
  ok <- dated & !is.na(dd$lat)
  r_sm <- rank(score[ok]); r_t <- rank(dd$mid[ok]); r_l <- rank(dd$lat[ok])
  res_s <- resid(lm(r_sm ~ r_l)); res_t <- resid(lm(r_t ~ r_l))
  cor(res_s, res_t)
}
usable <- !is.na(rho) && abs(rho) >= 0.3 && ct$p.value < 0.001

# Calibration: linear regression of style date on CA score (dated stones), prediction for the rest
dd$score <- score
cal <- lm(mid ~ score, data = dd[dated, ])
pred <- predict(cal, newdata = dd, interval = "prediction", level = 0.8)
dd$est <- pred[, "fit"]; dd$lo <- pred[, "lwr"]; dd$hi <- pred[, "upr"]
resid_sd <- sigma(cal)
mae <- mean(abs(dd$est[dated] - dd$mid[dated]))
# Leave-one-out check of the calibration, same model
loo <- sapply(which(dated), function(i) {
  m <- lm(mid ~ score, data = dd[setdiff(which(dated), i), ])
  predict(m, newdata = dd[i, ])
})
mae_loo <- mean(abs(loo - dd$mid[dated]))
mae_naive <- mean(abs(mean(dd$mid[dated]) - dd$mid[dated]))
per_style <- dd[dated, ] %>% mutate(style = sub(" .*", "", style)) %>% group_by(style) %>%
  summarise(n = n(), mid = first(mid), mean_score = r3(mean(score)), mean_est = round(mean(est))) %>% arrange(mid)

# ---- the whole corpus: what do the main CA dimensions follow? ----------------------------------------------
# A dimension that follows neither time (Gräslund) nor geography is reported as an unexplained pattern.
inc_all <- incidence(all_d)
da <- all_d[inc_all$keep, ]
fa <- ca(inc_all$I, nd = 3)
mid_a <- ifelse(!is.na(da$style_from), (da$style_from + da$style_to) / 2, NA)
eta2 <- function(y, g) { ok <- !is.na(y) & !is.na(g); y <- y[ok]; g <- g[ok]
  sum(tapply(y, g, function(v) length(v) * (mean(v) - mean(y))^2)) / sum((y - mean(y))^2) }
corpus_dims <- lapply(1:3, function(k) {
  sc <- fa$rowcoord[, k]
  rt <- suppressWarnings(cor(sc, mid_a, method = "spearman", use = "complete.obs"))
  rlat <- suppressWarnings(cor(sc, da$lat, method = "spearman", use = "complete.obs"))
  rlon <- suppressWarnings(cor(sc, da$lon, method = "spearman", use = "complete.obs"))
  e_prov <- eta2(sc, da$province)
  e_carv <- eta2(sc, ifelse(da$carver %in% names(which(table(da$carver) >= 8)), da$carver, NA))
  cs <- fa$colcoord[, k] * sqrt(fa$colmass)
  neg <- names(sort(cs))[1:6]; pos <- names(sort(cs, decreasing = TRUE))[1:6]
  explained <- c(if (abs(rt) >= 0.3) "tid", if (max(abs(rlat), abs(rlon)) >= 0.3 || e_prov >= 0.1) "geografi",
                 if (!is.na(e_carv) && e_carv >= 0.3) "ristare")
  # Provinces at either end
  pm <- sort(tapply(sc, da$province, function(v) if (length(v) >= 20) mean(v) else NA))
  list(dim = k, inertia_pct = r1(100 * fa$sv[k]^2 / sum(fa$sv^2)), rho_time = r3(rt), rho_lat = r3(rlat),
       rho_lon = r3(rlon), eta2_province = r3(e_prov), eta2_carver = r3(e_carv), negative = neg, positive = pos,
       provinces_low = head(names(pm), 3), provinces_high = tail(names(pm), 3),
       explained_by = if (length(explained)) explained else character(0), unexplained = !length(explained))
})

# ---- figures -------------------------------------------------------------------------------------------
pf <- dd[dated, ] %>% mutate(style = factor(sub(" .*", "", style), levels = c("RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5")))
p <- ggplot(pf %>% filter(!is.na(style)), aes(style, score)) +
  geom_boxplot(fill = SEQ[1], colour = SERIES[1], outlier.size = 0.4, outlier.colour = MUTED, width = 0.6) +
  labs(title = "Seriationen mot Gräslunds stilkronologi (Uppland)",
       subtitle = sprintf("Spearmans rho = %.2f (n = %d); stilgruppen ingick inte i korrespondensanalysen", rho, sum(dated)),
       x = tr("Stilgrupp (Gräslund), äldst till vänster", "Style group (Gräslund), earliest on the left"),
       y = tr("Position på första CA-dimensionen", "Position on the first CA dimension")) +
  theme_runor()
fig_valid <- save_fig(p, out, "seriation_validering.png", 6.5, 4.5)

# Battleship-style seriation plot: attribute frequency along the ordered stones (10 bins)
dd$bin <- cut(rank(score, ties.method = "first"), 10, labels = FALSE)
top_attr <- names(sort(abs(fit$colcoord[, 1]) * sqrt(fit$colmass), decreasing = TRUE))[1:min(24, ncol(I))]
bs <- bind_rows(lapply(top_attr, function(at) data.frame(attr = at, bin = 1:10,
                                                         share = tapply(I[, at], dd$bin, mean))))
bs$attr <- factor(bs$attr, levels = top_attr[order(-attr_score[top_attr])])
hmax <- max(bs$share)
p <- ggplot(bs, aes(xmin = bin - 0.45, xmax = bin + 0.45, ymin = as.numeric(attr) - 0.45 * share / hmax,
                    ymax = as.numeric(attr) + 0.45 * share / hmax)) +
  geom_rect(fill = SERIES[1]) +
  scale_y_continuous(breaks = seq_along(levels(bs$attr)), labels = levels(bs$attr), expand = c(0.01, 0.01)) +
  scale_x_continuous(breaks = 1:10, labels = c(tr("tidigt", "early"), rep("", 8), tr("sent", "late"))) +
  labs(title = "Seriationsdiagram", x = tr("Stenarna ordnade efter seriationen, i tio lika stora grupper",
                                           "Stones in seriation order, in ten equal groups"), y = NULL,
       subtitle = "Stapelns höjd = andel stenar i gruppen med draget; dragen sorterade efter sin position") +
  theme_runor() + theme(panel.grid.major = element_blank())
fig_battle <- save_fig(p, out, "seriation_diagram.png", 8, 7)

und <- dd[!dated, ]
if (usable && nrow(und)) {
  p <- ggplot(und, aes(est)) +
    geom_histogram(binwidth = 10, fill = SERIES[1], colour = "white", linewidth = 0.3) +
    labs(title = "Skattad tid för stenar utan stilgrupp", x = tr("År (skattat ur seriationen)", "Year (estimated from the seriation)"), y = tr("Antal stenar", "Stones"),
         subtitle = sprintf("80 %% prediktionsintervall ± %.0f år; medelfel vid korsvalidering %.0f år", 1.28 * resid_sd, mae_loo)) +
    theme_runor()
  fig_est <- save_fig(p, out, "seriation_skattning.png", 6.5, 4)
} else fig_est <- NULL

write.csv(data.frame(signum = dd$signum, score = r3(dd$score), est = round(dd$est), lo = round(dd$lo), hi = round(dd$hi),
                     dated_by_style = dated),
          file.path(out, "chronology_stones.csv"), row.names = FALSE, fileEncoding = "UTF-8")

attributes <- data.frame(attribute = names(attr_score), score = r3(attr_score), n = colSums(I)) %>% arrange(score)
result <- list(
  region = REGION, n_stones = nrow(dd), n_dated = sum(dated), n_attributes = ncol(I), inertia_pct = r1(inertia[1:3]),
  validation = list(rho = r3(rho), p = signif(ct$p.value, 3), lat_rho = r3(lat_rho), partial_rho = r3(partial),
                    usable = usable, mae_years = round(mae), mae_loo_years = round(mae_loo),
                    mae_naive_years = round(mae_naive), resid_sd_years = round(resid_sd)),
  per_style = per_style, corpus_dimensions = corpus_dims, n_corpus = nrow(da),
  calibration = list(intercept = r1(coef(cal)[1]), slope = r1(coef(cal)[2])),
  early = head(attributes, 10), late = head(attributes[order(-attributes$score), ], 10),
  undated = if (usable) list(n = nrow(und), median = round(median(und$est))) else NULL,
  figures = list(validation = fig_valid, diagram = fig_battle, estimates = fig_est),
  method = paste(
    "Seriationen gjordes på Upplands runstenar, det material Gräslunds stilkronologi bygger på; i hela korpusen",
    "följer första dimensionen regionala skillnader snarare än tid.",
    "Korrespondensanalys (ca; Greenacre) av en incidensmatris med stenar och drag (språkdrag, formler, kors,",
    "kortkvistrunor och innehållskategorier; drag på minst", MIN_ATTR, "stenar, stenar med minst", MIN_PER_STONE,
    "drag). Stilgruppen ingick inte, så att ordningen kan prövas mot Gräslunds stilkronologi (Spearmans rangkorrelation",
    "mot stilgruppens mittår). Eftersom språkdrag också varierar geografiskt redovisas korrelationen med latitud och",
    "den partiella korrelationen med tid när latituden hållits konstant. Skattade år kommer från en linjär regression av",
    "mittåret på CA-positionen, med 80 % prediktionsintervall; modellens fel mättes med korsvalidering (lämna en ute)."
  )
)
write_result(result, out, "chronology")
