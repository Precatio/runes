# Budskapen: vad runstenarna berättar om den döde (src/messages.py) och var och när de berättar det.
#
# För varje budskap (dödsuppgift, död utanför Norden, resa, gäld, arv, gård, egen minnessten, beröm):
#   landsdel  andelen per landsdel, rå och justerad: logistisk regression (mgcv) med tidsskikt (stilgruppens period,
#             odaterade stenar som eget skikt) och ristaren som slumpeffekt (stenar utan säker ristare grupperas per
#             socken, som i change.R). Götaland mot Svealand redovisas som oddskvot med 95 % konfidensintervall.
#             Kontroll: samma modell bara på daterade stenar, med mittåret som jämn kurva.
#   resorna   bland stenar om en resa utanför Norden: säger stenen att mannen dog utanför Norden (msg_dod_borta; en
#             död hemma eller i Norden räknas inte)? Prövas mot landsdel och resans riktning (väst/öst): exakt
#             Mantel–Haenszel med riktningen som skikt och med riktning × tidsskikt som skikt, logistisk regression
#             med tidsskikt, samma modell med ristaren som slumpeffekt, och om skillnaden mellan landsdelarna skiljer
#             sig mellan väst och öst (interaktion, likelihoodkvot, med kvoten mellan oddskvoterna och dess intervall).
#             En icke-signifikant interaktion visar inte att skillnaden är densamma: de götländska resestenarna är få.
#   hemma     bland stenar som inte nämner någon resa: säger stenen hur eller var den döde dog?
#   känslighet  läsbarhetsgränsen i src/messages.py är låg (fyra läsbara ord), så ett fragment får 0 för alla budskap.
#             Samma test görs därför också bara på stenar med minst STRICT_WORDS läsbara ord (kolumnen legible_words).
#   facit     överensstämmelsen med handkodningarna (data/messages_check.json, skrivs av scripts/check_messages.py),
#             med en flagga när kontrollen gjordes med en annan version av src/messages.py.
# Indata: params$corpus (korpusen) och params$messages (CSV: signum, region, direction, legible_words, msg_*).
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages(library(mgcv))

a <- cli_args(); P <- a$params; out <- a$out
set.seed(if (is.null(P$seed)) 2026 else P$seed)
MIN_EVENTS <- 15  # stenar med budskapet i Götaland och Svealand tillsammans för att modellera det
STRICT_WORDS <- if (is.null(P$strict_words)) 10 else P$strict_words  # som STRICT_WORDS i src/messages.py

d <- read_corpus(P$corpus)
m <- read.csv(P$messages, encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d <- merge(d, m, by = "signum")
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
d$carver_f <- factor(ifelse(!is.na(d$carver) & d$carver != "", d$carver,
                            paste0("_", d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish))))
REGIONS <- c("Götaland", "Svealand", "Gotland", "Norrland")
KEYS <- c("dod_uppgift", "dod_borta", "resa", "gald", "arv", "gard", "egen", "berom")
LAB <- list(
  dod_uppgift = c("Säger hur eller var den döde dog", "Says how or where the dead person died"),
  dod_borta = c("Dog utanför Norden", "Died outside Scandinavia"),
  resa = c("Resa eller vistelse utanför Norden", "Journey or stay outside Scandinavia"),
  gald = c("Gäld, guld eller silver", "Payment, gold or silver"),
  arv = c("Arv", "Inheritance"), gard = c("Gård och ägande", "Farm and ownership"),
  egen = c("Rest åt sig själv i livstiden", "Raised for oneself in one's lifetime"),
  berom = c("Beröm av den döde", "Praise of the dead"))
lab <- function(k) tr(LAB[[k]][1], LAB[[k]][2])

# Götaland mot Svealand ur en anpassad modell: oddskvot, intervall och p (Wald) för landsdelens koefficient
or_row <- function(fit, term = "regionGötaland") {
  s <- summary(fit)$p.table
  if (!term %in% rownames(s)) return(NULL)
  b <- s[term, 1]; se <- s[term, 2]
  list(or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se), p = s[term, 4])
}
or_row_glm <- function(fit, term = "regionGötaland") {
  s <- summary(fit)$coefficients
  b <- s[term, 1]; se <- s[term, 2]
  list(or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se), p = s[term, 4])
}
# Andelen per landsdel enligt modellen, med tidsskikten vägda som i data och utan ristarens slumpeffekt
adj_share <- function(fit, dd) {
  sapply(levels(dd$region), function(r) {
    nd <- dd; nd$region <- factor(r, levels(dd$region))
    mean(predict(fit, nd, type = "response", exclude = "s(carver_f)"))
  })
}
fit_gam <- function(f, dd) suppressWarnings(gam(f, family = binomial, data = dd, method = "REML"))
fisher_row <- function(tab) {
  ft <- fisher.test(tab)
  list(or = unname(ft$estimate), lo = ft$conf.int[1], hi = ft$conf.int[2], p = ft$p.value)
}
has_words <- "legible_words" %in% names(d)
strict <- function(x) if (has_words) x[!is.na(x$legible_words) & x$legible_words >= STRICT_WORDS, ] else x[0, ]

# Läsbarheten per landsdel: läsbara stenar (budskapen kända) och stenar med minst STRICT_WORDS läsbara ord
legibility <- if (has_words) list(
  min_words = min(d$legible_words[!is.na(d$msg_berom)]), strict_words = STRICT_WORDS,
  by_region = lapply(REGIONS, function(r) {
    x <- d[d$region == r, ]
    list(region = r, n = nrow(x), legible = sum(!is.na(x$msg_berom)),
         strict = sum(!is.na(x$msg_berom) & x$legible_words >= STRICT_WORDS))
  })) else NULL

elements <- list()
for (k in KEYS) {
  col <- paste0("msg_", k)
  dd <- d[!is.na(d[[col]]) & d$region %in% REGIONS, ]
  dd$y <- dd[[col]]
  raw <- lapply(REGIONS, function(r) {
    x <- dd$y[dd$region == r]
    list(region = r, n = length(x), k = sum(x), share = if (length(x)) mean(x) else NA)
  })
  e <- list(key = k, label = lab(k), n = nrow(dd), k = sum(dd$y), by_region = raw)
  gs <- dd[dd$region %in% c("Götaland", "Svealand"), ]
  gs$region <- factor(gs$region, c("Svealand", "Götaland"))
  # Fishers exakta test alltid; regressionen bara när budskapet finns i båda landsdelarna (annars skattas ingen
  # oddskvot: en landsdel utan budskapet ger oändlig kvot) och när minst MIN_EVENTS stenar har budskapet och minst
  # lika många saknar det (för sällsynta budskap bär modellen inte tidsskikt och ristare)
  e$fisher <- fisher_row(table(gs$region, gs$y))
  both <- all(tapply(gs$y, gs$region, sum) > 0)
  e$separation <- !both
  # Känsligheten: samma test (modellen om den används, annars Fisher) på stenar med minst STRICT_WORDS läsbara ord
  st <- strict(gs)
  if (nrow(st)) {
    e$strict <- list(words = STRICT_WORDS, n = nrow(st), k = sum(st$y), by_region = lapply(c("Götaland", "Svealand"),
      function(r) list(region = r, n = sum(st$region == r), k = sum(st$y[st$region == r]))),
      fisher = fisher_row(table(st$region, st$y)))
  }
  if (both && sum(gs$y) >= MIN_EVENTS && sum(1 - gs$y) >= MIN_EVENTS) {
    fit <- fit_gam(y ~ region + period + s(carver_f, bs = "re"), gs)
    e$model <- or_row(fit)
    if (!is.null(e$strict) && all(tapply(st$y, st$region, sum) > 0))
      e$strict$model <- or_row(fit_gam(y ~ region + period + s(carver_f, bs = "re"), st))
    sh <- adj_share(fit, gs)
    e$adjusted <- lapply(names(sh), function(r) list(region = r, share = unname(sh[r])))
    dated <- gs[!is.na(gs$year), ]
    if (sum(dated$y) >= MIN_EVENTS) {
      dated$t50 <- (dated$year - 1050) / 50
      e$model_dated <- or_row(fit_gam(y ~ region + s(t50, k = 4) + s(carver_f, bs = "re"), dated))
      e$n_dated <- nrow(dated)
    }
  }
  elements[[k]] <- e
}

# Resorna: säger stenen att mannen dog utanför Norden, i väst och i öst? (Inte msg_dod_uppgift: den räknar också en
# död hemma, som Sö 55 'then died grievously at home', och i Norden, som U 539 'He died in Jútland'.)
# Bara stenar med en enda riktning; stenar med båda riktningarna eller ingen (som Vg 197, Sö 173) räknas för sig
ta <- d[!is.na(d$msg_resa) & d$msg_resa == 1 & d$region %in% c("Götaland", "Svealand") & !is.na(d$msg_dod_borta), ]
all_journeys <- lapply(c("Götaland", "Svealand"), function(r) {
  x <- ta[ta$region == r, ]
  list(region = r, n = nrow(x), k = sum(x$msg_dod_borta), single = sum(x$direction %in% c("väst", "öst")))
})
tv <- ta[ta$direction %in% c("väst", "öst"), ]
tv$y <- tv$msg_dod_borta
tv$region <- factor(tv$region, c("Svealand", "Götaland")); tv$direction <- factor(tv$direction, c("väst", "öst"))
cells <- lapply(split(tv, list(tv$region, tv$direction)), function(x)
  list(region = as.character(x$region[1]), direction = as.character(x$direction[1]), n = nrow(x), k = sum(x$y)))
f_add <- fit_gam(y ~ region + direction + period + s(carver_f, bs = "re"), tv)
# Interaktionen: skiljer sig skillnaden mellan väst och öst? Likelihoodkvot mellan vanliga logistiska modeller
# (slumpeffekten gör kvottestet opålitligt i mgcv). Kvoten mellan oddskvoterna (öst/väst) med intervall visar hur
# svagt testet är: ett högt p betyder bara att ingen skillnad mellan riktningarna kan visas.
g_add <- glm(y ~ region + direction + period, binomial, tv)
g_int <- glm(y ~ region * direction + period, binomial, tv)
p_int <- anova(g_add, g_int, test = "Chisq")[2, "Pr(>Chi)"]
int_term <- "regionGötaland:directionöst"
interaction <- if (int_term %in% rownames(summary(g_int)$coefficients)) or_row_glm(g_int, int_term) else NULL
# Utan modell: exakt Mantel–Haenszel med riktningen som skikt, och med riktning × tidsskikt som skikt. Skikt där bara
# en landsdel eller ett utfall finns bär ingen information i det betingade testet och tas bort (testet kräver minst
# två stenar per skikt).
mh_test <- function(strata, x = tv) {
  tab <- xtabs(~ region + y + s, data.frame(region = x$region, y = factor(x$y, 0:1), s = droplevels(strata)))
  keep <- apply(tab, 3, function(x) all(rowSums(x) > 0) && all(colSums(x) > 0))
  tab <- tab[, , keep, drop = FALSE]
  t <- mantelhaen.test(tab, exact = TRUE)
  list(or = unname(t$estimate), lo = t$conf.int[1], hi = t$conf.int[2], p = t$p.value, strata = sum(keep),
       n = as.integer(sum(tab)))
}
mh <- mh_test(tv$direction)
mh_time <- mh_test(interaction(tv$direction, tv$period, sep = " "))
tv_strict <- strict(tv)
mh_strict <- if (nrow(tv_strict)) c(list(words = STRICT_WORDS),
  tryCatch(mh_test(tv_strict$direction, tv_strict), error = function(e) NULL)) else NULL
# Riktning för riktning: Fishers exakta test på den råa tabellen (oddskvot, intervall och p ur samma test) och den
# logistiska modellen med tidsskikt (oddskvot, intervall och p ur modellen), var för sig
by_dir <- lapply(c("väst", "öst"), function(dir) {
  x <- tv[tv$direction == dir, ]
  fr <- fisher_row(table(x$region, x$y))
  c(list(direction = dir, n = nrow(x), fisher_p = fr$p, fisher = fr), or_row(fit_gam(y ~ region + period, x)))
})
travel <- list(n = nrow(tv), outcome = "dod_borta", cells = unname(cells), all_journeys = all_journeys,
               common = or_row(f_add), common_glm = or_row_glm(g_add), mh = mh, mh_time = mh_time, mh_strict = mh_strict,
               p_interaction = p_int, interaction = interaction, by_direction = by_dir)

# Facit: reglerna mot handkodningarna (scripts/check_messages.py), med en flagga om reglerna har ändrats sedan dess
check_file <- if (is.null(P$check)) file.path(.here, "..", "data", "messages_check.json") else P$check
rules_file <- file.path(.here, "..", "src", "messages.py")
rule_check <- if (file.exists(check_file)) {
  ck <- fromJSON(check_file, simplifyVector = FALSE)
  ck$stale <- file.exists(rules_file) && !identical(unname(tools::md5sum(rules_file)), ck$rules_md5)
  ck
} else NULL

# Hemma: stenar utan resa, säger de hur den döde dog?
hm <- d[!is.na(d$msg_resa) & d$msg_resa == 0 & d$region %in% c("Götaland", "Svealand"), ]
hm$y <- hm$msg_dod_uppgift; hm$region <- factor(hm$region, c("Svealand", "Götaland"))
home <- list(n = nrow(hm), cells = lapply(levels(hm$region), function(r)
  list(region = r, n = sum(hm$region == r), k = sum(hm$y[hm$region == r]))),
  model = if (sum(hm$y) >= MIN_EVENTS) or_row(fit_gam(y ~ region + period + s(carver_f, bs = "re"), hm)) else NULL)

# Figur: andelen per budskap i Götaland och Svealand, justerad för tid och ristare
fig <- do.call(rbind, lapply(elements, function(e) if (!is.null(e$adjusted))
  do.call(rbind, lapply(e$adjusted, function(a) data.frame(label = e$label, region = a$region, share = a$share)))))
figs <- list()
if (!is.null(fig) && nrow(fig)) {
  fig$label <- factor(fig$label, rev(unique(fig$label)))
  p <- ggplot(fig, aes(share * 100, label, fill = region)) +
    geom_col(position = position_dodge(width = 0.75), width = 0.7) +
    scale_fill_manual(values = c("Götaland" = "#b7410e", "Svealand" = "#0891b2"), name = NULL) +
    labs(x = tr("Andel av stenarna (%), justerad för tid och ristare", "Share of stones (%), adjusted for time and carver"),
         y = NULL, title = tr("Vad stenarna berättar om den döde", "What the stones tell about the dead")) +
    theme_runor() + theme(legend.position = "top")
  figs$regions <- save_fig(p, out, "budskap_landsdel.png", 7.5, 4.8)
}

write_result(list(
  method = tr("Budskapen klassas med en regel per budskap i Rundatas engelska översättning (src/messages.py) och prövas med logistisk regression (mgcv) mot landsdel och tidsskikt, med ristaren som slumpeffekt.",
              "The messages are classified with one rule per message in Rundata's English translation (src/messages.py) and tested with logistic regression (mgcv) against region and time layer, with the carver as a random effect."),
  n_stones = nrow(d), n_legible = sum(!is.na(d$msg_berom)), min_events = MIN_EVENTS, legibility = legibility,
  elements = unname(elements), travel = travel, home = home, rule_check = rule_check,
  figures = figs), out, "messages")
