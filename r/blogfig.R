# Figures for the articles, in place of links into the app (the public website has only the articles and the landing
# page; the app runs locally): the map tool's time view of a pattern, a map of the few stones with a rare pattern, and
# the change model's curves for chosen features. Called from src/blog_maps.py, one figure per call and language.
#
#   Rscript blogfig.R params.json outdir
#   params: kind ("timemap" | "points" | "curves"), langs, corpus, water_dir, key, label, label_en, split, hex_km,
#           min_stones (timemap); key, label, label_en (points); change, keys, labels, labels_en (curves); name
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(sf) })
sf_use_s2(FALSE)

a <- cli_args(); P <- a$params; out <- a$out
langs <- P$langs %||% "sv"
wrap <- function(x, w = 110) paste(strwrap(x, w), collapse = "\n")
fmt <- function(n) format(n, big.mark = if (identical(LANG, "en")) "," else " ")

# The map tool's share classes (web/src/lib/patternMap.ts), so that the figure looks like the map in the app
CLASSES <- c("0–20 %" = "#b7d3f6", "20–40 %" = "#86b6ef", "40–60 %" = "#3987e5", "60–80 %" = "#1c5cab", "80–100 %" = "#0d366b")
TOO_FEW <- "#e7e5e0"
SPLITS <- list("1020" = c("RAK", "Fp–Pr5"), "1050" = c("RAK–Pr2", "Pr3–Pr5"), "1075" = c("RAK–Pr3", "Pr4–Pr5"))

land_outline <- function() {
  wat <- tryCatch(read_water(P$water_dir), error = function(e) NULL)
  if (!is.null(wat$land)) st_boundary(wat$land) else NULL
}

# The view: where nearly all the stones are (a few far to the north would otherwise shrink the map)
view_of <- function(pts) {
  xy <- st_coordinates(pts)
  list(x = quantile(xy[, 1], c(0.01, 0.99)) + c(-30000, 30000), y = quantile(xy[, 2], c(0.01, 0.99)) + c(-30000, 30000))
}

timemap <- function() {
  d <- read_corpus(P$corpus)
  col <- paste0("pm_", P$key)
  d <- d[!is.na(d$lat) & !is.na(d$lon) & !is.na(d[[col]]) & !is.na(d$style_from), ]
  d$year <- (d$style_from + d$style_to) / 2
  split <- P$split %||% 1050
  sp <- SPLITS[[as.character(split)]] %||% SPLITS[["1050"]]
  hex <- (P$hex_km %||% 20) * 1000
  minn <- P$min_stones %||% 5
  pts <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), SWEREF)
  grid <- st_sf(geometry = st_make_grid(st_as_sfc(st_bbox(pts)), cellsize = hex, square = FALSE))
  early <- d$year < split
  per <- c(tr(sprintf("Före ca %d (%s)", split, sp[1]), sprintf("Before c. %d (%s)", split, sp[1])),
           tr(sprintf("Efter ca %d (%s)", split, sp[2]), sprintf("After c. %d (%s)", split, sp[2])))
  cells <- do.call(rbind, lapply(1:2, function(i) {
    sub <- pts[if (i == 1) early else !early, ]
    hits <- st_intersects(grid, sub)
    g <- grid
    g$n <- lengths(hits)
    g$k <- vapply(hits, function(ix) sum(sub[[col]][ix]), numeric(1))
    g <- g[g$n > 0, ]
    share <- g$k / g$n
    g$cls <- ifelse(g$n < minn, "few", names(CLASSES)[pmin(5, findInterval(share, c(0.2, 0.4, 0.6, 0.8)) + 1)])
    g$period <- sprintf("%s – %s %%, %s %s", per[i], round(100 * mean(sub[[col]])), fmt(nrow(sub)), tr("stenar", "stones"))
    g
  }))
  cells$period <- factor(cells$period, unique(cells$period))
  lab <- if (identical(LANG, "en")) P$label_en %||% P$label else P$label
  v <- view_of(pts)
  outline <- land_outline()
  values <- c(CLASSES, few = TOO_FEW)
  p <- ggplot() + geom_sf(data = cells, aes(fill = cls), colour = "white", linewidth = 0.15)
  if (!is.null(outline)) p <- p + geom_sf(data = outline, colour = MUTED, linewidth = 0.2, inherit.aes = FALSE)
  p <- p + facet_wrap(~period) +
    scale_fill_manual(values = values, breaks = c(names(CLASSES), "few"),
                      labels = c(names(CLASSES), sprintf(tr("färre än %d stenar", "fewer than %d stones"), minn)),
                      name = tr("Andel med mönstret", "Share with the pattern"), drop = FALSE) +
    coord_sf(crs = SWEREF, xlim = v$x, ylim = v$y, expand = FALSE, datum = NA) +
    labs(title = tr(sprintf("%s före och efter omkring %d", lab, split), sprintf("%s before and after about %d", lab, split)),
         subtitle = wrap(tr(sprintf("Andelen stenar med mönstret per sexkant om %d km (minst %d stenar; grått: färre). Stenar med läsbar text och daterad stilgrupp.", hex / 1000, minn),
                            sprintf("The share of stones with the pattern per %d km hexagon (at least %d stones; grey: fewer). Stones with a legible text and a dated style group.", hex / 1000, minn))),
         caption = tr("Källa: Vitkis mönsterkarta (r/blogfig.R); Samnordisk runtextdatabas (ODbL); stilgrupper efter Gräslund (2006).",
                      "Source: Vitki's pattern map (r/blogfig.R); Scandinavian Runic-text Data Base (ODbL); style groups after Gräslund (2006).")) +
    theme_map(9) + theme(legend.key.width = unit(0.7, "cm"), strip.text = element_text(size = 9))
  p <- p + guides(fill = guide_legend(nrow = 1))
  save_fig(p, out, sprintf("%s_%s.png", P$name, LANG), 9, 7)
}

points_map <- function() {
  d <- read_corpus(P$corpus)
  d <- d[!is.na(d$lat) & !is.na(d$lon), ]
  col <- paste0("pm_", P$key)
  yes <- d[!is.na(d[[col]]) & d[[col]] == 1, ]
  if (length(P$exclude)) yes <- yes[!yes$signum %in% P$exclude, ]
  all <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), SWEREF)
  ys <- st_transform(st_as_sf(yes, coords = c("lon", "lat"), crs = 4326), SWEREF)
  xy <- data.frame(st_coordinates(ys), signum = yes$signum)
  lab <- if (identical(LANG, "en")) P$label_en %||% P$label else P$label
  v <- view_of(all)
  outline <- land_outline()
  p <- ggplot() + geom_sf(data = all, colour = FAINT, size = 0.5)
  if (!is.null(outline)) p <- p + geom_sf(data = outline, colour = MUTED, linewidth = 0.2, inherit.aes = FALSE)
  p <- p + geom_point(data = xy, aes(X, Y), colour = ACCENT, size = 2.6) +
    ggrepel::geom_text_repel(data = xy, aes(X, Y, label = signum), colour = INK, size = 3.2, fontface = "bold",
                             min.segment.length = 0, seed = 1, box.padding = 0.5) +
    coord_sf(crs = SWEREF, xlim = v$x, ylim = v$y, expand = FALSE, datum = NA) +
    labs(title = lab,
         subtitle = wrap(tr(sprintf("%d stenar med mönstret (rött) bland alla %s runstenar med känd plats (grått).", nrow(yes), fmt(nrow(d))),
                            sprintf("%d stones with the pattern (red) among all %s runestones with a known place (grey).", nrow(yes), fmt(nrow(d))))),
         caption = tr("Källa: Vitkis mönsterkarta (r/blogfig.R); Samnordisk runtextdatabas (ODbL).",
                      "Source: Vitki's pattern map (r/blogfig.R); Scandinavian Runic-text Data Base (ODbL).")) +
    theme_map(9)
  save_fig(p, out, sprintf("%s_%s.png", P$name, LANG), 6.5, 7)
}

curves <- function() {
  ch <- jsonlite::fromJSON(P$change, simplifyVector = FALSE)
  feats <- Filter(function(f) f$key %in% P$keys, ch$features)
  labs_ <- if (identical(LANG, "en")) P$labels_en %||% P$labels else P$labels
  name_of <- function(k) labs_[[match(k, P$keys)]]
  ord <- vapply(P$keys, name_of, "")
  pts <- do.call(rbind, lapply(feats, function(f) do.call(rbind, lapply(f$time$by_style, function(b)
    data.frame(feature = name_of(f$key), year = b$year, share = b$share, lo = b$lo, hi = b$hi, n = b$n)))))
  cur <- do.call(rbind, lapply(feats, function(f) do.call(rbind, lapply(f$time$curve, function(c)
    data.frame(feature = name_of(f$key), year = c$year, share = c$share, lo = c$lo, hi = c$hi)))))
  pts$feature <- factor(pts$feature, ord); cur$feature <- factor(cur$feature, ord)
  p <- ggplot() +
    geom_ribbon(data = cur, aes(year, ymin = lo, ymax = hi), fill = SERIES[1], alpha = 0.12) +
    geom_line(data = cur, aes(year, share), colour = SERIES[1], linewidth = 0.9) +
    geom_linerange(data = pts, aes(year, ymin = lo, ymax = hi), colour = INK, linewidth = 0.35) +
    geom_point(data = pts, aes(year, share, size = n), colour = INK) +
    facet_wrap(~feature, nrow = 1) +
    scale_y_continuous(labels = function(x) paste0(round(100 * x), " %"), limits = c(0, NA)) +
    scale_size_area(max_size = 3, guide = "none") +
    labs(x = tr("Stilgruppens mittår", "Mid-year of the style group"), y = NULL,
         title = tr("Modellens kurvor", "The model's curves"),
         subtitle = wrap(tr("Punkter: andelen per stilgrupp med 95 % intervall (större punkt: fler stenar). Linje och band: andelen med plats och ristare konstanta, med 95 % intervall.",
                            "Points: the share per style group with a 95 % interval (larger point: more stones). Line and band: the share with place and carver held constant, with a 95 % interval.")),
         caption = tr("Källa: Vitkis korpusanalys i R (change.R; mgcv); Samnordisk runtextdatabas (ODbL); stilgrupper efter Gräslund (2006).",
                      "Source: Vitki's corpus analysis in R (change.R; mgcv); Scandinavian Runic-text Data Base (ODbL); style groups after Gräslund (2006).")) +
    theme_runor(9)
  save_fig(p, out, sprintf("%s_%s.png", P$name, LANG), 3 * length(P$keys) + 1, 3.8)
}

files <- list()
for (l in langs) {
  LANG <<- l
  files[[l]] <- switch(P$kind, timemap = timemap(), points = points_map(), curves = curves())
}
writeLines(jsonlite::toJSON(files, auto_unbox = TRUE), file.path(out, "blogfig.json"))
