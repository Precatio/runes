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
       change = c(est[length(years)] - est[1], if (nsim > 0) quantile(dch, c(0.025, 0.975)) else c(NA, NA)),
       sims = if (nsim > 0) sims else NULL)
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
  # A peak or trough year is uncertain: the interval covers where the top lies in the coefficient draws, widened below
  # by the refits with years redrawn within the style groups
  peak_lo <- NA; peak_hi <- NA
  if (shape$shape %in% c("peak", "trough") && !is.null(cur$sims)) {
    pk <- years[apply(cur$sims, 1, if (shape$shape == "peak") which.max else which.min)]
    peak_lo <- unname(quantile(pk, 0.025, type = 1)); peak_hi <- unname(quantile(pk, 0.975, type = 1))
  }
  # The style group gives an interval, not a year: refit with years drawn evenly within each interval
  draws <- vapply(seq_len(N_DRAWS), function(i) {
    dd$tt <- (runif(n, dd$style_from, dd$style_to) - 1050) / 50
    md <- fit(form, dd)
    if (is.null(md)) return(c(NA, NA, NA, NA))
    cd <- adjusted(md, dd, years, nsim = 0)$curve
    dsc <- describe(cd)
    c(smooth_p(md, "tt"), tail(cd$share, 1) - cd$share[1], as.numeric(dsc$shape == shape$shape),
      if (dsc$shape == shape$shape && !is.na(dsc$peak_year)) dsc$peak_year else NA)
  }, numeric(4))
  ok <- !is.na(draws[1, ])
  # How large is the change over time against the differences between carvers (both on the logit scale)?
  vc <- tryCatch(gam.vcomp(m, rescale = FALSE), error = function(e) NULL)
  sd_carver <- tryCatch(unname(sqrt(vc[grep("carver", rownames(vc))[1], 1]^2)), error = function(e) NA)
  lr <- range(qlogis(pmin(pmax(cur$curve$share, 1e-4), 1 - 1e-4)))
  rp <- draws[4, ok & !is.na(draws[4, ])]
  if (!is.na(peak_lo) && length(rp)) { peak_lo <- min(peak_lo, rp); peak_hi <- max(peak_hi, rp) }
  c(base, list(tested = TRUE, p = signif(p, 3), shape = shape$shape, peak_year = shape$peak_year,
               peak_lo = peak_lo, peak_hi = peak_hi, peak_share = r3(max(cur$curve$share)),
               trough_share = r3(min(cur$curve$share)), refit_peaks = I(sort(unique(rp))),
               time_logit_range = r3(diff(lr)), carver_sd = r3(sd_carver),
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
  # Observed shares in stones whose style group covers the middle of the period (1050), and how many carvers (and
  # parish groups of unattributed stones) the province comparison rests on
  mid <- dd[!is.na(dd$style_from) & dd$style_from <= 1050 & dd$style_to >= 1050, ]
  rows <- lapply(seq_along(pn), function(i) {
    cy <- if (is.null(cross)) c(NA, NA, NA) else cross[[i]]
    inside <- !is.na(cy[1]) && cy[1] >= 950 && cy[1] <= 1150
    pv_mid <- mid[mid$province == tab$province[i], ]
    cf <- unique(as.character(dd$carver_f[dd$province == tab$province[i]]))
    data.frame(province = tab$province[i], n = tab$n[i], share = r3(tab$k[i] / tab$n[i]),
               n_mid = nrow(pv_mid), share_mid = if (nrow(pv_mid)) r3(mean(pv_mid$y)) else NA,
               n_carvers = sum(!startsWith(cf, "_")), n_groups = length(cf),
               share1050 = r3(plogis(sum(X[i, ] * b))), lo1050 = r3(quantile(sims[i, ], 0.025)),
               hi1050 = r3(quantile(sims[i, ], 0.975)),
               cross_year = if (inside) round(cy[1]) else NA, cross_lo = if (inside) round(cy[2]) else NA,
               cross_hi = if (inside) round(cy[3]) else NA)
  })
  # Do the provinces differ at the same time? Wald test of the province levels against each other
  k <- length(pn)
  C <- cbind(-1, diag(k - 1))
  cb <- C %*% b[pn]; chi <- as.numeric(t(cb) %*% solve(C %*% V[pn, pn] %*% t(C)) %*% cb)
  # The same comparison without the carver effect: a difference that only appears (or disappears) with the carver in
  # the model depends on how the attributions were made
  m0 <- fit(y ~ 0 + prov + s(t50, k = 4), dd)
  p0 <- NA
  if (!is.null(m0)) {
    b0 <- coef(m0)[pn]; V0 <- vcov(m0)[pn, pn]
    c0 <- C %*% b0; p0 <- pchisq(as.numeric(t(c0) %*% solve(C %*% V0 %*% t(C)) %*% c0), k - 1, lower.tail = FALSE)
  }
  # Carvers with stones in both Uppland and Södermanland: the feature's share in each province among their own stones
  both <- NULL
  if (all(c("U", "Sö") %in% tab$province)) {
    cb <- dd %>% filter(province %in% c("U", "Sö"), !startsWith(as.character(carver_f), "_")) %>%
      group_by(carver_f) %>% filter(n_distinct(province) == 2) %>% ungroup()
    if (nrow(cb) >= 6) both <- list(carvers = length(unique(cb$carver_f)), n = nrow(cb),
                                    share_U = r3(mean(cb$y[cb$province == "U"])), n_U = sum(cb$province == "U"),
                                    share_So = r3(mean(cb$y[cb$province == "Sö"])), n_So = sum(cb$province == "Sö"))
  }
  # Dating outside Uppland and Södermanland is least tested: the comparison again with those provinces' stones dated
  # 25 years earlier and 25 years later; if the difference holds both ways it is less likely to be a hidden time effect
  shifted <- lapply(c(earlier = -0.5, later = 0.5), function(sh) {
    ds <- dd; out_u <- !ds$province %in% c("U", "Sö"); ds$t50[out_u] <- ds$t50[out_u] + sh
    ms <- fit(y ~ 0 + prov + s(t50, k = 4) + s(carver_f, bs = "re"), ds)
    if (is.null(ms)) return(NULL)
    Xs <- predict(ms, newdata = nd, type = "lpmatrix", exclude = "s(carver_f)")
    bs <- coef(ms); Vs <- vcov(ms)
    cs <- C %*% bs[pn]; ps <- pchisq(as.numeric(t(cs) %*% solve(C %*% Vs[pn, pn] %*% t(C)) %*% cs), k - 1, lower.tail = FALSE)
    list(p = signif(ps, 3), share1050 = setNames(as.list(r3(plogis(as.vector(Xs %*% bs)))), tab$province))
  })
  list(rows = bind_rows(rows), p_differ = signif(pchisq(chi, k - 1, lower.tail = FALSE), 3), df = k - 1,
       p_differ_nocarver = signif(p0, 3), shifted = shifted, carvers_both = both)
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
# Holm over the province comparisons too (one per feature)
pp <- vapply(results, function(r) if (is.null(r$provinces)) NA_real_ else r$provinces$p_differ, numeric(1))
qp <- pp; qp[!is.na(pp)] <- p.adjust(pp[!is.na(pp)], "holm")
for (k in names(results)) if (!is.null(results[[k]]$provinces)) results[[k]]$provinces$q_differ <- signif(qp[[k]], 3)

# ---- the monophthong in æi words: robustness ----------------------------------------------------------------------
# The trend in "stin for stain" (any æi word with a monophthong spelling) is checked in the ways a runologist would ask
# for: per word instead of per stone (a stone with many æi words has more chances), per lexeme (stæinn against the
# other words), for attributed and unattributed stones separately (the attributions may rest partly on spelling),
# within the same carver over time, without the earliest and latest style groups (the ends are thin), and for Uppland
# and Södermanland separately. Each check is a straight trend in time: the log odds per 50 years with a 95 % interval
# (negative = the monophthong spelling becomes rarer).
ai_trend <- function(dd, resp, re = TRUE, space = TRUE) {
  dd <- dd[!is.na(dd$t50), ]
  if (nrow(dd) < 30) return(list(n = nrow(dd), tested = FALSE))
  rhs <- c("t50", if (space) sprintf("s(east, north, k = %d)", min(10, k_space(nrow(dd)))), if (re) "s(carver_f, bs = \"re\")")
  m <- fit(as.formula(paste(resp, "~", paste(rhs, collapse = " + "))), dd)
  ct <- coef_test(m, "t50")
  if (is.null(ct)) return(list(n = nrow(dd), tested = FALSE))
  list(n = nrow(dd), tested = TRUE, b = r3(ct$b), lo = r3(ct$b - 1.96 * ct$se), hi = r3(ct$b + 1.96 * ct$se),
       p = signif(ct$p, 3))
}
ai_checks <- function() {
  a <- d[!is.na(d$ai_n) & d$ai_n > 0 & !is.na(d$year), ]
  if (nrow(a) < 50) return(NULL)
  a$y <- as.integer(a$ai_mono > 0)
  a$other_n <- a$ai_n - a$ai_sten_n; a$other_mono <- a$ai_mono - a$ai_sten_mono
  word <- "cbind(ai_mono, ai_n - ai_mono)"
  attributed <- !is.na(a$carver) & a$carver != ""
  # Within carvers: attributed stones of carvers with at least five such stones in at least two style groups
  wc <- a[attributed, ] %>% group_by(carver) %>% filter(n() >= 5, n_distinct(style_short) >= 2) %>% ungroup()
  within <- NULL
  if (nrow(wc) >= 20 && length(unique(wc$carver)) >= 2) {
    mw <- tryCatch(suppressWarnings(glm(cbind(ai_mono, ai_n - ai_mono) ~ factor(carver) + t50, data = wc, family = binomial)),
                   error = function(e) NULL)
    ct <- coef_test(mw, "t50")
    if (!is.null(ct)) within <- list(n = nrow(wc), carvers = length(unique(wc$carver)), tested = TRUE, b = r3(ct$b),
                                     lo = r3(ct$b - 1.96 * ct$se), hi = r3(ct$b + 1.96 * ct$se), p = signif(ct$p, 3))
  }
  by_style <- a %>% filter(style_short %in% STYLE_ORDER) %>% group_by(style = style_short) %>%
    summarise(n = n(), words = sum(ai_n), share_words = r3(sum(ai_mono) / sum(ai_n)),
              mono_i = r3(sum(ai_mono_i) / sum(ai_n)), mono_e = r3(sum(ai_mono_e) / sum(ai_n))) %>%
    arrange(match(style, STYLE_ORDER))
  ends <- c(head(by_style$style, 1), tail(by_style$style, 1))
  # Per province: does stæinn make up a different share of the æi words, and does it behave like the other words?
  by_province <- a %>% group_by(province) %>% filter(n() >= 15) %>%
    summarise(stones = n(), words = sum(ai_n), share_sten = r3(sum(ai_sten_n) / sum(ai_n)),
              mono_sten = r3(sum(ai_sten_mono) / max(1, sum(ai_sten_n))),
              mono_other = r3(sum(other_mono) / max(1, sum(other_n))),
              mono_i = r3(sum(ai_mono_i) / sum(ai_n)), mono_e = r3(sum(ai_mono_e) / sum(ai_n))) %>% arrange(-stones)
  list(
    n_stones = nrow(a), n_words = sum(a$ai_n), share_sten = r3(sum(a$ai_sten_n) / sum(a$ai_n)),
    by_style = by_style, by_province = by_province,
    checks = list(
      stone = c(list(label = "per sten (minst ett ord med monoftong)"), ai_trend(a, "y")),
      word = c(list(label = "per ord (andelen æi-ord med monoftong)"), ai_trend(a, word)),
      sten = c(list(label = "bara stæinn"), ai_trend(a[a$ai_sten_n > 0, ], "cbind(ai_sten_mono, ai_sten_n - ai_sten_mono)")),
      other = c(list(label = "bara andra æi-ord än stæinn"), ai_trend(a[a$other_n > 0, ], "cbind(other_mono, other_n - other_mono)")),
      attributed = c(list(label = "bara stenar med säker ristare"), ai_trend(a[attributed, ], word)),
      unattributed = c(list(label = "bara stenar utan säker ristare"), ai_trend(a[!attributed, ], word)),
      signed = c(list(label = "bara signerade stenar"), ai_trend(a[!is.na(a$signed) & a$signed == 1, ], word)),
      no_carver = c(list(label = "utan ristaren i modellen"), ai_trend(a, word, re = FALSE)),
      within = c(list(label = "inom samma ristare (ristare med stenar i minst två stilgrupper)"),
                 if (is.null(within)) list(tested = FALSE) else within),
      trimmed = c(list(label = sprintf("utan den tidigaste och senaste stilgruppen (%s)", paste(ends, collapse = ", "))),
                  ai_trend(a[!a$style_short %in% ends, ], word)),
      uppland = c(list(label = "bara Uppland"), ai_trend(a[a$province == "U", ], word)),
      sodermanland = c(list(label = "bara Södermanland"), ai_trend(a[a$province == "Sö", ], word))
    )
  )
}
ai_robust <- tryCatch(ai_checks(), error = function(e) list(error = conditionMessage(e)))

# ---- dotted runes: robustness, per rune and against the monophthong -----------------------------------------------
# "At least one dotted rune" favours long inscriptions and says nothing about how consistently the runes were used.
# The checks: the share of runes that could have been dotted (i/e, u/y, k/g, t/d) that are dotted; the stone measure
# with text length as a covariate; without the first and last style groups; signed stones; within carvers; Uppland and
# Södermanland. Per rune, word by word among words whose normalised form has the sound (y/ø for stungen u, e/æ for
# stungen i, g for stungen k), so that the measure is about writing habit, not about which words a text contains; and
# how the y sound is written (dotted u, plain u or i) over the style groups. Last, on stone level within the same
# period: do stones with dotted runes have fewer monophthong spellings (a joint move towards fuller spelling)?
dotted_checks <- function() {
  a <- d[!is.na(d$year) & !is.na(d$dot_cand) & d$dot_cand > 0 & !is.na(d$trait_stungna), ]
  if (nrow(a) < 50) return(NULL)
  a$y <- as.integer(a$trait_stungna == "ja")
  a$logw <- log(pmax(a$n_words, 1))
  share <- "cbind(dot_n, dot_cand - dot_n)"
  attributed <- !is.na(a$carver) & a$carver != ""
  wc <- a[attributed, ] %>% group_by(carver) %>% filter(n() >= 5, n_distinct(style_short) >= 2) %>% ungroup()
  within <- list(tested = FALSE)
  if (nrow(wc) >= 20 && length(unique(wc$carver)) >= 2) {
    mw <- tryCatch(suppressWarnings(glm(cbind(dot_n, dot_cand - dot_n) ~ factor(carver) + t50, data = wc, family = binomial)),
                   error = function(e) NULL)
    ct <- coef_test(mw, "t50")
    if (!is.null(ct)) within <- list(n = nrow(wc), carvers = length(unique(wc$carver)), tested = TRUE, b = r3(ct$b),
                                     lo = r3(ct$b - 1.96 * ct$se), hi = r3(ct$b + 1.96 * ct$se), p = signif(ct$p, 3))
  }
  sty <- a %>% filter(style_short %in% STYLE_ORDER)
  ends <- c(STYLE_ORDER[STYLE_ORDER %in% sty$style_short][1], tail(STYLE_ORDER[STYLE_ORDER %in% sty$style_short], 1))
  length_fit <- {
    rhs <- sprintf("t50 + logw + s(east, north, k = %d) + s(carver_f, bs = \"re\")", min(10, k_space(nrow(a))))
    m <- fit(as.formula(paste("y ~", rhs)), a); ct <- coef_test(m, "t50")
    if (is.null(ct)) list(tested = FALSE) else list(n = nrow(a), tested = TRUE, b = r3(ct$b), lo = r3(ct$b - 1.96 * ct$se),
                                                  hi = r3(ct$b + 1.96 * ct$se), p = signif(ct$p, 3))
  }
  checks <- list(
    stone = c(list(label = "per sten (minst en stungen runa)"), ai_trend(a, "y")),
    share = c(list(label = "andelen stungna av de runor som kunde vara stungna"), ai_trend(a, share)),
    length = c(list(label = "per sten med textlängden som kovariat"), length_fit),
    attributed = c(list(label = "bara stenar med säker ristare"), ai_trend(a[attributed, ], share)),
    unattributed = c(list(label = "bara stenar utan säker ristare"), ai_trend(a[!attributed, ], share)),
    signed = c(list(label = "bara signerade stenar"), ai_trend(a[!is.na(a$signed) & a$signed == 1, ], share)),
    within = c(list(label = "inom samma ristare (ristare med stenar i minst två stilgrupper)"), within),
    trimmed = c(list(label = sprintf("utan den tidigaste och senaste stilgruppen (%s)", paste(ends, collapse = ", "))),
                ai_trend(a[!a$style_short %in% ends, ], share)),
    uppland = c(list(label = "bara Uppland"), ai_trend(a[a$province == "U", ], share)),
    sodermanland = c(list(label = "bara Södermanland"), ai_trend(a[a$province == "Sö", ], share))
  )
  # Per rune, word by word among the words where the dotted rune can be expected
  per_rune <- lapply(c(y = "stungen u (y)", e = "stungen i (e)", g = "stungen k (g)"), function(lbl) lbl)
  per_rune <- lapply(names(per_rune), function(r) {
    ex <- paste0("dot_", r, "_exp"); ob <- paste0("dot_", r, "_obs")
    b <- d[!is.na(d$year) & !is.na(d[[ex]]) & d[[ex]] > 0, ]
    st <- b %>% filter(style_short %in% STYLE_ORDER) %>% group_by(style = style_short) %>%
      summarise(stones = n(), words = sum(.data[[ex]]), share = r3(sum(.data[[ob]]) / sum(.data[[ex]]))) %>%
      arrange(match(style, STYLE_ORDER))
    c(list(rune = r, label = per_rune[[r]], words = sum(b[[ex]]), share = r3(sum(b[[ob]]) / max(1, sum(b[[ex]]))), by_style = st),
      ai_trend(b, sprintf("cbind(%s, %s - %s)", ob, ex, ob)))
  })
  # How the y sound is written over the style groups
  yb <- d[!is.na(d$year) & !is.na(d$dot_y_exp) & d$dot_y_exp > 0 & d$style_short %in% STYLE_ORDER, ]
  y_writing <- yb %>% group_by(style = style_short) %>%
    summarise(words = sum(dot_y_exp), dotted = r3(sum(dot_y_obs) / sum(dot_y_exp)), u = r3(sum(dot_y_u) / sum(dot_y_exp)),
              i = r3(sum(dot_y_i) / sum(dot_y_exp))) %>% arrange(match(style, STYLE_ORDER))
  # Stone level, same period: dotted runes and the monophthong together
  j <- d[!is.na(d$year) & !is.na(d$ai_n) & d$ai_n > 0 & !is.na(d$trait_stungna), ]
  joint <- list(tested = FALSE)
  if (nrow(j) >= 50) {
    j$mono <- as.integer(j$ai_mono > 0); j$dot <- as.integer(j$trait_stungna == "ja")
    m <- fit(y ~ dot + t50 + s(carver_f, bs = "re"), transform(j, y = mono))
    ct <- coef_test(m, "dot")
    if (!is.null(ct)) joint <- list(n = nrow(j), tested = TRUE, b = r3(ct$b), lo = r3(ct$b - 1.96 * ct$se),
                                    hi = r3(ct$b + 1.96 * ct$se), p = signif(ct$p, 3),
                                    mono_with_dot = r3(mean(j$mono[j$dot == 1])), mono_without_dot = r3(mean(j$mono[j$dot == 0])))
  }
  list(n_stones = nrow(a), share_overall = r3(sum(a$dot_n) / sum(a$dot_cand)), checks = checks, per_rune = per_rune,
       y_writing = y_writing, joint_monophthong = joint)
}
dotted_robust <- tryCatch(dotted_checks(), error = function(e) list(error = conditionMessage(e)))

# ---- the soul prayer: damaged ends and wording ----------------------------------------------------------------------
# The prayer usually comes last, in the serpent's tail, where stones are often damaged: the trend again on stones whose
# inscription ends intact. And the wording: does sál replace and/ônd over time (a change in word choice, less a matter
# of whether the sponsor wanted a prayer at all), and how often is Guðs móðir added?
prayer_checks <- function() {
  b <- d[!is.na(d$year) & !is.na(d$trait_sjal), ]
  b$y <- as.integer(b$trait_sjal == "ja")
  intact <- c(list(label = "bara stenar där inskriftens slut är bevarat"), ai_trend(b[!is.na(b$end_intact) & b$end_intact == 1, ], "y"))
  p <- b[b$y == 1 & !is.na(b$prayer_sal), ]
  p$sal <- as.integer(p$prayer_sal == 1 & p$prayer_and == 0)
  wording <- p %>% filter(style_short %in% STYLE_ORDER) %>% group_by(style = style_short) %>%
    summarise(prayers = n(), sal = r3(mean(sal)), gudsmodir = r3(mean(prayer_gudsmodir))) %>%
    arrange(match(style, STYLE_ORDER))
  sal_trend <- c(list(label = "sál i stället för and/ônd bland själsbönerna"), ai_trend(p, "sal", space = FALSE))
  list(n_prayers = nrow(p), intact = intact, wording = wording, sal_trend = sal_trend,
       share_sal = r3(mean(p$sal)), share_gudsmodir = r3(mean(p$prayer_gudsmodir)))
}
prayer_robust <- tryCatch(prayer_checks(), error = function(e) list(error = conditionMessage(e)))

# ---- ʀ and r at the end of words -------------------------------------------------------------------------------------
# r for ʀ word by word, for æftiʀ and for the other words separately (the preposition varies, so only stones where the
# words occur count), and the reverse spelling ʀ for r (hypercorrect), which tells more about a merger in speech: if
# both directions occur and grow, the sounds had merged and the spelling had become uncertain.
r_checks <- function() {
  b <- d[!is.na(d$year) & !is.na(d$R_n), ]
  b$o_n <- b$R_n - b$R_eftir_n; b$o_r <- b$R_r - b$R_eftir_r
  sty <- function(x, n, k) x %>% filter(style_short %in% STYLE_ORDER, .data[[n]] > 0) %>% group_by(style = style_short) %>%
    summarise(stones = n(), words = sum(.data[[n]]), share = r3(sum(.data[[k]]) / sum(.data[[n]]))) %>%
    arrange(match(style, STYLE_ORDER))
  list(
    all = c(list(label = "r för ʀ, alla ord på -ʀ", words = sum(b$R_n), share = r3(sum(b$R_r) / max(1, sum(b$R_n))),
                 by_style = sty(b, "R_n", "R_r")), ai_trend(b[b$R_n > 0, ], "cbind(R_r, R_n - R_r)")),
    eftir = c(list(label = "r för ʀ i æftiʀ", words = sum(b$R_eftir_n), share = r3(sum(b$R_eftir_r) / max(1, sum(b$R_eftir_n))),
                   by_style = sty(b, "R_eftir_n", "R_eftir_r")), ai_trend(b[b$R_eftir_n > 0, ], "cbind(R_eftir_r, R_eftir_n - R_eftir_r)")),
    other = c(list(label = "r för ʀ i andra ord än æftiʀ", words = sum(b$o_n), share = r3(sum(b$o_r) / max(1, sum(b$o_n))),
                   by_style = sty(b, "o_n", "o_r")), ai_trend(b[b$o_n > 0, ], "cbind(o_r, o_n - o_r)")),
    reverse = c(list(label = "ʀ för r (omvänd stavning)", words = sum(b$r_n), share = r3(sum(b$r_R) / max(1, sum(b$r_n))),
                     by_style = sty(b, "r_n", "r_R")), ai_trend(b[b$r_n > 0, ], "cbind(r_R, r_n - r_R)"))
  )
}
r_robust <- tryCatch(r_checks(), error = function(e) list(error = conditionMessage(e)))

# ---- the ós-rune, 'och', and æftiʀ for dotted i ---------------------------------------------------------------------
# The ós-rune word by word among words with etymological /o/, and for words with the old nasal ą (and/ônd): if the rune
# is given up for ą while taken up for /o/, its value shifted. 'och' occurrence by occurrence as auk, uk, ok and ak.
# Dotted i in æftiʀ against the other words with e/æ (some provinces use at instead of æftiʀ).
spelling_checks <- function() {
  b <- d[!is.na(d$year), ]
  sty <- function(x, n, cols) x %>% filter(style_short %in% STYLE_ORDER, .data[[n]] > 0) %>% group_by(style = style_short) %>%
    summarise(stones = n(), words = sum(.data[[n]]), across(all_of(cols), ~ r3(sum(.x) / sum(.data[[n]])))) %>%
    arrange(match(style, STYLE_ORDER))
  b$e_other_exp <- b$dot_e_exp - b$dot_e_eftir_exp; b$e_other_obs <- b$dot_e_obs - b$dot_e_eftir_obs
  list(
    o = c(list(label = "åsrunan för /o/", words = sum(b$o_n), share = r3(sum(b$o_o) / max(1, sum(b$o_n))),
               by_style = sty(b, "o_n", "o_o")), ai_trend(b[b$o_n > 0, ], "cbind(o_o, o_n - o_o)")),
    nasal = c(list(label = "åsrunan för ą (and/ônd)", words = sum(b$aa_n), share = r3(sum(b$aa_o) / max(1, sum(b$aa_n))),
                   by_style = sty(b, "aa_n", "aa_o")), ai_trend(b[b$aa_n > 0, ], "cbind(aa_o, aa_n - aa_o)", space = FALSE)),
    och = list(label = "'och' per förekomst", words = sum(b$och_n),
               by_style = sty(b, "och_n", c("och_auk", "och_uk", "och_ok", "och_ak"))),
    e_eftir = c(list(label = "stungen i i æftiʀ", words = sum(b$dot_e_eftir_exp),
                     share = r3(sum(b$dot_e_eftir_obs) / max(1, sum(b$dot_e_eftir_exp))),
                     by_style = sty(b, "dot_e_eftir_exp", "dot_e_eftir_obs")),
                ai_trend(b[b$dot_e_eftir_exp > 0, ], "cbind(dot_e_eftir_obs, dot_e_eftir_exp - dot_e_eftir_obs)")),
    e_other = c(list(label = "stungen i i andra ord", words = sum(b$e_other_exp),
                     share = r3(sum(b$e_other_obs) / max(1, sum(b$e_other_exp))),
                     by_style = sty(b, "e_other_exp", "e_other_obs")),
                ai_trend(b[b$e_other_exp > 0, ], "cbind(e_other_obs, e_other_exp - e_other_obs)"))
  )
}
spelling_robust <- tryCatch(spelling_checks(), error = function(e) list(error = conditionMessage(e)))

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
  form <- y ~ xx + s(east, north, k = k_space(nrow(dd))) + s(carver_f, bs = "re")
  m <- fit(form, dd)
  ct <- coef_test(m, "xx")
  dt <- dd[!is.na(dd$t50), ]
  # Time as in the peak models: the prayer has its own peak, so bridge stones from the same period must not create it
  ct_t <- coef_test(fit(y ~ xx + s(t50, k = 4) + s(east, north, k = k_space(nrow(dt))) + s(carver_f, bs = "re"), dt), "xx")
  ors <- function(r) if (is.null(r)) NULL else
    list(or = r3(exp(r$b)), lo = r3(exp(r$b - 1.96 * r$se)), hi = r3(exp(r$b + 1.96 * r$se)), p = signif(r$p, 3))
  # Text length, and stones whose inscription ends intact (prayers come last)
  dd$logw <- log(pmax(dd$n_words, 1))
  ct_len <- coef_test(fit(y ~ xx + logw + s(east, north, k = k_space(nrow(dd))) + s(carver_f, bs = "re"), dd), "xx")
  di <- dd[!is.na(dd$end_intact) & dd$end_intact == 1, ]
  ct_int <- coef_test(fit(y ~ xx + s(east, north, k = k_space(nrow(di))) + s(carver_f, bs = "re"), di), "xx")
  # How many carvers and parishes the bridge stones with the feature spread over, and the estimate with one carver (or
  # one parish) left out at a time: can a few workshops carry the whole effect?
  bx <- dd[dd$xx == 1 & dd$y == 1, ]
  carv <- unique(bx$carver[!is.na(bx$carver) & bx$carver != ""]); par <- unique(bx$parish[!is.na(bx$parish)])
  loo <- function(groups, col) {
    vals <- vapply(groups, function(g) { r <- coef_test(fit(form, dd[is.na(dd[[col]]) | dd[[col]] != g, ]), "xx")
      if (is.null(r)) NA_real_ else exp(r$b) }, 0)
    if (all(is.na(vals))) NULL else list(min_or = r3(min(vals, na.rm = TRUE)), max_or = r3(max(vals, na.rm = TRUE)),
                                         n = sum(!is.na(vals)))
  }
  list(key = s$key, label = s$label, n = nrow(dd), n_x = sum(dd$xx), share_x = r3(share_x), share_other = r3(share_o),
       k_x = nrow(bx), n_carvers_x = length(carv), n_parishes_x = length(par),
       all = ors(ct), dated = c(list(n = nrow(dt)), ors(ct_t)), length = ors(ct_len),
       intact = c(list(n = nrow(di)), ors(ct_int)),
       loo_carver = if (length(carv)) loo(carv, "carver") else NULL,
       loo_parish = if (length(par) && length(par) <= 60) loo(par, "parish") else NULL)
})
pa <- vapply(assoc, function(s) if (is.null(s$all$p)) NA_real_ else s$all$p, numeric(1))
qa <- pa; qa[!is.na(pa)] <- p.adjust(pa[!is.na(pa)], "holm")
for (i in seq_along(assoc)) assoc[[i]]$all$q <- if (is.na(qa[i])) NA else signif(qa[i], 3)

# ---- figures ------------------------------------------------------------------------------------------------------
SHAPE <- c(rises = tr("ökar", "rises"), falls = tr("minskar", "falls"), peak = tr("vanligast omkring %d (%d–%d)", "most common around %d (%d–%d)"),
           trough = tr("ovanligast omkring %d (%d–%d)", "least common around %d (%d–%d)"), flat = tr("oförändrad", "unchanged"))
pct <- function(x) paste0(round(100 * x), " %")
fmt_time <- function(t) {
  if (!isTRUE(t$tested)) return(tr("för få daterade stenar", "too few dated stones"))
  sh <- if (t$shape %in% c("peak", "trough")) sprintf(SHAPE[[t$shape]], t$peak_year, t$peak_lo, t$peak_hi) else SHAPE[[t$shape]]
  q <- if (t$q < 0.001) tr("q < 0,001", "q < 0.001") else sprintf("q = %.3f", t$q)
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
  features = unname(results), assoc = assoc, ai_robustness = ai_robust, dotted_robustness = dotted_robust,
  prayer_robustness = prayer_robust, r_robustness = r_robust, spelling_robustness = spelling_robust,
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
