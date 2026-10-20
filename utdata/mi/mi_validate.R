# Maskeringsprovet för den multipla imputationen av tidsskiktet (utdata/mi/analysplan_mi.md, punkt 3–5).
#   Rscript --vanilla utdata/mi/mi_validate.R utdata/mi/korpus_mi.csv utdata/mi/validering.json [upprepningar]
# 20 upprepningar: 30 % av de daterade stenarna maskeras (MAR efter sannolikheten att sakna stilgrupp, och MCAR per
# landskap), tidsskiktet imputeras med mice (polr, m = 20) utan (A) och med (B) språkdateringen, och oddskvoten för varje
# drag från 1050 mot före 1050 (Mantel–Haenszel över landskap) jämförs med värdet när alla daterade stenar är kända.
suppressPackageStartupMessages({ library(mice); library(jsonlite) })

args <- commandArgs(TRUE)
d <- read.csv(args[1], stringsAsFactors = FALSE, na.strings = c("", "NA"), encoding = "UTF-8")
out_path <- args[2]
REPS <- if (length(args) >= 3) as.integer(args[3]) else 20L
M <- 20L
LEVELS <- c("före 1020", "1020–1050", "1050–1075", "1075 och senare")
TRAITS <- c("kristen", "hednisk", "neutral", "bon", "sjal", "kors", "stungna", "monoftong", "o_runa", "r_for_R", "auk",
            "at", "h_skrivet", "nasal", "bindrunor", "signatur", "bro", "fard", "arv", "sjalvminne", "ristare_kand", "signerad")
LANG <- c("stungna", "monoftong", "o_runa", "r_for_R", "auk", "at", "h_skrivet", "nasal", "bindrunor")
stopifnot(all(TRAITS %in% names(d)))

d$E <- factor(d$E, levels = LEVELS, ordered = TRUE)
for (t in TRAITS) d[[t]] <- factor(d[[t]], levels = c("nej", "ja", "okänd"))
d$province_imp <- factor(d$province_imp)
d$family <- factor(d$family)
dated <- !is.na(d$E)
# Language dating in quintiles, the limits from the dated stones (the values, not their dating), and "okänd"
q5 <- function(x) {
  br <- unique(quantile(x[dated], 0:5 / 5, na.rm = TRUE))
  f <- cut(x, br, include.lowest = TRUE, labels = FALSE)
  factor(ifelse(is.na(f), "okänd", paste0("q", f)))
}
d$aux1q <- q5(d$aux1)
d$aux2q <- q5(d$aux2)
pkey <- paste(d$province, ifelse(is.na(d$parish), paste0("_", d$signum), d$parish))

# The parish's other dated stones: the layer of their mean mid-year, the stone itself left out; only known years count
parish_ctx <- function(year_known) {
  s <- tapply(ifelse(is.na(year_known), 0, year_known), pkey, sum)[pkey]
  n <- tapply(!is.na(year_known), pkey, sum)[pkey]
  own <- ifelse(is.na(year_known), 0, year_known)
  k <- n - as.integer(!is.na(year_known))
  m <- ifelse(k > 0, (s - own) / pmax(k, 1), NA)
  factor(ifelse(is.na(m), "ingen", LEVELS[findInterval(m, c(1020, 1050, 1075)) + 1]))
}

PRED_A <- c("province_imp", TRAITS, "family", "logwords", "parish_ctx")
PRED_B <- c(PRED_A, "aux1q", "aux2q")

impute <- function(E, year_known, preds, m = M, seed = 2026L) {
  dat <- d
  dat$E <- E
  dat$parish_ctx <- parish_ctx(year_known)
  dat <- dat[, c("E", preds)]
  meth <- make.method(dat); meth[] <- ""; meth["E"] <- "polr"
  pm <- make.predictorMatrix(dat); pm[, ] <- 0; pm["E", preds] <- 1
  suppressWarnings(mice(dat, m = m, maxit = 1, method = meth, predictorMatrix = pm, seed = seed, printFlag = FALSE))
}

# Mantel–Haenszel log odds ratio (trait yes vs no, from 1050 vs before) over provinces, with the Robins–Breslow–Greenland
# variance; strata without both groups or both values are skipped, as in src/question.py
mh <- function(trait, E) {
  y <- trait == "ja"; ok <- trait != "okänd" & !is.na(E)
  x <- as.integer(E[ok]) >= 3; y <- y[ok]; st <- d$province[ok]
  R <- S <- PR <- PSQR <- QS <- 0
  for (s in unique(st)) {
    i <- st == s
    a <- sum(x[i] & y[i]); b <- sum(x[i] & !y[i]); c <- sum(!x[i] & y[i]); dd <- sum(!x[i] & !y[i])
    n <- a + b + c + dd
    if (a + b == 0 || c + dd == 0 || a + c == 0 || b + dd == 0 || n < 2) next
    r <- a * dd / n; s_ <- b * c / n; p <- (a + dd) / n; q <- (b + c) / n
    R <- R + r; S <- S + s_; PR <- PR + p * r; PSQR <- PSQR + p * s_ + q * r; QS <- QS + q * s_
  }
  if (R <= 0 || S <= 0) return(c(est = NA, var = NA))
  c(est = log(R / S), var = PR / (2 * R^2) + PSQR / (2 * R * S) + QS / (2 * S^2))
}

pooled <- function(imp, trait) {
  ests <- t(sapply(seq_len(imp$m), function(k) mh(d[[trait]], complete(imp, k)$E)))
  if (any(is.na(ests))) return(c(est = NA, lo = NA, hi = NA))
  p <- pool.scalar(ests[, "est"], ests[, "var"], n = nrow(d), k = 1)
  half <- qt(0.975, p$df) * sqrt(p$t)
  c(est = p$qbar, lo = p$qbar - half, hi = p$qbar + half)
}

truth <- sapply(TRAITS, function(t) mh(d[[t]], d$E))
usable <- TRAITS[!is.na(truth["est", ])]
message("drag som går att pröva: ", length(usable), " av ", length(TRAITS))

# The probability that a stone lacks a certain style group, for the MAR masking (no parish context, no language dating)
prop <- glm(reformulate(c("province_imp", TRAITS, "family", "logwords"), "undated"),
            data = transform(d, undated = as.integer(!dated)), family = binomial)
p_und <- predict(prop, type = "response")[dated]
scale_to <- function(p, target = 0.3) {
  f <- function(c) mean(pmin(c * p, 0.95)) - target
  pmin(uniroot(f, c(1e-6, 1e3))$root * p, 0.95)
}
p_mar <- scale_to(p_und)
idx_dated <- which(dated)

one_rep <- function(rep) {
  set.seed(rep)
  masks <- list(
    MAR = idx_dated[runif(length(idx_dated)) < p_mar],
    MCAR = unlist(lapply(split(idx_dated, d$province[idx_dated]), function(ix) ix[sample.int(length(ix), round(0.3 * length(ix)))]))
  )
  res <- list()
  for (mk in names(masks)) {
    hide <- masks[[mk]]
    E <- d$E; E[hide] <- NA
    yk <- d$year; yk[hide] <- NA
    cc <- sapply(usable, function(t) { r <- mh(d[[t]], E); c(est = r[["est"]], lo = r[["est"]] - 1.96 * sqrt(r[["var"]]), hi = r[["est"]] + 1.96 * sqrt(r[["var"]])) })
    arms <- list()
    for (arm in c("A", "B")) {
      imp <- impute(E, yk, if (arm == "A") PRED_A else PRED_B)
      est <- sapply(usable, function(t) pooled(imp, t))
      draws <- sapply(seq_len(imp$m), function(k) as.integer(complete(imp, k)$E[hide]))
      mode <- apply(draws, 1, function(v) as.integer(names(which.max(table(v)))))
      arms[[arm]] <- list(est = est, accuracy = mean(mode == as.integer(d$E[hide])))
    }
    res[[mk]] <- list(n_masked = length(hide), cc = cc, arms = arms)
  }
  message("upprepning ", rep, " klar")
  res
}

reps <- lapply(seq_len(REPS), one_rep)

summ <- function(mk, which) {
  cover <- c(); bias <- c(); bias_cc <- c(); per_trait <- list(); acc <- c()
  for (r in reps) {
    x <- r[[mk]]
    est <- if (which == "CC") x$cc else x$arms[[which]]$est
    for (t in usable) {
      tr <- truth["est", t]
      if (is.na(est["est", t])) next
      hit <- est["lo", t] <= tr && tr <= est["hi", t]
      cover <- c(cover, hit); bias <- c(bias, abs(est["est", t] - tr))
      per_trait[[t]] <- c(per_trait[[t]], hit)
    }
    if (which != "CC") acc <- c(acc, x$arms[[which]]$accuracy)
  }
  list(coverage = mean(cover), n_intervals = length(cover), mean_abs_bias = mean(bias),
       coverage_language = mean(unlist(per_trait[intersect(LANG, names(per_trait))])),
       coverage_per_trait = lapply(per_trait, mean), accuracy = if (length(acc)) mean(acc) else NULL)
}

out <- list(plan_sha256 = "d97e20ba6d2c5b96248a62cded09deb0e9df635d7ef956315e90a65225128b7b",
            n = nrow(d), n_dated = sum(dated), reps = REPS, m = M, usable = usable,
            truth = as.list(truth["est", usable]), mar_mean_mask = mean(p_mar))
for (mk in c("MAR", "MCAR")) out[[mk]] <- list(CC = summ(mk, "CC"), A = summ(mk, "A"), B = summ(mk, "B"))

# The decision, by the plan's rules (point 4)
mar <- out$MAR
pass <- function(a) a$coverage >= 0.90 && a$mean_abs_bias < mar$CC$mean_abs_bias
use_B <- pass(mar$B) && (mar$B$accuracy - mar$A$accuracy) >= 0.02
out$decision <- list(
  A_passes = pass(mar$A), B_passes = pass(mar$B),
  arm = if (use_B) "B" else if (pass(mar$A)) "A" else "ingen",
  language_arm = if (use_B && mar$B$coverage_language >= 0.90) "B" else if (pass(mar$A)) "A" else "ingen")
write_json(out, out_path, auto_unbox = TRUE, digits = 6, pretty = TRUE)
message("klart: ", out_path)
