# Okända ristare: grupper av stenar utan ristare i Rundata som liknar varandra i handens drag och ligger nära
# varandra – möjliga ristare eller verkstäder som ännu saknar namn.
#
# 1. Likhet: Gowers avstånd på stilgrupp, kors, kortkvistrunor, språkdrag (stavning, skiljetecken, bindrunor),
#    formler och runbigram. Innehåll och plats ingår inte i likheten.
# 2. Kalibrering på stenar med känd ristare: par inom LINK_KM km av samma ristare mot par av olika ristare. Gränsen är
#    det största avstånd där par under gränsen är minst LR_MIN gånger vanligare bland samma ristares par.
# 3. Graf: stenar utan ristare länkas när de ligger inom LINK_KM km och under gränsen; grupper med Louvain. En grupp
#    redovisas bara om den inte är mer utspridd än 90 % av de kända ristarnas stenar (median till mitten).
# 4. Validering: samma förfarande på stenar med känd ristare, som om ristaren vore okänd. Hur stor del av en grupp
#    är samma ristare, jämfört med grupper av lika många närliggande stenar (bara geografi)?
# 5. Varje grupp jämförs med kända ristare i närheten (avstånd i handens drag och attribueringsmodellens förslag).
#    Grupper som inte liknar någon känd ristare får ett arbetsnamn efter typstenens socken, där typstenen är den
#    sten som i genomsnitt ligger närmast de andra i gruppen.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(cluster); library(igraph) })

a <- cli_args(); P <- a$params; out <- a$out; cdir <- P$corpus_dir
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
LINK_KM <- 30      # stenar längre ifrån varandra länkas inte
LR_MIN <- 12       # par under gränsen ska vara minst så många gånger vanligare bland samma ristares par
# LINK_KM and LR_MIN were chosen by the validation on known carvers (15–30 km, 4–12): 30 km and 12 gave the purest
# groups that still covered several hundred stones
MIN_GROUP <- 4     # minsta grupp som redovisas
MIN_CARVER <- 3    # ristare med minst så många säkra stenar används i kalibrering och validering
MIN_WORDS <- 5     # stenar med kortare läsbar text har för lite av handens drag
NEAR_CARVER_KM <- 50
N_BOOT <- if (is.null(P$boot)) 50 else P$boot

d <- read_corpus(P$corpus)
geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
full <- d %>% left_join(geo %>% select(signum, x, y), by = "signum") %>% left_join(txt, by = "signum") %>%
  filter(!is.na(x), n_words >= MIN_WORDS)
full$style_short <- ifelse(is.na(full$style), NA, sub("[ ?].*", "", full$style))
full$parish_name <- sub(" sn$", "", full$parish)

tc <- trait_cols(d)
fcols <- grep("^formula_", names(txt), value = TRUE)
bcols <- grep("^bg_", names(txt), value = TRUE)
HAND <- c("style_short", "cross", "short_twig", tc, fcols, bcols)
X <- full[, HAND]
for (col in c("style_short", "cross", "short_twig", tc, fcols)) X[[col]] <- factor(X[[col]])
G <- as.matrix(daisy(X, metric = "gower"))
K <- as.matrix(dist(cbind(full$x, full$y))) / 1000
# Median distance (km) from the stones to their centre; a group may not be more spread out than 90 % of the known
# carvers with at least five stones
spread <- function(idx) {
  cx <- mean(full$x[idx]); cy <- mean(full$y[idx])
  median(sqrt((full$x[idx] - cx)^2 + (full$y[idx] - cy)^2)) / 1000
}

# ---- calibration on stones with a known carver --------------------------------------------------------------------
carver_n <- table(full$carver)
known <- which(!is.na(full$carver) & full$carver %in% names(carver_n[carver_n >= MIN_CARVER]))
carver_spread <- vapply(names(carver_n[carver_n >= 5]), function(cv) spread(which(full$carver == cv)), 0)
MAX_SPREAD <- unname(quantile(carver_spread, 0.9))
ut <- upper.tri(diag(length(known)))
near <- K[known, known] <= LINK_KM & ut
same <- outer(full$carver[known], full$carver[known], "==")
gk <- G[known, known]
d_same <- gk[near & same]; d_diff <- gk[near & !same]
grid <- sort(unique(quantile(c(d_same, d_diff), seq(0.005, 0.5, by = 0.005), na.rm = TRUE)))
cal <- data.frame(t = grid, tpr = vapply(grid, function(t) mean(d_same <= t), 0),
                  fpr = vapply(grid, function(t) mean(d_diff <= t), 0))
cal$lr <- cal$tpr / pmax(cal$fpr, 1e-9)
ok <- cal$lr >= LR_MIN & cal$tpr > 0
THRESH <- if (any(ok)) max(cal$t[ok]) else min(cal$t)
crow <- cal[cal$t == THRESH, ][1, ]
# Of linked pairs among known carvers, how many are the same carver?
precision <- sum(d_same <= THRESH) / (sum(d_same <= THRESH) + sum(d_diff <= THRESH))

# ---- groups -------------------------------------------------------------------------------------------------------
link_graph <- function(idx, drop = 0) {
  A <- (G[idx, idx] <= THRESH) & (K[idx, idx] <= LINK_KM)
  diag(A) <- FALSE
  W <- ifelse(A, 1 - G[idx, idx] / (THRESH + 1e-9) + 0.05, 0)
  if (drop > 0) {
    e <- which(upper.tri(W) & W > 0)
    W[e[runif(length(e)) < drop]] <- 0
    W[lower.tri(W)] <- t(W)[lower.tri(W)]
  }
  graph_from_adjacency_matrix(W, mode = "undirected", weighted = TRUE, diag = FALSE)
}
communities <- function(idx, drop = 0) {
  g <- link_graph(idx, drop)
  m <- as.integer(membership(cluster_louvain(g)))
  sz <- table(m)
  keep <- as.integer(names(sz[sz >= MIN_GROUP]))
  Filter(function(grp) spread(grp) <= MAX_SPREAD, lapply(keep, function(k) idx[m == k]))
}

# Validation: the same procedure on stones with a known carver
purity <- function(grp) max(table(full$carver[grp])) / length(grp)
val_groups <- communities(known)
val_purity <- vapply(val_groups, purity, 0)
# Baseline: the same number of nearest stones with a known carver around each group's type stone (geography only)
geo_purity <- vapply(val_groups, function(grp) {
  centre <- grp[which.min(rowSums(G[grp, grp]))]
  nn <- known[order(K[centre, known])][seq_along(grp)]
  purity(nn)
}, 0)
val_sizes <- vapply(val_groups, length, 0)

unk <- which(is.na(full$carver) & full$has_carver == 0)
groups <- communities(unk)
groups <- groups[order(-vapply(groups, length, 0))]

# Stability: drop 20 % of the links at random and see whether the group comes back (best Jaccard match)
stab <- if (length(groups)) {
  sims <- replicate(N_BOOT, {
    gb <- communities(unk, drop = 0.2)
    vapply(groups, function(grp) if (!length(gb)) 0 else
      max(vapply(gb, function(h) length(intersect(grp, h)) / length(union(grp, h)), 0)), 0)
  })
  if (is.null(dim(sims))) mean(sims) else rowMeans(sims)
} else numeric(0)

# ---- describe each group ------------------------------------------------------------------------------------------
pred <- tryCatch(fromJSON(file.path(cdir, "attribution.json"))$predictions, error = function(e) NULL)
known_carvers <- names(carver_n[carver_n >= MIN_CARVER])
cat_cols_hand <- c("style_short", tc, fcols)
label_of <- function(col) {
  if (col == "style_short") return(tr("Stilgrupp", "Style group"))
  if (col %in% names(TRAIT_LABELS)) return(trait_label(col))
  if (identical(LANG, "en") && col %in% names(FORMULA_LABELS_EN)) return(FORMULA_LABELS_EN[[col]])
  c(formula_raising = "Resarformel", formula_monument = "Monument", formula_order = "Ordföljd",
    formula_signature = "Ristarsignatur", formula_prayer = "Bön")[[col]]
}
# "Vagnhärads sn (nu Trosa-Vagnhärad)" -> "Vagnhäradsristaren", "Grästorps köping (Tengene sn)" -> "Grästorpsristaren"
work_name <- function(parish) {
  p <- trimws(gsub("\\s*\\(.*?\\)", "", parish))
  p <- trimws(gsub("\\s+(sn|socken|köping|stad|landsförs\\.?)$", "", p))
  if (grepl(" ", p)) paste0(p, "-", tr("ristaren", "carver")) else paste0(p, tr("ristaren", " carver"))
}

desc <- lapply(seq_along(groups), function(i) {
  grp <- groups[[i]]
  type_i <- grp[which.min(rowSums(G[grp, grp]))]
  within <- mean(G[grp, grp][upper.tri(G[grp, grp])])
  # The area: other stones within 50 km of the type stone
  area <- setdiff(which(K[type_i, ] <= NEAR_CARVER_KM), grp)
  marks <- bind_rows(lapply(cat_cols_hand, function(col) {
    v <- as.character(full[[col]]); ok_g <- !is.na(v[grp]); ok_a <- !is.na(v[area])
    if (sum(ok_g) < 3 || sum(ok_a) < 5) return(NULL)
    lv <- names(sort(table(v[grp][ok_g]), decreasing = TRUE))[1]
    sg <- mean(v[grp][ok_g] == lv); sa <- mean(v[area][ok_a] == lv)
    if (lv %in% c("ingen", "ej bestämbar", "nej")) return(NULL)
    data.frame(feature = paste0(label_of(col), ": ", trv(lv)), share_group = r3(sg), share_area = r3(sa))
  }))
  if (nrow(marks)) marks <- marks %>% filter(share_group >= 0.5, share_group - share_area >= 0.25) %>%
    arrange(-(share_group - share_area)) %>% head(6)
  # Known carvers nearby: how close are their stones in the carver's hand?
  near_c <- bind_rows(lapply(known_carvers, function(cv) {
    cs <- which(full$carver == cv)
    if (!any(K[type_i, cs] <= NEAR_CARVER_KM)) return(NULL)
    data.frame(carver = cv, n = length(cs), dist = mean(G[grp, cs]), km = r1(min(K[type_i, cs])))
  }))
  nearest <- if (nrow(near_c)) near_c[which.min(near_c$dist), ] else NULL
  similar <- !is.null(nearest) && nearest$dist <= median(d_same)
  # The attribution model's suggestions for the group's stones (only stones near the model's training stones)
  model <- NULL
  if (!is.null(pred) && length(pred)) {
    pg <- pred[pred$signum %in% full$signum[grp], ]
    if (nrow(pg)) {
      top <- names(sort(table(pg$top), decreasing = TRUE))[1]
      model <- list(n = nrow(pg), carver = top, share = r3(mean(pg$top == top & pg$p >= 0.5)),
                    mean_p = r3(mean(pg$p[pg$top == top])))
    }
  }
  model_says <- !is.null(model) && model$n >= 2 && model$share >= 0.5
  status <- if (similar || model_says) "known" else "candidate"
  styles <- table(full$style_short[grp])
  list(id = i, type_stone = full$signum[type_i], parish = full$parish_name[type_i], n = length(grp),
       spread_km = r1(spread(grp)),
       stones = full$signum[grp], parishes = names(sort(table(full$parish_name[grp]), decreasing = TRUE)),
       provinces = names(sort(table(full$province[grp]), decreasing = TRUE)),
       styles = if (length(styles)) data.frame(style = names(styles), n = as.integer(styles)) else NULL,
       within = r3(within), stability = r3(stab[i]), marks = marks,
       nearest_carver = if (!is.null(nearest)) list(carver = nearest$carver, n = nearest$n, dist = r3(nearest$dist),
                                                    km = nearest$km, as_close_as_same_carver = similar) else NULL,
       model = model, status = status,
       centre = list(lat = r3(mean(full$lat[grp])), lon = r3(mean(full$lon[grp]))))
})

# Working names for candidates; unique, and never the same as a carver in Rundata
taken <- unique(c(na.omit(d$carver), unlist(strsplit(na.omit(d$carvers_all), ";"))))
used <- character(0)
for (i in seq_along(desc)) {
  if (desc[[i]]$status != "candidate") { desc[[i]]$name <- NULL; next }
  base <- work_name(desc[[i]]$parish); nm <- base; k <- 2
  while (nm %in% c(used, taken)) { nm <- paste(base, as.roman(k)); k <- k + 1 }
  used <- c(used, nm); desc[[i]]$name <- nm
}

# ---- figure -------------------------------------------------------------------------------------------------------
fig_map <- NULL
if (length(desc)) {
  pts <- bind_rows(lapply(desc, function(g) data.frame(id = g$id, status = g$status,
                                                      x = full$x[match(g$stones, full$signum)],
                                                      y = full$y[match(g$stones, full$signum)])))
  lab <- pts %>% group_by(id, status) %>% summarise(x = mean(x), y = mean(y))
  wat <- tryCatch(read_water(P$water_dir), error = function(e) NULL)
  p <- ggplot()
  if (!is.null(wat$land)) p <- p + geom_sf(data = st_boundary(wat$land), colour = FAINT, linewidth = 0.15)
  p <- p + geom_point(data = full, aes(x, y), colour = FAINT, size = 0.4) +
    geom_point(data = pts, aes(x, y, colour = status), size = 1.2) +
    geom_label(data = lab, aes(x, y, label = id, colour = status), size = 2.4, linewidth = 0.2,
               label.padding = unit(0.1, "lines"), fill = "white", show.legend = FALSE) +
    scale_colour_manual(values = c(candidate = ACCENT, known = SERIES[1]),
                        labels = c(candidate = tr("möjlig okänd ristare", "possible unknown carver"),
                                   known = tr("liknar en känd ristare", "resembles a known carver")), name = NULL) +
    labs(title = tr("Grupper av stenar utan ristare", "Groups of stones without a carver"),
         subtitle = tr("Numren hänvisar till tabellen; grå punkter är övriga stenar med läsbar text",
                       "Numbers refer to the table; grey points are other stones with legible text")) +
    theme_map()
  if (!is.null(wat$land)) p <- p + coord_sf(crs = SWEREF, xlim = range(full$x), ylim = range(full$y), datum = NA)
  else p <- p + coord_equal()
  fig_map <- save_fig(p, out, "okanda_ristare.png", 7, 8)
}

result <- list(
  n_stones = nrow(full), n_unattributed = length(unk), n_known = length(known),
  calibration = list(threshold = r3(THRESH), link_km = LINK_KM, lr_min = LR_MIN, lr = r1(crow$lr), tpr = r3(crow$tpr),
                     fpr = r3(crow$fpr), max_spread_km = r1(MAX_SPREAD), median_carver_spread_km = r1(median(carver_spread)),
                     precision = r3(precision), n_same_pairs = length(d_same), n_diff_pairs = length(d_diff),
                     median_same = r3(median(d_same)), median_diff = r3(median(d_diff))),
  validation = list(n_groups = length(val_groups), n_stones = sum(val_sizes),
                    purity = if (length(val_groups)) r3(weighted.mean(val_purity, val_sizes)) else NA,
                    purity_geography = if (length(val_groups)) r3(weighted.mean(geo_purity, val_sizes)) else NA,
                    share_pure = if (length(val_groups)) r3(mean(val_purity >= 0.75)) else NA),
  groups = desc, n_candidates = sum(vapply(desc, function(g) g$status == "candidate", TRUE)),
  figures = list(map = fig_map),
  method = paste(
    "Stenar med minst fem läsbara ord. Likhet i handens drag: Gowers avstånd på stilgrupp, kors, kortkvistrunor,",
    "språkdrag (stavning, skiljetecken, bindrunor), formler och runbigram – inte innehåll och plats.",
    sprintf("Gränsen för att länka två stenar kalibrerades på par av stenar med känd ristare inom %d km:", LINK_KM),
    sprintf("par under gränsen är minst %d gånger vanligare bland samma ristares par än bland olika ristares.", LR_MIN),
    "Stenar utan ristare i Rundata länkades när de låg inom avståndet och under gränsen, och grupperades med Louvain;",
    sprintf("grupper med minst %d stenar som inte är mer utspridda än 90 %% av de kända ristarnas stenar", MIN_GROUP),
    "(median till mitten) redovisas. Förfarandet prövades på stenar med känd ristare (som om ristaren",
    "vore okänd) och jämfördes med grupper av lika många närliggande stenar; avståndet och gränsen valdes efter den",
    "valideringen (15–30 km, kvot 4–12), vilket gör att den kan överskatta träffsäkerheten något. Stabilitet: andel av gruppen som",
    sprintf("återkommer (Jaccard) när 20 %% av länkarna tas bort, %d gånger. En grupp räknas som lik en känd ristare", N_BOOT),
    sprintf("när ristarens stenar inom %d km i genomsnitt ligger lika nära gruppen som två stenar av samma ristare", NEAR_CARVER_KM),
    "brukar göra (medianen), eller när attribueringsmodellen föreslår samma ristare med minst 50 % för hälften av",
    "gruppens stenar. Övriga grupper får ett arbetsnamn efter typstenens socken; namnet är en etikett för gruppen, inte",
    "ett påstående om en person, och gruppen kan lika gärna vara en verkstad eller flera ristare i samma tradition."
  )
)
write_result(result, out, "anonymous")
