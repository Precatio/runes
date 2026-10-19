# Hávamál ur Codex Regius-texten (Guðni Jónssons utgåva): är dikten ett stycke eller flera? Fyra oberoende
# mätningar på samma strofer, allt skrivet för att kunna granskas:
#   1  stilometri: Burrows' Delta på de vanligaste orden (funktionsorden), strofblock om ~15–25 strofer,
#      jämförda inom och mellan utgåvans sex delar; dendrogram + PCA (stylo för Delta, factoextra för PCA)
#   2  ämnen: LDA (topicmodels) med strofen som dokument, funktionsorden bortrensade; ämnesföljden över dikten
#   3  versmåttsproxy: utgåvans kommatering bevarar versgränserna – segment per strof och segmentlängd skiljer
#      ljóðaháttr från längre mått; dessutom upprepningsformeln i Ljóðatal
#   4  ordförrådets ålderssignal: andelen ordtyper med vikingatida runbelägg (ur havamal_prep.py)
# Небольшой материал: ~5 000 ord totalt – allt redovisas med det förbehållet.
#   Rscript utdata/Edda/havamal.R
suppressPackageStartupMessages({
  library(dplyr); library(tidyr); library(stringr); library(tidytext)
  library(ggplot2); library(ragg); library(topicmodels); library(factoextra)
})
set.seed(2026)
HERE <- "utdata/Edda"
d <- read.csv(file.path(HERE, "havamal_strofer.csv"), encoding = "UTF-8")
d$del <- factor(d$del, levels = c("I", "II", "III", "IV", "V", "VI"))
DEL_NAMN <- c(I = "I Gästvisdom 1–83", II = "II Kvinnoråd 84–102", III = "III Gunnlöd 103–110",
              IV = "IV Loddfáfnir 111–137", V = "V Runatal 138–145", VI = "VI Ljóðatal 146–164")

tok <- d %>% select(nr, del, text) %>%
  unnest_tokens(ord, text, token = "regex", pattern = "[^a-zþðæöøáéíóúýœå]+") %>%
  filter(nchar(ord) > 0)

# ---- 1. stilometri: Delta på strofblock -----------------------------------------------------------------
# block om högst ~22 strofer inom varje del, så att varje del får minst ett block och I/IV flera (intern baslinje)
blk <- d %>% group_by(del) %>% mutate(block = paste0(del, letters[ceiling(row_number() / 22)])) %>%
  ungroup() %>% select(nr, block)
tokb <- tok %>% inner_join(blk, by = "nr")
mfw <- tok %>% count(ord, sort = TRUE) %>% slice_head(n = 60) %>% pull(ord)
frek <- tokb %>% filter(ord %in% mfw) %>% count(block, ord) %>%
  group_by(block) %>% mutate(f = n / sum(n)) %>% ungroup() %>%
  select(-n) %>% pivot_wider(names_from = ord, values_from = f, values_fill = 0)
M <- as.matrix(frek[-1]); rownames(M) <- frek$block
Z <- scale(M)  # Burrows' Delta = medelavstånd i z-poäng (manhattan/antal ord)
delta <- as.matrix(dist(Z, method = "manhattan")) / ncol(Z)
hc <- hclust(as.dist(delta), method = "ward.D2")
ragg::agg_png(file.path(HERE, "fig_delta_dendrogram.png"), width = 1400, height = 900, res = 160)
plot(hc, main = "Hávamál: Burrows' Delta på strofblock (60 vanligaste orden)", xlab = "", sub = "", ylab = "Delta")
dev.off()
p <- fviz_pca_ind(prcomp(Z), repel = TRUE, title = "Strofblocken i de två första huvudkomponenterna (funktionsord)")
ggsave(file.path(HERE, "fig_delta_pca.png"), p, width = 9, height = 6.5, dpi = 160)
# inom- mot mellanavstånd: är delarna mer olika varandra än sina egna halvor?
same <- c(); other <- c()
for (i in rownames(delta)) for (j in rownames(delta)) if (i < j) {
  if (sub("[a-z]$", "", i) == sub("[a-z]$", "", j)) same <- c(same, delta[i, j]) else other <- c(other, delta[i, j])
}
# stylo:s egen Delta som kontroll av handräkningen (samma matematik ska ge samma ordning)
stylo_ok <- tryCatch({
  sd2 <- as.matrix(stylo::dist.delta(M)); cor(as.dist(delta), as.dist(sd2[rownames(delta), rownames(delta)])) > 0.99
}, error = function(e) NA)
stil <- list(inom_medel = round(mean(same), 3), mellan_medel = round(mean(other), 3),
             n_inom = length(same), n_mellan = length(other))

# lexikal variation per del (quanteda): typ/token-kvot på lika stora stickprov (minsta delens ordmassa)
qtok <- quanteda::tokens(setNames(vapply(split(d$text, d$del), paste, "", collapse = " "), levels(d$del)),
                         what = "fastestword")
minn <- min(quanteda::ntoken(qtok))
ttr <- round(vapply(seq_along(qtok), function(i)
  length(unique(head(as.character(qtok[[i]]), minn))) / minn, 0), 3)
names(ttr) <- names(qtok)

# ---- 2. ämnen: LDA med strofen som dokument -------------------------------------------------------------
stopp <- tok %>% count(ord, sort = TRUE) %>% slice_head(n = 45) %>% pull(ord)
dtm <- tok %>% filter(!ord %in% stopp) %>% count(nr, ord) %>% cast_dtm(nr, ord, n)
lda <- LDA(dtm, k = 5, control = list(seed = 2026))
amnen <- tidy(lda, matrix = "beta") %>% group_by(topic) %>% slice_max(beta, n = 8) %>%
  summarise(ord = paste(term, collapse = " "))
strof_amne <- tidy(lda, matrix = "gamma") %>% group_by(document) %>% slice_max(gamma, n = 1) %>%
  ungroup() %>% transmute(nr = as.integer(document), amne = topic, gamma = round(gamma, 2))
sa <- d %>% select(nr, del) %>% inner_join(strof_amne, by = "nr")
p <- ggplot(sa, aes(nr, 1, fill = factor(amne))) + geom_tile() +
  geom_vline(xintercept = c(83.5, 102.5, 110.5, 137.5, 145.5), linetype = 2) +
  scale_fill_brewer(palette = "Set2", name = "Ämne") +
  labs(title = "Dominerande LDA-ämne per strof (streck = utgåvans delgränser)", x = "Strof", y = NULL) +
  theme_minimal() + theme(axis.text.y = element_blank())
ggsave(file.path(HERE, "fig_amnen_per_strof.png"), p, width = 11, height = 2.8, dpi = 160)
renhet <- sa %>% count(del, amne) %>% group_by(del) %>% summarise(dominans = round(max(n) / sum(n), 2))

# ---- 3. versmåttsproxy och Ljóðatals formel -------------------------------------------------------------
p <- ggplot(d, aes(del, n_segment)) + geom_boxplot(fill = "#f2c4a7") +
  labs(title = "Versgränser per strof (utgåvans kommatering som proxy)", x = NULL, y = "segment per strof") +
  theme_minimal()
ggsave(file.path(HERE, "fig_versmatt.png"), p, width = 8, height = 5, dpi = 160)
matt <- d %>% group_by(del) %>% summarise(strofer = n(), ord_median = median(n_ord),
                                          segment_median = median(n_segment), seglangd = median(medel_segment))
kann <- sum(str_detect(d$text[d$del == "VI"], "kann ek"))

# ---- 4. ordförrådets ålderssignal ----------------------------------------------------------------------
runsign <- d %>% group_by(del) %>% summarise(andel = round(sum(runbelagda) / sum(ordtyper), 3), typer = sum(ordtyper))
p <- ggplot(runsign, aes(del, andel)) + geom_col(fill = "#b7410e") +
  geom_text(aes(label = scales::percent(andel, accuracy = 1)), vjust = -0.4) + ylim(0, 0.72) +
  labs(title = "Andel ordtyper med vikingatida runbelägg (runlm.key över normaliseringarna)",
       x = NULL, y = NULL) + theme_minimal()
ggsave(file.path(HERE, "fig_runbelagg.png"), p, width = 8, height = 5, dpi = 160)

ut <- list(delar = DEL_NAMN, stilometri = c(stil, stylo_kontroll = stylo_ok), ttr = as.list(ttr),
           delta_block = round(delta, 3),
           amnen = amnen, amnesdominans_per_del = renhet, versmatt = matt,
           ljodatal_kann_ek = kann, runbelagg = runsign,
           forbehall = paste("Codex Regius är enda källan (ca 1270) och Guðni Jónssons normalisering dess utgåva;",
                             "~5 000 ord är lite för stilometri; segmenten är en proxy för versrader;",
                             "skillnad mellan delar kan bero på genre lika väl som på hand eller tid."))
jsonlite::write_json(ut, file.path(HERE, "havamal_resultat.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
cat("klart: utdata/Edda/havamal_resultat.json + fyra figurer\n")
print(stil); print(ttr); print(renhet); print(matt); print(runsign); cat("'kann ek' i VI:", kann, "\n")
