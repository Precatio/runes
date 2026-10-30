# Signerade stenar intill de tre öppna grupperna (Konungsund, Vetlanda, Husaby; data/carver_literature.json nearby_signed):
# liknar de gruppen mer än traktens stenar gör? Beskrivande prov efter artikeln, inte i någon låst plan (2026-10-30).
# Samma avstånd som r/anonymous.R (Gower på handens drag), men utan formula_signature: att stenen är signerad är det vi
# vill förklara, inte ett handdrag. För varje signerad sten: medelavståndet till gruppens stenar, jämfört med 10 000
# slumpgrupper av samma storlek bland stenar utan ristare inom 30 km från någon av gruppens stenar (andel slumpgrupper som ligger
# minst lika nära = p), percentilen bland traktens övriga stenar utanför gruppen (den rätta jämförelsen, eftersom
# slumpgrupperna dras ur stenar som klustringen valt bort och därför ligger längre från gruppen), och gruppens stenar rangordnade bland alla stenar inom 30 km efter likhet med den signerade.
#     Rscript utdata/okanda_ristare/signerade_grannar.R      Skriver signerade_grannar.json.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
root <- normalizePath(file.path(.here, "..", ".."))
source(file.path(root, "r", "common.R"))
suppressPackageStartupMessages({ library(cluster); library(jsonlite); library(dplyr) })
set.seed(2026)
cdir <- file.path(root, "data", "cache", "r", "corpus", "3f58e9339191761e")
an <- fromJSON(file.path(cdir, "anonymous.json"), simplifyVector = FALSE)
d <- read_corpus(file.path(cdir, "corpus.csv"))
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
full <- d %>% left_join(geo %>% select(signum, x, y), by = "signum") %>% left_join(txt, by = "signum") %>%
  filter(!is.na(x), n_words >= 5)
full$style_short <- ifelse(is.na(full$style), NA, sub("[ ?].*", "", full$style))
tc <- trait_cols(d)
fcols <- setdiff(grep("^formula_", names(txt), value = TRUE), "formula_signature")
bcols <- grep("^bg_", names(txt), value = TRUE)
HAND <- c("style_short", "cross", "short_twig", tc, fcols, bcols)
X <- full[, HAND]
for (col in c("style_short", "cross", "short_twig", tc, fcols)) X[[col]] <- factor(X[[col]])
G <- as.matrix(daisy(X, metric = "gower"))
idx <- setNames(seq_len(nrow(full)), full$signum)

probes <- list(list(stone = "Ög 234", group = 2), list(stone = "Ög 235", group = 2), list(stone = "Sm 96", group = 5),
               list(stone = "Vg 59", group = 13))
out <- list()
for (pr in probes) {
  g <- Filter(function(x) x$id == pr$group, an$groups)[[1]]
  members <- intersect(unlist(g$stones), full$signum)
  if (!pr$stone %in% full$signum) { out[[pr$stone]] <- list(missing = TRUE); next }
  s <- idx[[pr$stone]]
  km <- apply(sapply(idx[members], function(m) sqrt((full$x - full$x[m])^2 + (full$y - full$y[m])^2) / 1000), 1, min)
  pool <- setdiff(full$signum[km <= 30 & is.na(full$carver)], c(members, pr$stone))
  obs <- mean(G[s, idx[members]])
  sims <- replicate(10000, mean(G[s, idx[sample(pool, length(members))]]))
  local <- setdiff(full$signum[km <= 30], pr$stone)
  ord <- local[order(G[s, idx[local]])]
  ranks <- match(members, ord)
  nearest <- head(ord, 5)
  # every other stone near the group but outside it (with or without carver): its mean distance to the group
  others <- setdiff(local, members)
  od <- vapply(others, function(o) mean(G[idx[[o]], idx[members]]), 0)
  out[[pr$stone]] <- list(group = g$parish, n_group = length(members), n_pool = length(pool), n_local = length(local),
                         mean_to_group = round(obs, 4), mean_random = round(mean(sims), 4),
                         p = round((sum(sims <= obs) + 1) / (length(sims) + 1), 4),
                         n_others = length(others), others_as_close = sum(od <= obs),
                         share_others_as_close = round(mean(od <= obs), 3),
                         closest_others = head(names(sort(od)), 5),
                         nearest5 = nearest, nearest5_in_group = sum(nearest %in% members),
                         group_ranks = setNames(as.list(ranks), members))
}
write(toJSON(out, auto_unbox = TRUE, pretty = TRUE), file.path(.here, "signerade_grannar.json"))
print(toJSON(lapply(out, function(o) o[c("group", "n_group", "n_pool", "mean_to_group", "mean_random", "p", "n_others", "others_as_close", "share_others_as_close", "closest_others", "nearest5", "nearest5_in_group")]), auto_unbox = TRUE, pretty = TRUE))
