# Lämningar kring runstenarna: avståndet till närmaste gravfält, hög, färdväg, bro, fornborg och hamnanläggning i
# Kulturmiljöregistret (Riksantikvarieämbetet, via K-samsök; scripts/fetch_raa_remains.py), mot slumpvisa punkter på
# land i stenarnas närhet. Därtill om närheten till gravfält och vägar skiftar med tiden, med kristna markörer och för
# brostenar – prövat i båda halvorna av korpusen, som i change.R.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages(library(sf))
sf_use_s2(FALSE)

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)

NOTE <- paste(
  "Lämningarna är Kulturmiljöregistrets (RAÄ) registrerade lämningar med ett läge per lämning (mittpunkten för en yta).",
  "Registret är olika väl inventerat i olika trakter, och de flesta lämningar är odaterade: färdvägar, broar och",
  "hamnanläggningar är ofta medeltida eller yngre, gravfält och högar oftast från järnåldern. Stenar som enligt Rundata",
  "står vid eller i en kyrka, i ett museum eller en samling räknas inte, eftersom de är flyttade."
)

if (is.null(P$remains) || !file.exists(P$remains)) {
  write_result(list(available = FALSE, note = tr("Lämningarna är inte hämtade (scripts/fetch_raa_remains.py).",
                                                 "The remains have not been fetched (scripts/fetch_raa_remains.py).")),
               out, "remains")
  quit(save = "no")
}

d <- read_corpus(P$corpus) %>% filter(!is.na(lat), !is.na(lon))
if ("moved" %in% names(d)) d <- d %>% filter(is.na(moved) | moved == 0)
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
pts <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326, remove = FALSE), SWEREF)

rem <- read.csv(P$remains, fileEncoding = "UTF-8", stringsAsFactors = FALSE) %>% filter(!is.na(lat), !is.na(lon))
rem_sf <- st_transform(st_as_sf(rem, coords = c("lon", "lat"), crs = 4326), SWEREF)
GROUPS <- list(gravfalt = "gravfält", hog = "hög", vag = c("färdväg", "färdvägssystem"), bro = "bro",
               fornborg = "fornborg", hamn = "hamnanläggning")
LABELS <- list(gravfalt = c("gravfält", "grave fields"), hog = c("högar", "mounds"),
               vag = c("färdvägar", "roads and tracks"), bro = c("broar", "bridges"),
               fornborg = c("fornborgar", "hillforts"), hamn = c("hamnanläggningar", "harbours"))
NEAR_KM <- 0.5

nearest_km <- function(from, to) {
  if (!nrow(to)) return(rep(NA_real_, length(from)))
  i <- st_nearest_feature(from, to)
  as.numeric(st_distance(from, to[i, ], by_element = TRUE)) / 1000
}

# The same local null as the water test in geography.R: random points on land within 5 km of the province's stones
LOCAL_KM <- 5
W <- read_water(P$water_dir)
rnd <- list()
for (pv in names(which(table(d$province) >= 10))) {
  g <- st_geometry(pts)[d$province == pv]
  area <- st_union(st_buffer(g, LOCAL_KM * 1000))
  if (!is.null(W$land)) area <- suppressWarnings(suppressMessages(st_intersection(area, W$land)))
  if (!length(area) || all(st_is_empty(area))) next
  s <- st_sample(area, size = length(g) * 2, type = "random")
  if (!is.null(W$lakes)) s <- s[!lengths(st_intersects(s, W$lakes))]
  s <- s[seq_len(min(length(s), length(g)))]
  if (length(s)) rnd[[pv]] <- st_sf(province = pv, geometry = s)
}
rnd <- do.call(rbind, rnd)

dist_rows <- list()
for (k in names(GROUPS)) {
  sub <- rem_sf[rem_sf$type %in% GROUPS[[k]], ]
  d[[paste0("km_", k)]] <- nearest_km(st_geometry(pts), sub)
  rk <- nearest_km(st_geometry(rnd), sub)
  s <- d[[paste0("km_", k)]][d$province %in% unique(rnd$province)]
  w <- wilcox.test(s, rk, alternative = "less")
  dist_rows[[k]] <- list(key = k, label = tr(LABELS[[k]][1], LABELS[[k]][2]), n_remains = nrow(sub),
                         n_stones = sum(!is.na(s)), n_random = length(rk),
                         median_stones_km = r3(median(s, na.rm = TRUE)), median_random_km = r3(median(rk)),
                         near_stones = r3(mean(s < NEAR_KM, na.rm = TRUE)), near_random = r3(mean(rk < NEAR_KM)),
                         p = w$p.value)
}
pq <- p.adjust(sapply(dist_rows, `[[`, "p"), "BH")
for (i in seq_along(dist_rows)) { dist_rows[[i]]$q_bh <- signif(pq[i], 3); dist_rows[[i]]$p <- signif(dist_rows[[i]]$p, 3) }

# ---- halves, as in change.R: whole parishes alternating within each province by mean dating ----------------------
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]

# A logistic model of being within NEAR_KM of the remains, with province held constant; the term's odds ratio
fit_term <- function(dd, formula, term) {
  m <- tryCatch(suppressWarnings(glm(formula, data = dd, family = binomial)), error = function(e) NULL)
  if (is.null(m) || !(term %in% rownames(coef(summary(m))))) return(NULL)
  cf <- coef(summary(m))[term, ]
  list(n = nrow(dd), or = r3(exp(cf[["Estimate"]])), lo = r3(exp(cf[["Estimate"]] - 1.96 * cf[["Std. Error"]])),
       hi = r3(exp(cf[["Estimate"]] + 1.96 * cf[["Std. Error"]])), p = signif(cf[["Pr(>|z|)"]], 3))
}
with_halves <- function(dd, formula, term) {
  all <- fit_term(dd, formula, term)
  if (is.null(all)) return(NULL)
  h <- lapply(c(A = "A", B = "B"), function(x) fit_term(dd[!is.na(dd$half) & dd$half == x, ], formula, term))
  same <- function(r) !is.null(r) && r$p < 0.05 && sign(log(r$or)) == sign(log(all$or))
  c(all, list(halves = list(A = h$A, B = h$B, replicated = same(h$A) && same(h$B))))
}

multi <- length(unique(d$province)) > 1
prov <- if (multi) " + factor(province)" else ""
d$near_gravfalt <- as.integer(d$km_gravfalt < NEAR_KM)
d$near_vag <- as.integer(d$km_vag < NEAR_KM)
d$near_bro <- as.integer(d$km_bro < NEAR_KM)
d$christian <- as.integer(d$cross == 1 | d$cat_kristen == 1)
dated <- d[!is.na(d$t50), ]

share <- function(x) r3(mean(x, na.rm = TRUE))
period_rows <- function(col) {
  e <- dated[dated$year < 1050, col]; l <- dated[dated$year >= 1050, col]
  list(early = share(e), late = share(l), n_early = sum(!is.na(e)), n_late = sum(!is.na(l)))
}

tests <- list(
  time_gravfalt = c(list(label = tr("Nära gravfält över tid (per 50 år)", "Near grave fields over time (per 50 years)")),
                    with_halves(dated, as.formula(paste("near_gravfalt ~ t50", prov)), "t50"),
                    list(periods = period_rows("near_gravfalt"))),
  time_vag = c(list(label = tr("Nära färdvägar över tid (per 50 år)", "Near roads over time (per 50 years)")),
               with_halves(dated, as.formula(paste("near_vag ~ t50", prov)), "t50"),
               list(periods = period_rows("near_vag"))),
  christian_gravfalt = c(list(label = tr("Kristna markörer och närhet till gravfält (med tiden konstant)",
                                         "Christian markers and nearness to grave fields (time held constant)")),
                         with_halves(dated, as.formula(paste("near_gravfalt ~ christian + t50", prov)), "christian")),
  bridge_vag = c(list(label = tr("Brostenar och närhet till färdvägar", "Bridge stones and nearness to roads")),
                 with_halves(d, as.formula(paste("near_vag ~ cat_bro_vag", prov)), "cat_bro_vag")),
  bridge_bro = c(list(label = tr("Brostenar och närhet till registrerade broar", "Bridge stones and nearness to registered bridges")),
                 with_halves(d, as.formula(paste("near_bro ~ cat_bro_vag", prov)), "cat_bro_vag"))
)
tests <- Filter(function(x) !is.null(x$or), tests)
tq <- p.adjust(sapply(tests, `[[`, "p"), "BH")
for (i in seq_along(tests)) tests[[i]]$q_bh <- signif(tq[i], 3)

# Per province for the grave fields: the share of stones and of random points within NEAR_KM
prov_rows <- lapply(split(seq_len(nrow(d)), d$province), function(ix) {
  pv <- d$province[ix[1]]
  if (length(ix) < 20 || is.null(rnd) || !(pv %in% rnd$province)) return(NULL)
  rk <- nearest_km(st_geometry(rnd[rnd$province == pv, ]), rem_sf[rem_sf$type %in% GROUPS$gravfalt, ])
  list(province = pv, n = length(ix), near_stones = share(d$near_gravfalt[ix]), near_random = r3(mean(rk < NEAR_KM)),
       p = signif(prop.test(c(sum(d$near_gravfalt[ix], na.rm = TRUE), sum(rk < NEAR_KM)),
                            c(sum(!is.na(d$near_gravfalt[ix])), length(rk)), alternative = "greater")$p.value, 3))
})
prov_rows <- unname(Filter(Negate(is.null), prov_rows))

# Figure: the share of stones and random points within NEAR_KM of each kind of remains
fig <- tryCatch({
  long <- bind_rows(lapply(dist_rows, function(r) data.frame(
    kind = r$label, group = c(tr("Runstenar", "Runestones"), tr("Slumpvisa punkter", "Random points")),
    share = c(r$near_stones, r$near_random))))
  p <- ggplot(long, aes(x = reorder(kind, -share), y = share, fill = group)) +
    geom_col(position = position_dodge(width = 0.75), width = 0.7) +
    scale_fill_manual(values = c(SERIES[1], "#b9b9b9"), name = NULL) +
    scale_y_continuous(labels = function(x) paste0(round(x * 100), " %")) +
    labs(x = NULL, y = tr(sprintf("Andel inom %s m", NEAR_KM * 1000), sprintf("Share within %s m", NEAR_KM * 1000))) +
    theme_runor()
  save_fig(p, out, "lamningar_narhet.png", width = 7, height = 4)
}, error = function(e) { message("figur: ", conditionMessage(e)); NULL })

write.csv(d[, c("signum", grep("^km_", names(d), value = TRUE))], file.path(out, "remains_stones.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

write_result(list(
  available = TRUE, note = NOTE, near_km = NEAR_KM, local_km = LOCAL_KM, n_stones = nrow(d),
  n_remains = nrow(rem), distances = unname(dist_rows), tests = tests, gravfalt_provinces = prov_rows,
  figures = list(near = fig),
  method = paste(
    "För varje runsten (utom flyttade) och för lika många slumpvisa punkter på land inom", LOCAL_KM, "km från stenarna i",
    "samma landskap beräknades avståndet till närmaste lämning av varje slag i Kulturmiljöregistret (SWEREF 99 TM).",
    "Stenar och punkter jämfördes med Wilcoxons rangsummetest (ensidigt, Benjamini–Hochberg över slagen). Närhet inom",
    NEAR_KM * 1000, "m modellerades med logistisk regression med landskapet konstant: mot stilgruppens mittår (per 50 år),",
    "kristna markörer (kors eller kristen formel, med tiden konstant) och brostenar. Varje samband prövades också i",
    "korpusens två halvor, uppdelade per socken som i change.R."
  )
), out, "remains")
