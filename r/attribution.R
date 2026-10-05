# Attribueringsmodell: random forest (tidymodels + ranger) som väger samman geografi, stil, språkdrag, formler,
# runbigram och innehåll. Utvärderas med upprepad korsvalidering; delmodeller visar vad varje slags belägg bidrar med.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({
  library(tidymodels)
  library(ranger)
})
tidymodels_prefer()

a <- cli_args(); P <- a$params; out <- a$out; cdir <- P$corpus_dir
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
MIN_CARVER <- 8
FOLDS <- 5
REPEATS <- 3
TREES <- 500
NEAR_KM <- 25

d <- read_corpus(P$corpus)
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
full <- d %>% left_join(geo %>% select(signum, x, y, water_km), by = "signum") %>% left_join(txt, by = "signum") %>%
  mutate(x_km = x / 1000, y_km = y / 1000)

tc <- trait_cols(d); cc <- cat_cols(d)
fcols <- grep("^formula_", names(txt), value = TRUE)
bcols <- grep("^bg_", names(txt), value = TRUE)
SETS <- list(
  "Geografi" = c("x_km", "y_km", "province"),
  "Stil" = c("style", "cross", "short_twig"),
  "Språk och innehåll" = c(tc, fcols, bcols, cc),
  "Alla" = c("x_km", "y_km", "province", "style", "cross", "short_twig", tc, fcols, bcols, cc)
)
GROUP <- c(setNames(rep("Geografi", 3), SETS$Geografi), setNames(rep("Stil", 3), SETS$Stil),
           setNames(rep("Språk och innehåll", length(SETS[[3]])), SETS[[3]]))
nominal <- c("province", "style", tc, fcols)

train <- full %>% filter(!is.na(carver)) %>% group_by(carver) %>% filter(n() >= MIN_CARVER) %>% ungroup()
train$carver <- factor(train$carver)
lv <- levels(train$carver)
for (col in nominal) train[[col]] <- as.character(train[[col]])

# Nominal levels are fixed by the training stones; unseen values in new stones become "okänd"
train_levels <- lapply(setNames(nominal, nominal), function(col) union(sort(unique(na.omit(train[[col]]))), "okänd"))
prep_frame <- function(df, cols) {
  df <- df[, c(intersect("carver", names(df)), cols), drop = FALSE]
  for (col in intersect(nominal, cols)) {
    v <- as.character(df[[col]])
    v[is.na(v) | !(v %in% train_levels[[col]])] <- "okänd"
    df[[col]] <- factor(v, levels = train_levels[[col]])
  }
  df
}

make_wf <- function(cols, importance = "none") {
  rec <- recipe(carver ~ ., data = prep_frame(train, cols)) %>%
    step_novel(all_nominal_predictors()) %>%
    step_impute_median(all_numeric_predictors()) %>%
    step_zv(all_predictors())
  mod <- rand_forest(trees = TREES, min_n = 2) %>%
    set_engine("ranger", importance = importance, seed = seed, num.threads = max(1, parallel::detectCores() - 1)) %>%
    set_mode("classification")
  workflow() %>% add_recipe(rec) %>% add_model(mod)
}

folds_for <- function(cols) {
  set.seed(seed)
  vfold_cv(prep_frame(train, cols), v = FOLDS, repeats = REPEATS, strata = carver)
}

pcols <- paste0(".pred_", lv)
evaluate <- function(name) {
  cols <- SETS[[name]]
  res <- fit_resamples(make_wf(cols), folds_for(cols), metrics = metric_set(accuracy, mn_log_loss),
                       control = control_resamples(save_pred = TRUE))
  pr <- collect_predictions(res, summarize = TRUE) %>% arrange(.row)
  probs <- as.matrix(pr[, pcols])
  truth <- as.integer(pr$carver)
  rank_truth <- sapply(seq_len(nrow(probs)), function(i) sum(probs[i, ] > probs[i, truth[i]]) + 1)
  onehot <- outer(truth, seq_along(lv), "==") * 1
  list(name = name, preds = pr, probs = probs, truth = truth,
       accuracy = mean(rank_truth == 1), top3 = mean(rank_truth <= 3),
       log_loss = mean(-log(pmax(probs[cbind(seq_len(nrow(probs)), truth)], 1e-15))),
       brier = mean(rowSums((probs - onehot)^2)))
}
evals <- lapply(names(SETS), evaluate)
names(evals) <- names(SETS)
E <- evals[["Alla"]]

majority <- max(table(train$carver)) / nrow(train)
ablation <- lapply(evals, function(e) list(features = e$name, accuracy = r3(e$accuracy), top3 = r3(e$top3),
                                           log_loss = r3(e$log_loss), brier = r3(e$brier)))

# Calibration of the full model (out-of-fold)
pmax_ <- apply(E$probs, 1, max)
pred_ <- apply(E$probs, 1, which.max)
correct <- pred_ == E$truth
bins <- cut(pmax_, breaks = seq(0, 1, 0.1), include.lowest = TRUE)
calib <- data.frame(bin = bins, p = pmax_, correct = correct) %>% group_by(bin) %>%
  summarise(n = n(), mean_p = mean(p), accuracy = mean(correct)) %>% filter(n > 0)
ece <- sum(calib$n * abs(calib$mean_p - calib$accuracy)) / sum(calib$n)
reliab <- lapply(c(0.3, 0.5, 0.7), function(t) {
  s <- pmax_ >= t
  list(threshold = t, n = sum(s), share_of_stones = r3(mean(s)), accuracy = if (any(s)) r3(mean(correct[s])) else NA)
})

per_carver <- lapply(seq_along(lv), function(j) {
  s <- E$truth == j
  list(carver = lv[j], n = sum(s), recall = r3(mean(pred_[s] == j)),
       precision = if (any(pred_ == j)) r3(mean(E$truth[pred_ == j] == j)) else NA)
})
conf <- table(truth = lv[E$truth], pred = lv[pred_])
confused <- as.data.frame(conf) %>% filter(truth != pred, Freq > 0) %>% arrange(desc(Freq)) %>% head(12)

# Final model on all training stones, with permutation importance
set.seed(seed)
final <- fit(make_wf(SETS$Alla, importance = "permutation"), prep_frame(train, SETS$Alla))
imp <- extract_fit_engine(final)$variable.importance
imp_df <- data.frame(feature = names(imp), importance = as.numeric(imp)) %>% arrange(desc(importance))
bg_names <- if (file.exists(file.path(cdir, "text.json"))) fromJSON(file.path(cdir, "text.json"))$bigrams else character(0)
label_feature <- function(f) {
  if (f %in% names(TRAIT_LABELS)) return(TRAIT_LABELS[[f]])
  if (f %in% names(CAT_LABELS)) return(CAT_LABELS[[f]])
  if (startsWith(f, "bg_")) { i <- as.integer(sub("bg_", "", f)); return(paste0("Runbigram ", bg_names[i])) }
  c(x_km = "Öst–väst (km)", y_km = "Nord–syd (km)", province = "Landskap", style = "Stilgrupp", cross = "Kors",
    short_twig = "Kortkvistrunor", formula_raising = "Resarformel", formula_monument = "Monument",
    formula_order = "Ordföljd", formula_signature = "Ristarsignatur", formula_prayer = "Bön")[[f]] %||% f
}
`%||%` <- function(x, y) if (is.null(x) || is.na(x)) y else x
imp_df$label <- vapply(imp_df$feature, function(f) tryCatch(label_feature(f), error = function(e) f), character(1))
imp_df$group <- unname(GROUP[imp_df$feature])
group_imp <- imp_df %>% group_by(group) %>% summarise(importance = sum(pmax(importance, 0))) %>%
  mutate(share = importance / sum(importance))

# Predictions for runestones without a certain carver near the training stones (closed set: only these carvers)
train_xy <- as.matrix(train[!is.na(train$x), c("x", "y")])
cand <- full %>% filter(is.na(carver), !is.na(x))
nearest <- sapply(seq_len(nrow(cand)), function(i) min(sqrt((train_xy[, 1] - cand$x[i])^2 + (train_xy[, 2] - cand$y[i])^2)) / 1000)
cand$near_km <- nearest
cand <- cand %>% filter(near_km <= NEAR_KM)
for (col in nominal) cand[[col]] <- as.character(cand[[col]])
cp <- predict(final, prep_frame(cand, SETS$Alla), type = "prob")
cpm <- as.matrix(cp[, pcols])
top_k <- function(row, k = 3) { o <- order(-row)[1:k]; list(carvers = lv[o], p = r3(row[o])) }
predictions <- lapply(seq_len(nrow(cand)), function(i) {
  t <- top_k(cpm[i, ])
  rundata <- if (!is.na(cand$carvers_all[i])) cand$carvers_all[i] else ""
  list(signum = cand$signum[i], province = cand$province[i], place = cand$place[i], near_km = r1(cand$near_km[i]),
       top = t$carvers[1], p = t$p[1], second = t$carvers[2], p2 = t$p[2], third = t$carvers[3], p3 = t$p[3],
       rundata_uncertain = rundata,
       agrees_rundata = if (nzchar(rundata)) t$carvers[1] %in% strsplit(rundata, ";")[[1]] else NA)
})
predictions <- predictions[order(-sapply(predictions, `[[`, "p"))]
unc <- Filter(function(p) nzchar(p$rundata_uncertain), predictions)

# ---- figures ------------------------------------------------------------------------------------------------
# Figure labels in the figure's language (the JSON keeps the Swedish keys)
SETN <- c("Geografi" = tr("Geografi", "Geography"), "Stil" = tr("Stil", "Style"),
          "Språk och innehåll" = tr("Språk och innehåll", "Language and content"), "Alla" = tr("Alla", "All"))
MET <- c(tr("Rätt ristare först", "Correct first choice"), tr("Rätt ristare bland tre främsta", "Correct among first three"))
ab <- bind_rows(lapply(evals, function(e) data.frame(set = e$name, metric = MET, value = c(e$accuracy, e$top3))))
ab$set <- factor(unname(SETN[ab$set]), levels = unname(SETN[names(SETS)]))
ab$metric <- factor(ab$metric, levels = MET)
p <- ggplot(ab, aes(set, value, fill = metric)) +
  geom_col(position = position_dodge(width = 0.75), width = 0.7, colour = "white", linewidth = 0.5) +
  geom_text(aes(label = sprintf("%.0f %%", 100 * value)), position = position_dodge(width = 0.75), vjust = -0.4,
            size = 2.8, colour = INK) +
  geom_hline(yintercept = majority, linetype = "dashed", colour = MUTED, linewidth = 0.4) +
  scale_fill_manual(values = SERIES[1:2], name = NULL) +
  scale_y_continuous(labels = scales::percent, limits = c(0, 1.05), expand = c(0, 0)) +
  labs(title = "Vad varje slags belägg räcker till", x = NULL, y = tr("Andel stenar (korsvaliderat)", "Share of stones (cross-validated)"),
       subtitle = sprintf("%d säkra stenar av %d ristare; %d-faldig korsvalidering upprepad %d gånger. Streckat: gissa alltid vanligaste ristaren (%.0f %%)",
                          nrow(train), length(lv), FOLDS, REPEATS, 100 * majority)) +
  theme_runor() + theme(panel.grid.major.x = element_blank())
fig_ablation <- save_fig(p, out, "modell_delmodeller.png", 7.5, 4.5)

p <- ggplot(calib, aes(mean_p, accuracy)) +
  geom_abline(slope = 1, intercept = 0, colour = MUTED, linetype = "dashed", linewidth = 0.4) +
  geom_line(colour = SERIES[1], linewidth = 0.7) +
  geom_point(aes(size = n), colour = SERIES[1]) +
  scale_size_area(max_size = 6, name = tr("Antal stenar", "Stones")) +
  coord_equal(xlim = c(0, 1), ylim = c(0, 1)) +
  labs(title = "Hur väl sannolikheterna stämmer", x = tr("Modellens sannolikhet för sitt förstaval", "The model's probability for its first choice"),
       y = tr("Andel där förstavalet var rätt", "Share of correct first choices"), subtitle = sprintf("Förväntat kalibreringsfel (ECE): %.3f", ece)) +
  theme_runor()
fig_calib <- save_fig(p, out, "modell_kalibrering.png", 5.5, 5.5)

ti <- head(imp_df, 20)
label_en <- function(f) {
  if (f %in% names(TRAIT_LABELS_EN)) return(TRAIT_LABELS_EN[[f]])
  if (f %in% names(CAT_LABELS_EN)) return(CAT_LABELS_EN[[f]])
  if (f %in% names(FORMULA_LABELS_EN)) return(FORMULA_LABELS_EN[[f]])
  if (startsWith(f, "bg_")) return(paste0("Rune bigram ", bg_names[as.integer(sub("bg_", "", f))]))
  c(x_km = "East–west position (km)", y_km = "North–south position (km)", province = "Province", style = "Style group",
    cross = "Cross", short_twig = "Short-twig runes")[[f]] %||% f
}
if (identical(LANG, "en")) ti$label <- vapply(ti$feature, function(f) tryCatch(label_en(f), error = function(e) f), character(1))
ti$label <- factor(ti$label, levels = rev(unique(ti$label)))
ti$group <- unname(SETN[ti$group])
p <- ggplot(ti, aes(importance, label, fill = group)) +
  geom_col(width = 0.7) +
  scale_fill_manual(values = setNames(SERIES, unname(SETN[c("Geografi", "Stil", "Språk och innehåll")])), name = NULL) +
  labs(title = "Variabler som modellen lutar sig mest mot", x = tr("Permutationsvikt", "Permutation importance"), y = NULL) +
  theme_runor() + theme(panel.grid.major.y = element_blank())
fig_imp <- save_fig(p, out, "modell_variabler.png", 7.5, 5.5)

cm <- as.data.frame(prop.table(conf, 1))
cm$truth <- factor(cm$truth, levels = rev(lv)); cm$pred <- factor(cm$pred, levels = lv)
p <- ggplot(cm, aes(pred, truth, fill = Freq)) +
  geom_tile(colour = "white", linewidth = 0.4) +
  scale_fill_gradient(low = "white", high = SEQ[3], name = tr("Andel", "Share"), labels = scales::percent) +
  labs(title = "Förväxlingar", x = tr("Modellens förstaval", "The model's first choice"),
       y = tr("Ristare enligt Rundata", "Carver in the database")) +
  theme_runor() + theme(axis.text.x = element_text(angle = 45, hjust = 1), panel.grid.major = element_blank())
fig_conf <- save_fig(p, out, "modell_forvaxling.png", 8, 7)

oof <- data.frame(signum = train$signum[E$preds$.row], carver = lv[E$truth], E$probs, check.names = FALSE)
write.csv(oof, file.path(out, "attribution_oof.csv"), row.names = FALSE, fileEncoding = "UTF-8")
saveRDS(list(final = final, levels = lv, cols = SETS$Alla, nominal = nominal, train_levels = train_levels, train_xy = train_xy,
             near_km = NEAR_KM), file.path(out, "attribution_model.rds"))

result <- list(
  n_train = nrow(train), carvers = lv, min_inscriptions = MIN_CARVER, folds = FOLDS, repeats = REPEATS, trees = TREES,
  majority_baseline = r3(majority), ablation = unname(ablation),
  calibration = list(ece = r3(ece), bins = calib %>% mutate(across(c(mean_p, accuracy), r3)), reliability = reliab),
  per_carver = per_carver, confused = confused,
  importance = head(imp_df %>% mutate(importance = signif(importance, 3)), 30),
  group_importance = group_imp %>% mutate(across(c(importance, share), r3)),
  predictions = head(predictions, 400), n_predictions = length(predictions), near_km = NEAR_KM,
  uncertain = list(n = length(unc), agree = sum(sapply(unc, function(p) isTRUE(p$agrees_rundata)))),
  figures = list(ablation = fig_ablation, calibration = fig_calib, importance = fig_imp, confusion = fig_conf),
  method = paste(
    "Random forest (Breiman 2001; ranger, tidymodels) med", TREES, "träd tränades på svenska vikingatida runstenar med en",
    "säker ristare i Rundata, för ristare med minst", MIN_CARVER, "stenar. Variablerna är koordinater och landskap,",
    "stilgrupp, kors och kortkvistrunor, elva språkdrag, fem formler, de 100 vanligaste runbigrammen och nio",
    "innehållskategorier. Modellen utvärderades med", FOLDS, "-faldig stratifierad korsvalidering upprepad", REPEATS,
    "gånger; sannolikheterna för varje sten kommer från de modeller som inte såg stenen. Delmodeller med bara geografi,",
    "bara stil respektive bara språk och innehåll visar vad varje slags belägg bidrar med. Förslag ges bara för stenar",
    "inom", NEAR_KM, "km från en träningssten, och sannolikheterna gäller under antagandet att ristaren är en av de",
    length(lv), "ristarna i modellen."
  ),
  caveat = paste(
    "Rundatas attribueringar i Södermanland, Uppland, Västmanland och Gästrikland bygger till stor del på Axelson (1993),",
    "som själv vägde in stil, stavning och geografi. Modellen lär sig därför delvis att återskapa de bedömningarna, och",
    "korsvalideringen mäter överensstämmelse med dem snarare än med en oberoende sanning."
  )
)
write_result(result, out, "attribution")
