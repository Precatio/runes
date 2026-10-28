# Människorna: vem reste stenen, efter vem och i vilken relation (src/people.py), enligt den låsta planen
# analysplaner/2026-10-28-manniskorna.md.
#
# Sex test, logistisk regression (mgcv) med landsdel, tidsskikt och ristaren som slumpeffekt (som messages.R):
#   1 kvinna bland resarna ~ landsdel           (Götaland mot Svealand)
#   2 kvinna bland resarna ~ tid                (t50, bara stilgruppsdaterade stenar)
#   3 drengr ~ den döde ung i släkten           (barn/syskon mot förälder/make, bara döda män)
#   4 þegn ~ ung                                (samma)
#   5 dog utanför Norden ~ ung                  (samma, där budskapet är känt)
#   6 bro eller väg ~ kvinna bland resarna
# Holm över de körda testen; varje test också i två halvor av korpusen (socken för socken, som change.R) och i fem
# robusthetsprov. Status: bekräftar (Holm < 0,05 och p < 0,05 åt samma håll i båda halvorna), mönster att pröva (Holm <
# 0,05 men inte båda halvorna), indikation (p < 0,05 men inte Holm), annars ingen skillnad påvisad.
# Indata: params$corpus (korpusen) och params$people (CSV ur src/people.py, en rad per vikingatida runsten).
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(mgcv); library(dplyr) })

a <- cli_args(); P <- a$params; out <- a$out
set.seed(if (is.null(P$seed)) 2026 else P$seed)
MIN_EVENTS <- 15

d <- read_corpus(P$corpus)
pp <- read.csv(P$people, encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d <- merge(d, pp, by = "signum")
d <- d[d$legible == 1 & d$region %in% c("Svealand", "Götaland", "Gotland", "Norrland"), ]
d$region <- factor(d$region, c("Svealand", "Götaland", "Gotland", "Norrland"))
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
d$carver_f <- factor(ifelse(!is.na(d$carver) & d$carver != "", d$carver,
                            paste0("_", d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish))))
d$kvinna <- as.integer(d$resare_k > 0)
young <- (d$rel_barn == 1 | d$rel_syskon == 1) & !(d$rel_foralder == 1 | d$rel_make == 1)
older <- (d$rel_foralder == 1 | d$rel_make == 1) & !(d$rel_barn == 1 | d$rel_syskon == 1)
d$ung <- ifelse(young, 1L, ifelse(older, 0L, NA_integer_))
d$ung_son <- ifelse(d$rel_barn == 1 & d$rel_syskon == 0 & d$rel_foralder == 0 & d$rel_make == 0, 1L,
                    ifelse(d$rel_foralder == 1 & d$rel_barn == 0 & d$rel_syskon == 0 & d$rel_make == 0, 0L, NA_integer_))
d$men_dead <- d$doda_k == 0 & d$doda_m >= 1
d$bro <- as.integer(d$cat_bro_vag == 1)

# Halvorna: socken för socken, växelvis inom varje landskap i sockenmedeldateringens ordning (som change.R)
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]

fit_gam <- function(f, dd) suppressWarnings(gam(f, family = binomial, data = droplevels(dd), method = "REML"))
coef_row <- function(fit, term) {
  s <- summary(fit)$p.table
  if (is.null(s) || !term %in% rownames(s)) return(NULL)
  b <- s[term, 1]; se <- s[term, 2]
  list(or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se), p = s[term, 4])
}
coef_glm <- function(fit, term) {
  s <- summary(fit)$coefficients
  if (!term %in% rownames(s)) return(NULL)
  b <- s[term, 1]; se <- s[term, 2]
  list(or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se), p = s[term, 4])
}
# Andelen enligt modellen när x sätts till 0 och 1 för alla stenar, utan ristarens slumpeffekt
shares <- function(fit, dd, x) {
  if (!x %in% names(dd)) return(NULL)
  sapply(c("0" = 0, "1" = 1), function(v) { nd <- dd; nd[[x]] <- v; mean(predict(fit, nd, type = "response",
                                                                               exclude = "s(carver_f)")) })
}

# Varje test: data, utfall, formel och den term som prövas. 'region' på formeln byts mot fixed om bara en landsdel finns.
TESTS <- list(
  list(key = "kvinna_landsdel", y = "kvinna", term = "regionGötaland", x = NULL,
       data = function(x) x[x$n_resare >= 1, ], rhs = "region + period",
       label = c("Kvinna bland resarna: Götaland mot Svealand", "A woman among the raisers: Götaland against Svealand")),
  list(key = "kvinna_tid", y = "kvinna", term = "t50", x = NULL,
       data = function(x) x[x$n_resare >= 1 & !is.na(x$t50), ], rhs = "region + t50",
       label = c("Kvinna bland resarna: förändring per 50 år", "A woman among the raisers: change per 50 years")),
  list(key = "drengr_ung", y = "drengr", term = "ung", x = "ung",
       data = function(x) x[x$men_dead & !is.na(x$ung), ], rhs = "ung + region + period",
       label = c("drengr: den döde son eller bror mot far eller make", "drengr: the dead a son or brother against a father or husband")),
  list(key = "thegn_ung", y = "thegn", term = "ung", x = "ung",
       data = function(x) x[x$men_dead & !is.na(x$ung), ], rhs = "ung + region + period",
       label = c("þegn: den döde son eller bror mot far eller make", "þegn: the dead a son or brother against a father or husband")),
  list(key = "dod_borta_ung", y = "dod_borta", term = "ung", x = "ung",
       data = function(x) x[x$men_dead & !is.na(x$ung) & !is.na(x$dod_borta), ], rhs = "ung + region + period",
       label = c("Dog utanför Norden: son eller bror mot far eller make", "Died outside Scandinavia: son or brother against father or husband")),
  list(key = "bro_kvinna", y = "bro", term = "kvinna", x = "kvinna",
       data = function(x) x[x$n_resare >= 1, ], rhs = "kvinna + region + period",
       label = c("Bro eller väg: kvinna bland resarna mot ingen kvinna", "Bridge or road: a woman among the raisers against none"))
)

run_one <- function(t, dd, carver = TRUE, rhs = t$rhs, term = t$term) {
  dd <- dd[!is.na(dd[[t$y]]), ]
  if (length(unique(dd$region)) < 2) rhs <- gsub("region \\+ |\\+ region", "", rhs)
  if (sum(dd[[t$y]]) < MIN_EVENTS || length(unique(dd[[t$y]])) < 2) return(list(n = nrow(dd), k = sum(dd[[t$y]]), too_few = TRUE))
  f <- as.formula(paste(t$y, "~", rhs, if (carver) "+ s(carver_f, bs = \"re\")" else ""))
  fit <- if (carver) fit_gam(f, dd) else suppressWarnings(glm(f, family = binomial, data = droplevels(dd)))
  r <- if (carver) coef_row(fit, term) else coef_glm(fit, term)
  reg <- if (carver && term == "regionGötaland") sapply(c(Svealand = "Svealand", Götaland = "Götaland"), function(g) {
    nd <- dd; nd$region <- factor(g, levels(droplevels(dd)$region))
    mean(predict(fit, nd, type = "response", exclude = "s(carver_f)")) }) else NULL
  c(list(n = nrow(dd), k = sum(dd[[t$y]]), too_few = FALSE), r,
    if (carver && !is.null(t$x)) list(shares = as.list(shares(fit, dd, t$x))) else list(),
    if (!is.null(reg)) list(shares_region = as.list(reg)) else list())
}

results <- lapply(TESTS, function(t) {
  base <- t$data(d)
  main <- run_one(t, base)
  halves <- lapply(c(A = "A", B = "B"), function(h) run_one(t, base[base$half == h, ]))
  rob <- list(
    ord10 = run_one(t, base[!is.na(base$n_words_core) & base$n_words_core >= 10, ]),
    kon_bestamt = if (t$key %in% c("kvinna_landsdel", "kvinna_tid", "bro_kvinna")) run_one(t, base[base$resare_okand == 0, ]) else NULL,
    utan_ristare = run_one(t, base, carver = FALSE),
    uppland = run_one(t, base[base$province == "U", ], term = if (t$term == "regionGötaland") "__none__" else t$term),
    son_far = if (!is.null(t$x) && t$x == "ung") {
      tt <- t; tt$rhs <- sub("^ung", "ung_son", t$rhs); tt$term <- "ung_son"
      sf <- d[d$men_dead & !is.na(d$ung_son), ]
      run_one(tt, sf[!is.na(sf[[t$y]]), ], rhs = tt$rhs, term = "ung_son")
    } else NULL)
  list(key = t$key, label = tr(t$label[1], t$label[2]), main = main, halves = halves, robustness = rob)
})

ps <- sapply(results, function(r) if (isTRUE(r$main$too_few) || is.null(r$main$p)) NA else r$main$p)
holm <- rep(NA, length(ps)); holm[!is.na(ps)] <- p.adjust(ps[!is.na(ps)], "holm")
for (i in seq_along(results)) {
  r <- results[[i]]; m <- r$main
  r$main$p_holm <- holm[i]
  same <- function(h) !isTRUE(h$too_few) && !is.null(h$p) && h$p < 0.05 && sign(log(h$or)) == sign(log(m$or))
  both <- !is.na(holm[i]) && same(r$halves$A) && same(r$halves$B)
  r$status <- if (is.na(holm[i])) "för få" else if (holm[i] < 0.05 && both) "bekräftar" else
    if (holm[i] < 0.05) "mönster att pröva" else if (m$p < 0.05) "indikation" else "ingen skillnad påvisad"
  r$replicated <- both
  results[[i]] <- r
}

write_result(list(
  method = tr("Kön och relation läses ur Rundatas engelska översättning (src/people.py, kontrollerad mot handkodning) och prövas med logistisk regression (mgcv) mot landsdel och tidsskikt, med ristaren som slumpeffekt, enligt en låst plan.",
              "Gender and relation are read from Rundata's English translation (src/people.py, checked against hand coding) and tested with logistic regression (mgcv) against region and time layer, with the carver as a random effect, following a locked plan."),
  plan = "analysplaner/2026-10-28-manniskorna.md", n_stones = nrow(d), min_events = MIN_EVENTS,
  tests = unname(results)), out, "people")
sg <- function(x, k = 3) if (is.null(x) || length(x) == 0 || is.na(x)) "–" else signif(x, k)
for (r in results) cat(sprintf("%-16s %-24s n=%s k=%s OR=%s [%s, %s] p=%s holm=%s halves=%s/%s\n", r$key, r$status,
  r$main$n, r$main$k, sg(r$main$or), sg(r$main$lo), sg(r$main$hi), sg(r$main$p),
  sg(r$main$p_holm), sg(r$halves$A$p, 2), sg(r$halves$B$p, 2)))
