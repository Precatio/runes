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
  groups <- c(tr("Runstenar", "Runestones"), tr("Slumpvisa punkter", "Random points"))
  long <- bind_rows(lapply(dist_rows, function(r) data.frame(
    kind = r$label, group = factor(groups, levels = groups), share = c(r$near_stones, r$near_random))))
  # Colours by group, not by the alphabetical order of the labels (which differs between the languages)
  p <- ggplot(long, aes(x = reorder(kind, -share), y = share, fill = group)) +
    geom_col(position = position_dodge(width = 0.75), width = 0.7) +
    scale_fill_manual(values = setNames(c(SERIES[1], "#b9b9b9"), groups), name = NULL) +
    scale_y_continuous(labels = function(x) paste0(round(x * 100), " %")) +
    labs(x = NULL, y = tr(sprintf("Andel inom %s m", NEAR_KM * 1000), sprintf("Share within %s m", NEAR_KM * 1000))) +
    theme_runor()
  save_fig(p, out, "lamningar_narhet.png", width = 7, height = 4)
}, error = function(e) { message("figur: ", conditionMessage(e)); NULL })

# ---- place names of pre-Christian cult (scripts/fetch_place_names.py) -----------------------------------------------
# Are Christian messages more common, or rarer, on stones near place names that suggest pre-Christian cult? Tier A:
# theophoric names (a god's name with a sacral or typical second element: Torsvi, Odensala, Ullevi, Frösö); tier B:
# sacral words without a god (Vi, Viby, Harg, Hov, Gudhem), less certain. And do these names lie nearer medieval
# churches than other place names of the same kind in the same areas (the church built on the cult site)?
CULT_KM <- 2
cult <- NULL
if (!is.null(P$cult_names) && file.exists(P$cult_names)) cult <- tryCatch({
  cn <- read.csv(P$cult_names, fileEncoding = "UTF-8", stringsAsFactors = FALSE)
  cn_sf <- st_transform(st_as_sf(cn, coords = c("lon", "lat"), crs = 4326), SWEREF)
  d$km_cult_a <- nearest_km(st_geometry(pts), cn_sf[cn_sf$tier == "A", ])
  d$km_cult_b <- nearest_km(st_geometry(pts), cn_sf[cn_sf$tier == "B", ])
  d$near_cult_a <- as.integer(d$km_cult_a < CULT_KM)
  d$near_cult_b <- as.integer(d$km_cult_b < CULT_KM)
  d$km_central <- nearest_km(st_geometry(pts), cn_sf[cn_sf$tier == "C", ])
  d$near_central <- as.integer(d$km_central < CULT_KM)
  d$cult_a_name <- cn_sf$name[cn_sf$tier == "A"][st_nearest_feature(st_geometry(pts), cn_sf[cn_sf$tier == "A", ])]
  d$prayer <- as.integer(d$cat_kristen == 1)
  d$pagan <- if ("pagan" %in% names(d)) as.integer(d$pagan == 1) else NA_integer_
  dated <- d[!is.na(d$t50), ]
  ra <- nearest_km(st_geometry(rnd), cn_sf[cn_sf$tier == "A", ])
  rb <- nearest_km(st_geometry(rnd), cn_sf[cn_sf$tier == "B", ])
  ctest <- function(dd, y, x, time, extra = "") {
    f <- as.formula(paste(y, "~", x, if (time) "+ t50" else "", extra, prov))
    r <- with_halves(dd, f, x)
    if (is.null(r)) return(NULL)
    near <- dd[[x]] == 1
    out <- c(r, list(share_near = share(dd[[y]][near]), share_far = share(dd[[y]][!near]), n_near = sum(near, na.rm = TRUE)))
    # Leave out the stones near one theophoric name at a time, so that one cluster of stones cannot carry the result
    if (x == "near_cult_a") {
      names_near <- unique(dd$cult_a_name[near & !is.na(near)])
      ors <- sapply(names_near, function(nm) {
        r2 <- fit_term(dd[!(near & dd$cult_a_name == nm), ], f, x)
        if (is.null(r2)) NA else r2$or
      })
      out$n_places <- length(names_near)
      out$loo <- list(min_or = r3(min(ors, na.rm = TRUE)), max_or = r3(max(ors, na.rm = TRUE)))
    }
    out
  }
  tests_c <- list(
    christian_a = c(list(label = tr("Kristna markörer nära teofora ortnamn", "Christian markers near theophoric place names")),
                    ctest(d, "christian", "near_cult_a", FALSE)),
    christian_a_time = c(list(label = tr("Kristna markörer nära teofora ortnamn, med tiden konstant",
                                         "Christian markers near theophoric place names, time held constant")),
                         ctest(dated, "christian", "near_cult_a", TRUE)),
    prayer_a = c(list(label = tr("Kristen bön nära teofora ortnamn", "Christian prayer near theophoric place names")),
                 ctest(d, "prayer", "near_cult_a", FALSE)),
    cross_a = c(list(label = tr("Kors nära teofora ortnamn", "Cross near theophoric place names")),
                ctest(d, "cross", "near_cult_a", FALSE)),
    christian_b = c(list(label = tr("Kristna markörer nära sakrala ortnamn (Vi, Harg, Hov)",
                                    "Christian markers near sacral place names (Vi, Harg, Hov)")),
                    ctest(d, "christian", "near_cult_b", FALSE)),
    prayer_central = c(list(label = tr("Kristen bön nära centralortsnamn utan kult (Husby, -tuna)",
                                       "Christian prayer near central-place names without cult (Husby, -tuna)")),
                       ctest(d, "prayer", "near_central", FALSE)),
    prayer_a_central = c(list(label = tr("Kristen bön nära teofora ortnamn, med närhet till centralortsnamn konstant",
                                         "Christian prayer near theophoric names, nearness to central-place names held constant")),
                         ctest(d, "prayer", "near_cult_a", FALSE, "+ near_central")),
    prayer_a_time = c(list(label = tr("Kristen bön nära teofora ortnamn, med tiden konstant",
                                      "Christian prayer near theophoric names, time held constant")),
                      ctest(dated, "prayer", "near_cult_a", TRUE))
  )
  # The same test at 1 and 3 km, so that the result does not hang on the radius
  radius <- lapply(c(1, 3), function(km) {
    d$near_tmp <- as.integer(d$km_cult_a < km)
    r <- fit_term(d, as.formula(paste("prayer ~ near_tmp", prov)), "near_tmp")
    if (is.null(r)) NULL else c(list(km = km, n_near = sum(d$near_tmp, na.rm = TRUE)), r)
  })
  tests_c <- Filter(function(x) !is.null(x$or), tests_c)
  cq <- p.adjust(sapply(tests_c, `[[`, "p"), "BH")
  for (i in seq_along(tests_c)) tests_c[[i]]$q_bh <- signif(cq[i], 3)

  # The few stones with explicit pagan markers (Thor, vígi, curses, alu, Thor motifs) and their nearest cult name
  pagan_rows <- if (all(is.na(d$pagan))) list() else lapply(which(d$pagan == 1), function(i) {
    list(signum = d$signum[i], km_a = r3(d$km_cult_a[i]), km_b = r3(d$km_cult_b[i]))
  })

  # Churches: cult names against other place names of the same kind within 10 km of a runestone
  churches <- NULL
  if (!is.null(P$churches) && file.exists(P$churches) && !is.null(P$places) && file.exists(P$places)) {
    ch <- read.csv(P$churches, fileEncoding = "UTF-8", stringsAsFactors = FALSE)
    ch_sf <- st_transform(st_as_sf(ch, coords = c("lon", "lat"), crs = 4326), SWEREF)
    pl <- read.csv(P$places, fileEncoding = "UTF-8", stringsAsFactors = FALSE)
    pl_sf <- st_transform(st_as_sf(pl, coords = c("lon", "lat"), crs = 4326), SWEREF)
    all_stones <- st_transform(st_as_sf(read_corpus(P$corpus) %>% filter(!is.na(lat), !is.na(lon)),
                                        coords = c("lon", "lat"), crs = 4326), SWEREF)
    region <- st_union(st_buffer(st_geometry(all_stones), 10000))
    in_region <- function(x) lengths(st_intersects(x, region)) > 0
    pl_sf <- pl_sf[in_region(pl_sf), ]
    cn_r <- cn_sf[in_region(cn_sf), ]
    is_cult <- paste(pl_sf$name, round(st_coordinates(pl_sf)[, 1]), round(st_coordinates(pl_sf)[, 2])) %in%
      paste(cn_r$name, round(st_coordinates(cn_r)[, 1]), round(st_coordinates(cn_r)[, 2]))
    other <- pl_sf[!is_cult, ]
    km_other <- nearest_km(st_geometry(other), ch_sf)
    row_for <- function(tier) {
      x <- cn_r[cn_r$tier == tier, ]
      if (nrow(x) < 5) return(NULL)
      k <- nearest_km(st_geometry(x), ch_sf)
      ft <- fisher.test(matrix(c(sum(k < 1), sum(k >= 1), sum(km_other < 1), sum(km_other >= 1)), 2))
      list(tier = tier, n = nrow(x), near_church = r3(mean(k < 1)), median_km = r3(median(k)),
           or = r3(unname(ft$estimate)), p = signif(ft$p.value, 3))
    }
    churches <- list(n_churches = nrow(ch), n_other = nrow(other), near_church_other = r3(mean(km_other < 1)),
                     median_km_other = r3(median(km_other)), near_km = 1,
                     rows = Filter(Negate(is.null), list(row_for("A"), row_for("B"))))
    d$km_church <- nearest_km(st_geometry(pts), ch_sf)
  }
  list(available = TRUE, near_km = CULT_KM, n_a = sum(cn_sf$tier == "A"), n_b = sum(cn_sf$tier == "B"),
       stones_near_a = sum(d$near_cult_a, na.rm = TRUE), stones_near_b = sum(d$near_cult_b, na.rm = TRUE),
       near_a_stones = share(d$near_cult_a), near_a_random = r3(mean(ra < CULT_KM)),
       near_b_stones = share(d$near_cult_b), near_b_random = r3(mean(rb < CULT_KM)),
       near_c_stones = share(d$near_central), n_c = sum(cn_sf$tier == "C"),
       tests = tests_c, radius = Filter(Negate(is.null), radius), pagan = pagan_rows, churches = churches,
       gods = as.list(table(cn_sf$god[cn_sf$tier == "A"])))
}, error = function(e) list(available = FALSE, error = conditionMessage(e)))

write.csv(d[, c("signum", grep("^km_", names(d), value = TRUE))], file.path(out, "remains_stones.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

write_result(list(
  available = TRUE, note = NOTE, near_km = NEAR_KM, local_km = LOCAL_KM, n_stones = nrow(d),
  n_remains = nrow(rem), distances = unname(dist_rows), tests = tests, gravfalt_provinces = prov_rows, cult = cult,
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
