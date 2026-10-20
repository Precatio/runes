# Pröva en egen fråga: två kontroller i R av sambandet som src/question.py räknar med Mantel–Haenszel (METHODS.md 1y).
#   Rscript --vanilla r/question.R params.json utmapp
# params: data (CSV med y, x, province, epoch, hand, xk, yk, moved) och kind (drag, landskap, tid eller bergart).
#
# 1. Ristaren som slumpeffekt (lme4::glmer, logistisk): y ~ x + landskap + tidsskikt + (1 | hand). "hand" är den
#    säkra ristaren, och stenar utan säker ristare grupperas per socken, som i r/words.R och r/change.R. Då räknas en
#    flitig ristares stenar inte som oberoende belägg: håller sambandet bara för att en ristare skrev så, försvinner det.
#    För ett landskap tas landskapet bort ur de fasta termerna, för en tidsgräns tidsskiktet.
# 2. Platsen som yta (mgcv::gam, logistisk): y ~ x + tidsskikt + s(xk, yk), där s() är en tunnplåtsyta över stenarnas
#    läge (km) i stället för landskapens grova gränser. Håller sambandet bara för att draget och jämförelsen hör hemma i
#    samma trakt, försvinner det. Flyttade stenar räknas inte, eftersom deras plats inte är den ursprungliga. Inte för
#    landskapsfrågor: där är platsen själva jämförelsen.
# Laddar bara jsonlite, lme4 och mgcv (inte common.R), så att en fråga tar några sekunder.
suppressPackageStartupMessages({ library(jsonlite); library(lme4); library(mgcv) })
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

fixed <- switch(kind, landskap = "epoch", tid = "province", c("province", "epoch"))
# A fixed term with one level says nothing and makes the design singular
fixed <- Filter(function(v) nlevels(droplevels(d[[v]])) > 1, fixed)

carver <- safe({
  f <- reformulate(c("x", fixed, "(1 | hand)"), "y")
  m <- glmer(f, data = d, family = binomial, control = glmerControl(optimizer = "bobyqa", calc.derivs = FALSE), nAGQ = 1)
  cf <- summary(m)$coefficients
  wald(cf["x", 1], cf["x", 2], "glmer(y ~ x + landskap + tidsskikt + (1 | ristare eller socken))",
       list(n = nrow(d), groups = nlevels(droplevels(d$hand)), sd_hand = as.numeric(attr(VarCorr(m)$hand, "stddev")),
            singular = isSingular(m)))
})

place <- if (kind == "landskap") list(skipped = "landskap") else safe({
  dd <- d[!is.na(d$xk) & !is.na(d$yk) & d$moved == 0, ]
  dd$epoch <- droplevels(dd$epoch)
  terms <- c("x", if (kind != "tid" && nlevels(dd$epoch) > 1) "epoch", "s(xk, yk, k = 60)")
  m <- gam(reformulate(terms, "y"), data = dd, family = binomial, method = "REML")
  pt <- summary(m)$p.table
  st <- summary(m)$s.table
  wald(pt["x", 1], pt["x", 2], "gam(y ~ x + tidsskikt + s(öst–väst, nord–syd))",
       list(n = nrow(dd), edf = st[1, "edf"]))
})

dir.create(out, showWarnings = FALSE, recursive = TRUE)
write_json(list(carver = carver, place = place), file.path(out, "question.json"), auto_unbox = TRUE, digits = NA)
