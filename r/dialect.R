# Stavning och dialekter: ortografiskt avstånd mellan härader (stringdist), prövat mot geografiskt avstånd
# (Mantel-test), grupper av härader med likartad stavning och kartor över utvalda ords stavning.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({
  library(stringdist)
  library(sf)
  library(cluster)
})
sf_use_s2(FALSE)

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
MIN_STONES <- 8
MIN_LEMMA <- 60
PERM <- 999

d <- read_corpus(P$corpus) %>% filter(!is.na(district), !is.na(lat), !is.na(pairs))
pairs <- d %>% select(signum, district, province, pairs) %>%
  mutate(pair = strsplit(pairs, "|", fixed = TRUE)) %>% select(-pairs) %>% unnest(pair) %>%
  separate(pair, c("lemma", "form"), sep = "=", extra = "merge", fill = "right") %>%
  filter(!is.na(form), form != "") %>% distinct(signum, lemma, .keep_all = TRUE)
lemmas <- pairs %>% count(lemma) %>% filter(n >= MIN_LEMMA) %>% pull(lemma)
pairs <- pairs %>% filter(lemma %in% lemmas)
districts <- d %>% count(district) %>% filter(n >= MIN_STONES) %>% pull(district)
pairs <- pairs %>% filter(district %in% districts)

# Form distribution per district and lemma
dist_forms <- pairs %>% count(district, lemma, form) %>% group_by(district, lemma) %>% mutate(p = n / sum(n)) %>% ungroup()

# Expected normalised Levenshtein distance between two districts' spellings of a lemma, averaged over lemmas
form_dist <- list()
for (l in lemmas) {
  f <- unique(pairs$form[pairs$lemma == l])
  m <- stringdistmatrix(f, f, method = "lv")
  len <- outer(nchar(f), nchar(f), pmax)
  form_dist[[l]] <- list(forms = f, D = m / pmax(len, 1))
}
nd <- length(districts)
OD <- matrix(NA_real_, nd, nd, dimnames = list(districts, districts))
for (i in seq_len(nd)) for (j in seq_len(nd)) {
  if (j < i) { OD[i, j] <- OD[j, i]; next }
  vals <- c()
  for (l in lemmas) {
    a1 <- dist_forms %>% filter(district == districts[i], lemma == l)
    b1 <- dist_forms %>% filter(district == districts[j], lemma == l)
    if (!nrow(a1) || !nrow(b1)) next
    fd <- form_dist[[l]]
    ia <- match(a1$form, fd$forms); ib <- match(b1$form, fd$forms)
    vals <- c(vals, sum(outer(a1$p, b1$p) * fd$D[ia, ib, drop = FALSE]))
  }
  OD[i, j] <- if (length(vals) >= 3) mean(vals) else NA
}
diag(OD) <- 0

# Geographic distance between district centroids (km)
cent <- d %>% filter(district %in% districts) %>% group_by(district) %>%
  summarise(lat = mean(lat), lon = mean(lon), n = n(), province = names(sort(table(province), decreasing = TRUE))[1])
cent <- cent[match(districts, cent$district), ]
cp <- st_transform(st_as_sf(cent, coords = c("lon", "lat"), crs = 4326), SWEREF)
xy <- st_coordinates(cp)
GD <- as.matrix(dist(xy)) / 1000
dimnames(GD) <- list(districts, districts)

ok <- rowSums(is.na(OD)) == 0
mantel <- function(A, B, perm) {
  lt <- lower.tri(A)
  obs <- cor(A[lt], B[lt], method = "spearman")
  null <- replicate(perm, { o <- sample(nrow(A)); cor(A[o, o][lt], B[lt], method = "spearman") })
  list(r = obs, p = (1 + sum(null >= obs)) / (1 + perm))
}
# Keep districts with complete distance rows (enough shared lemmas)
keep_d <- names(which(ok))
if (length(keep_d) < nrow(OD)) {
  sub <- OD[keep_d, keep_d]
  while (any(is.na(sub))) {
    worst <- names(which.max(rowSums(is.na(sub))))
    keep_d <- setdiff(keep_d, worst); sub <- OD[keep_d, keep_d]
  }
}
OD2 <- OD[keep_d, keep_d]; GD2 <- GD[keep_d, keep_d]
mt <- mantel(OD2, GD2, PERM)

# Distance classes: orthographic distance by geographic distance (correlogram-like)
lt <- lower.tri(OD2)
dc <- data.frame(geo = GD2[lt], ortho = OD2[lt]) %>%
  mutate(band = cut(geo, breaks = c(0, 25, 50, 100, 150, 200, 300, 500, 2000), right = FALSE)) %>%
  group_by(band) %>% summarise(n = n(), mean_ortho = mean(ortho), geo_mid = median(geo)) %>% filter(n >= 5)

# Groups of districts (PAM on orthographic distance)
ks <- 2:min(6, length(keep_d) - 1)
sils <- sapply(ks, function(k) pam(as.dist(OD2), k, diss = TRUE)$silinfo$avg.width)
k <- ks[which.max(sils)]
grp <- pam(as.dist(OD2), k, diss = TRUE)$clustering
cent2 <- cent[match(keep_d, cent$district), ] %>% mutate(group = grp, x = xy[match(keep_d, districts), 1],
                                                          y = xy[match(keep_d, districts), 2])
group_rows <- lapply(seq_len(k), function(g) {
  dd <- cent2[cent2$group == g, ]
  pv <- sort(table(dd$province), decreasing = TRUE)
  list(group = g, n = nrow(dd), districts = dd$district,
       provinces = paste0(names(pv), " (", as.integer(pv), ")", collapse = ", "))
})
# What characterises each group: per lemma, the form most over-represented relative to all districts
char_rows <- lapply(seq_len(k), function(g) {
  ds <- cent2$district[cent2$group == g]
  inn <- pairs %>% filter(district %in% ds) %>% count(lemma, form) %>% group_by(lemma) %>% mutate(p_in = n / sum(n))
  all <- pairs %>% filter(district %in% keep_d) %>% count(lemma, form) %>% group_by(lemma) %>% mutate(p_all = n / sum(n))
  j <- inn %>% inner_join(all %>% select(lemma, form, p_all), by = c("lemma", "form")) %>% ungroup() %>%
    filter(n >= 5) %>% mutate(lift = p_in / p_all) %>% arrange(desc(lift)) %>% head(6)
  list(group = g, forms = lapply(seq_len(nrow(j)), function(i) list(lemma = j$lemma[i], form = j$form[i],
                                                                     share_in_group = r3(j$p_in[i]), share_all = r3(j$p_all[i]))))
})

# Per lemma: is spelling associated with province? (Cramér's V, simulated p)
lemma_geo <- lapply(lemmas, function(l) {
  g <- pairs %>% filter(lemma == l)
  forms <- g %>% count(form) %>% filter(n >= 3) %>% pull(form)
  g$form2 <- ifelse(g$form %in% forms, g$form, "övriga")
  tab <- table(g$province, g$form2)
  list(lemma = l, n = nrow(g), cramers_v = r3(cramers_v(tab)), p = signif(chisq_p(tab, 1000), 3))
})
lq <- p.adjust(sapply(lemma_geo, `[[`, "p"), "BH")
for (i in seq_along(lemma_geo)) lemma_geo[[i]]$q <- signif(lq[i], 3)
lemma_geo <- lemma_geo[order(-sapply(lemma_geo, `[[`, "cramers_v"))]

# ---- figures -------------------------------------------------------------------------------------------------
W <- read_water(P$water_dir)
base_map <- function() {
  p <- ggplot()
  if (!is.null(W) && !is.null(W$coast)) p <- p + geom_sf(data = W$coast, colour = WATER, linewidth = 0.2)
  if (!is.null(W) && !is.null(W$lakes)) p <- p + geom_sf(data = W$lakes, fill = "#e6eef8", colour = WATER, linewidth = 0.1)
  p
}
lim <- list(x = range(cent2$x) + c(-40000, 40000), y = range(cent2$y) + c(-40000, 40000))
gp <- bind_rows(lapply(seq_len(k), function(g) cent2 %>% mutate(panel = sprintf("Grupp %d", g), member = group == g)))
p <- base_map() +
  geom_point(data = gp %>% filter(!member), aes(x, y), colour = FAINT, size = 1.2) +
  geom_point(data = gp %>% filter(member), aes(x, y, size = n), colour = SERIES[1], alpha = 0.85) +
  scale_size_area(max_size = 4, name = "Stenar i häradet") +
  facet_wrap(~panel) +
  coord_sf(xlim = lim$x, ylim = lim$y, crs = SWEREF, datum = NA) +
  labs(title = "Härader med likartad stavning",
       subtitle = sprintf("PAM på ortografiskt avstånd (k = %d). Grupperna bildades utan geografi.", k),
       caption = "Punkt = häradets runstenars medelposition. Källa: Samnordisk runtextdatabas.") +
  theme_map()
fig_groups <- save_fig(p, out, "dialekt_grupper.png", 9, 6)

p <- ggplot(dc, aes(geo_mid, mean_ortho)) +
  geom_line(colour = SERIES[1], linewidth = 0.7) + geom_point(aes(size = n), colour = SERIES[1]) +
  scale_size_area(max_size = 5, name = "Par av härader") +
  labs(title = "Stavningen skiljer sig mer ju längre ifrån varandra häraderna ligger",
       subtitle = sprintf("Mantel-test (Spearman): r = %.2f, p = %s (%d permutationer, %d härader)", mt$r,
                          format.pval(mt$p, digits = 2), PERM, length(keep_d)),
       x = "Avstånd mellan häradernas runstenar (km)", y = "Ortografiskt avstånd (normerad Levenshtein)") +
  theme_runor()
fig_mantel <- save_fig(p, out, "dialekt_avstand.png", 6.5, 4.5)

# Spelling maps for 'efter' (first vowel) and 'stæin' (diphthong)
spell <- d %>% select(signum, lat, lon, pairs) %>% mutate(pair = strsplit(pairs, "|", fixed = TRUE)) %>%
  unnest(pair) %>% separate(pair, c("lemma", "form"), sep = "=", extra = "merge", fill = "right")
mk <- function(l, f, title) {
  s <- spell %>% filter(lemma == l, !is.na(form)) %>% mutate(v = f(form))
  top <- names(sort(table(s$v), decreasing = TRUE))[1:min(3, length(unique(s$v)))]
  s$v <- factor(ifelse(s$v %in% top, s$v, "övriga"), levels = c(top, "övriga"))
  sp <- st_transform(st_as_sf(s, coords = c("lon", "lat"), crs = 4326), SWEREF)
  xy <- st_coordinates(sp); s$x <- xy[, 1]; s$y <- xy[, 2]
  base_map() +
    geom_point(data = s, aes(x, y, colour = v), size = 0.9, alpha = 0.85) +
    scale_colour_manual(values = c(setNames(SERIES[seq_along(top)], top), "övriga" = OTHER_COL), name = NULL) +
    coord_sf(xlim = range(s$x) + c(-20000, 20000), ylim = range(s$y) + c(-20000, 20000), crs = SWEREF, datum = NA) +
    labs(title = title) + theme_map() + guides(colour = guide_legend(override.aes = list(size = 3)))
}
OTHER_COL <- "#94a3b8"
fig_efter <- tryCatch(save_fig(mk("æftir", function(w) substr(w, 1, 1), "Första runan i 'efter' (æftiR)"), out,
                               "dialekt_efter.png", 6.5, 7), error = function(e) NULL)
fig_sten <- tryCatch(save_fig(mk("stæin", function(w) ifelse(grepl("ai|ia|æi", w), "ai (diftong)", "i/e (monoftong)"),
                                 "Diftongen i 'sten' (stæin)"), out, "dialekt_sten.png", 6.5, 7), error = function(e) NULL)

result <- list(
  n_districts = length(keep_d), min_stones = MIN_STONES, lemmas = lemmas, min_lemma = MIN_LEMMA,
  mantel = list(r = r3(mt$r), p = signif(mt$p, 3), permutations = PERM),
  distance_bands = dc %>% mutate(across(c(mean_ortho, geo_mid), r3)),
  groups = group_rows, group_forms = char_rows, k = k, silhouette = r3(max(sils)),
  lemma_geography = lemma_geo,
  district_groups = lapply(seq_len(nrow(cent2)), function(i) list(district = cent2$district[i], group = cent2$group[i],
                                                                  province = cent2$province[i], n = cent2$n[i])),
  figures = list(groups = fig_groups, distance = fig_mantel, efter = fig_efter, sten = fig_sten),
  method = paste(
    "För varje härad med minst", MIN_STONES, "runstenar och varje ord som förekommer minst", MIN_LEMMA, "gånger beräknades",
    "fördelningen av stavningsformer. Avståndet mellan två härader är det förväntade normerade Levenshtein-avståndet",
    "(stringdist) mellan en slumpvis form från vardera häradet, i medel över de ord båda har (minst tre).",
    "Sambandet med geografiskt avstånd prövades med ett Mantel-test (Spearman,", PERM, "permutationer).",
    "Grupperna av härader bildades med PAM enbart på det ortografiska avståndet."
  ),
  caveat = paste(
    "Stavning speglar både uttal (dialekt), ristarens skrivvanor och tid. Eftersom ristare ofta arbetade inom ett",
    "område kan en geografisk stavningsgräns lika gärna vara en gräns mellan ristarverkstäder som mellan dialekter."
  )
)
write_result(result, out, "dialect")
