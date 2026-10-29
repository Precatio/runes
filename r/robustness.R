# Robusthetstrappan: samma steg för varje mönster i korpusanalyserna (METHODS.md 1v, src/robustness.py).
#   Rscript --vanilla r/robustness.R params.json utmapp
# params: data (CSV: pattern, y, x, province, epoch, half, hand, parish, xk, yk, moved, moved_runor), specs (ett per
# mönster: id, adjust, x_lo, x_hi, lopo, place, moved, coding) och seed.
#
# Varje mönster är ett samband mellan ett utfall y (0/1) och en jämförelse x (0/1, eller tiden i 50-årssteg) på
# stenarna. Stegen, i ordning:
#   raw       logistisk regression y ~ x, ingenting justerat
#   adjusted  y ~ x + landskap + tidsskikt (de justeringar mönstret tål: för en landskaps- eller landsdelsskillnad inte
#             landskapet, för en tidsförändring inte tidsskiktet)
#   carver    samma med ristaren som slumpeffekt (lme4; stenar utan säker ristare grupperas per socken)
#   parish    samma med socknen som slumpeffekt: håller en skillnad mellan landskap eller landsdelar också när
#             socknarna får skilja sig sinsemellan, eller är den några socknars egenhet?
#   place     platsen som yta (mgcv, s(öst, nord)) i stället för landskapsgränser, utan flyttade stenar; inte för
#             mönster där platsen är själva jämförelsen
#   halves    den justerade modellen i var halva av korpusen (hela socknar växelvis inom landskapet)
#   lopo      den justerade modellen utan ett landskap i taget (landskap med minst 30 stenar): riktningen ska hålla
#             utan vart och ett, p < 0,05 bara där minst två tredjedelar av stenarna är kvar; den sämsta utgången och
#             de landskap utan vilka riktningen vänder
#   moved     den justerade modellen utan de stenar som Rundatas placering anger som flyttade, och utan dem som
#             Riksantikvarieämbetets Runor 2020 anger som inte på ursprunglig plats; för mönster som hänger på platsen
# Ett steg håller när p < 0,05 och riktningen är densamma som i det justerade steget. Därtill:
#   effect    skillnaden i procentenheter mellan x_lo och x_hi (marginaleffects::avg_comparisons på den justerade
#             modellen, medelvärdet över stenarna som de är), med andelarna på var sida
#   check     DHARMa på ristarmodellen: residualernas fördelning, överspridning, kvarvarande rumsligt mönster
#   coding    när utfallet (eller jämförelsen) kodas av regler och det finns ett handkodat facit: n_sim omräkningar
#             där varje regelkodad sten får sitt "sanna" värde dragit ur facit (andelen rätt bland regelns ja och bland
#             dess nej, Jeffreys-fördelning), så att osäkerheten i kodningen följer med in i resultatet
suppressPackageStartupMessages({ library(jsonlite); library(lme4); library(mgcv) })
has_me <- requireNamespace("marginaleffects", quietly = TRUE)
has_dh <- requireNamespace("DHARMa", quietly = TRUE)
options(warn = 1)

args <- commandArgs(TRUE)
P <- fromJSON(args[1], simplifyVector = FALSE)
out <- args[2]
set.seed(if (is.null(P$seed)) 2026 else P$seed)
D <- read.csv(P$data, stringsAsFactors = FALSE, encoding = "UTF-8", na.strings = c("", "NA"))
ALPHA <- 0.05
MIN_PROVINCE <- 30

safe <- function(expr) tryCatch(expr, error = function(e) list(error = conditionMessage(e)))
ctrl <- glmerControl(optimizer = "bobyqa", calc.derivs = FALSE)

coef_x <- function(m) {
  cf <- if (inherits(m, "gam")) summary(m)$p.table else summary(m)$coefficients
  if (!"x" %in% rownames(cf)) return(list(error = "x saknas i modellen"))
  est <- cf["x", 1]; se <- cf["x", 2]
  list(or = exp(est), ci = exp(est + c(-1.96, 1.96) * se), p = 2 * pnorm(-abs(est / se)), direction = sign(est))
}

fixed_terms <- function(dd, adjust) Filter(function(v) nlevels(droplevels(factor(dd[[v]]))) > 1, unlist(adjust))
fit_glm <- function(dd, adjust) {
  f <- reformulate(c("x", fixed_terms(dd, adjust)), "y")
  suppressWarnings(glm(f, data = dd, family = binomial))
}
glm_rung <- function(dd, adjust) {
  if (nrow(dd) < 20 || length(unique(dd$y)) < 2 || length(unique(dd$x)) < 2) return(list(skipped = "för få stenar", n = nrow(dd)))
  safe(c(coef_x(fit_glm(dd, adjust)), list(n = nrow(dd))))
}
holds <- function(r, direction) {
  if (is.null(r) || !is.null(r$error) || !is.null(r$skipped) || is.null(r$p) || is.na(r$p)) return(NULL)
  r$p < ALPHA && r$direction == direction
}

model_check <- function(m, dd) {
  if (!has_dh) return(NULL)
  tryCatch({
    r <- DHARMa::simulateResiduals(m, n = 250, plot = FALSE)
    o <- list(uniformity_p = DHARMa::testUniformity(r, plot = FALSE)$p.value,
              dispersion_p = DHARMa::testDispersion(r, plot = FALSE)$p.value)
    sel <- !is.na(dd$xk) & !is.na(dd$yk) & dd$moved == 0
    if (sum(sel) > 30) {
      g <- paste(round(dd$xk), round(dd$yk))
      rg <- DHARMa::recalculateResiduals(r, group = g, sel = sel)
      first <- which(sel)[!duplicated(g[sel])]
      o$spatial_p <- DHARMa::testSpatialAutocorrelation(rg, x = dd$xk[first], y = dd$yk[first], plot = FALSE)$p.value
    }
    o$ok <- all(unlist(o) >= 0.05)
    o
  }, error = function(e) list(error = conditionMessage(e)))
}

effect <- function(m, lo, hi, ...) {
  if (!has_me) return(NULL)
  tryCatch({
    pr <- as.data.frame(marginaleffects::avg_predictions(m, variables = list(x = c(lo, hi)), ...))
    k <- match(c(lo, hi), pr$x)
    cmp <- as.data.frame(marginaleffects::avg_comparisons(m, variables = list(x = c(lo, hi)), ...))
    list(share_lo = pr$estimate[k[1]], share_hi = pr$estimate[k[2]],
         diff = cmp$estimate[1], diff_ci = c(cmp$conf.low[1], cmp$conf.high[1]))
  }, error = function(e) list(error = conditionMessage(e)))
}

coding_sim <- function(dd, adjust, cd, direction) {
  n_sim <- if (is.null(cd$n_sim)) 200 else cd$n_sim
  v <- cd$var
  coded <- dd[[v]]
  res <- vapply(seq_len(n_sim), function(i) {
    ppv <- rbeta(1, cd$ppv[[1]] + 0.5, cd$ppv[[2]] + 0.5)  # facit: rätt och fel bland regelns ja
    npv <- rbeta(1, cd$npv[[1]] + 0.5, cd$npv[[2]] + 0.5)  # facit: rätt och fel bland regelns nej
    sim <- dd
    sim[[v]] <- ifelse(coded == 1, rbinom(nrow(dd), 1, ppv), rbinom(nrow(dd), 1, 1 - npv))
    if (length(unique(sim$y)) < 2 || length(unique(sim$x)) < 2) return(c(NA, NA))
    r <- tryCatch(coef_x(fit_glm(sim, adjust)), error = function(e) NULL)
    if (is.null(r) || is.null(r$p)) c(NA, NA) else c(log(r$or), as.numeric(r$p < ALPHA && r$direction == direction))
  }, numeric(2))
  ok <- !is.na(res[1, ])
  list(var = v, n_sim = sum(ok), share_holds = mean(res[2, ok]), or_median = exp(median(res[1, ok])),
       or_range = exp(unname(quantile(res[1, ok], c(0.025, 0.975)))), ppv = cd$ppv, npv = cd$npv)
}

ladder <- function(sp) {
  dd <- D[D$pattern == sp$id, ]
  dd$province <- factor(dd$province); dd$epoch <- factor(dd$epoch)
  dd$hand <- factor(dd$hand); dd$parish <- factor(dd$parish)
  adjust <- sp$adjust
  o <- list(id = sp$id, n = nrow(dd), k = sum(dd$y), rungs = list())
  o$rungs$raw <- glm_rung(dd, list())
  o$rungs$adjusted <- glm_rung(dd, adjust)
  a <- o$rungs$adjusted
  if (!is.null(a$error) || !is.null(a$skipped)) return(o)
  dir <- a$direction
  o$direction <- dir
  fx <- fixed_terms(dd, adjust)
  m_carver <- NULL
  o$rungs$carver <- safe({
    m_carver <- glmer(reformulate(c("x", fx, "(1 | hand)"), "y"), data = dd, family = binomial, control = ctrl, nAGQ = 1)
    c(coef_x(m_carver), list(n = nrow(dd), groups = nlevels(droplevels(dd$hand)), singular = isSingular(m_carver)))
  })
  o$rungs$parish <- safe({
    m <- glmer(reformulate(c("x", fx, "(1 | parish)"), "y"), data = dd, family = binomial, control = ctrl, nAGQ = 1)
    c(coef_x(m), list(n = nrow(dd), groups = nlevels(droplevels(dd$parish)), singular = isSingular(m)))
  })
  if (isTRUE(sp$place)) o$rungs$place <- safe({
    dp <- dd[!is.na(dd$xk) & !is.na(dd$yk) & dd$moved == 0, ]
    if (nrow(dp) < 100) list(skipped = "för få stenar med ursprunglig plats", n = nrow(dp)) else {
      terms <- c("x", if ("epoch" %in% fx && nlevels(droplevels(dp$epoch)) > 1) "epoch",
                 sprintf("s(xk, yk, k = %d)", min(60, floor(nrow(dp) / 10))))
      m <- gam(reformulate(terms, "y"), data = dp, family = binomial, method = "REML")
      c(coef_x(m), list(n = nrow(dp)))
    }
  })
  o$rungs$half_A <- glm_rung(dd[dd$half == "A", ], adjust)
  o$rungs$half_B <- glm_rung(dd[dd$half == "B", ], adjust)
  if (isTRUE(sp$lopo)) {
    provs <- names(which(table(dd$province) >= MIN_PROVINCE))
    if (length(unique(dd$province)) >= 3 && length(provs) >= 2) {
      each <- lapply(provs, function(p) c(glm_rung(dd[dd$province != p, ], adjust), list(without = p)))
      ps <- vapply(each, function(r) if (is.null(r$p)) NA_real_ else r$p, numeric(1))
      # The direction must hold without every province; p < 0.05 only where two thirds of the stones remain (without
      # Uppland half the material is gone, and a test with half the stones cannot be required to stay significant)
      ok <- vapply(each, function(r) {
        if (is.null(r$p) || is.na(r$p)) return(FALSE)
        r$direction == dir && (r$p < ALPHA || r$n < 2 / 3 * nrow(dd))
      }, logical(1))
      flips <- vapply(each, function(r) !is.null(r$direction) && r$direction != dir, logical(1))
      worst <- if (any(!ok)) each[!ok][[which.max(replace(ps[!ok], is.na(ps[!ok]), 1))]] else each[[which.max(replace(ps, is.na(ps), 1))]]
      o$rungs$lopo <- c(worst[c("or", "ci", "p", "direction", "n", "without")],
                        list(all_hold = all(ok), n_provinces = length(provs), flips = as.list(provs[flips])))
    }
  }
  if (isTRUE(sp$moved)) {
    o$rungs$moved_rundata <- glm_rung(dd[dd$moved == 0, ], adjust)
    o$rungs$moved_runor <- glm_rung(dd[dd$moved == 0 & dd$moved_runor == 0, ], adjust)
  }
  for (k in names(o$rungs)) {
    r <- o$rungs[[k]]
    o$rungs[[k]]$holds <- if (k == "lopo") isTRUE(r$all_hold) else holds(r, dir)
  }
  lo <- if (is.null(sp$x_lo)) 0 else sp$x_lo
  hi <- if (is.null(sp$x_hi)) 1 else sp$x_hi
  if (!is.null(m_carver)) o$check <- model_check(m_carver, dd)
  # Averaged over the stones as they are (the adjusted model): with a strong carver effect a "typical carver" (re.form =
  # NA) can sit at the edge of the scale and hide a difference that is plain in the data
  o$effect <- effect(fit_glm(dd, adjust), lo, hi)
  if (!is.null(sp$coding)) o$coding <- safe(coding_sim(dd, adjust, sp$coding, dir))
  o
}

res <- lapply(P$specs, function(sp) safe(ladder(sp)))
names(res) <- vapply(P$specs, function(sp) sp$id, character(1))
dir.create(out, showWarnings = FALSE, recursive = TRUE)
write_json(list(patterns = res, alpha = ALPHA, min_province = MIN_PROVINCE,
                packages = list(marginaleffects = has_me, DHARMa = has_dh)),
           file.path(out, "robustness.json"), auto_unbox = TRUE, digits = NA, null = "null", na = "null")
