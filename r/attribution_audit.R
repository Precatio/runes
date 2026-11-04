# Attribueringsmodellen prövad mot de signerade stenarna, enligt den låsta planen
# analysplaner/2026-11-04-attribuering-provad.md.
#   Rscript r/attribution_audit.R KORPUSMAPP UTMAPP
# Samma data, variabler och skog som r/attribution.R; korsvalidering grupperad per socken; facit = signerade stenar.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(tidymodels); library(ranger); library(lme4) })
tidymodels_prefer()
.a <- commandArgs(trailingOnly = TRUE); cdir <- .a[1]; out <- .a[2]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
seed <- 2026; set.seed(seed)
MIN_CARVER <- 8; FOLDS <- 5; REPEATS <- 3; TREES <- 500; MIN_SIGNED_S <- 5; BOOT <- 2000

d <- read_corpus(file.path(cdir, "corpus.csv"))
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
full <- d %>% left_join(geo %>% select(signum, x, y, water_km), by = "signum") %>% left_join(txt, by = "signum") %>%
  mutate(x_km = x / 1000, y_km = y / 1000)
tc <- trait_cols(d); cc <- cat_cols(d)
fcols <- grep("^formula_", names(txt), value = TRUE); bcols <- grep("^bg_", names(txt), value = TRUE)
ALL <- c("x_km", "y_km", "province", "style", "cross", "short_twig", tc, fcols, bcols, cc)
GEO <- c("x_km", "y_km", "province")
nominal <- c("province", "style", tc, fcols)

train <- full %>% filter(!is.na(carver)) %>% group_by(carver) %>% filter(n() >= MIN_CARVER) %>% ungroup()
train$carver <- factor(train$carver); lv <- levels(train$carver)
for (col in nominal) train[[col]] <- as.character(train[[col]])
train$signed <- as.integer(!is.na(train$signed) & train$signed == 1)
train_levels <- lapply(setNames(nominal, nominal), function(col) union(sort(unique(na.omit(train[[col]]))), "okänd"))
prep_frame <- function(df, cols) {
  df <- df[, c(intersect("carver", names(df)), cols), drop = FALSE]
  for (col in intersect(nominal, cols)) {
    v <- as.character(df[[col]]); v[is.na(v) | !(v %in% train_levels[[col]])] <- "okänd"
    df[[col]] <- factor(v, levels = train_levels[[col]])
  }
  df
}
fit_rf <- function(df, cols) {
  df <- prep_frame(df, cols); df$carver <- droplevels(df$carver)
  rec <- recipe(carver ~ ., data = df) %>% step_novel(all_nominal_predictors()) %>%
    step_impute_median(all_numeric_predictors()) %>% step_zv(all_predictors())
  mod <- rand_forest(trees = TREES, min_n = 2) %>%
    set_engine("ranger", seed = seed, num.threads = max(1, parallel::detectCores() - 1)) %>% set_mode("classification")
  fit(workflow() %>% add_recipe(rec) %>% add_model(mod), df)
}
probs_for <- function(m, df, cols, levs) {
  P <- matrix(0, nrow(df), length(levs), dimnames = list(NULL, levs))
  pr <- predict(m, prep_frame(df, cols)[, cols, drop = FALSE], type = "prob")
  for (cn in names(pr)) { k <- sub("^\\.pred_", "", cn); if (k %in% levs) P[, k] <- pr[[cn]] }
  P
}

gkey <- ifelse(is.na(train$parish) | !nzchar(train$parish), paste0("_", train$signum), train$parish)
sig_n <- table(train$carver[train$signed == 1])
S <- names(sig_n)[sig_n >= MIN_SIGNED_S]
cat("Träningsstenar", nrow(train), "· signerade", sum(train$signed), "· ristare", length(lv), "· S =", paste(S, collapse = ", "), "\n")

set.seed(seed)
g <- group_vfold_cv(prep_frame(train, ALL) %>% mutate(.group = gkey), group = .group, v = FOLDS, repeats = REPEATS)
rows <- list()
for (k in seq_along(g$splits)) {
  sp <- g$splits[[k]]; tr_i <- sp$in_id; te_i <- complement(sp)
  rep_id <- if ("id" %in% names(g)) g$id[k] else "Repeat1"
  tr <- train[tr_i, ]; te <- train[te_i, ]
  mA <- fit_rf(tr, ALL); PA <- probs_for(mA, te, ALL, lv)
  mG <- fit_rf(tr, GEO); PG <- probs_for(mG, te, GEO, lv)
  ok <- !is.na(tr$x_km)
  nn <- vapply(seq_len(nrow(te)), function(i) {
    if (is.na(te$x_km[i])) return(NA_character_)
    as.character(tr$carver[ok][which.min((tr$x_km[ok] - te$x_km[i])^2 + (tr$y_km[ok] - te$y_km[i])^2)])
  }, "")
  trB <- tr[tr$signed == 1 & tr$carver %in% S, ]
  PB <- if (length(unique(trB$carver)) >= 2) probs_for(fit_rf(trB, ALL), te, ALL, S) else matrix(NA, nrow(te), length(S), dimnames = list(NULL, S))
  rows[[k]] <- data.frame(rep = rep_id, fold = k, .row = te_i, signum = te$signum, carver = as.character(te$carver),
                          signed = te$signed, parish = gkey[te_i],
                          A = I(lapply(seq_len(nrow(te)), function(i) PA[i, ])),
                          G = I(lapply(seq_len(nrow(te)), function(i) PG[i, ])),
                          B = I(lapply(seq_len(nrow(te)), function(i) PB[i, ])), nn = nn)
  cat("del", k, "av", length(g$splits), "\n")
}
R <- do.call(rbind, rows)
saveRDS(R, file.path(out, "oof.rds"))

top1 <- function(p) names(p)[which.max(p)]
R$okA <- mapply(function(p, t) top1(p) == t, R$A, R$carver)
R$top3A <- mapply(function(p, t) t %in% names(sort(-p))[1:3] || t %in% names(p)[order(-p)][1:3], R$A, R$carver)
R$llA <- mapply(function(p, t) -log(max(p[[t]], 1e-15)), R$A, R$carver)
R$okG <- mapply(function(p, t) top1(p) == t, R$G, R$carver)
R$okNN <- !is.na(R$nn) & R$nn == R$carver
inS <- R$carver %in% S & R$signed == 1
R$okAS <- NA; R$okB <- NA
R$okAS[inS] <- mapply(function(p, t) { q <- p[S]; if (sum(q) == 0) FALSE else top1(q) == t }, R$A[inS], R$carver[inS])
R$okB[inS] <- mapply(function(p, t) if (all(is.na(p))) FALSE else top1(p) == t, R$B[inS], R$carver[inS])

# Per sten: medel över upprepningarna
per_stone <- R %>% group_by(signum, carver, signed, parish) %>%
  summarise(okA = mean(okA), top3A = mean(top3A), llA = mean(llA), okG = mean(okG), okNN = mean(okNN),
            okAS = mean(okAS), okB = mean(okB), .groups = "drop")
boot <- function(df, f) {
  ps <- unique(df$parish); set.seed(seed)
  v <- replicate(BOOT, { s <- sample(ps, replace = TRUE); f(df[unlist(lapply(s, function(p) which(df$parish == p))), ]) })
  c(est = f(df), lo = unname(quantile(v, 0.025)), hi = unname(quantile(v, 0.975)))
}
r3 <- function(x) round(x, 3)
sig <- per_stone[per_stone$signed == 1, ]; att <- per_stone[per_stone$signed == 0, ]

q1 <- list(n = nrow(sig), carvers = length(unique(sig$carver)),
           top1 = r3(boot(sig, function(x) mean(x$okA))), top3 = r3(boot(sig, function(x) mean(x$top3A))),
           log_loss = r3(mean(sig$llA)),
           per_carver = sig %>% group_by(carver) %>% summarise(n = n(), top1 = r3(mean(okA)), .groups = "drop"))
gm <- tryCatch(glmer(okA ~ signed + (1 | carver) + (1 | signum), family = binomial, data = R,
                     control = glmerControl(optimizer = "bobyqa")), error = function(e) NULL)
q2 <- list(attributed = list(n = nrow(att), top1 = r3(boot(att, function(x) mean(x$okA)))),
           signed = list(n = nrow(sig), top1 = q1$top1),
           glmer = if (is.null(gm)) NULL else {
             s <- summary(gm)$coefficients
             list(b_signed = r3(s["signed", 1]), se = r3(s["signed", 2]), p = signif(s["signed", 4], 3))
           },
           per_carver = per_stone %>% group_by(carver) %>%
             summarise(n_sign = sum(signed == 1), top1_sign = r3(mean(okA[signed == 1])),
                       n_attr = sum(signed == 0), top1_attr = r3(mean(okA[signed == 0])), .groups = "drop"))
sS <- per_stone[per_stone$carver %in% S & per_stone$signed == 1, ]
q3 <- list(S = S, n = nrow(sS), A = r3(boot(sS, function(x) mean(x$okAS))), B = r3(boot(sS, function(x) mean(x$okB))),
           A_minus_B = r3(boot(sS, function(x) mean(x$okAS - x$okB))))
q3$verdict <- if (q3$A_minus_B[["lo"]] > 0) "attribueringarna hjälper" else if (q3$A_minus_B[["hi"]] < 0) "attribueringarna skadar" else "ingen påvisad skillnad"
q4 <- list(geografi = r3(boot(sig, function(x) mean(x$okG))), narmaste_sten = r3(boot(sig, function(x) mean(x$okNN))))
best <- if (q4$geografi[["est"]] >= q4$narmaste_sten[["est"]]) "okG" else "okNN"
q4$best <- best
q4$A_minus_best <- r3(boot(sig, function(x) mean(x$okA - x[[best]])))
q4$verdict <- if (q4$A_minus_best[["lo"]] > 0) "slår geografin" else "slår inte geografin påvisbart"

# Fråga 5: kalibrering (medelsannolikheter per sten över upprepningarna)
avgP <- R %>% group_by(signum) %>% summarise(P = list(Reduce(`+`, A) / n()), carver = first(carver), signed = first(signed),
                                             parish = first(parish), .groups = "drop")
ece <- function(P, truth) {
  pm <- vapply(P, max, 0); ok <- mapply(function(p, t) top1(p) == t, P, truth)
  b <- cut(pm, seq(0, 1, 0.1), include.lowest = TRUE)
  t <- data.frame(b, pm, ok) %>% group_by(b) %>% summarise(n = n(), p = mean(pm), a = mean(ok), .groups = "drop")
  list(ece = r3(sum(t$n * abs(t$p - t$a)) / sum(t$n)), bins = t %>% mutate(p = r3(p), a = r3(a)))
}
powcal <- function(P, a) lapply(P, function(p) { q <- p^a; if (sum(q) > 0) q / sum(q) else p })
llf <- function(P, truth) mean(mapply(function(p, t) -log(max(p[[t]], 1e-15)), P, truth))
ps <- sort(unique(avgP$parish)); half1 <- ps[seq(1, length(ps), 2)]
h1 <- avgP$parish %in% half1
grid_a <- seq(0.5, 5, 0.05)
a_best <- grid_a[which.min(vapply(grid_a, function(a) llf(powcal(avgP$P[h1], a), avgP$carver[h1]), 0))]
h2s <- !h1 & avgP$signed == 1
q5 <- list(ece_signed = ece(avgP$P[avgP$signed == 1], avgP$carver[avgP$signed == 1]), a = a_best,
           half2_signed = list(n = sum(h2s),
                               before = list(ece = ece(avgP$P[h2s], avgP$carver[h2s])$ece, log_loss = r3(llf(avgP$P[h2s], avgP$carver[h2s]))),
                               after = list(ece = ece(powcal(avgP$P[h2s], a_best), avgP$carver[h2s])$ece,
                                            log_loss = r3(llf(powcal(avgP$P[h2s], a_best), avgP$carver[h2s])))))
# ”Någon annan”: varje ristare utelämnad, mot de grupperade sannolikheterna för kända signerade stenar
set.seed(seed)
loco <- bind_rows(lapply(lv, function(cn) {
  m <- fit_rf(train[train$carver != cn, ], ALL)
  te <- train[train$carver == cn, ]
  data.frame(carver = cn, signed = te$signed, p = apply(probs_for(m, te, ALL, setdiff(lv, cn)), 1, max))
}))
known <- vapply(avgP$P[avgP$signed == 1], max, 0)
gridt <- seq(0.05, 0.6, 0.005)
J <- vapply(gridt, function(t) mean(loco$p < t) + mean(known >= t) - 1, 0)
thr <- gridt[which.max(J)]
okk <- mapply(function(p, t) top1(p) == t, avgP$P[avgP$signed == 1], avgP$carver[avgP$signed == 1])
q5$someone_else <- list(threshold = thr, J = r3(max(J)), known_signed_flagged = r3(mean(known < thr)),
                        left_out_flagged = r3(mean(loco$p < thr)),
                        accuracy_kept_signed = r3(mean(okk[known >= thr])), share_kept_signed = r3(mean(known >= thr)),
                        old_threshold_0.35 = list(known_signed_flagged = r3(mean(known < 0.35)), left_out_flagged = r3(mean(loco$p < 0.35))))

res <- list(plan = "analysplaner/2026-11-04-attribuering-provad.md", korpus = basename(cdir), n_train = nrow(train),
            n_signed = sum(train$signed), carvers = lv, q1 = q1, q2 = q2, q3 = q3, q4 = q4, q5 = q5)
write_json(res, file.path(out, "resultat.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
write.csv(per_stone, file.path(out, "per_sten.csv"), row.names = FALSE, fileEncoding = "UTF-8")
str(res[c("q1", "q3", "q4")], max.level = 2)
