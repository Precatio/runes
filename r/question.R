# Pröva en egen fråga: två kontroller i R av sambandet som src/question.py räknar med Mantel–Haenszel (METHODS.md 1y).
#   Rscript --vanilla r/question.R params.json utmapp
# params: data (CSV med y, x, province, epoch, hand, parish, xk, yk, moved) och kind (drag, landskap, tid eller bergart).
#
# 1. Ristaren som slumpeffekt (lme4::glmer, logistisk): y ~ x + landskap + tidsskikt + (1 | hand). "hand" är den
#    säkra ristaren, och stenar utan säker ristare grupperas per socken, som i r/words.R och r/change.R. Då räknas en
#    flitig ristares stenar inte som oberoende belägg: håller sambandet bara för att en ristare skrev så, försvinner det.
#    För ett landskap tas landskapet bort ur de fasta termerna, för en tidsgräns tidsskiktet.
# 2. Platsen som yta (mgcv::gam, logistisk): y ~ x + tidsskikt + s(xk, yk), där s() är en tunnplåtsyta över stenarnas
#    läge (km) i stället för landskapens grova gränser. Håller sambandet bara för att draget och jämförelsen hör hemma i
#    samma trakt, försvinner det. Flyttade stenar räknas inte, eftersom deras plats inte är den ursprungliga. Inte för
#    landskapsfrågor: där är platsen själva jämförelsen.
# 3. För båda (2026-10-27): andelen med A när B finns och när det inte finns, med övrigt som i datan
#    (marginaleffects::avg_predictions; för ristarmodellen en typisk ristare, re.form = NA), så att svaret kan sägas i
#    andelar och inte bara som oddskvot; och en modellkontroll med simulerade residualer (DHARMa): är residualerna jämnt
#    fördelade, finns överspridning, och – för ristarmodellen, som inte har platsen i sig – finns ett kvarvarande rumsligt
#    mönster (stenar på samma plats slås ihop). Kontrollen ändrar inte domen; den visas, så att en modell som inte passar
#    datan syns.
# Laddar bara jsonlite, lme4, mgcv, marginaleffects och DHARMa (inte common.R), så att en fråga tar några sekunder.
suppressPackageStartupMessages({ library(jsonlite); library(lme4); library(mgcv) })
has_me <- requireNamespace("marginaleffects", quietly = TRUE)
has_dh <- requireNamespace("DHARMa", quietly = TRUE)
options(warn = 1)

args <- commandArgs(TRUE)
P <- fromJSON(args[1])
out <- args[2]
d <- read.csv(P$data, stringsAsFactors = FALSE, encoding = "UTF-8", na.strings = c("", "NA"))
kind <- P$kind
d$province <- factor(d$province)
d$epoch <- factor(d$epoch)
d$hand <- factor(d$hand)

wald <- function(est, se, model, extra = list()) {
  z <- est / se
  c(list(or = exp(est), ci = exp(est + c(-1.96, 1.96) * se), p = 2 * pnorm(-abs(z)), direction = sign(est),
         model = model), extra)
}
safe <- function(expr) tryCatch(expr, error = function(e) list(error = conditionMessage(e)))

# The share with A when B is absent (x = 0) and present (x = 1), averaged over the data as it is
shares <- function(m, ...) {
  if (!has_me) return(NULL)
  tryCatch({
    pr <- marginaleffects::avg_predictions(m, variables = list(x = c(0, 1)), ...)
    pr <- as.data.frame(pr)
    k <- match(c(0, 1), pr$x)
    list(without = pr$estimate[k[1]], with = pr$estimate[k[2]],
         without_ci = c(pr$conf.low[k[1]], pr$conf.high[k[1]]), with_ci = c(pr$conf.low[k[2]], pr$conf.high[k[2]]))
  }, error = function(e) list(error = conditionMessage(e)))
}

# DHARMa's checks on simulated residuals; spatial only when coordinates are given (locations with several stones pooled)
model_check <- function(m, coords = NULL) {
  if (!has_dh) return(NULL)
  tryCatch({
    set.seed(1)
    r <- DHARMa::simulateResiduals(m, n = 250, plot = FALSE)
    out <- list(uniformity_p = DHARMa::testUniformity(r, plot = FALSE)$p.value,
                dispersion_p = DHARMa::testDispersion(r, plot = FALSE)$p.value)
    if (!is.null(coords)) {
      # only stones with a place of their own (not moved); stones on the same spot (to the km) are pooled
      sel <- !is.na(coords$xk) & !is.na(coords$yk) & coords$moved == 0
      if (sum(sel) > 30) {
        g <- paste(round(coords$xk), round(coords$yk))
        rg <- DHARMa::recalculateResiduals(r, group = g, sel = sel)
        first <- which(sel)[!duplicated(g[sel])]
        out$spatial_p <- DHARMa::testSpatialAutocorrelation(rg, x = coords$xk[first], y = coords$yk[first], plot = FALSE)$p.value
      }
    }
    out$ok <- all(unlist(out) >= 0.05)
    out
  }, error = function(e) list(error = conditionMessage(e)))
}

fixed <- switch(kind, landskap = "epoch", tid = "province", c("province", "epoch"))
# A fixed term with one level says nothing and makes the design singular
fixed <- Filter(function(v) nlevels(droplevels(d[[v]])) > 1, fixed)

carver <- safe({
  f <- reformulate(c("x", fixed, "(1 | hand)"), "y")
  m <- glmer(f, data = d, family = binomial, control = glmerControl(optimizer = "bobyqa", calc.derivs = FALSE), nAGQ = 1)
  cf <- summary(m)$coefficients
  wald(cf["x", 1], cf["x", 2], "glmer(y ~ x + landskap + tidsskikt + (1 | ristare eller socken))",
       list(n = nrow(d), groups = nlevels(droplevels(d$hand)), sd_hand = as.numeric(attr(VarCorr(m)$hand, "stddev")),
            singular = isSingular(m), shares = shares(m, re.form = NA),
            check = model_check(m, d[, c("xk", "yk", "moved")])))
})

# 4. Socknen som slumpeffekt (2026-10-29, som robusthetstrappan): håller sambandet när socknarna får skilja sig
#    sinsemellan, eller är det några socknars egenhet? Saknas socknen i underlaget räknas steget inte.
parish <- if (!"parish" %in% names(d)) list(skipped = "socken saknas") else safe({
  d$parish <- factor(d$parish)
  f <- reformulate(c("x", fixed, "(1 | parish)"), "y")
  m <- glmer(f, data = d, family = binomial, control = glmerControl(optimizer = "bobyqa", calc.derivs = FALSE), nAGQ = 1)
  cf <- summary(m)$coefficients
  wald(cf["x", 1], cf["x", 2], "glmer(y ~ x + landskap + tidsskikt + (1 | socken))",
       list(n = nrow(d), groups = nlevels(droplevels(d$parish)), singular = isSingular(m)))
})

place <- if (kind == "landskap") list(skipped = "landskap") else safe({
  dd <- d[!is.na(d$xk) & !is.na(d$yk) & d$moved == 0, ]
  dd$epoch <- droplevels(dd$epoch)
  terms <- c("x", if (kind != "tid" && nlevels(dd$epoch) > 1) "epoch", "s(xk, yk, k = 60)")
  m <- gam(reformulate(terms, "y"), data = dd, family = binomial, method = "REML")
  pt <- summary(m)$p.table
  st <- summary(m)$s.table
  wald(pt["x", 1], pt["x", 2], "gam(y ~ x + tidsskikt + s(öst–väst, nord–syd))",
       list(n = nrow(dd), edf = st[1, "edf"], shares = shares(m), check = model_check(m)))
})

dir.create(out, showWarnings = FALSE, recursive = TRUE)
write_json(list(carver = carver, place = place, parish = parish), file.path(out, "question.json"), auto_unbox = TRUE, digits = NA)
