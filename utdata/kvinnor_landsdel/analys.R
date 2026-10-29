# Varför stod kvinnorna i Svealand oftare på stenen? Enligt den låsta planen
# analysplaner/2026-10-29-kvinnorna-i-svealand.md.
#   Rscript utdata/kvinnor_landsdel/analys.R KORPUSMAPP UTMAPP
.args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({ library(mgcv); library(dplyr); library(jsonlite) })
D <- .args[1]; out <- .args[2]
dir.create(out, showWarnings = FALSE, recursive = TRUE)
MIN_EVENTS <- 15

d <- read.csv(file.path(D, "corpus.csv"), stringsAsFactors = FALSE, na.strings = "", check.names = FALSE)
pp <- read.csv(file.path(D, "people.csv"), stringsAsFactors = FALSE, na.strings = "")
ms <- read.csv(file.path(D, "messages.csv"), stringsAsFactors = FALSE, na.strings = "")
d <- merge(d, pp, by = "signum")
d <- merge(d, ms[, c("signum", "msg_resa", "msg_dod_borta")], by = "signum", all.x = TRUE)
d <- d[d$legible == 1 & d$region %in% c("Svealand", "Götaland", "Gotland", "Norrland") & d$n_resare >= 1, ]
d$region <- factor(d$region, c("Svealand", "Götaland", "Gotland", "Norrland"))
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
d$carver_f <- factor(ifelse(!is.na(d$carver) & d$carver != "", d$carver,
                            paste0("_", d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish))))
d$kvinna <- as.integer(d$resare_k > 0)
d$kvinna_make <- as.integer(d$resare_k > 0 & d$rel_make == 1)
# Planens definition: kvinnor bland resarna, inga män, alla resares kön bestämt (people.csv har ingen sådan kolumn)
d$kvinna_ensam <- as.integer(d$resare_k > 0 & d$resare_m == 0 & d$resare_okand == 0)
d$lres <- log(d$n_resare)
d$kristen <- as.integer(d$cat_kristen == 1)
d$gotaland <- as.integer(d$region == "Götaland")
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]

fit <- function(y, rhs, dd, carver = TRUE) {
  dd <- droplevels(dd[!is.na(dd[[y]]), ])
  f <- as.formula(paste(y, "~", rhs, if (carver) "+ s(carver_f, bs = \"re\")" else ""))
  if (carver) suppressWarnings(gam(f, family = binomial, data = dd, method = "REML"))
  else suppressWarnings(glm(f, family = binomial, data = dd))
}
coef_of <- function(m, term) {
  s <- if (inherits(m, "gam")) summary(m)$p.table else summary(m)$coefficients
  if (!term %in% rownames(s)) return(NULL)
  b <- s[term, 1]; se <- s[term, 2]
  list(or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se), p = s[term, 4], logor = b)
}
share_by_region <- function(m, dd) {
  sapply(c(Svealand = "Svealand", Götaland = "Götaland"), function(g) {
    nd <- droplevels(dd); nd$region <- factor(g, levels(nd$region))
    mean(predict(m, nd, type = "response", exclude = "s(carver_f)"))
  })
}
TESTS <- list(
  list(key = "t0_huvud", y = "kvinna", rhs = "region + period", term = "regionGötaland", data = function(x) x,
       label = "Huvudtestet: kvinna bland resarna"),
  list(key = "t1_anka", y = "kvinna_make", rhs = "region + period", term = "regionGötaland", data = function(x) x,
       label = "A1 Kvinna reser efter make"),
  list(key = "t2_utan_resa", y = "kvinna", rhs = "region + period", term = "regionGötaland",
       data = function(x) x[!is.na(x$msg_resa) & x$msg_resa == 0 & !is.na(x$msg_dod_borta) & x$msg_dod_borta == 0, ],
       label = "A2 Kvinna bland resarna, utan resestenar"),
  list(key = "t3_antal", y = "kvinna", rhs = "region + period + lres", term = "regionGötaland", data = function(x) x,
       label = "B3 Kvinna bland resarna, antalet resare konstant"),
  list(key = "t4_ensam", y = "kvinna_ensam", rhs = "region + period", term = "regionGötaland", data = function(x) x,
       label = "C4 En ensam kvinna reser stenen"),
  list(key = "t5_son", y = "kvinna", rhs = "region + period", term = "regionGötaland",
       data = function(x) x[x$rel_barn == 1, ], label = "D5 Stenar efter söner: modern"),
  list(key = "t6_far", y = "kvinna", rhs = "region + period", term = "regionGötaland",
       data = function(x) x[x$rel_foralder == 1 & x$rel_make == 0, ], label = "D6 Stenar efter fäder: dotter eller hustru"),
  list(key = "t7_bror", y = "kvinna", rhs = "region + period", term = "regionGötaland",
       data = function(x) x[x$rel_syskon == 1, ], label = "D7 Stenar efter bröder: syster eller mor"),
  list(key = "t8_kristen", y = "kristen", rhs = "kvinna + region + period", term = "kvinna", data = function(x) x,
       label = "E8 Kristen markör: kvinna bland resarna"),
  list(key = "t9_kristen_landsdel", y = "kristen", rhs = "kvinna * gotaland + region + period", term = "kvinna:gotaland",
       data = function(x) x, label = "E9 Kristen markör: skillnaden mellan landsdelarna (kvinna × Götaland)")
)
run <- function(t, dd, carver = TRUE) {
  dd <- dd[!is.na(dd[[t$y]]), ]
  k <- sum(dd[[t$y]])
  if (k < MIN_EVENTS || k == nrow(dd)) return(list(n = nrow(dd), k = k, too_few = TRUE))
  m <- tryCatch(fit(t$y, t$rhs, dd, carver), error = function(e) NULL)
  if (is.null(m)) return(list(n = nrow(dd), k = k, too_few = TRUE, error = TRUE))
  r <- coef_of(m, t$term)
  extra <- if (carver && t$term == "regionGötaland") list(shares = as.list(share_by_region(m, dd))) else list()
  c(list(n = nrow(dd), k = k, too_few = FALSE), r, extra)
}
res <- lapply(TESTS, function(t) {
  base <- t$data(d)
  big <- base$province %in% c("U", "Sö", "Ög", "Vg", "Sm")
  list(key = t$key, label = t$label, main = run(t, base),
       halves = lapply(c(A = "A", B = "B"), function(h) run(t, base[base$half == h, ])),
       robustness = list(ord10 = run(t, base[!is.na(base$n_words_core) & base$n_words_core >= 10, ]),
                         stora_landskap = run(t, base[big, ]), utan_ristare = run(t, base, carver = FALSE)),
       raw = if (t$term == "regionGötaland") lapply(c(Svealand = "Svealand", Götaland = "Götaland"), function(g) {
         x <- base[base$region == g & !is.na(base[[t$y]]), ]; list(k = sum(x[[t$y]]), n = nrow(x)) }) else NULL)
})
# Holm över test 1–9 (huvudtestet är referensen, inte ett av planens nio)
ix <- which(sapply(res, function(r) r$key) != "t0_huvud")
ps <- sapply(res[ix], function(r) if (isTRUE(r$main$too_few)) NA else r$main$p)
holm <- rep(NA, length(ps)); holm[!is.na(ps)] <- p.adjust(ps[!is.na(ps)], "holm")
for (j in seq_along(ix)) {
  i <- ix[j]; r <- res[[i]]; m <- r$main
  r$main$p_holm <- holm[j]
  same <- function(h) !isTRUE(h$too_few) && !is.null(h$p) && h$p < 0.05 && sign(h$logor) == sign(m$logor)
  both <- !is.na(holm[j]) && same(r$halves$A) && same(r$halves$B)
  r$utslag <- if (is.na(holm[j])) "för få" else if (holm[j] < 0.05 && both) "håller" else
    if (holm[j] < 0.05 || m$p < 0.05) "antydan" else "ingen skillnad påvisad"
  res[[i]] <- r
}
names(res) <- sapply(res, function(r) r$key)
# Andelen av huvudskillnaden (logodds) som försvinner med antalet resare konstant (planens regel B)
b0 <- res$t0_huvud$main$logor; b3 <- res$t3_antal$main$logor
attenuation <- if (!is.null(b0) && !is.null(b3)) 1 - b3 / b0 else NA
write_json(list(plan = "analysplaner/2026-10-29-kvinnorna-i-svealand.md", n_stones = nrow(d), tests = res,
                attenuation_B = attenuation), file.path(out, "kvinnor_landsdel.json"), auto_unbox = TRUE, digits = NA,
           pretty = TRUE, null = "null", na = "null")
sg <- function(x, k = 3) if (is.null(x) || length(x) == 0 || is.na(x)) "–" else signif(x, k)
for (r in res) cat(sprintf("%-52s n=%s k=%s OR=%s [%s, %s] p=%s holm=%s halvor=%s/%s %s\n", r$label, r$main$n, r$main$k,
  sg(r$main$or), sg(r$main$lo), sg(r$main$hi), sg(r$main$p), sg(r$main$p_holm), sg(r$halves$A$p, 2), sg(r$halves$B$p, 2),
  if (is.null(r$utslag)) "" else r$utslag))
cat("Andel av huvudskillnaden som försvinner med antalet resare konstant:", sg(attenuation), "\n")
