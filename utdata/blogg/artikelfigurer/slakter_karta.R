# Karta till artikeln om släkterna: de 42 släkterna (stenar som säkra länkar knyter ihop, data/links.json) med
# länkarna som streck, över alla svenska vikingatida runstenar, och Uppland i närbild. Svenska och engelska.
#   Rscript --vanilla utdata/blogg/artikelfigurer/slakter_karta.R
suppressPackageStartupMessages({ library(sf); library(ggplot2); library(jsonlite); library(patchwork) })
sf_use_s2(FALSE)
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
root <- normalizePath(file.path(here, "..", "..", ".."))
ne <- file.path(root, "data", "cache", "r", "naturalearth")
K <- fromJSON(file.path(here, "slakter_karta.json"))
box <- st_as_sfc(st_bbox(c(xmin = 4, ymin = 52, xmax = 26, ymax = 67), crs = st_crs(4326)))
layer <- function(name) {
  f <- list.files(file.path(ne, name), pattern = "\\.shp$", full.names = TRUE)[1]
  x <- st_make_valid(st_zm(st_read(f, quiet = TRUE)))
  st_transform(suppressWarnings(suppressMessages(st_intersection(st_geometry(x), box))), 3006)
}
land <- layer("land"); lakes <- c(layer("lakes"), layer("lakes_europe"))
to_sf <- function(d, lon = "lon", lat = "lat") st_transform(st_as_sf(d, coords = c(lon, lat), crs = 4326), 3006)
bg <- to_sf(K$bakgrund); st <- to_sf(K$stones)
la <- st_coordinates(to_sf(K$lines, "lon_a", "lat_a")); lb <- st_coordinates(to_sf(K$lines, "lon_b", "lat_b"))
seg <- data.frame(x = la[, 1], y = la[, 2], xend = lb[, 1], yend = lb[, 2])
xy <- st_coordinates(st); st$x <- xy[, 1]; st$y <- xy[, 2]
st$big <- factor(ifelse(st$size >= 3, "3", "2"), levels = c("2", "3"))
view <- st_bbox(st_transform(st_as_sfc(st_bbox(c(xmin = 10.9, ymin = 55.25, xmax = 20.2, ymax = 63.0), crs = st_crs(4326))), 3006))
zx <- st_bbox(st_transform(st_as_sfc(st_bbox(c(xmin = 16.9, ymin = 59.25, xmax = 18.9, ymax = 60.3), crs = st_crs(4326))), 3006))
INK <- "#1e293b"; ACCENT <- "#b7410e"; MUTED <- "#64748b"
theme_k <- function() theme_void(base_size = 11) +
  theme(plot.background = element_rect(fill = "white", colour = NA), legend.position = "bottom",
        plot.title = element_text(face = "bold", colour = INK, margin = margin(b = 4)),
        plot.subtitle = element_text(colour = "#475569", size = 9.5, lineheight = 1.15, margin = margin(b = 8)),
        plot.caption = element_text(colour = MUTED, size = 8, hjust = 0, lineheight = 1.1), plot.margin = margin(12, 12, 10, 12))
for (lang in c("sv", "en")) {
  sv <- lang == "sv"
  lab <- if (sv) c("2" = "släkt på två stenar", "3" = "släkt på tre eller fyra stenar") else c("2" = "family on two stones", "3" = "family on three or four stones")
  panel <- function(z) ggplot() +
    geom_sf(data = land, fill = "#f4f4f2", colour = "#94a3b8", linewidth = 0.25) +
    geom_sf(data = lakes, fill = "white", colour = "#cbd5e1", linewidth = 0.15) +
    geom_sf(data = bg, colour = "#d6dbe1", size = if (z) 0.8 else 0.4) +
    geom_segment(data = seg, aes(x, y, xend = xend, yend = yend), colour = ACCENT, linewidth = if (z) 0.8 else 0.5) +
    geom_point(data = st, aes(x, y, size = big), colour = ACCENT, fill = "white", shape = 21, stroke = 0.9) +
    scale_size_manual(values = c("2" = 1.9, "3" = 3), labels = lab, name = NULL) +
    coord_sf(xlim = if (z) c(zx["xmin"], zx["xmax"]) else c(view["xmin"], view["xmax"]),
             ylim = if (z) c(zx["ymin"], zx["ymax"]) else c(view["ymin"], view["ymax"]), expand = FALSE, datum = NA) +
    theme_k()
  pm <- panel(FALSE) + annotate("rect", xmin = zx["xmin"], xmax = zx["xmax"], ymin = zx["ymin"], ymax = zx["ymax"], fill = NA, colour = INK, linewidth = 0.5) +
    theme(legend.position = "none")
  pz <- panel(TRUE) + labs(subtitle = if (sv) "Uppland och Södermanland, rutan på kartan" else "Uppland and Södermanland, the box on the map") +
    theme(panel.border = element_rect(fill = NA, colour = INK, linewidth = 0.5))
  p <- (pm | pz) + plot_layout(widths = c(1, 1.15), guides = "collect") +
    plot_annotation(
      title = if (sv) sprintf("%d släkter som går att följa över flera runstenar", K$n_families) else sprintf("%d families that can be followed across several runestones", K$n_families),
      subtitle = if (sv) sprintf("Strecken förenar stenar som nämner samma personer oftare än slumpen ger på samma avstånd (%d stenar). Grå: övriga vikingatida runstenar.", K$n_stones) else
                   sprintf("The lines join stones that name the same people more often than chance gives at the same distance (%d stones). Grey: the other Viking-age runestones.", K$n_stones),
      caption = if (sv) "Karta: Vitki, ur Samnordisk runtextdatabas; kustlinjer och sjöar: Natural Earth." else "Map: Vitki, from the Scandinavian Runic-text Database; coastlines and lakes: Natural Earth.",
      theme = theme_k()) & theme(legend.position = "bottom")
  ggsave(file.path(here, paste0("slakter_karta_", lang, ".png")), p, width = 11, height = 7.4, dpi = 200, bg = "white")
}
message("klar")
