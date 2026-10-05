# Text och språk: stavningsvarianter per ord (lemma), ordformer och runföljder som utmärker en ristare,
# och inskrifternas formler (resarformel, monument, ordföljd, ristarsignatur, bön).
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages(library(tidytext))

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
MIN_CARVER <- 8
N_BIGRAMS <- 100

d <- read_corpus(P$corpus)
d$words[is.na(d$words)] <- ""
d$pairs[is.na(d$pairs)] <- ""
d$normalization[is.na(d$normalization)] <- ""
carvers <- d %>% filter(!is.na(carver)) %>% count(carver) %>% filter(n >= MIN_CARVER) %>% pull(carver)
dc <- d %>% filter(carver %in% carvers)

# ---- formulas (normalisation, Old Norse) --------------------------------------------------------
norm <- str_to_lower(str_replace_all(d$normalization, "[\"\\[\\]()]", ""))
first_match <- function(x, patterns, none = "ingen") {
  out <- rep(none, length(x))
  for (lab in rev(names(patterns))) out[str_detect(x, patterns[[lab]])] <- lab
  out
}
formulas <- data.frame(
  signum = d$signum,
  formula_raising = first_match(norm, list(
    "lét resa" = "\\b(let|letu|lét|létu|lata|lætu)\\s+(\\S+\\s+){0,3}(ræisa|reisa|gærva|giærva|gæra|giæra|hoggva|haggva|retta|rætta|ræisþa)",
    "reste" = "\\b(ræisti|ræistu|reisti|reistu|raisti|ræisþi|ræisþu)\\b",
    "rätte" = "\\b(retti|rettu|rætti|rættu)\\b",
    "satte" = "\\b(satti|sattu|setti|settu|lagði|lagðu)\\b",
    "gjorde" = "\\b(gærði|gærðu|gerði|gørði|giærði|giærðu)\\b",
    "högg" = "\\b(hiogg|hiuggu|hjó)\\b.*\\b(stæin|kumbl)"
  )),
  formula_monument = first_match(norm, list(
    "sten" = "\\bstæin(a|n)?\\b|\\bstæina\\b",
    "kumbl" = "\\bkumbl",
    "merki" = "\\bmerki",
    "bro" = "\\b(bro|bru|brú)\\b",
    "stav" = "\\bstaf"
  )),
  formula_order = first_match(norm, list(
    "substantiv–pronomen" = "\\b(stæin\\w*|kumbl\\w*|merki\\w*|bro\\w*)\\s+(þenna|þessi|þessa|þetta|þæssi|þæsi|þæssa|þennsi|þannsi|þennsa|þannsa|þinsi|þænsi)\\b",
    "pronomen–substantiv" = "\\b(þenna|þessi|þessa|þetta|þæssi|þæsi|þæssa|þennsi|þannsi|þennsa|þannsa|þinsi|þænsi)\\s+(stæin\\w*|kumbl\\w*|merki\\w*|bro\\w*)"
  ), none = "ej bestämbar"),
  formula_signature = first_match(norm, list(
    "risti" = "\\b(risti|ristu|ræist)\\b",
    "hjó" = "\\b(hiogg|hiuggu)\\b(?!.*\\bstæin)",
    "markaði" = "\\bmarkaði",
    "fáði" = "\\b(faði|fáði|fað)\\b",
    "ræð" = "\\b(ræð|raðu|raði)\\b"
  )),
  formula_prayer = first_match(norm, list(
    "Guð hjälpe själ" = "guð\\s+(ok\\s+guðs\\s+moðir\\s+)?hialpi\\s+(and|ǫnd|salu|sal|sial)",
    "Guð och Guds moder" = "guð\\s+ok\\s+guðs\\s+moðir",
    "Guð hjälpe" = "guð\\s+hialpi",
    "annan bön" = "\\bguð\\b"
  ))
)
formula_cols <- grep("^formula_", names(formulas), value = TRUE)
FORMULA_LABELS <- c(formula_raising = "Resarformel", formula_monument = "Monument", formula_order = "Ordföljd",
                    formula_signature = "Ristarsignatur", formula_prayer = "Bön")
fc <- formulas %>% filter(signum %in% dc$signum) %>% left_join(dc %>% select(signum, carver), by = "signum")
formula_tests <- lapply(formula_cols, function(col) {
  tab <- table(fc$carver, fc[[col]])
  list(formula = col, label = FORMULA_LABELS[[col]], cramers_v = r3(cramers_v(tab)), p = signif(chisq_p(tab), 3),
       overall = as.list(round(prop.table(table(formulas[[col]])), 3)))
})
fq <- p.adjust(sapply(formula_tests, `[[`, "p"), "BH")
for (i in seq_along(formula_tests)) formula_tests[[i]]$q <- signif(fq[i], 3)
formula_profiles <- lapply(carvers, function(cn) {
  g <- fc[fc$carver == cn, ]
  c(list(carver = cn, n = nrow(g)), lapply(setNames(formula_cols, formula_cols), function(col) {
    t <- sort(table(g[[col]]), decreasing = TRUE)
    list(top = names(t)[1], share = r3(as.numeric(t[1]) / nrow(g)), dist = as.list(round(t / nrow(g), 3)))
  }))
})

# ---- spelling variants per lemma ------------------------------------------------------------------
pairs <- d %>% select(signum, carver, pairs) %>% filter(pairs != "") %>%
  unnest_tokens(pair, pairs, token = "regex", pattern = "\\|", to_lower = FALSE) %>%
  separate(pair, c("lemma", "form"), sep = "=", extra = "merge", fill = "right") %>%
  filter(!is.na(form), form != "") %>% distinct(signum, lemma, form, .keep_all = TRUE)
pc <- pairs %>% filter(carver %in% carvers)
lemmas <- pc %>% count(lemma) %>% filter(n >= 40) %>% pull(lemma)
lemma_tests <- lapply(lemmas, function(l) {
  g <- pc %>% filter(lemma == l)
  forms <- g %>% count(form, sort = TRUE)
  if (nrow(forms) < 2) return(NULL)
  # Rare forms folded into "övriga" to keep the table testable
  keep_forms <- forms$form[forms$n >= 3]
  g$form2 <- ifelse(g$form %in% keep_forms, g$form, "övriga")
  tab <- table(g$carver, g$form2)
  list(lemma = l, n = nrow(g), n_forms = nrow(forms), cramers_v = r3(cramers_v(tab)), p = signif(chisq_p(tab), 3),
       forms = head(lapply(seq_len(nrow(forms)), function(i) list(form = forms$form[i], n = forms$n[i])), 6))
})
lemma_tests <- Filter(Negate(is.null), lemma_tests)
lq <- p.adjust(sapply(lemma_tests, `[[`, "p"), "BH")
for (i in seq_along(lemma_tests)) lemma_tests[[i]]$q <- signif(lq[i], 3)
lemma_tests <- lemma_tests[order(-sapply(lemma_tests, `[[`, "cramers_v"))]

# Spelling forms that mark out a carver (Fisher's exact test among stones that have the word)
distinctive <- list()
for (cn in carvers) {
  rows <- list()
  own <- pc %>% filter(carver == cn)
  for (key in unique(paste(own$lemma, own$form, sep = "="))) {
    lf <- strsplit(key, "=", fixed = TRUE)[[1]]
    l <- lf[1]; f <- lf[2]
    g <- pairs %>% filter(lemma == l)
    a1 <- sum(g$carver == cn & g$form == f, na.rm = TRUE)
    if (a1 < 3) next
    b1 <- sum(g$carver == cn & g$form != f, na.rm = TRUE)
    c1 <- sum((is.na(g$carver) | g$carver != cn) & g$form == f)
    d1 <- sum((is.na(g$carver) | g$carver != cn) & g$form != f)
    ft <- fisher.test(matrix(c(a1, b1, c1, d1), 2), alternative = "greater")
    rows[[key]] <- list(lemma = l, form = f, carver_k = a1, carver_n = a1 + b1, others_k = c1, others_n = c1 + d1,
                        share_carver = r3(a1 / (a1 + b1)), share_others = r3(c1 / max(1, c1 + d1)),
                        odds_ratio = r1(min(999, unname(ft$estimate))), p = ft$p.value)
  }
  if (length(rows)) distinctive[[cn]] <- rows
}
all_p <- unlist(lapply(distinctive, function(r) sapply(r, `[[`, "p")))
all_q <- p.adjust(all_p, "BH")
i <- 0
for (cn in names(distinctive)) for (key in names(distinctive[[cn]])) {
  i <- i + 1
  distinctive[[cn]][[key]]$q <- signif(all_q[i], 3)
  distinctive[[cn]][[key]]$p <- signif(distinctive[[cn]][[key]]$p, 3)
}
distinctive_out <- lapply(names(distinctive), function(cn) {
  r <- Filter(function(x) x$q < 0.05, distinctive[[cn]])
  r <- r[order(sapply(r, `[[`, "q"))]
  list(carver = cn, forms = head(unname(r), 8))
})

# ---- words and rune bigrams (tidytext) ----------------------------------------------------------------
words <- d %>% select(signum, carver, words) %>%
  unnest_tokens(word, words, token = "regex", pattern = " ", to_lower = FALSE) %>% filter(word != "")
tfidf <- words %>% filter(carver %in% carvers) %>% count(carver, word) %>% bind_tf_idf(word, carver, n) %>%
  group_by(carver) %>% filter(n >= 3) %>% slice_max(tf_idf, n = 8, with_ties = FALSE) %>% ungroup()
tfidf_out <- lapply(carvers, function(cn) {
  t <- tfidf %>% filter(carver == cn)
  list(carver = cn, words = lapply(seq_len(nrow(t)), function(i) list(word = t$word[i], n = t$n[i], tf_idf = r3(t$tf_idf[i]))))
})

bigrams <- words %>% mutate(padded = paste0("#", word, "#")) %>%
  mutate(bg = lapply(padded, function(w) substring(w, 1:(nchar(w) - 1), 2:nchar(w)))) %>%
  select(signum, bg) %>% unnest(bg)
top_bg <- bigrams %>% count(bg, sort = TRUE) %>% head(N_BIGRAMS) %>% pull(bg)
bg_mat <- bigrams %>% filter(bg %in% top_bg) %>% count(signum, bg) %>%
  group_by(signum) %>% mutate(share = n / sum(n)) %>% ungroup() %>%
  mutate(col = sprintf("bg_%03d", match(bg, top_bg))) %>% select(signum, col, share) %>%
  pivot_wider(names_from = col, values_from = share, values_fill = 0)
features <- formulas %>% left_join(bg_mat, by = "signum")
bgcols <- sprintf("bg_%03d", seq_along(top_bg))
for (col in bgcols) { if (!col %in% names(features)) features[[col]] <- 0; features[[col]][is.na(features[[col]])] <- 0 }
write.csv(features, file.path(out, "text_features.csv"), row.names = FALSE, fileEncoding = "UTF-8")

# ---- figures ------------------------------------------------------------------------------------------------
fp <- bind_rows(lapply(c("formula_raising", "formula_signature"), function(col) {
  fc %>% count(carver, value = .data[[col]]) %>% group_by(carver) %>% mutate(share = n / sum(n)) %>% ungroup() %>%
    mutate(formula = if (identical(LANG, "en")) FORMULA_LABELS_EN[[col]] else FORMULA_LABELS[[col]], value = trv(value))
}))
fp$carver <- factor(fp$carver, levels = rev(carvers))
p <- ggplot(fp, aes(value, carver, fill = share)) +
  geom_tile(colour = "white", linewidth = 0.6) +
  geom_text(aes(label = ifelse(share >= 0.05, round(100 * share), "")), size = 2.4,
            colour = ifelse(fp$share > 0.55, "white", INK)) +
  facet_wrap(~formula, scales = "free_x") +
  scale_fill_gradient(low = SEQ[1], high = SEQ[3], name = tr("Andel av ristarens stenar (%)", "Share of the carver's stones (%)"), labels = function(x) round(100 * x)) +
  labs(title = "Formler per ristare", x = NULL, y = NULL,
       subtitle = "Resarformel och ristarsignatur i ristarnas säkra inskrifter (Rundatas normalisering)") +
  theme_runor() + theme(panel.grid.major = element_blank(), axis.text.x = element_text(angle = 35, hjust = 1))
fig_formulas <- save_fig(p, out, "text_formler.png", 9, max(4.5, 0.3 * length(carvers) + 2))

lt <- head(lemma_tests, 15)
lt_df <- data.frame(lemma = sapply(lt, `[[`, "lemma"), v = sapply(lt, `[[`, "cramers_v"), q = sapply(lt, `[[`, "q"))
lt_df$lemma <- factor(lt_df$lemma, levels = rev(lt_df$lemma))
p <- ggplot(lt_df, aes(v, lemma)) +
  geom_col(fill = SERIES[1], width = 0.65) +
  geom_text(aes(label = sprintf("%.2f", v)), hjust = -0.2, size = 2.8, colour = INK) +
  scale_x_continuous(limits = c(0, max(lt_df$v) * 1.15), expand = c(0, 0)) +
  labs(title = "Ord vars stavning bäst skiljer ristarna åt", x = tr("Cramérs V (stavningsform × ristare)", "Cramér's V (spelling × carver)"), y = NULL,
       subtitle = sprintf("Ord som förekommer minst 40 gånger hos ristare med minst %d säkra stenar", MIN_CARVER)) +
  theme_runor() + theme(panel.grid.major.y = element_blank())
fig_lemmas <- save_fig(p, out, "text_stavning.png", 7, 5)

result <- list(
  carvers = carvers, min_inscriptions = MIN_CARVER,
  formulas = list(tests = formula_tests, profiles = formula_profiles),
  lemmas = lemma_tests, distinctive = distinctive_out, tfidf = tfidf_out,
  bigrams = top_bg,
  figures = list(formulas = fig_formulas, lemmas = fig_lemmas),
  method = paste(
    "Formlerna klassades med reguljära uttryck på Rundatas normalisering (stringr). Stavningsvarianterna är",
    "translittereringen parad ord för ord med normaliseringen; egennamn ingår inte. För varje ord med minst 40",
    "förekomster hos ristare med minst", MIN_CARVER, "säkra stenar prövades sambandet mellan stavning och ristare",
    "(χ² med simulerat p-värde, Cramérs V, Benjamini–Hochberg). Ordformer som utmärker en ristare prövades med",
    "Fishers exakta test mot alla andra stenar med samma ord. Ordformer och runbigram (två runor i följd inom ord)",
    "räknades med tidytext; de", N_BIGRAMS, "vanligaste bigrammen används som variabler i attribueringsmodellen."
  )
)
write_result(result, out, "text")
