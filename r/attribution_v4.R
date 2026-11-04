# Attribueringsmodellen version 4 enligt analysplaner/2026-11-04-attribuering-v4-ornamentik.md: ornament- och
# runformsdragen ur Sveriges runinskrifter (src/sri_text.py) ovanpå appens modell (K0: A + korsform, kalibrerad).
#   Rscript r/attribution_v4.R KORPUSMAPP DRAG_V2.csv UTMAPP SRI.csv
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
sri_path <- commandArgs(trailingOnly = TRUE)[4]
V2_LIB_ONLY <- TRUE
source(file.path(.here, "attribution_v2.R"))
sri <- read.csv(sri_path, encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE, na.strings = "")
SRI <- setdiff(names(sri), c("signum", "sri_artikel"))
train <- train %>% left_join(sri, by = "signum")
log_("SRI-drag:", length(SRI), "· träningsstenar med artikel:", sum(train$sri_artikel == 1, na.rm = TRUE), "av", nrow(train),
     "· signerade med artikel:", sum(train$sri_artikel == 1 & train$signed == 1, na.rm = TRUE))

h1rows <- function(R) R$parish %in% HALF1
calib <- function(R, grid = seq(0.5, 15, 0.05)) {
  h <- h1rows(R)
  ll <- vapply(grid, function(a) llf(powcal(R$P[h], a), R$carver[h]), 0)
  a <- grid[which.min(ll)]
  R$P <- I(powcal(R$P, a)); attr(R, "a") <- a; R
}
h2 <- function(R) R[!h1rows(R), ]
K0 <- calib(run_rf(c(BASE, KORS), "K0 A+korsform"))
K5 <- calib(run_rf(c(BASE, KORS, SRI), "K5 A+korsform+SRI"))
S0 <- calib(run_rf(c("style", "cross", "short_twig", KORS), "Stil"))
S1 <- calib(run_rf(c("style", "cross", "short_twig", KORS, SRI), "Stil+SRI"))
evalv <- function(R, ref, name) {
  a <- per_stone(h2(R)); b <- per_stone(h2(ref)); s <- a[a$signed == 1, ]; sb <- b[b$signed == 1, ]
  d1 <- boot_diff(a, b, f_top1); d2 <- boot_diff(a, b, f_macro); full <- per_stone(R)
  list(name = name, a = attr(R, "a"),
       half2 = list(n_signed = nrow(s), top1 = round(mean(s$ok), 4), macro = round(f_macro(s), 4), log_loss = round(mean(s$ll), 4),
                    d_top1 = round(d1, 4), d_macro = round(d2, 4), log_loss_not_worse = mean(s$ll) <= mean(sb$ll) + 1e-9),
       all = list(top1_signed = round(mean(full$ok[full$signed == 1]), 4), macro_signed = round(f_macro(full[full$signed == 1, ]), 4),
                  top1_attributed = round(mean(full$ok[full$signed == 0]), 4), log_loss_signed = round(mean(full$ll[full$signed == 1]), 4)),
       per_carver = full[full$signed == 1, ] %>% group_by(carver) %>% summarise(n = n(), top1 = round(mean(ok), 3), .groups = "drop"))
}
V <- list(K0 = evalv(K0, K0, "K0"), K5 = evalv(K5, K0, "K5 +SRI"), S0 = evalv(S0, S0, "Stil"), S1 = evalv(S1, S0, "Stil+SRI"))
h <- V$K5$half2
keep <- h$d_top1[["est"]] > 0 && h$d_macro[["est"]] > 0 && h$log_loss_not_worse
for (k in names(V)) { x <- V[[k]]; log_(x$name, sprintf("halva 2: top1 %.3f (%+.3f [%.3f, %.3f]) macro %.3f (%+.3f) ll %.3f | hela: top1 %.3f macro %.3f attribuerade %.3f",
  x$half2$top1, x$half2$d_top1[["est"]], x$half2$d_top1[["lo"]], x$half2$d_top1[["hi"]], x$half2$macro, x$half2$d_macro[["est"]], x$half2$log_loss,
  x$all$top1_signed, x$all$macro_signed, x$all$top1_attributed)) }
log_("SRI-dragen", if (keep) "BEHÅLLS" else "behålls inte", if (keep && h$d_top1[["lo"]] > 0) "(påvisad)" else "")
# Vilka SRI-drag skogen lutar sig mot (permutationsvikt, hela träningsdatan)
set.seed(seed)
df <- prep_frame(train, c(BASE, KORS, SRI)); df$carver <- droplevels(factor(df$carver))
rec <- recipe(carver ~ ., data = df) %>% step_novel(all_nominal_predictors()) %>% step_impute_median(all_numeric_predictors()) %>% step_zv(all_predictors())
fit_imp <- fit(workflow() %>% add_recipe(rec) %>% add_model(rand_forest(trees = TREES, min_n = 2) %>%
  set_engine("ranger", seed = seed, importance = "permutation") %>% set_mode("classification")), df)
imp <- extract_fit_engine(fit_imp)$variable.importance
top_sri <- sort(imp[intersect(names(imp), SRI)], decreasing = TRUE)
write_json(list(plan = "analysplaner/2026-11-04-attribuering-v4-ornamentik.md", varianter = V, behalls = keep,
                pavisad = keep && h$d_top1[["lo"]] > 0, sri_drag = SRI, sri_vikt = as.list(round(top_sri, 5)),
                vikt_rang = match(names(top_sri), names(sort(imp, decreasing = TRUE)))),
           file.path(out, "resultat.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
saveRDS(list(K0 = K0, K5 = K5, S0 = S0, S1 = S1), file.path(out, "oof_v4.rds"))
