# Steg 3: alla prov i den låsta planen ur avstånden från steg 1 och 2.  Rscript --vanilla utdata/strand/03_statistik.R
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "config.R"))
S <- load_stones()
all <- S$all; all6 <- S$all6
A <- lapply(PROVS, function(pv) readRDS(file.path(WORK, paste0(pv_key(pv), "_avstand.rds")))); names(A) <- PROVS
SL <- c("then", "now", "sea", paste0("s", c(R1, R1X)))

# Distances onto the stones (all six provinces, moved included) and the random point sets
dist_st <- bind_rows(lapply(A, function(a) a$stones))
all6 <- cbind(all6, dist_st[match(all6$signum, dist_st$signum), SL])
rset <- function(k) bind_rows(lapply(A, function(a) a$rnd[[k]]))
rnd <- rset("main"); r2 <- rset("r2"); r10 <- rset("r10"); rall <- rset("d1")
d <- all6[all6$moved == 0, ]
other_counts <- as.list(table(all$province[all$moved == 0 & !(all$province %in% PROVS)]))

# Halves, exactly as in r/remains.R
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
rnd$half <- NA_character_
for (pv in PROVS) {
  ri <- which(rnd$province == pv); si <- which(d$province == pv)
  nn <- st_nearest_feature(st_as_sf(rnd[ri, ], coords = c("x", "y"), crs = SWEREF),
                           st_as_sf(d[si, ], coords = c("x", "y"), crs = SWEREF))
  rnd$half[ri] <- d$half[si][nn]
}
# Sites: stones within SITE_M of each other (single linkage, within the province)
d$site <- NA_character_
for (pv in PROVS) {
  ix <- which(d$province == pv)
  cl <- if (length(ix) > 1) cutree(hclust(dist(cbind(d$x[ix], d$y[ix])), "single"), h = SITE_M) else 1
  d$site[ix] <- paste(pv, cl)
}

# Grave fields
rem <- read.csv(REMAINS, fileEncoding = "UTF-8", stringsAsFactors = FALSE) %>% filter(!is.na(lat), !is.na(lon))
gf <- st_transform(st_as_sf(rem[rem$type == "gravfält", ], coords = c("lon", "lat"), crs = 4326), SWEREF)
nearest_m <- function(df) {
  p <- st_as_sf(df, coords = c("x", "y"), crs = SWEREF)
  as.numeric(st_distance(p, gf[st_nearest_feature(p, gf), ], by_element = TRUE))
}
d$grave <- nearest_m(d); rnd$grave <- nearest_m(rnd); r2$grave <- nearest_m(r2); r10$grave <- nearest_m(r10)
all6$grave <- nearest_m(all6); rall$grave <- nearest_m(rall)
say("avstånd samlade: ", nrow(d), " stenar, ", nrow(rnd), " punkter, ", nrow(gf), " gravfält")

# ---- statistics -----------------------------------------------------------------------------------------------------
auc <- function(s, r) {
  n1 <- length(s); n2 <- length(r)
  rk <- rank(c(s, r))
  1 - (sum(rk[seq_len(n1)]) - n1 * (n1 + 1) / 2) / (n1 * n2)
}
summ <- function(s, r, near = c(500, 1000)) {
  s <- s[!is.na(s)]; r <- r[!is.na(r)]
  if (length(s) < 3 || length(r) < 3) return(NULL)
  w <- suppressWarnings(wilcox.test(s, r, alternative = "less", exact = FALSE))
  out <- list(n_stones = length(s), n_random = length(r), median_stones_m = round(median(s)),
              median_random_m = round(median(r)), ratio = r3(median(s) / median(r)), auc = r3(auc(s, r)),
              p = signif(w$p.value, 3))
  for (k in near) {
    out[[paste0("within_", k, "_stones")]] <- r3(mean(s < k)); out[[paste0("within_", k, "_random")]] <- r3(mean(r < k))
  }
  out
}
by_prov <- function(ds, rs, col, bh = TRUE) {
  rows <- lapply(PROVS, function(pv) c(list(province = pv, name = PROV_NAME[[pv]]),
                                       summ(ds[[col]][ds$province == pv], rs[[col]][rs$province == pv])))
  if (bh) { q <- p.adjust(sapply(rows, `[[`, "p"), "BH"); for (i in seq_along(rows)) rows[[i]]$q_bh <- signif(q[i], 3) }
  rows
}
halves <- function(ds, rs, col) lapply(c(A = "A", B = "B"), function(h) c(list(n_parishes = length(unique(pkey[d$half == h]))),
  summ(ds[[col]][ds$half == h], rs[[col]][rs$half == h])))
sites <- function(ds, rs, col) {
  sm <- ds %>% group_by(site) %>% summarise(v = median(.data[[col]]), .groups = "drop")
  c(list(n_sites = nrow(sm)), summ(sm$v, rs[[col]]))
}

# H1 and today's water
H1 <- list(overall = summ(d$then, rnd$then), provinces = by_prov(d, rnd, "then"),
           halves = halves(d, rnd, "then"), sites = sites(d, rnd, "then"))
NOWres <- list(overall = summ(d$now, rnd$now), provinces = by_prov(d, rnd, "now"), halves = halves(d, rnd, "now"))

# H2: bootstrap of AUC(then) − AUC(now); stones resampled by site within province, random points within province
set.seed(SEED)
site_ix <- split(seq_len(nrow(d)), d$site)
site_prov <- sapply(names(site_ix), function(s) d$province[site_ix[[s]][1]])
rnd_ix <- split(seq_len(nrow(rnd)), rnd$province)
boot <- replicate(B_BOOT, {
  si <- unlist(lapply(PROVS, function(pv) { ss <- names(site_ix)[site_prov == pv]
    unlist(site_ix[sample(ss, length(ss), replace = TRUE)], use.names = FALSE) }))
  ri <- unlist(lapply(PROVS, function(pv) sample(rnd_ix[[pv]], length(rnd_ix[[pv]]), replace = TRUE)))
  auc(d$then[si], rnd$then[ri]) - auc(d$now[si], rnd$now[ri])
})
H2 <- list(auc_then = H1$overall$auc, auc_now = NOWres$overall$auc,
           delta_auc = r3(auc(d$then, rnd$then) - auc(d$now, rnd$now)),
           ci95 = r3(unname(quantile(boot, c(0.025, 0.975)))), ratio_then = H1$overall$ratio,
           ratio_now = NOWres$overall$ratio, B = B_BOOT,
           provinces = lapply(PROVS, function(pv) list(province = pv,
             auc_then = r3(auc(d$then[d$province == pv], rnd$then[rnd$province == pv])),
             auc_now = r3(auc(d$now[d$province == pv], rnd$now[rnd$province == pv])))))

# H3: grave fields
prop_p <- function(s, r, k = 500) signif(suppressWarnings(prop.test(c(sum(s < k), sum(r < k)), c(length(s), length(r)),
                                                                    alternative = "greater"))$p.value, 3)
H3 <- list(overall = c(summ(d$grave, rnd$grave), list(p_share500 = prop_p(d$grave, rnd$grave))),
           provinces = by_prov(d, rnd, "grave"), halves = halves(d, rnd, "grave"), sites = sites(d, rnd, "grave"))
for (i in seq_along(H3$provinces)) {
  pv <- H3$provinces[[i]]$province
  H3$provinces[[i]]$p_share500 <- prop_p(d$grave[d$province == pv], rnd$grave[rnd$province == pv])
}
say("H1–H3")

# Secondary tests
fit_term <- function(dd, formula, term) {
  m <- tryCatch(suppressWarnings(glm(formula, data = dd, family = binomial)), error = function(e) NULL)
  if (is.null(m) || !(term %in% rownames(coef(summary(m))))) return(NULL)
  cf <- coef(summary(m))[term, ]
  list(n = nrow(dd), or = r3(exp(cf[["Estimate"]])), lo = r3(exp(cf[["Estimate"]] - 1.96 * cf[["Std. Error"]])),
       hi = r3(exp(cf[["Estimate"]] + 1.96 * cf[["Std. Error"]])), p = signif(cf[["Pr(>|z|)"]], 3))
}
with_halves <- function(dd, formula, term) {
  a <- fit_term(dd, formula, term)
  if (is.null(a)) return(NULL)
  h <- lapply(c(A = "A", B = "B"), function(x) fit_term(dd[!is.na(dd$half) & dd$half == x, ], formula, term))
  same <- function(r) !is.null(r) && r$p < 0.05 && sign(log(r$or)) == sign(log(a$or))
  c(a, list(halves = list(A = h$A, B = h$B, replicated = same(h$A) && same(h$B))))
}
both <- bind_rows(data.frame(y = 1, province = d$province, half = d$half, then = d$then, grave = d$grave),
                  data.frame(y = 0, province = rnd$province, half = rnd$half, then = rnd$then, grave = rnd$grave))
both$closer_water <- -log2(both$then + 250); both$closer_grave <- -log2(both$grave + 250)
f1 <- y ~ closer_water + closer_grave + factor(province)
d$near1k <- as.integer(d$then < 1000)
dated <- d[!is.na(d$t50), ]
SEC <- list(
  S1a = c(list(label = "Närmare vatten år 1050, med närheten till gravfält konstant (oddskvot när avståndet halveras)"),
          with_halves(both, f1, "closer_water")),
  S1b = c(list(label = "Närmare gravfält, med närheten till vatten år 1050 konstant (oddskvot när avståndet halveras)"),
          with_halves(both, f1, "closer_grave")),
  S2 = c(list(label = "Inom 1 km från vatten år 1050 över tid (per 50 år)"),
         with_halves(dated, near1k ~ t50 + factor(province), "t50"),
         list(early = r3(mean(dated$near1k[dated$year < 1050])), late = r3(mean(dated$near1k[dated$year >= 1050])),
              n_early = sum(dated$year < 1050), n_late = sum(dated$year >= 1050))),
  S3 = c(list(label = "Kristna markörer och närhet till vatten år 1050 (tiden konstant)"),
         with_halves(dated, near1k ~ christian + t50 + factor(province), "christian"),
         list(share_christian = r3(mean(dated$near1k[dated$christian == 1])),
              share_other = r3(mean(dated$near1k[dated$christian == 0])),
              n_christian = sum(dated$christian == 1), n_other = sum(dated$christian == 0))),
  S4 = c(list(label = "Bro- och vägstenar och närhet till vatten år 1050"),
         with_halves(d, near1k ~ cat_bro_vag + factor(province), "cat_bro_vag"),
         list(n_bridge = sum(d$cat_bro_vag == 1), median_bridge_m = round(median(d$then[d$cat_bro_vag == 1])),
              median_other_m = round(median(d$then[d$cat_bro_vag == 0])),
              share_bridge = r3(mean(d$near1k[d$cat_bro_vag == 1])), share_other = r3(mean(d$near1k[d$cat_bro_vag == 0]))))
)
sq <- p.adjust(sapply(SEC, `[[`, "p"), "BH")
for (i in seq_along(SEC)) SEC[[i]]$q_bh <- signif(sq[i], 3)
say("sekundära")

# ---- robustness ------------------------------------------------------------------------------------------------------
slice_res <- function(col, bp) c(list(bp = as.integer(bp), year = bp_year(bp)), summ(d[[col]], rnd[[col]]),
  list(provinces = lapply(PROVS, function(pv) c(list(province = pv), summ(d[[col]][d$province == pv], rnd[[col]][rnd$province == pv])))))
R1res <- lapply(c(R1, R1X), function(bp) slice_res(paste0("s", bp), bp)); names(R1res) <- paste0("AD", bp_year(c(R1, R1X)))
R2res <- c(list(codes = "hav (kod 1)"), slice_res("sea", MAIN))
R5res <- c(list(n_excluded = sum(d$then == 0)), summ(d$then[d$then > 0], rnd$then))
R7res <- list(r2km = list(radius_m = 2000, water = summ(d$then, r2$then), grave = summ(d$grave, r2$grave),
                          water_provinces = lapply(PROVS, function(pv) c(list(province = pv), summ(d$then[d$province == pv], r2$then[r2$province == pv])))),
              r10km = list(radius_m = 10000, water = summ(d$then, r10$then), grave = summ(d$grave, r10$grave),
                           water_provinces = lapply(PROVS, function(pv) c(list(province = pv), summ(d$then[d$province == pv], r10$then[r10$province == pv])))))
R6res <- NULL
r6f <- file.path(WORK, paste0(sapply(PROVS, pv_key), "_r6.rds"))
if (all(file.exists(r6f))) {
  R6 <- lapply(r6f, readRDS)
  R6res <- lapply(c(-1, 0, 1), function(dl) {
    col <- paste0("d", dl)
    s <- unlist(lapply(R6, function(z) z$stones[[col]][match(d$signum[d$province == z$province], z$stones$signum)]))
    r <- unlist(lapply(R6, function(z) { v <- z$main[[col]]; v[!is.na(v) & v > 0] }))
    prov <- lapply(R6, function(z) {
      ss <- z$stones[[col]][match(d$signum[d$province == z$province], z$stones$signum)]
      rr <- z$main[[col]]; rr <- rr[!is.na(rr) & rr > 0]
      c(list(province = z$province, level_m = z$level_m + dl, random_dropped = sum(z$main[[col]] == 0, na.rm = TRUE)), summ(ss, rr))
    })
    c(list(delta_m = dl), summ(s, r), list(provinces = prov))
  })
  names(R6res) <- c("minus1", "zero", "plus1")
}
flagged <- sum(sapply(A, `[[`, "flagged"))

# ---- T1 (tillägget analysplaner/2026-10-31-strand-tillagg.md): stenar som står kvar enligt den låsta korpusen, dagens
# korpus e83202e01a5e6d27 (moved = 0, lost = 0) och Runor 2020 (inte original = false); samma slumppunkter, inga nya avstånd
now_c <- read_corpus(file.path(REPO, "data/cache/r/corpus/e83202e01a5e6d27/corpus.csv"))
keep_now <- now_c$signum[!is.na(now_c$moved) & now_c$moved == 0 & !is.na(now_c$lost) & now_c$lost == 0]
runor <- jsonlite::fromJSON(file.path(REPO, "data/raa/runor_2020.json"), simplifyVector = TRUE)
runor <- if (is.data.frame(runor)) runor else runor$inscriptions
moved_runor <- runor$signum[!is.na(runor$original) & runor$original == FALSE]
t1 <- d$signum %in% keep_now & !(d$signum %in% moved_runor)
T1res <- list(plan = "analysplaner/2026-10-31-strand-tillagg.md", n = sum(t1), dropped = as.list(table(d$province[!t1])),
              water = c(summ(d$then[t1], rnd$then),
                        list(provinces = lapply(PROVS, function(pv) c(list(province = pv),
                             summ(d$then[t1 & d$province == pv], rnd$then[rnd$province == pv]))))),
              grave = summ(d$grave[t1], rnd$grave))
T1res$water_holds <- !is.null(T1res$water$p) && T1res$water$p < 0.05 && T1res$water$auc > 0.5
T1res$grave_holds <- !is.null(T1res$grave$p) && T1res$grave$p < 0.05 && T1res$grave$auc > 0.5
say("T1: ", T1res$n, " stenar; vatten ", T1res$water_holds, ", gravfält ", T1res$grave_holds)

# ---- D1 (moved included) and D2 (the corpus today) ----------------------------------------------------------------------
D1 <- list(n_all = nrow(all6), n_moved = sum(all6$moved == 1), then = summ(all6$then, rall$then),
           now = summ(all6$now, rall$now), grave = summ(all6$grave, rall$grave),
           moved_only_then = summ(all6$then[all6$moved == 1], rall$then))
old <- file.path(REPO, "data/cache/r/corpus/5fdfd1e095bfb6fb")
og <- jsonlite::fromJSON(file.path(old, "geography.json"), simplifyVector = FALSE)$water
orr <- jsonlite::fromJSON(file.path(old, "remains.json"), simplifyVector = FALSE)
D2 <- list(water_viking = og$viking_shore[c("n_stones", "median_stones_km", "median_random_km", "p")],
           water_viking_provinces = og$viking_shore$provinces,
           water_today = og$overall[c("n_stones", "median_stones_km", "median_random_km", "p")],
           gravfalt = Filter(function(x) x$key == "gravfalt", orr$distances)[[1]][c("n_stones", "near_stones", "near_random",
                                                                                   "median_stones_km", "median_random_km")])

# ---- verdict -------------------------------------------------------------------------------------------------------
ok <- function(r) !is.null(r) && !is.null(r$p) && !is.na(r$p) && r$p < 0.05 && r$auc > 0.5
crit <- list(c1_overall = ok(H1$overall), c2_halves = ok(H1$halves$A) && ok(H1$halves$B), c3_sites = ok(H1$sites),
             c4_slices = all(sapply(R1res[paste0("AD", bp_year(R1))], ok)), c5_sea_only = ok(R2res))
verdict_h1 <- if (!crit$c1_overall) "inte stött" else if (all(unlist(crit))) "håller" else "indikation"
crit_h3 <- list(overall = ok(H3$overall), halves = ok(H3$halves$A) && ok(H3$halves$B), sites = ok(H3$sites))
verdict_h3 <- if (all(unlist(crit_h3))) "håller" else if (crit_h3$overall) "indikation" else "inte stött"
h2_txt <- if (H2$ci95[1] > 0) "tydligare med dåtidens vatten" else if (H2$ci95[2] < 0) "svagare med dåtidens vatten" else
  "ingen säker skillnad"
sig_prov <- function(rows) unlist(lapply(Filter(function(r) !is.null(r$q_bh) && r$q_bh < 0.05 && r$auc > 0.5, rows), `[[`, "province"))

result <- list(
  plan = "analysplaner/2026-10-23-strand-och-gravfalt.md",
  plan_sha256 = trimws(sub(" .*", "", readLines(file.path(REPO, "analysplaner/2026-10-23-strand-och-gravfalt.sha256"))[1])),
  computed_at = format(Sys.time(), "%Y-%m-%d %H:%M"), r_version = R.version.string,
  population = list(n = nrow(d), provinces = as.list(table(d$province)), other_provinces_not_tested = other_counts,
                    n_sites = length(unique(d$site)), n_random = nrow(rnd), halves = as.list(table(d$half)),
                    stones_in_water_1050 = sum(d$then == 0), stones_in_water_1949 = sum(d$now == 0),
                    stones_in_water_1050_by_province = as.list(table(d$province[d$then == 0])),
                    n_dated = nrow(dated), n_gravfalt = nrow(gf), distances_at_tile_margin = flagged),
  H1 = H1, today = NOWres, H2 = H2, H3 = H3, secondary = SEC,
  robustness = list(R1 = R1res, R2 = R2res, R5 = R5res, R6 = R6res, R7 = R7res), T1 = T1res,
  D1 = D1, D2 = D2,
  verdict = list(H1 = verdict_h1, H1_criteria = crit, H3 = verdict_h3, H3_criteria = crit_h3, H2 = h2_txt,
                 R6_all_delta = if (is.null(R6res)) NA else all(sapply(R6res, ok)),
                 provinces_h1 = sig_prov(H1$provinces), provinces_h3 = sig_prov(H3$provinces))
)
write_json(result, file.path(OUT, "resultat.json"), auto_unbox = TRUE, digits = NA, null = "null", na = "null", pretty = TRUE)
write.csv(d[, c("signum", "province", "parish", "half", "site", "year", "christian", "cat_bro_vag", "then", "now", "grave")],
          file.path(OUT, "stenar.csv"), row.names = FALSE, fileEncoding = "UTF-8")
say("H1: ", verdict_h1, "; H3: ", verdict_h3, "; H2: ", h2_txt, "; R6: ", result$verdict$R6_all_delta)
