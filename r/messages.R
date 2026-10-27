# Budskapen: vad runstenarna berättar om den döde (src/messages.py) och var och när de berättar det.
#
# För varje budskap (dödsuppgift, död utanför Norden, resa, gäld, arv, gård, egen minnessten, beröm):
#   landsdel  andelen per landsdel, rå och justerad: logistisk regression (mgcv) med tidsskikt (stilgruppens period,
#             odaterade stenar som eget skikt) och ristaren som slumpeffekt (stenar utan säker ristare grupperas per
#             socken, som i change.R). Götaland mot Svealand redovisas som oddskvot med 95 % konfidensintervall.
#             Kontroll: samma modell bara på daterade stenar, med mittåret som jämn kurva.
#   resorna   bland stenar om en resa utanför Norden: säger stenen att mannen dog där? Prövas mot landsdel och resans
#             riktning (väst/öst) med samma kontroller, och om skillnaden mellan landsdelarna är densamma åt båda håll
#             (interaktion, likelihoodkvot). Samma skillnad åt båda håll talar för en sed i hur man berättade, inte för
#             att en viss färd var farligare.
#   hemma     bland stenar som inte nämner någon resa: säger stenen hur eller var den döde dog?
# Indata: params$corpus (korpusen) och params$messages (CSV: signum, region, direction, msg_*).
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages(library(mgcv))

a <- cli_args(); P <- a$params; out <- a$out
set.seed(if (is.null(P$seed)) 2026 else P$seed)
MIN_EVENTS <- 15  # stenar med budskapet i Götaland och Svealand tillsammans för att modellera det

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
  # oddskvot: en landsdel utan budskapet ger oändlig kvot)
  ft <- fisher.test(table(gs$region, gs$y))
  e$fisher <- list(or = unname(ft$estimate), lo = ft$conf.int[1], hi = ft$conf.int[2], p = ft$p.value)
  both <- all(tapply(gs$y, gs$region, sum) > 0)
  e$separation <- !both
  if (both && sum(gs$y) >= MIN_EVENTS && sum(1 - gs$y) >= MIN_EVENTS) {
    fit <- fit_gam(y ~ region + period + s(carver_f, bs = "re"), gs)
    e$model <- or_row(fit)
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

# Resorna: dog mannen där, i väst och i öst?
tv <- d[!is.na(d$msg_resa) & d$msg_resa == 1 & d$direction %in% c("väst", "öst") & d$region %in% c("Götaland", "Svealand"), ]
tv$y <- tv$msg_dod_uppgift
tv$region <- factor(tv$region, c("Svealand", "Götaland")); tv$direction <- factor(tv$direction, c("väst", "öst"))
cells <- lapply(split(tv, list(tv$region, tv$direction)), function(x)
  list(region = as.character(x$region[1]), direction = as.character(x$direction[1]), n = nrow(x), k = sum(x$y)))
f_add <- fit_gam(y ~ region + direction + period + s(carver_f, bs = "re"), tv)
# Interaktionen: samma skillnad åt båda håll? Likelihoodkvot mellan vanliga logistiska modeller (slumpeffekten gör
# kvottestet opålitligt i mgcv)
g_add <- glm(y ~ region + direction + period, binomial, tv)
g_int <- glm(y ~ region * direction + period, binomial, tv)
p_int <- anova(g_add, g_int, test = "Chisq")[2, "Pr(>Chi)"]
# Över båda riktningarna, utan modell: exakt Mantel–Haenszel med riktningen som skikt
mh <- mantelhaen.test(xtabs(~ region + y + direction, tv), exact = TRUE)
by_dir <- lapply(c("väst", "öst"), function(dir) {
  x <- tv[tv$direction == dir, ]
  c(list(direction = dir, fisher_p = fisher.test(table(x$region, x$y))$p.value), or_row(fit_gam(y ~ region + period, x)))
})
travel <- list(n = nrow(tv), cells = unname(cells), common = or_row(f_add), common_glm = or_row_glm(g_add),
               mh = list(or = unname(mh$estimate), lo = mh$conf.int[1], hi = mh$conf.int[2], p = mh$p.value),
               p_interaction = p_int, by_direction = by_dir)

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
  n_stones = nrow(d), n_legible = sum(!is.na(d$msg_berom)), elements = unname(elements), travel = travel, home = home,
  figures = figs), out, "messages")
