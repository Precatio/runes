# Formelnätverk (igraph, tidygraph, ggraph): ord i normaliseringen som förekommer i samma inskrifter,
# grupper av formelord (Louvain) och släktrelationerna i inskrifterna efter landskap, tid och kategori.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({
  library(igraph)
  library(tidygraph)
  library(ggraph)
})

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
MIN_WORD <- 25
MIN_EDGE <- 8

d <- read_corpus(P$corpus) %>% filter(!is.na(normalization))

# Words of the normalisation without names (names are marked with " in Rundata)
tok <- d %>% select(signum, normalization) %>%
  mutate(word = strsplit(normalization, "\\s+")) %>% select(-normalization) %>% unnest(word) %>%
  filter(!str_detect(word, '^"'), !str_detect(word, "^§")) %>%
  mutate(word = str_to_lower(str_replace_all(word, "[.,;:!?()\\[\\]<>{}|/]", ""))) %>%
  filter(nchar(word) > 1) %>% distinct(signum, word)
freq <- tok %>% count(word) %>% filter(n >= MIN_WORD)
tok <- tok %>% filter(word %in% freq$word)
N <- n_distinct(d$signum)

# Co-occurrence with positive pointwise mutual information (corrects for frequent words)
pairs <- tok %>% inner_join(tok, by = "signum", relationship = "many-to-many") %>% filter(word.x < word.y) %>%
  count(word.x, word.y, name = "n")
pairs <- pairs %>% left_join(freq %>% rename(word.x = word, nx = n), by = "word.x") %>%
  left_join(freq %>% rename(word.y = word, ny = n), by = "word.y") %>%
  mutate(pmi = log2((n / N) / ((nx / N) * (ny / N)))) %>% filter(n >= MIN_EDGE, pmi > 0)

g <- graph_from_data_frame(pairs %>% transmute(from = word.x, to = word.y, weight = pmi, n = n), directed = FALSE,
                           vertices = freq %>% filter(word %in% c(pairs$word.x, pairs$word.y)) %>% rename(name = word))
comm <- cluster_louvain(g, weights = E(g)$weight)
V(g)$community <- membership(comm)
V(g)$degree <- degree(g)
V(g)$strength <- strength(g, weights = E(g)$weight)
mod <- modularity(comm)
communities <- lapply(sort(unique(V(g)$community)), function(cm) {
  v <- V(g)[V(g)$community == cm]
  o <- order(-v$n)
  list(community = cm, size = length(v), words = head(lapply(o, function(i) list(word = v$name[i], n = v$n[i])), 12))
})

# Which community dominates each inscription, and how communities relate to province, style period and category
tok$community <- V(g)$community[match(tok$word, V(g)$name)]
dom <- tok %>% filter(!is.na(community)) %>% count(signum, community) %>% group_by(signum) %>%
  slice_max(n, n = 1, with_ties = FALSE) %>% ungroup() %>% select(signum, community)
dd <- d %>% inner_join(dom, by = "signum") %>%
  mutate(period = case_when(is.na(style_from) ~ NA_character_, style_to <= 1050 ~ "före ca 1050", TRUE ~ "efter ca 1050"))
assoc <- function(col) {
  x <- dd[!is.na(dd[[col]]), ]
  tab <- table(x$community, x[[col]])
  tab <- tab[, colSums(tab) >= 10, drop = FALSE]
  list(variable = col, cramers_v = r3(cramers_v(tab)), p = signif(chisq_p(tab, 1000), 3))
}
community_assoc <- list(assoc("province"), assoc("period"))

# ---- kinship ----------------------------------------------------------------------------------------------------
KIN <- list(
  "fader" = "\\bfaður\\b|\\bfoður\\b", "moder" = "\\bmoður\\b|\\bmøður\\b", "son" = "\\bsun\\b|\\bsyni\\b|\\bsyniR\\b|\\bsona\\b",
  "dotter" = "\\bdottur\\b|\\bdøtr", "broder" = "\\bbroður\\b|\\bbrøðr", "syster" = "\\bsystur\\b",
  "hustru" = "\\bkonu\\b|\\bkona\\b", "make" = "\\bbonda\\b|\\bbondi\\b|\\bver\\b", "fosterson/fosterfar" = "\\bfostra|\\bfostr",
  "farbror/morbror" = "\\bfaðurbroður|\\bmoðurbroður|\\bfaðurbrøðr", "svåger/måg" = "\\bmag\\b|\\bmagi\\b|\\bmaga\\b",
  "partner/kamrat" = "\\bfelaga\\b|\\bfelagi\\b|\\bhæimþega|\\bdrængR?\\b"
)
low <- str_to_lower(d$normalization)
K <- sapply(KIN, function(rx) str_detect(low, rx))
kin <- as.data.frame(K); kin$signum <- d$signum; kin$province <- d$province
kin$period <- case_when(is.na(d$style_from) ~ NA_character_, d$style_to <= 1050 ~ "före ca 1050", TRUE ~ "efter ca 1050")
kin$kristen <- d$cat_kristen == 1
kin_rows <- lapply(names(KIN), function(k) {
  x <- kin[[k]]
  per <- kin %>% filter(!is.na(period)) %>% group_by(period) %>% summarise(share = mean(.data[[k]]))
  ft <- tryCatch(fisher.test(table(kin$period[!is.na(kin$period)], x[!is.na(kin$period)]))$p.value, error = function(e) NA)
  kr <- tryCatch(fisher.test(table(kin$kristen, x))$p.value, error = function(e) NA)
  list(relation = k, n = sum(x), share = r3(mean(x)),
       early = r3(per$share[per$period == "före ca 1050"]), late = r3(per$share[per$period == "efter ca 1050"]),
       p_period = signif(ft, 3), share_christian = r3(mean(x[kin$kristen])), share_other = r3(mean(x[!kin$kristen])),
       p_christian = signif(kr, 3))
})
pk <- p.adjust(c(sapply(kin_rows, `[[`, "p_period"), sapply(kin_rows, `[[`, "p_christian")), "BH")
for (i in seq_along(kin_rows)) {
  kin_rows[[i]]$q_period <- signif(pk[i], 3)
  kin_rows[[i]]$q_christian <- signif(pk[length(kin_rows) + i], 3)
}
kin_prov <- kin %>% group_by(province) %>% filter(n() >= 40) %>%
  summarise(n = n(), across(all_of(names(KIN)), mean)) %>% pivot_longer(-c(province, n), names_to = "relation", values_to = "share")

# ---- figures ---------------------------------------------------------------------------------------------------
tg <- as_tbl_graph(g) %>% activate(nodes) %>% mutate(community = factor(community))
top_comm <- names(sort(table(V(g)$community), decreasing = TRUE))[1:min(3, length(unique(V(g)$community)))]
g_lab <- tr("Grupp", "Group"); o_lab <- tr("Övriga grupper", "Other groups")
tg <- tg %>% mutate(colour_group = ifelse(as.character(community) %in% top_comm, paste(g_lab, community), o_lab))
lvl <- c(paste(g_lab, top_comm), o_lab)
cols <- setNames(c(SERIES[seq_along(top_comm)], "#94a3b8"), lvl)
p <- ggraph(tg, layout = "fr", weights = weight) +
  geom_edge_link(aes(alpha = weight), colour = MUTED, show.legend = FALSE) +
  scale_edge_alpha(range = c(0.05, 0.4)) +
  geom_node_point(aes(size = n, colour = factor(colour_group, levels = lvl))) +
  geom_node_text(aes(label = ifelse(n >= quantile(n, 0.6), name, "")), repel = TRUE, size = 2.6, colour = INK, family = FONT) +
  scale_colour_manual(values = cols, name = NULL) +
  scale_size_area(max_size = 6, name = tr("Inskrifter", "Inscriptions")) +
  labs(title = "Formelnätverk", subtitle = sprintf(
    "Ord i minst %d inskrifter; kant = förekommer tillsammans (PMI > 0, minst %d gånger). Modularitet %.2f.",
    MIN_WORD, MIN_EDGE, mod), caption = "Grupperna (Louvain) är ord som oftare står i samma inskrifter än slumpen ger.") +
  theme_void(base_size = 10, base_family = FONT) + theme(plot.title = element_text(face = "bold", colour = INK),
                                     plot.subtitle = element_text(colour = MUTED, size = 9),
                                     plot.caption = element_text(colour = MUTED, size = 8, hjust = 0),
                                     legend.position = "bottom", plot.background = element_rect(fill = "white", colour = NA))
fig_net <- save_fig(p, out, "natverk_formler.png", 9, 8)

kp <- kin_prov %>% filter(relation %in% names(KIN)[sapply(kin_rows, `[[`, "n") >= 30])
KIN_EN <- c("fader" = "father", "moder" = "mother", "son" = "son", "dotter" = "daughter", "broder" = "brother",
            "syster" = "sister", "hustru" = "wife", "make" = "husband", "fosterson/fosterfar" = "foster son/father",
            "farbror/morbror" = "paternal/maternal uncle", "svåger/måg" = "brother-in-law/son-in-law",
            "partner/kamrat" = "partner (félagi)")
rel_lab <- function(x) if (identical(LANG, "en")) unname(KIN_EN[x]) else x
kp$relation <- factor(rel_lab(kp$relation), levels = rev(rel_lab(names(KIN))))
p <- ggplot(kp, aes(province, relation, fill = share)) +
  geom_tile(colour = "white", linewidth = 0.6) +
  geom_text(aes(label = round(100 * share)), size = 2.6, colour = ifelse(kp$share > 0.35, "white", INK)) +
  scale_fill_gradient(low = SEQ[1], high = SEQ[3], name = tr("Andel inskrifter (%)", "Share of inscriptions (%)"), labels = function(x) round(100 * x)) +
  labs(title = "Släktrelationer i inskrifterna per landskap", x = NULL, y = NULL,
       subtitle = "Andel av landskapets runstenar som nämner relationen (landskap med minst 40 stenar)") +
  theme_runor() + theme(panel.grid.major = element_blank())
fig_kin <- save_fig(p, out, "natverk_slakt.png", 7.5, 5)

result <- list(
  n_inscriptions = N, n_words = vcount(g), n_edges = ecount(g), modularity = r3(mod),
  min_word = MIN_WORD, min_edge = MIN_EDGE, communities = communities, community_association = community_assoc,
  kinship = kin_rows,
  figures = list(network = fig_net, kinship = fig_kin),
  method = paste(
    "Orden i Rundatas normalisering (utan egennamn) som förekommer i minst", MIN_WORD, "inskrifter bildar noder; två ord",
    "förbinds om de står i samma inskrift minst", MIN_EDGE, "gånger och oftare än slumpen ger (positiv punktvis ömsesidig",
    "information, PMI). Grupper av ord hittades med Louvain-metoden (igraph). Släktrelationerna söktes med reguljära",
    "uttryck i normaliseringen; skillnader mellan tidig och sen stilgrupp och mellan kristna och övriga inskrifter",
    "prövades med Fishers exakta test (Benjamini–Hochberg). Rundata saknar uppgifter om släkter, så släktorden i",
    "inskrifterna är det närmaste vi kommer."
  )
)
write_result(result, out, "network")
