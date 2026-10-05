# En sten mot korpusanalyserna: läget i förhållande till kandidaternas områden och till vatten, gruppen i
# klustringen och närmaste grannar, modellens sannolikheter och inskriftens formler jämförda med kandidaternas.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({
  library(sf)
  library(cluster)
})
sf_use_s2(FALSE)

a <- cli_args(); P <- a$params; out <- a$out; cdir <- P$corpus_dir
d <- read_corpus(P$corpus)
signum <- P$signum
row <- d[d$signum == signum, ]
if (!nrow(row)) stop("Stenen finns inte i korpusen (svenska vikingatida runstenar): ", signum)
cands <- unique(as.character(unlist(P$candidates)))
cands <- cands[nzchar(cands)]
has <- function(f) file.exists(file.path(cdir, f))
res <- list(signum = signum, place = row$place, province = row$province, candidates = cands, figures = list())

# ---- model -------------------------------------------------------------------------------------------------
model <- NULL
if (has("attribution_model.rds")) {
  suppressPackageStartupMessages({ library(tidymodels); library(ranger) })
  M <- readRDS(file.path(cdir, "attribution_model.rds"))
  oof <- read.csv(file.path(cdir, "attribution_oof.csv"), encoding = "UTF-8", check.names = FALSE)
  geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8")
  txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", check.names = FALSE)
  pcols <- paste0(".pred_", M$levels)
  if (signum %in% oof$signum) {
    probs <- unlist(oof[oof$signum == signum, pcols][1, ])
    source_note <- tr("korsvaliderad: sannolikheterna kommer från modeller som inte såg stenen",
                      "cross-validated: probabilities from models that did not see the stone")
  } else {
    f <- row %>% left_join(geo %>% select(signum, x, y), by = "signum") %>% left_join(txt, by = "signum") %>%
      mutate(x_km = x / 1000, y_km = y / 1000)
    f <- f[, M$cols, drop = FALSE]
    for (col in intersect(M$nominal, M$cols)) {
      v <- as.character(f[[col]])
      v[is.na(v) | !(v %in% M$train_levels[[col]])] <- "okänd"
      f[[col]] <- factor(v, levels = M$train_levels[[col]])
    }
    probs <- unlist(predict(M$final, f, type = "prob")[1, pcols])
    source_note <- tr("stenen ingick inte i träningen", "the stone was not in the training data")
  }
  names(probs) <- M$levels
  g <- geo[geo$signum == signum, ]
  near <- if (nrow(g) && !is.na(g$x)) min(sqrt((M$train_xy[, 1] - g$x)^2 + (M$train_xy[, 2] - g$y)^2)) / 1000 else NA
  o <- order(-probs)
  model <- list(
    source = source_note, near_km = r1(near), in_range = !is.na(near) && near <= M$near_km, near_limit_km = M$near_km,
    top = lapply(o[1:6], function(i) list(carver = M$levels[i], p = r3(probs[i]))),
    candidates = lapply(cands, function(cn) list(carver = cn, p = if (cn %in% M$levels) r3(probs[[cn]]) else NA,
                                                 in_model = cn %in% M$levels,
                                                 rank = if (cn %in% M$levels) which(M$levels[o] == cn) else NA)),
    rundata_carver = if (!is.na(row$carver)) row$carver else NULL
  )
  att <- fromJSON(file.path(cdir, "attribution.json"))
  model$reliability <- att$calibration$reliability
  top <- data.frame(carver = M$levels[o[1:6]], p = probs[o[1:6]])
  top$carver <- factor(top$carver, levels = rev(top$carver))
  k_c <- tr("Kandidat i syntesen", "Candidate in the synthesis"); k_o <- tr("Övriga", "Other")
  top$kind <- ifelse(as.character(top$carver) %in% cands, k_c, k_o)
  p <- ggplot(top, aes(p, carver, fill = kind)) +
    geom_col(width = 0.65) +
    geom_text(aes(label = sprintf("%.0f %%", 100 * p)), hjust = -0.2, size = 3, colour = INK) +
    scale_fill_manual(values = setNames(c(SERIES[1], FAINT), c(k_c, k_o)), name = NULL) +
    scale_x_continuous(labels = scales::percent, limits = c(0, min(1, max(top$p) * 1.25 + 0.02)), expand = c(0, 0)) +
    labs(title = sprintf(tr("Attribueringsmodellen: %s", "Attribution model: %s"), signum),
         x = tr("Sannolikhet (bland modellens ristare)", "Probability (among the model's carvers)"), y = NULL,
         subtitle = paste0("Random forest; ", source_note)) +
    theme_runor() + theme(panel.grid.major.y = element_blank())
  res$figures$model <- save_fig(p, out, "sten_modell.png", 6.5, 3.6)
  carv_model <- M$levels[o[1:3]]
} else carv_model <- character(0)
res$model <- model

# ---- geography ------------------------------------------------------------------------------------------------
if (has("geography_stones.csv") && !is.na(row$lat)) {
  geo <- read.csv(file.path(cdir, "geography_stones.csv"), encoding = "UTF-8")
  dx <- d %>% inner_join(geo, by = "signum")
  s <- dx[dx$signum == signum, ]
  show <- unique(c(cands, carv_model))
  rows <- lapply(show, function(cn) {
    g <- dx[!is.na(dx$carver) & dx$carver == cn & dx$signum != signum, ]
    if (nrow(g) < 2) return(list(carver = cn, n = nrow(g)))
    cx <- mean(g$x); cy <- mean(g$y)
    own <- sqrt((g$x - cx)^2 + (g$y - cy)^2) / 1000
    dist_c <- sqrt((s$x - cx)^2 + (s$y - cy)^2) / 1000
    nearest <- min(sqrt((g$x - s$x)^2 + (g$y - s$y)^2)) / 1000
    hull <- st_convex_hull(st_union(st_as_sf(g, coords = c("x", "y"), crs = SWEREF)))
    inside <- st_is(hull, "POLYGON") && as.numeric(st_distance(st_sfc(st_point(c(s$x, s$y)), crs = SWEREF), hull)) < 50
    list(carver = cn, n = nrow(g), centroid_km = r1(dist_c), nearest_km = r1(nearest), inside_hull = inside,
         share_farther = r3(mean(own >= dist_c)), median_own_km = r1(median(own)))
  })
  res$geography <- list(candidates = rows, water_km = r3(s$water_km), water_pct = r3(s$water_pct),
                        water_note = if (!is.na(s$water_km)) WATER_NOTE else NULL)
  # Map: the stone, up to three candidates' stones, hulls
  W <- read_water(P$water_dir)
  mc <- head(show, 3)
  cs <- dx %>% filter(carver %in% mc) %>% mutate(carver = factor(carver, levels = mc))
  near_pts <- bind_rows(s, cs %>% filter(sqrt((x - s$x)^2 + (y - s$y)^2) < 150000))
  pad <- 15000
  xl <- range(near_pts$x) + c(-pad, pad); yl <- range(near_pts$y) + c(-pad, pad)
  span <- max(diff(xl), diff(yl), 60000)
  xl <- mean(xl) + c(-span, span) / 2; yl <- mean(yl) + c(-span, span) / 2
  hulls <- bind_rows(lapply(mc, function(cn) {
    g <- cs[cs$carver == cn, ]
    if (nrow(g) < 3) return(NULL)
    h <- st_convex_hull(st_union(st_as_sf(g, coords = c("x", "y"), crs = SWEREF)))
    if (!st_is(h, "POLYGON")) return(NULL)
    cc <- st_coordinates(h)
    data.frame(carver = cn, x = cc[, 1], y = cc[, 2])
  }))
  p <- ggplot()
  if (!is.null(W) && !is.null(W$lakes)) p <- p + geom_sf(data = W$lakes, fill = "#e6eef8", colour = WATER, linewidth = 0.15)
  if (!is.null(W) && !is.null(W$coast)) p <- p + geom_sf(data = W$coast, colour = WATER, linewidth = 0.3)
  p <- p + geom_point(data = dx, aes(x, y), colour = FAINT, size = 0.5)
  if (nrow(hulls)) {
    hulls$carver <- factor(hulls$carver, levels = mc)
    p <- p + geom_polygon(data = hulls, aes(x, y, colour = carver, group = carver), fill = NA, linewidth = 0.4, show.legend = FALSE)
  }
  p <- p + geom_point(data = cs, aes(x, y, colour = carver, shape = carver), size = 1.6) +
    scale_shape_manual(values = c(16, 17, 15)[seq_along(mc)], name = tr("Säkra stenar av", "Certain stones by")) +
    geom_point(data = s, aes(x, y), shape = 23, size = 4, fill = ACCENT, colour = "white", stroke = 0.8) +
    annotate("text", x = s$x, y = s$y, label = signum, vjust = -1.3, size = 3.2, colour = INK, fontface = "bold") +
    scale_colour_manual(values = SERIES[seq_along(mc)], name = tr("Säkra stenar av", "Certain stones by")) +
    annotate("rect", xmin = xl[1] + 0.04 * diff(xl), xmax = xl[1] + 0.04 * diff(xl) + 20000, ymin = yl[1] + 0.04 * diff(yl),
             ymax = yl[1] + 0.04 * diff(yl) + 0.012 * diff(yl), fill = INK) +
    annotate("text", x = xl[1] + 0.04 * diff(xl) + 10000, y = yl[1] + 0.04 * diff(yl) + 0.04 * diff(yl), label = "20 km",
             size = 3, colour = INK) +
    coord_sf(xlim = xl, ylim = yl, crs = SWEREF, datum = NA) +
    labs(title = sprintf(tr("%s och kandidaternas stenar", "%s and the candidates' stones"), signum),
         subtitle = tr("Konvexa höljen kring varje ristares säkra stenar. Grått: övriga runstenar.",
                       "Convex hulls around each carver's certain stones. Grey: other runestones."),
         caption = tr("Källa: Samnordisk runtextdatabas; vatten: Natural Earth 1:10 milj.",
                      "Source: Scandinavian Runic-text Database; water: Natural Earth 1:10m.")) +
    theme_map()
  res$figures$map <- save_fig(p, out, "sten_karta.png", 7, 7)
}

# ---- cluster --------------------------------------------------------------------------------------------------------
if (has("clusters_model.rds")) {
  C <- readRDS(file.path(cdir, "clusters_model.rds"))
  cj <- fromJSON(file.path(cdir, "clusters.json"), simplifyVector = FALSE)
  idx <- match(signum, C$signum)
  if (is.na(idx)) {
    res$cluster <- list(included = FALSE, note = sprintf("Stenen har färre än %d bestämbara drag och ingick inte i klustringen.",
                                                         cj$min_features))
  } else {
    D <- as.matrix(daisy(C$X, metric = "gower", type = C$types))[idx, ]
    D[idx] <- NA
    o <- order(D)[1:10]
    cs <- read.csv(file.path(cdir, "clusters_stones.csv"), encoding = "UTF-8")
    me <- cs[cs$signum == signum, ]
    prof <- cj$clusters[[me$cluster]]
    res$cluster <- list(
      included = TRUE, cluster = me$cluster, k = cj$k, silhouette = r3(me$sil_width), structure = cj$structure,
      profile = prof,
      neighbours = lapply(o, function(i) list(signum = C$signum[i], distance = r3(D[i]),
                                              carver = if (!is.na(C$carver[i])) C$carver[i] else NULL,
                                              cluster = C$cluster[i])),
      neighbour_carvers = as.list(sort(table(C$carver[o]), decreasing = TRUE))
    )
    p <- ggplot(cs, aes(dim1, dim2)) +
      geom_point(colour = FAINT, size = 0.5) +
      geom_point(data = cs[cs$cluster == me$cluster, ], colour = SERIES[1], size = 0.7) +
      geom_point(data = me, shape = 23, size = 4, fill = ACCENT, colour = "white", stroke = 0.8) +
      annotate("text", x = me$dim1, y = me$dim2, label = signum, vjust = -1.3, size = 3.2, fontface = "bold", colour = INK) +
      labs(title = sprintf(tr("%s i MCA-rummet", "%s in the MCA space"), signum), x = "Dimension 1", y = "Dimension 2",
           subtitle = sprintf(tr("Stenens grupp (%d av %d) i blått; övriga klustrade stenar i grått",
                                 "The stone's group (%d of %d) in blue; other clustered stones in grey"), me$cluster, cj$k)) +
      theme_runor()
    res$figures$mca <- save_fig(p, out, "sten_mca.png", 6.5, 5)
  }
}

# ---- formulas -------------------------------------------------------------------------------------------------------------
if (has("text_features.csv")) {
  txt <- read.csv(file.path(cdir, "text_features.csv"), encoding = "UTF-8", check.names = FALSE)
  fcols <- grep("^formula_", names(txt), value = TRUE)
  labels <- c(formula_raising = "Resarformel", formula_monument = "Monument", formula_order = "Ordföljd",
              formula_signature = "Ristarsignatur", formula_prayer = "Bön")
  me <- txt[txt$signum == signum, ]
  tj <- txt %>% inner_join(d %>% select(signum, carver), by = "signum")
  res$formulas <- lapply(fcols, function(col) {
    v <- me[[col]]
    list(formula = col, label = labels[[col]], value = v,
         overall_share = r3(mean(txt[[col]] == v)),
         candidates = lapply(unique(c(cands, carv_model)), function(cn) {
           g <- tj[!is.na(tj$carver) & tj$carver == cn & tj$signum != signum, ]
           list(carver = cn, n = nrow(g), k = sum(g[[col]] == v), share = if (nrow(g)) r3(mean(g[[col]] == v)) else NA)
         }))
  })
}

# ---- chronology (Uppland seriation) ---------------------------------------------------------------------------------
if (has("chronology_stones.csv")) {
  ch <- read.csv(file.path(cdir, "chronology_stones.csv"), encoding = "UTF-8")
  cj <- fromJSON(file.path(cdir, "chronology.json"), simplifyVector = FALSE)
  me <- ch[ch$signum == signum, ]
  if (!nrow(me)) {
    res$chronology <- list(included = FALSE, region = cj$region,
                           note = if (row$province != cj$region) "Seriationen gäller Upplands runstenar; stenen står i ett annat landskap."
                                  else "Stenen har för få bestämbara drag för seriationen.")
  } else {
    res$chronology <- list(included = TRUE, region = cj$region, score = me$score, percentile = r3(mean(ch$score <= me$score)),
                           estimate = me$est, lo = me$lo, hi = me$hi, usable = cj$validation$usable,
                           rho = cj$validation$rho, mae_loo_years = cj$validation$mae_loo_years,
                           mae_naive_years = cj$validation$mae_naive_years,
                           style = if (!is.na(row$style)) row$style else NULL,
                           style_from = if (!is.na(row$style_from)) row$style_from else NULL,
                           style_to = if (!is.na(row$style_to)) row$style_to else NULL)
  }
}

write_result(res, out, "stone")
