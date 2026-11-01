# Två artikelkartor ur kartdata.json (kartdata.py), på svenska och engelska. Kartunderlag: Natural Earth.
#   Rscript --vanilla utdata/blogg/artikelfigurer/artikelkartor.R
suppressPackageStartupMessages({ library(sf); library(ggplot2); library(jsonlite); library(ggrepel); library(patchwork) })
sf_use_s2(FALSE)
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
root <- normalizePath(file.path(here, "..", "..", ".."))
ne <- file.path(root, "data", "cache", "r", "naturalearth")
K <- fromJSON(file.path(here, "kartdata.json"))
box <- st_as_sfc(st_bbox(c(xmin = 4, ymin = 52, xmax = 26, ymax = 67), crs = st_crs(4326)))
layer <- function(name) {
  f <- list.files(file.path(ne, name), pattern = "\\.shp$", full.names = TRUE)[1]
  x <- st_make_valid(st_zm(st_read(f, quiet = TRUE)))
  st_transform(suppressWarnings(suppressMessages(st_intersection(st_geometry(x), box))), 3006)
}
land <- layer("land"); lakes <- c(layer("lakes"), layer("lakes_europe"))
to_sf <- function(d) st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), 3006)
view <- st_bbox(st_transform(st_as_sfc(st_bbox(c(xmin = 10.9, ymin = 55.25, xmax = 20.2, ymax = 63.5), crs = st_crs(4326))), 3006))
INK <- "#1e293b"; ACCENT <- "#b7410e"; MUTED <- "#64748b"
base <- function() list(
  geom_sf(data = land, fill = "#f4f4f2", colour = "#94a3b8", linewidth = 0.25),
  geom_sf(data = lakes, fill = "white", colour = "#cbd5e1", linewidth = 0.15))
theme_k <- function() theme_void(base_size = 11) +
  theme(plot.background = element_rect(fill = "white", colour = NA),
        plot.title = element_text(face = "bold", colour = INK, margin = margin(b = 4)),
        plot.subtitle = element_text(colour = "#475569", size = 9.5, lineheight = 1.15, margin = margin(b = 8)),
        plot.caption = element_text(colour = MUTED, size = 8, hjust = 0, lineheight = 1.1),
        legend.position = "bottom", legend.text = element_text(size = 9.5), plot.margin = margin(12, 12, 10, 12))
save <- function(p, name, w = 7, h = 9) ggsave(file.path(here, name), p, width = w, height = h, dpi = 200, bg = "white")

# ---- 1. Ristarna ---------------------------------------------------------------------------------------------------------
r <- to_sf(K$ristare); r$val <- factor(ifelse(r$known, "k", "m"), levels = c("k", "m"))
r <- r[order(r$val), ]
inMal <- r$prov %in% c("U", "Sö")
nU <- sum(inMal); mU <- sum(inMal & !r$known); nO <- sum(!inMal); mO <- sum(!inMal & !r$known)
stopifnot(nU == 139, mU == 2, nO == 38, mO == 18)
for (lang in c("sv", "en")) {
  sv <- lang == "sv"
  lab <- if (sv) c(k = "ristaren finns i databasen", m = "ristaren saknas i databasen") else
    c(k = "the carver is in the database", m = "the carver is missing from the database")
  p <- ggplot() + base() +
    geom_sf(data = r, aes(colour = val, size = val), alpha = 0.9) +
    scale_colour_manual(values = c(k = "#94a3b8", m = ACCENT), labels = lab, name = NULL) +
    scale_size_manual(values = c(k = 1.3, m = 2.6), labels = lab, name = NULL) +
    coord_sf(xlim = c(view["xmin"], view["xmax"]), ylim = c(view["ymin"], view["ymax"]), expand = FALSE, datum = NA) +
    labs(title = if (sv) "Runstenar där ristaren signerade: finns han i databasen?" else
                   "Runestones the carver signed: is he in the database?",
         subtitle = if (sv) sprintf("Varje punkt är en runsten med ristarsignatur (%d stenar).\nUppland och Södermanland: ristaren saknas på %d av %d. Övriga Sverige: på %d av %d.", nrow(r), mU, nU, mO, nO) else
                      sprintf("Each point is a runestone with a carver's signature (%d stones).\nUppland and Södermanland: the carver is missing on %d of %d. Rest of Sweden: on %d of %d.", nrow(r), mU, nU, mO, nO),
         caption = if (sv) "Karta: Vitki, ur Källström (2007, Bilaga 1, signaturer av typ B:1–2) och Samnordisk runtextdatabas (Rundata 3.1).\nKustlinjer och sjöar: Natural Earth." else
                     "Map: Vitki, from Källström (2007, Appendix 1, signatures of type B:1–2) and the Scandinavian Runic-text Database (Rundata 3.1).\nCoastlines and lakes: Natural Earth.") +
    theme_k()
  save(p, paste0("ristare_karta_", lang, ".png"))
}

# ---- 2. Döttrarna --------------------------------------------------------------------------------------------------------
bg <- to_sf(K$bakgrund); d <- to_sf(K$dottrar)
d$val <- factor(ifelse(d$mother, "m", "f"), levels = c("m", "f"))
stopifnot(nrow(d) == 14, sum(d$mother) == 7)
xy <- st_coordinates(d); d$x <- xy[, 1]; d$y <- xy[, 2]
zx <- st_bbox(st_transform(st_as_sfc(st_bbox(c(xmin = 17.0, ymin = 59.25, xmax = 18.75, ymax = 60.15), crs = st_crs(4326))), 3006))
inz <- d$x > zx["xmin"] & d$x < zx["xmax"] & d$y > zx["ymin"] & d$y < zx["ymax"]
stopifnot(all(inz == startsWith(d$signum, "U ")))
for (lang in c("sv", "en")) {
  sv <- lang == "sv"
  lab <- if (sv) c(m = "modern är med och reser stenen", f = "utan modern") else c(m = "the mother helps raise the stone", f = "without the mother")
  pts <- function(z) list(
    geom_sf(data = bg, colour = "#cbd5e1", size = if (z) 0.9 else 0.45),
    geom_sf(data = d, aes(shape = val), colour = ACCENT, fill = ACCENT, size = 3, stroke = 1),
    scale_shape_manual(values = c(m = 21, f = 1), labels = lab, name = NULL),
    geom_text_repel(data = d[if (z) inz else !inz, ], aes(x, y, label = signum), size = 3.1, colour = INK, min.segment.length = 0,
                    segment.colour = "#94a3b8", box.padding = 0.5, point.padding = 0.3, max.overlaps = 50, seed = 2026))
  pm <- ggplot() + base() + pts(FALSE) +
    annotate("rect", xmin = zx["xmin"], xmax = zx["xmax"], ymin = zx["ymin"], ymax = zx["ymax"], fill = NA, colour = INK, linewidth = 0.5) +
    coord_sf(xlim = c(view["xmin"], view["xmax"]), ylim = c(view["ymin"], 6900000), expand = FALSE, datum = NA) + theme_k() +
    theme(legend.position = "none")
  pz <- ggplot() + base() + pts(TRUE) +
    coord_sf(xlim = c(zx["xmin"], zx["xmax"]), ylim = c(zx["ymin"], zx["ymax"]), expand = FALSE, datum = NA) +
    labs(subtitle = if (sv) "Uppland, rutan på kartan" else "Uppland, the box on the map") + theme_k() +
    theme(panel.border = element_rect(fill = NA, colour = INK, linewidth = 0.5))
  p <- (pm | pz) + patchwork::plot_layout(widths = c(1, 1.15), guides = "collect") +
    patchwork::plot_annotation(
      title = if (sv) "De fjorton runstenarna efter döttrar" else "The fourteen runestones for daughters",
      subtitle = if (sv) sprintf("Fylld punkt: modern är med och reser stenen (%d). Ring: utan modern (%d). Grå: alla andra vikingatida runstenar i Sverige.", sum(d$mother), sum(!d$mother)) else
                   sprintf("Filled point: the mother helps raise the stone (%d). Ring: without the mother (%d). Grey: all other Viking-age runestones in Sweden.", sum(d$mother), sum(!d$mother)),
      caption = if (sv) "Karta: Vitki, ur Samnordisk runtextdatabas; stenarna efter döttrar genomgångna för hand.\nKustlinjer och sjöar: Natural Earth." else
                  "Map: Vitki, from the Scandinavian Runic-text Database; the stones for daughters read one by one.\nCoastlines and lakes: Natural Earth.",
      theme = theme_k()) & theme(legend.position = "bottom")
  save(p, paste0("dottrar_karta_", lang, ".png"), 11, 7.6)
}
message("kartor klara")
