# Förändring i tid och rum: hur språkdrag, skrift och kristna drag förändras över tid och varierar i landet.
#
# För varje drag (t.ex. monoftong i 'sten', stungna runor, kristen bön) prövas med logistisk regression (mgcv):
#   tid       draget mot stilgruppens mittår (Gräslund) bland daterade stenar, med en rumslig utjämning
#             s(öst, nord) i SWEREF 99 TM och ristaren som slumpeffekt, så att stenar av samma ristare inte räknas
#             som oberoende och förändringen inte bara är en förskjutning mellan områden med olika datering;
#             stenar utan säker ristare grupperas per socken (en grov ersättning för okänd ristare eller verkstad)
#   rum       var draget är vanligast: rumslig utjämning på alla stenar där draget kan bestämmas (ristaren som
#             slumpeffekt), som karta
#   landskap  hur vanligt draget är omkring år 1050 i olika landskap och när det blir vanligare än hälften
#             (gemensam lutning över tid, egen nivå per landskap), med osäkerhet ur modellens kovariansmatris
# Dateringens osäkerhet prövas genom att dra årtal jämnt inom stilgruppens intervall. Därtill prövas om bro- och
# vägstenar oftare har kristen bön och kors än andra stenar, med samma kontroller.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(mgcv); library(sf) })

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
N_DRAWS <- if (is.null(P$draws)) 10 else P$draws
MIN_DATED <- 60   # daterade stenar där draget kan bestämmas
MIN_EVENTS <- 10  # minst så många stenar med och utan draget
MIN_PROV <- 25    # daterade stenar per landskap i landskapsjämförelsen
MIN_PROV_EACH <- 3
CELL_KM <- 10     # kartans rutor
REACH_CELLS <- 3  # kartan visas bara inom tre rutor (ca 30 km) från en sten där draget kan bestämmas

d <- read_corpus(P$corpus)
d <- d[!is.na(d$lat) & !is.na(d$lon), ]
xy <- st_coordinates(st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), SWEREF)) / 1000
d$east <- xy[, 1]; d$north <- xy[, 2]
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$style_short <- sub(" .*", "", d$style)
# Ristaren som slumpeffekt; stenar utan säker ristare grupperas per socken, eftersom de ofta är huggna av samma
# okända ristare eller verkstad (en egen grupp per sten gav samma skattningar men tog tio gånger längre tid)
d$carver_f <- ifelse(!is.na(d$carver) & d$carver != "", d$carver,
                     paste0("_", d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish)))
# Inskriften är tolkningsbar nog för formler och kors (språkdragen för bön finns då)
d$legible <- !is.na(d$trait_bon)

FEATURES <- list(
  list(key = "ai_alla", col = "trait_ai_alla", yes = c("monoftong", "båda"), no = "diftong", group = "språk",
       label = tr("Monoftong i något ai-ord (stin för stain)", "Monophthong in an ai word (stin for stain)")),
  list(key = "au_och", col = "trait_au_och", yes = "monoftong", no = "auk", group = "språk",
       label = tr("Monoftong i 'och' (uk för auk)", "Monophthong in 'and' (uk for auk)")),
  list(key = "r_for_R", col = "trait_r_for_R", yes = c("r för ʀ", "båda"), no = "ʀ-runa", group = "språk",
       label = tr("r för ʀ (æftir för æftiR)", "r for ʀ (æftir for æftiR)")),
  list(key = "o_runa", col = "trait_o_runa", yes = c("o-runa", "båda"), no = "u-runa", group = "språk",
       label = tr("o-runan för o-ljud (broþur för bruþur)", "o-rune for o (broþur for bruþur)")),
  list(key = "h", col = "trait_h_bortfall", yes = "h saknas", no = "h skrivet", group = "språk",
       label = tr("h-bortfall (ans för hans)", "Loss of initial h (ans for hans)")),
  list(key = "nasal", col = "trait_nasal", yes = "skriven", no = "utelämnad", group = "språk",
       label = tr("Nasal skriven före konsonant", "Nasal written before consonant")),
  list(key = "preposition", col = "trait_preposition", yes = c("at", "båda"), no = "æftiR", group = "språk",
       label = tr("Prepositionen at (i stället för æftiR)", "The preposition at (instead of æftiR)")),
  list(key = "stungna", col = "trait_stungna", yes = "ja", no = "nej", group = "skrift",
       label = tr("Stungna runor", "Dotted runes")),
  list(key = "stungen_e", col = "trait_stungen_e", yes = "ja", no = "nej", group = "skrift",
       label = tr("Stungen i (e)", "Dotted i (e)")),
  list(key = "stungen_y", col = "trait_stungen_y", yes = "ja", no = "nej", group = "skrift",
       label = tr("Stungen u (y)", "Dotted u (y)")),
  list(key = "stungen_g", col = "trait_stungen_g", yes = "ja", no = "nej", group = "skrift",
       label = tr("Stungen k (g)", "Dotted k (g)")),
  list(key = "bon", col = "trait_bon", yes = "ja", no = "nej", group = "kristnande",
       label = tr("Kristen bön", "Christian prayer")),
  list(key = "sjal", col = "trait_sjal", yes = "ja", no = "nej", group = "kristnande",
       label = tr("Själsbön", "Prayer for the soul")),
  list(key = "cross", col = "cross", yes = 1, no = 0, group = "kristnande", legible = TRUE,
       label = tr("Kors", "Cross")),
  list(key = "bro", col = "cat_bro_vag", yes = 1, no = 0, group = "innehåll", legible = TRUE,
       label = tr("Bro- eller vägbygge", "Bridge or road building")),
  list(key = "signatur", col = "trait_signatur", yes = "ja", no = "nej", group = "innehåll",
       label = tr("Ristarsignatur", "Carver's signature"))
)

outcome <- function(f) {
  v <- as.character(d[[f$col]])
  y <- ifelse(v %in% as.character(f$yes), 1L, ifelse(v %in% as.character(f$no), 0L, NA_integer_))
  if (isTRUE(f$legible)) y[!d$legible] <- NA_integer_
  y
}

k_space <- function(n) max(5, min(30, floor(n / 15)))

# bam med diskretiserade kovariater: samma skattningar som gam/REML i provkörningar, men snabbt nog för
# dragningarna inom stilgruppernas intervall
fit <- function(form, dd) {
  dd$carver_f <- factor(dd$carver_f)
  tryCatch(suppressWarnings(bam(form, data = dd, family = binomial, method = "fREML", discrete = TRUE)),
           error = function(e) NULL)
}

coef_test <- function(m, term) {
  if (is.null(m) || !(term %in% names(coef(m)))) return(NULL)
  b <- unname(coef(m)[term]); se <- sqrt(vcov(m)[term, term])
  list(b = b, se = se, p = 2 * pnorm(-abs(b / se)))
}

wilson <- function(k, n, z = 1.96) {
  if (n == 0) return(c(NA, NA))
  p <- k / n; den <- 1 + z^2 / n
  c((p + z^2 / (2 * n) - z * sqrt(p * (1 - p) / n + z^2 / (4 * n^2))) / den,
    (p + z^2 / (2 * n) + z * sqrt(p * (1 - p) / n + z^2 / (4 * n^2))) / den)
}

STYLE_ORDER <- c("RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5")
MIN_STYLE_N <- 20  # the curve covers the style groups with at least this many stones

smooth_p <- function(m, term) {
  st <- summary(m)$s.table
  st[grep(paste0("^s\\(", term), rownames(st))[1], "p-value"]
}

# Adjusted share at each year: every stone in the data moved to that year, the carver effect left out (a typical
# carver) and the predictions averaged, so that the curve is not a shift between areas or carvers. The interval
# comes from draws of the model coefficients.
adjusted <- function(m, dd, years, nsim = 300, newdata = function(nd, y) { nd$tt <- (y - 1050) / 50; nd }) {
  dd$carver_f <- factor(dd$carver_f)
  b <- coef(m)
  B <- if (nsim > 0) rmvn(nsim, b, vcov(m)) else NULL
  est <- numeric(length(years)); sims <- matrix(NA_real_, max(nsim, 1), length(years))
  for (i in seq_along(years)) {
    X <- predict(m, newdata = newdata(dd, years[i]), type = "lpmatrix", exclude = "s(carver_f)")
    est[i] <- mean(plogis(X %*% b))
    if (nsim > 0) sims[, i] <- colMeans(plogis(X %*% t(B)))
  }
  q <- function(pr) if (nsim > 0) apply(sims, 2, quantile, pr) else NA
  dch <- if (nsim > 0) sims[, length(years)] - sims[, 1] else NA
  list(curve = data.frame(year = years, share = est, lo = q(0.025), hi = q(0.975)),
       change = c(est[length(years)] - est[1], if (nsim > 0) quantile(dch, c(0.025, 0.975)) else c(NA, NA)))
}

# The shape of the adjusted curve: rises, falls, peak or trough in between (at least 5 percentage points), or flat
describe <- function(curve, min_diff = 0.05) {
  s <- curve$share; n <- length(s); i_max <- which.max(s); i_min <- which.min(s)
  if (i_max > 1 && i_max < n && s[i_max] - s[1] >= min_diff && s[i_max] - s[n] >= min_diff)
    return(list(shape = "peak", peak_year = curve$year[i_max]))
  if (i_min > 1 && i_min < n && s[1] - s[i_min] >= min_diff && s[n] - s[i_min] >= min_diff)
    return(list(shape = "trough", peak_year = curve$year[i_min]))
  if (abs(s[n] - s[1]) < min_diff) return(list(shape = "flat", peak_year = NA))
  list(shape = if (s[n] > s[1]) "rises" else "falls", peak_year = NA)
}

# ---- time ---------------------------------------------------------------------------------------------------------
time_part <- function(dd) {
  dd <- dd[!is.na(dd$year), ]
  n_yes <- sum(dd$y); n <- nrow(dd)
  by_style <- dd %>% group_by(style = style_short) %>%
    summarise(year = round(mean(year)), n = n(), k = sum(y)) %>%
    filter(style %in% STYLE_ORDER) %>% arrange(match(style, STYLE_ORDER))
  ci <- t(mapply(wilson, by_style$k, by_style$n))
  by_style <- by_style %>% mutate(share = r3(k / n), lo = r3(ci[, 1]), hi = r3(ci[, 2])) %>% select(-k)
  base <- list(n = n, n_yes = n_yes, by_style = by_style)
  if (n < MIN_DATED || n_yes < MIN_EVENTS || n - n_yes < MIN_EVENTS) return(c(base, list(tested = FALSE)))
  big <- by_style$year[by_style$n >= MIN_STYLE_N]
  if (length(big) < 2 || diff(range(big)) < 40) return(c(base, list(tested = FALSE)))
  # Time as a smooth (k = 4): a feature can rise and fall again, which a straight trend would hide
  form <- y ~ s(tt, k = 4) + s(east, north, k = k_space(n)) + s(carver_f, bs = "re")
  dd$tt <- dd$t50
  m <- fit(form, dd)
  if (is.null(m)) return(c(base, list(tested = FALSE)))
  p <- smooth_p(m, "tt")
  span <- range(by_style$year[by_style$n >= MIN_STYLE_N])
  years <- unique(c(seq(span[1], span[2], by = 5), span[2]))
  cur <- adjusted(m, dd, years)
  shape <- describe(cur$curve)
  # The style group gives an interval, not a year: refit with years drawn evenly within each interval
  draws <- vapply(seq_len(N_DRAWS), function(i) {
    dd$tt <- (runif(n, dd$style_from, dd$style_to) - 1050) / 50
    md <- fit(form, dd)
    if (is.null(md)) return(c(NA, NA, NA))
    cd <- adjusted(md, dd, years, nsim = 0)$curve
    c(smooth_p(md, "tt"), tail(cd$share, 1) - cd$share[1], as.numeric(describe(cd)$shape == shape$shape))
  }, numeric(3))
  ok <- !is.na(draws[1, ])
  c(base, list(tested = TRUE, p = signif(p, 3), shape = shape$shape, peak_year = shape$peak_year,
               year_first = span[1], year_last = span[2],
               first = r3(cur$curve$share[1]), last = r3(tail(cur$curve$share, 1)),
               change = r3(cur$change[1]), change_lo = r3(cur$change[2]), change_hi = r3(cur$change[3]),
               curve = cur$curve %>% mutate(across(c(share, lo, hi), r3)),
               draws = list(n = sum(ok), share_sig = if (any(ok)) r3(mean(draws[1, ok] < 0.05)) else NA,
                            share_same_shape = if (any(ok)) r3(mean(draws[3, ok])) else NA,
                            change_min = if (any(ok)) r3(min(draws[2, ok])) else NA,
                            change_max = if (any(ok)) r3(max(draws[2, ok])) else NA)))
}

# ---- provinces ----------------------------------------------------------------------------------------------------
province_part <- function(dd, monotone) {
  dd <- dd[!is.na(dd$year), ]
  tab <- dd %>% group_by(province) %>% summarise(n = n(), k = sum(y)) %>%
    filter(n >= MIN_PROV, k >= MIN_PROV_EACH, n - k >= MIN_PROV_EACH) %>% arrange(-n)
  if (nrow(tab) < 2) return(NULL)
  dd <- dd[dd$province %in% tab$province, ]
  dd$prov <- factor(dd$province, levels = tab$province)
  # Same course over time in every province, own level per province
  m <- fit(y ~ 0 + prov + s(t50, k = 4) + s(carver_f, bs = "re"), dd)
  if (is.null(m)) return(NULL)
  pn <- paste0("prov", tab$province)
  lv <- levels(factor(dd$carver_f))
  nd <- data.frame(prov = factor(tab$province, levels = tab$province), t50 = 0, carver_f = factor(lv[1], levels = lv))
  X <- predict(m, newdata = nd, type = "lpmatrix", exclude = "s(carver_f)")
  b <- coef(m); V <- vcov(m)
  sims <- plogis(X %*% t(rmvn(4000, b, V)))
  # When the feature rises or falls steadily: the year it passes one half, from a model with a straight trend
  cross <- NULL
  if (monotone) {
    ml <- fit(y ~ 0 + prov + t50 + s(carver_f, bs = "re"), dd)
    if (!is.null(ml)) {
      bl <- coef(ml)[c(pn, "t50")]
      sl <- rmvn(4000, bl, vcov(ml)[c(pn, "t50"), c(pn, "t50")])
      cross <- lapply(seq_along(pn), function(i) quantile(1050 - 50 * sl[, i] / sl[, ncol(sl)], c(0.5, 0.025, 0.975)))
    }
  }
  rows <- lapply(seq_along(pn), function(i) {
    cy <- if (is.null(cross)) c(NA, NA, NA) else cross[[i]]
    inside <- !is.na(cy[1]) && cy[1] >= 950 && cy[1] <= 1150
    data.frame(province = tab$province[i], n = tab$n[i], share = r3(tab$k[i] / tab$n[i]),
               share1050 = r3(plogis(sum(X[i, ] * b))), lo1050 = r3(quantile(sims[i, ], 0.025)),
               hi1050 = r3(quantile(sims[i, ], 0.975)),
               cross_year = if (inside) round(cy[1]) else NA, cross_lo = if (inside) round(cy[2]) else NA,
               cross_hi = if (inside) round(cy[3]) else NA)
  })
  # Do the provinces differ at the same time? Wald test of the province levels against each other
  k <- length(pn)
  C <- cbind(-1, diag(k - 1))
  cb <- C %*% b[pn]; chi <- as.numeric(t(cb) %*% solve(C %*% V[pn, pn] %*% t(C)) %*% cb)
  list(rows = bind_rows(rows), p_differ = signif(pchisq(chi, k - 1, lower.tail = FALSE), 3), df = k - 1)
}

# ---- space --------------------------------------------------------------------------------------------------------
space_part <- function(dd) {
  n <- nrow(dd)
  if (n < MIN_DATED || sum(dd$y) < MIN_EVENTS || n - sum(dd$y) < MIN_EVENTS) return(NULL)
  m <- fit(y ~ s(east, north, k = k_space(n)) + s(carver_f, bs = "re"), dd)
  if (is.null(m)) return(NULL)
  st <- summary(m)$s.table
  row <- grep("east", rownames(st))
  # Typical carver: the carver effect is left out of the prediction
  nd <- dd; nd$carver_f <- factor(nd$carver_f)
  dd$pred <- as.numeric(predict(m, newdata = nd, type = "response", exclude = "s(carver_f)"))
  pv <- dd %>% group_by(province) %>% summarise(n = n(), pred = mean(pred)) %>% filter(n >= 15) %>% arrange(-pred)
  # Grid within reach of the stones
  cells <- unique(data.frame(cx = floor(dd$east / CELL_KM), cy = floor(dd$north / CELL_KM)))
  off <- expand.grid(dx = -REACH_CELLS:REACH_CELLS, dy = -REACH_CELLS:REACH_CELLS)
  off <- off[off$dx^2 + off$dy^2 <= REACH_CELLS^2, ]
  grid <- unique(data.frame(cx = rep(cells$cx, each = nrow(off)) + off$dx, cy = rep(cells$cy, each = nrow(off)) + off$dy))
  grid$east <- (grid$cx + 0.5) * CELL_KM; grid$north <- (grid$cy + 0.5) * CELL_KM
  grid$carver_f <- factor(levels(nd$carver_f)[1], levels = levels(nd$carver_f))
  grid$p <- as.numeric(predict(m, newdata = grid, type = "response", exclude = "s(carver_f)"))
  list(n = n, edf = r1(st[row, "edf"]), p = signif(st[row, "p-value"], 3),
       high = I(head(pv$province, 3)), low = I(rev(tail(pv$province, 3))), provinces = pv %>% mutate(pred = r3(pred)),
       grid = grid[, c("east", "north", "p")])
}

results <- list(); grids <- list()
for (f in FEATURES) {
  dd <- d; dd$y <- outcome(f); dd <- dd[!is.na(dd$y), ]
  if (nrow(dd) < MIN_EVENTS) next
  tp <- time_part(dd)
  monotone <- isTRUE(tp$tested) && tp$p < 0.05 && tp$shape %in% c("rises", "falls")
  sp <- space_part(dd)
  if (!is.null(sp)) { grids[[f$key]] <- sp$grid; sp$grid <- NULL }
  results[[f$key]] <- list(key = f$key, label = f$label, group = f$group,
                           yes = paste(trv(as.character(f$yes)), collapse = ", "), no = paste(trv(as.character(f$no)), collapse = ", "), n = nrow(dd), share = r3(mean(dd$y)),
                           time = tp, provinces = province_part(dd, monotone), space = sp)
}

# Holm over the time tests
ps <- vapply(results, function(r) if (isTRUE(r$time$tested)) r$time$p else NA_real_, numeric(1))
qs <- ps; qs[!is.na(ps)] <- p.adjust(ps[!is.na(ps)], "holm")
for (k in names(results)) {
  results[[k]]$time$q <- if (is.na(qs[[k]])) NA else signif(qs[[k]], 3)
}

# ---- bridges and Christianity -------------------------------------------------------------------------------------
yv <- function(key) { f <- Filter(function(x) x$key == key, FEATURES)[[1]]; outcome(f) }
ASSOC <- list(
  list(key = "bro_bon", y = "bon", x = "bro", label = tr("Kristen bön på bro- och vägstenar", "Christian prayer on bridge stones")),
  list(key = "bro_sjal", y = "sjal", x = "bro", label = tr("Själsbön på bro- och vägstenar", "Prayer for the soul on bridge stones")),
  list(key = "bro_cross", y = "cross", x = "bro", label = tr("Kors på bro- och vägstenar", "Cross on bridge stones"))
)
assoc <- lapply(ASSOC, function(s) {
  dd <- d; dd$y <- yv(s$y); dd$xx <- yv(s$x); dd <- dd[!is.na(dd$y) & !is.na(dd$xx), ]
  share_x <- mean(dd$y[dd$xx == 1]); share_o <- mean(dd$y[dd$xx == 0])
  m <- fit(y ~ xx + s(east, north, k = k_space(nrow(dd))) + s(carver_f, bs = "re"), dd)
  ct <- coef_test(m, "xx")
  dt <- dd[!is.na(dd$t50), ]
  ct_t <- coef_test(fit(y ~ xx + s(t50, k = 4) + s(east, north, k = k_space(nrow(dt))) + s(carver_f, bs = "re"), dt), "xx")
  ors <- function(r) if (is.null(r)) NULL else
    list(or = r3(exp(r$b)), lo = r3(exp(r$b - 1.96 * r$se)), hi = r3(exp(r$b + 1.96 * r$se)), p = signif(r$p, 3))
  list(key = s$key, label = s$label, n = nrow(dd), n_x = sum(dd$xx), share_x = r3(share_x), share_other = r3(share_o),
       all = ors(ct), dated = c(list(n = nrow(dt)), ors(ct_t)))
})
pa <- vapply(assoc, function(s) if (is.null(s$all$p)) NA_real_ else s$all$p, numeric(1))
qa <- pa; qa[!is.na(pa)] <- p.adjust(pa[!is.na(pa)], "holm")
for (i in seq_along(assoc)) assoc[[i]]$all$q <- if (is.na(qa[i])) NA else signif(qa[i], 3)

# ---- figures ------------------------------------------------------------------------------------------------------
SHAPE <- c(rises = tr("ökar", "rises"), falls = tr("minskar", "falls"), peak = tr("vanligast omkring %d", "most common around %d"),
           trough = tr("ovanligast omkring %d", "least common around %d"), flat = tr("oförändrad", "unchanged"))
pct <- function(x) paste0(round(100 * x), " %")
fmt_time <- function(t) {
  if (!isTRUE(t$tested)) return(tr("för få daterade stenar", "too few dated stones"))
  sh <- if (t$shape %in% c("peak", "trough")) sprintf(SHAPE[[t$shape]], t$peak_year) else SHAPE[[t$shape]]
  q <- if (t$q < 0.001) "q < 0,001" else sprintf("q = %.3f", t$q)
  sprintf("%s: %s → %s (%s)", sh, pct(t$first), pct(t$last), q)
}
tl <- bind_rows(lapply(results, function(r) if (nrow(r$time$by_style)) r$time$by_style %>%
  mutate(feature = paste0(r$label, "\n", fmt_time(r$time)), key = r$key) else NULL))
tc <- bind_rows(lapply(results, function(r) if (isTRUE(r$time$tested)) r$time$curve %>%
  mutate(feature = paste0(r$label, "\n", fmt_time(r$time))) else NULL))
fig_time <- NULL
if (nrow(tl)) {
  tl$feature <- factor(tl$feature, levels = unique(tl$feature))
  if (nrow(tc)) tc$feature <- factor(tc$feature, levels = levels(tl$feature))
  p <- ggplot(tl %>% filter(n >= 5), aes(year, share))
  if (nrow(tc)) p <- p + geom_ribbon(data = tc, aes(year, ymin = lo, ymax = hi), inherit.aes = FALSE, fill = SEQ[1]) +
    geom_line(data = tc, aes(year, share), colour = SERIES[1], linewidth = 0.7)
  p <- p +
    geom_errorbar(aes(ymin = lo, ymax = hi), colour = MUTED, width = 0, linewidth = 0.4) +
    geom_point(aes(size = n), colour = INK) +
    scale_size_area(max_size = 3, guide = "none") +
    scale_y_continuous(labels = function(x) paste0(round(100 * x), " %"), limits = c(0, 1)) +
    facet_wrap(~feature, ncol = 3) +
    labs(title = tr("Dragen över tid", "Features over time"),
         subtitle = tr("Punkter: andel per stilgrupp (Gräslund) med 95 % intervall. Linje: justerad andel med plats och ristare konstanta.",
                       "Points: share per style group (Gräslund) with 95% interval. Line: adjusted share with place and carver held constant."),
         x = tr("Stilgruppens mittår", "Midpoint of the style group"), y = NULL) +
    theme_runor(9)
  fig_time <- save_fig(p, out, "forandring_tid.png", 9, 2.6 * ceiling(length(unique(tl$feature)) / 3) + 1)
}

wat <- tryCatch(read_water(P$water_dir), error = function(e) NULL)
sig <- names(Filter(function(r) !is.null(r$space) && r$space$p < 0.05, results))
sig <- head(sig[order(-vapply(results[sig], function(r) r$n, numeric(1)))], 6)
fig_map <- NULL
if (length(sig)) {
  gm <- bind_rows(lapply(sig, function(k) grids[[k]] %>% mutate(feature = results[[k]]$label)))
  gm$feature <- factor(gm$feature, levels = unique(gm$feature))
  p <- ggplot(gm) + geom_tile(aes(east * 1000, north * 1000, fill = p), width = CELL_KM * 1000, height = CELL_KM * 1000)
  if (!is.null(wat$land)) p <- p + geom_sf(data = st_boundary(wat$land), colour = MUTED, linewidth = 0.15, inherit.aes = FALSE)
  rng <- c(range(gm$east), range(gm$north)) * 1000
  p <- p + scale_fill_gradientn(colours = SEQ, limits = c(0, 1),
                               labels = function(x) paste0(round(100 * x), " %"), name = tr("Andel (modell)", "Share (model)")) +
    coord_sf(crs = SWEREF, xlim = rng[1:2], ylim = rng[3:4], expand = FALSE, datum = NA) +
    facet_wrap(~feature, ncol = 3) +
    labs(title = tr("Var dragen är vanligast", "Where the features are most common"),
         subtitle = tr("Rumslig utjämning (ristaren som slumpeffekt), visad inom ca 30 km från stenar där draget kan bestämmas",
                       "Spatial smooth (carver as random effect), shown within about 30 km of stones where the feature can be determined")) +
    theme_map(9) + theme(legend.key.width = unit(1.2, "cm"))
  fig_map <- save_fig(p, out, "forandring_karta.png", 9, 4.2 * ceiling(length(sig) / 3) + 0.8)
}

pr <- bind_rows(lapply(results, function(r) if (!is.null(r$provinces)) r$provinces$rows %>% mutate(feature = r$label) else NULL))
fig_prov <- NULL
if (nrow(pr)) {
  pr$feature <- factor(pr$feature, levels = unique(pr$feature))
  p <- ggplot(pr, aes(share1050, province)) +
    geom_errorbar(aes(xmin = lo1050, xmax = hi1050), orientation = "y", width = 0, colour = SERIES[1], linewidth = 0.5) +
    geom_point(aes(size = n), colour = SERIES[1]) + scale_size_area(max_size = 3, guide = "none") +
    scale_x_continuous(labels = function(x) paste0(round(100 * x), " %"), limits = c(0, 1)) +
    facet_wrap(~feature, ncol = 3, scales = "free_y") +
    labs(title = tr("Landskapen omkring år 1050", "The provinces around 1050"),
         subtitle = tr("Skattad andel för en typisk ristare, 95 % intervall; landskap med minst 25 daterade stenar",
                       "Estimated share for a typical carver, 95% interval; provinces with at least 25 dated stones"),
         x = NULL, y = NULL) + theme_runor(9)
  fig_prov <- save_fig(p, out, "forandring_landskap.png", 9, 2.2 * ceiling(length(unique(pr$feature)) / 3) + 1)
}

result <- list(
  n_stones = nrow(d), n_dated = sum(!is.na(d$year)), draws = N_DRAWS,
  features = unname(results), assoc = assoc,
  figures = list(time = fig_time, map = fig_map, provinces = fig_prov),
  method = paste(
    "Logistisk regression (mgcv::bam, fREML) för varje drag. Tid: draget mot stilgruppens mittår (Gräslund) bland",
    "daterade stenar som en utjämnad kurva (k = 4, så att ett drag kan öka och minska igen), med en rumslig utjämning",
    "(tunnplattspline på SWEREF 99 TM-koordinater) och ristaren som slumpeffekt (stenar utan säker ristare grupperade",
    "per socken). Kurvan visas som justerad andel: alla daterade stenar flyttas till varje år och modellens",
    "sannolikheter för en typisk ristare medelvärdesbildas, med 95 % intervall ur 300 dragningar av koefficienterna.",
    "Dateringens osäkerhet",
    sprintf("prövades genom att dra årtal jämnt inom stilgruppens intervall (%d dragningar).", N_DRAWS),
    "Rum: rumslig utjämning på alla stenar där draget kan bestämmas, ristaren som slumpeffekt, kartan för en typisk",
    "ristare inom ca 30 km från stenarna. Landskap: egen nivå per landskap och samma utjämnade tidskurva, andelen",
    "omkring 1050 med osäkerhet ur modellens kovariansmatris (4 000 dragningar); skillnaden mellan landskapen prövad",
    "med Wald-test. När draget ökar eller minskar stadigt anges också året då det passerar hälften, ur en modell med",
    "rak trend.",
    "Bro- och vägstenar mot kristen bön, själsbön och kors: samma modell med bro som förklaring, på alla tolkningsbara",
    "inskrifter och med tid bland daterade. p-värdena är Holm-justerade inom tidstesten respektive brotesten.",
    "Formler och kors räknas bara på inskrifter som är tolkningsbara nog för att språkdragen ska kunna bestämmas."
  )
)
write_result(result, out, "change")
