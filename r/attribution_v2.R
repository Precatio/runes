# Attribueringsmodellen version 2, enligt den låsta planen analysplaner/2026-11-04-attribuering-v2.md: framåtval på
# provbänken (signerade stenar, korsvalidering grupperad per socken) – korsform, stavningsavtryck, ristarens bygd och tid,
# och en ”samma hand”-modell.
#   Rscript r/attribution_v2.R KORPUSMAPP DRAG_V2.csv UTMAPP
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(tidymodels); library(ranger) })
tidymodels_prefer()
.a <- commandArgs(trailingOnly = TRUE); cdir <- .a[1]; v2_path <- .a[2]; out <- .a[3]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
seed <- 2026; set.seed(seed)
MIN_CARVER <- 8; FOLDS <- 5; REPEATS <- 3; TREES <- 500; BOOT <- 2000; BW_KM <- 15; PAIR_TREES <- 300; NEG_PER_POS <- 3
log_ <- function(...) { cat(format(Sys.time(), "%H:%M:%S"), ..., "\n"); flush.console() }

d <- read_corpus(file.path(cdir, "corpus.csv"))
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
v2 <- read.csv(v2_path, encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE, na.strings = "")
full <- d %>% left_join(geo %>% select(signum, x, y, water_km), by = "signum") %>% left_join(txt, by = "signum") %>%
  left_join(v2, by = "signum") %>% mutate(x_km = x / 1000, y_km = y / 1000)
tc <- trait_cols(d); cc <- cat_cols(d)
fcols <- grep("^formula_", names(txt), value = TRUE); bcols <- grep("^bg_", names(txt), value = TRUE)
KORS <- grep("^kors_", names(v2), value = TRUE)
SPELL <- c(grep("^sp_", names(v2), value = TRUE), "skilj_forst", "skilj_sist")
GEOC <- c("x_km", "y_km", "province")
BASE <- c(GEOC, "style", "cross", "short_twig", tc, fcols, bcols, cc)
nominal_all <- c("province", "style", tc, fcols, SPELL)

pool <- full %>% filter(!is.na(carver))                      # alla stenar med säker ristare
train <- pool %>% group_by(carver) %>% filter(n() >= MIN_CARVER) %>% ungroup()
train$carver <- factor(train$carver); lv <- levels(train$carver)
train$signed <- as.integer(!is.na(train$signed) & train$signed == 1)
for (df in c("train", "pool")) for (col in nominal_all) { z <- get(df); z[[col]] <- as.character(z[[col]]); assign(df, z) }
train_levels <- lapply(setNames(nominal_all, nominal_all), function(col) union(sort(unique(na.omit(c(train[[col]], pool[[col]])))), "okänd"))
prep_frame <- function(df, cols) {
  df <- df[, c(intersect("carver", names(df)), cols), drop = FALSE]
  for (col in intersect(nominal_all, cols)) {
    v <- as.character(df[[col]]); v[is.na(v) | !(v %in% train_levels[[col]])] <- "okänd"
    df[[col]] <- factor(v, levels = train_levels[[col]])
  }
  df
}
fit_rf <- function(df, cols) {
  df <- prep_frame(df, cols); df$carver <- droplevels(factor(df$carver))
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
gkey_of <- function(df) ifelse(is.na(df$parish) | !nzchar(df$parish), paste0("_", df$signum), df$parish)
train$gkey <- gkey_of(train); pool$gkey <- gkey_of(pool)

# Samma uppdelning som provningen (r/attribution_audit.R): samma data, samma seed
set.seed(seed)
G <- group_vfold_cv(prep_frame(train, BASE) %>% mutate(.group = train$gkey), group = .group, v = FOLDS, repeats = REPEATS)
SPL <- lapply(G$splits, function(s) list(tr = s$in_id, te = complement(s)))

top1 <- function(p) names(p)[which.max(p)]
# Rader: en per (del, provsten) med sannolikheter över lv
rows_from <- function(Ps) do.call(rbind, lapply(seq_along(SPL), function(k) {
  te <- SPL[[k]]$te
  data.frame(fold = k, .row = te, signum = train$signum[te], carver = as.character(train$carver[te]),
             signed = train$signed[te], parish = train$gkey[te], P = I(lapply(seq_along(te), function(i) Ps[[k]][i, ])))
}))
run_rf <- function(cols, name) {
  log_("variant", name, length(cols), "variabler")
  Ps <- lapply(seq_along(SPL), function(k) { m <- fit_rf(train[SPL[[k]]$tr, ], cols); probs_for(m, train[SPL[[k]]$te, ], cols, lv) })
  rows_from(Ps)
}

per_stone <- function(R) {
  R$ok <- mapply(function(p, t) sum(p) > 0 && top1(p) == t, R$P, R$carver)
  R$ll <- mapply(function(p, t) -log(max(p[[t]], 1e-15)), R$P, R$carver)
  R %>% group_by(signum, carver, signed, parish) %>% summarise(ok = mean(ok), ll = mean(ll), .groups = "drop")
}
macro <- function(ps) { s <- ps[ps$signed == 1, ]; mean(tapply(s$ok, s$carver, mean)) }
boot_diff <- function(a, b, f) {      # parvis, bootstrap över socknar bland de signerade
  s <- a$signed == 1; A <- a[s, ]; B <- b[match(A$signum, b$signum), ]
  ps <- unique(A$parish); set.seed(seed)
  v <- replicate(BOOT, { k <- unlist(lapply(sample(ps, replace = TRUE), function(p) which(A$parish == p))); f(A[k, ]) - f(B[k, ]) })
  c(est = f(A) - f(B), lo = unname(quantile(v, .025)), hi = unname(quantile(v, .975)))
}
f_top1 <- function(x) mean(x$ok)
f_macro <- function(x) mean(tapply(x$ok, x$carver, mean))
avgP <- function(R) R %>% group_by(signum) %>% summarise(P = list(Reduce(`+`, P) / n()), carver = first(carver),
                                                          signed = first(signed), parish = first(parish), .groups = "drop")
ece <- function(P, truth) {
  pm <- vapply(P, max, 0); ok <- mapply(function(p, t) top1(p) == t, P, truth)
  b <- cut(pm, seq(0, 1, 0.1), include.lowest = TRUE)
  t <- data.frame(b, pm, ok) %>% group_by(b) %>% summarise(n = n(), p = mean(pm), a = mean(ok), .groups = "drop")
  sum(t$n * abs(t$p - t$a)) / sum(t$n)
}
powcal <- function(P, a) lapply(P, function(p) { q <- p^a; if (sum(q) > 0) q / sum(q) else p })
llf <- function(P, truth) mean(mapply(function(p, t) -log(max(p[[t]], 1e-15)), P, truth))
ps_all <- sort(unique(train$gkey)); HALF1 <- ps_all[seq(1, length(ps_all), 2)]
summ <- function(R, name) {
  ps <- per_stone(R); s <- ps[ps$signed == 1, ]; a <- ps[ps$signed == 0, ]
  AP <- avgP(R); h1 <- AP$parish %in% HALF1
  grid_a <- seq(0.5, 5, 0.05); a_best <- grid_a[which.min(vapply(grid_a, function(x) llf(powcal(AP$P[h1], x), AP$carver[h1]), 0))]
  h2s <- !h1 & AP$signed == 1
  list(name = name, top1 = round(mean(s$ok), 4), macro = round(f_macro(s), 4), log_loss = round(mean(s$ll), 4),
       attributed_top1 = round(mean(a$ok), 4), cal_a = a_best,
       ece_half2_after = round(ece(powcal(AP$P[h2s], a_best), AP$carver[h2s]), 4),
       per_carver = s %>% group_by(carver) %>% summarise(n = n(), top1 = round(mean(ok), 3), .groups = "drop"))
}
decide <- function(Rnew, Rbest, name) {
  a <- per_stone(Rnew); b <- per_stone(Rbest)
  d1 <- boot_diff(a, b, f_top1); d2 <- boot_diff(a, b, f_macro)
  ll_ok <- mean(a$ll[a$signed == 1]) <= mean(b$ll[b$signed == 1]) + 1e-9
  keep <- d1[["est"]] > 0 && d2[["est"]] > 0 && ll_ok
  log_(name, sprintf("top1 %+.3f [%.3f, %.3f], macro %+.3f, logloss ok %s → %s", d1[["est"]], d1[["lo"]], d1[["hi"]],
                     d2[["est"]], ll_ok, if (keep) "BEHÅLLS" else "behålls inte"))
  list(step = name, d_top1 = round(d1, 4), d_macro = round(d2, 4), log_loss_not_worse = ll_ok, keep = keep,
       proven = keep && d1[["lo"]] > 0)
}

# r/attribution_v3.R läser in allt ovan (V2_LIB_ONLY) och kör inte stegen
if (!isTRUE(get0("V2_LIB_ONLY"))) {
steps <- list(); summaries <- list()
R0 <- run_rf(BASE, "A (dagens)"); summaries$A <- summ(R0, "A (dagens)"); best <- R0; best_cols <- BASE; best_name <- "A"
saveRDS(R0, file.path(out, "oof_A.rds"))
# Steg 1: korsformen
R1 <- run_rf(c(best_cols, KORS), "1 korsform"); summaries$s1 <- summ(R1, "1 korsform")
steps$s1 <- decide(R1, best, "1 korsform")
if (steps$s1$keep) { best <- R1; best_cols <- c(best_cols, KORS); best_name <- "A+1" }
# Steg 2: stavningsavtrycket
R2 <- run_rf(c(best_cols, SPELL), "2 stavning"); summaries$s2 <- summ(R2, "2 stavning")
steps$s2 <- decide(R2, best, "2 stavning")
if (steps$s2$keep) { best <- R2; best_cols <- c(best_cols, SPELL); best_name <- paste0(best_name, "+2") }
saveRDS(list(best = best, cols = best_cols, name = best_name), file.path(out, "best_efter_2.rds"))

# Steg 3: bygd och tid i stället för råa koordinater
cols3 <- setdiff(best_cols, GEOC)
log_("variant 3 bygd och tid", length(cols3), "variabler")
R3raw <- lapply(seq_along(SPL), function(k) {
  tr <- train[SPL[[k]]$tr, ]; te <- train[SPL[[k]]$te, ]
  P <- probs_for(fit_rf(tr, cols3), te, cols3, lv)
  dens <- sapply(lv, function(cn) {
    s <- tr[tr$carver == cn & !is.na(tr$x_km), ]
    vapply(seq_len(nrow(te)), function(i) {
      if (is.na(te$x_km[i]) || !nrow(s)) return(NA_real_)
      mean(exp(-((s$x_km - te$x_km[i])^2 + (s$y_km - te$y_km[i])^2) / (2 * BW_KM^2))) / (2 * pi * BW_KM^2) + 1e-9
    }, 0)
  })
  tid <- sapply(lv, function(cn) {
    s <- tr[tr$carver == cn & !is.na(tr$style_from), ]
    vapply(seq_len(nrow(te)), function(i) {
      if (is.na(te$style_from[i]) || !nrow(s)) return(NA_real_)
      (sum(s$style_to >= te$style_from[i] & s$style_from <= te$style_to[i]) + 0.5) / (nrow(s) + 1)
    }, 0)
  })
  list(P = P, dens = matrix(dens, nrow = nrow(te)), tid = matrix(tid, nrow = nrow(te)))
})
combine <- function(w) lapply(R3raw, function(z) {
  D <- z$dens; D[is.na(D)] <- 1; Tm <- z$tid; Tm[is.na(Tm)] <- 1
  Q <- z$P * D^w * Tm^w; Q <- Q / pmax(rowSums(Q), 1e-300); colnames(Q) <- lv; Q
})
grid_w <- seq(0, 2, 0.25)
wl <- vapply(grid_w, function(w) {
  Rw <- rows_from(combine(w)); h1 <- Rw$parish %in% HALF1
  mean(mapply(function(p, t) -log(max(p[[t]], 1e-15)), Rw$P[h1], Rw$carver[h1]))
}, 0)
w_best <- grid_w[which.min(wl)]
R3 <- rows_from(combine(w_best)); summaries$s3 <- summ(R3, sprintf("3 bygd och tid (w = %.2f)", w_best))
# Beslutet för steg 3 fattas på sockenhalva 2 (w valdes på halva 1)
h2 <- function(R) R[!(R$parish %in% HALF1), ]
steps$s3 <- decide(h2(R3), h2(best), sprintf("3 bygd och tid, halva 2 (w = %.2f)", w_best))
steps$s3$w <- w_best; steps$s3$w_logloss <- setNames(round(wl, 4), grid_w)
if (steps$s3$keep) { best <- R3; best_name <- paste0(best_name, "+3"); use_prior <- TRUE } else use_prior <- FALSE
saveRDS(list(best = best, cols = if (use_prior) cols3 else best_cols, prior = use_prior, w = w_best, name = best_name),
        file.path(out, "best_efter_3.rds"))

# Steg 4: ”samma hand?” – parmodell
pair_cols <- if (use_prior) cols3 else setdiff(best_cols, GEOC)
pool2 <- pool %>% group_by(carver) %>% filter(n() >= 2) %>% ungroup()
num_cols <- setdiff(pair_cols, nominal_all); nom_cols <- intersect(pair_cols, nominal_all)
pair_X <- function(A, B) {          # A, B: frames med samma antal rader
  X <- list()
  for (cn in num_cols) { a <- suppressWarnings(as.numeric(A[[cn]])); b <- suppressWarnings(as.numeric(B[[cn]])); v <- abs(a - b); v[is.na(v)] <- -1; X[[cn]] <- v }
  for (cn in nom_cols) { a <- as.character(A[[cn]]); b <- as.character(B[[cn]]); v <- ifelse(is.na(a) | is.na(b) | a == "okänd" | b == "okänd", 0.5, as.numeric(a == b)); X[[cn]] <- v }
  dk <- sqrt((A$x_km - B$x_km)^2 + (A$y_km - B$y_km)^2); dk[is.na(dk)] <- -1; X$avstand_km <- dk
  ov <- ifelse(is.na(A$style_from) | is.na(B$style_from), 0.5, as.numeric(A$style_to >= B$style_from & A$style_from <= B$style_to)); X$tid_overlapp <- ov
  as.data.frame(X)
}
fit_pairs <- function(P) {
  set.seed(seed)
  idx <- split(seq_len(nrow(P)), P$carver)
  pos <- do.call(rbind, lapply(idx, function(ii) if (length(ii) >= 2) t(combn(ii, 2)) else NULL))
  n_neg <- NEG_PER_POS * nrow(pos)
  i <- sample(nrow(P), n_neg * 2, replace = TRUE); j <- sample(nrow(P), n_neg * 2, replace = TRUE)
  ok <- P$carver[i] != P$carver[j]; neg <- cbind(i[ok], j[ok])[seq_len(min(n_neg, sum(ok))), , drop = FALSE]
  ij <- rbind(pos, neg); y <- factor(c(rep(1, nrow(pos)), rep(0, nrow(neg))))
  X <- pair_X(P[ij[, 1], ], P[ij[, 2], ]); X$y <- y
  ranger(y ~ ., data = X, num.trees = PAIR_TREES, min.node.size = 5, probability = TRUE, seed = seed,
         num.threads = max(1, parallel::detectCores() - 1))
}
score_pairs <- function(m, te, ref) {   # te: provstenar, ref: referensstenar (med carver)
  cs <- sort(unique(ref$carver))
  t(vapply(seq_len(nrow(te)), function(i) {
    X <- pair_X(te[rep(i, nrow(ref)), ], ref)
    p <- predict(m, X)$predictions[, "1"]
    s <- vapply(cs, function(cn) { v <- sort(p[ref$carver == cn], decreasing = TRUE); mean(v[seq_len(min(3, length(v)))]) }, 0)
    s / max(sum(s), 1e-12)
  }, numeric(length(cs)))) -> M
  colnames(M) <- cs; M
}
log_("variant 4 samma hand", length(pair_cols), "variabler, pool", nrow(pool2), "stenar,", length(unique(pool2$carver)), "ristare")
R4a <- list(); R4b <- list()
for (k in seq_along(SPL)) {
  te <- train[SPL[[k]]$te, ]
  test_parishes <- unique(te$gkey)
  ref <- pool2[!(pool2$gkey %in% test_parishes), ]
  ref <- ref %>% group_by(carver) %>% filter(n() >= 2) %>% ungroup()
  m <- fit_pairs(ref)
  M <- score_pairs(m, te, ref)
  A18 <- matrix(0, nrow(te), length(lv), dimnames = list(NULL, lv)); for (cn in intersect(lv, colnames(M))) A18[, cn] <- M[, cn]
  A18 <- A18 / pmax(rowSums(A18), 1e-12)
  R4a[[k]] <- A18; R4b[[k]] <- M
  log_("del", k, "av", length(SPL), "ref", nrow(ref))
}
R4 <- rows_from(R4a); summaries$s4 <- summ(R4, "4 samma hand (bland de 18)")
steps$s4 <- decide(R4, best, "4 samma hand")
# (b) bland alla ristare i referensen
okb <- unlist(lapply(seq_along(SPL), function(k) { te <- SPL[[k]]$te; M <- R4b[[k]]; colnames(M)[max.col(M, ties.method = "first")] == as.character(train$carver[te]) }))
rb <- data.frame(signum = unlist(lapply(SPL, function(s) train$signum[s$te])), signed = unlist(lapply(SPL, function(s) train$signed[s$te])), ok = okb) %>%
  group_by(signum, signed) %>% summarise(ok = mean(ok), .groups = "drop")
summaries$s4$all_carvers_top1_signed <- round(mean(rb$ok[rb$signed == 1]), 4)
if (steps$s4$keep) { best <- R4; best_name <- paste0(best_name, "+4") }
saveRDS(list(R4 = R4, R4b = R4b), file.path(out, "oof_samma_hand.rds"))

res <- list(plan = "analysplaner/2026-11-04-attribuering-v2.md", korpus = basename(cdir), n_train = nrow(train),
            n_signed = sum(train$signed), slutmodell = best_name, steg = steps, sammanfattning = summaries)
write_json(res, file.path(out, "resultat.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
log_("klart; slutmodell", best_name)
}
