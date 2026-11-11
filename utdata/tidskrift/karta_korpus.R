# Korpus nr 1, helsideskartan "Var stenarna står": varje svensk vikingatida runsten i Rundata som en prick,
# försvunna stenar i rost. Kartan ritas i A4 + 3 mm utfall (216 x 303 mm) i 320 dpi så att samma bild fungerar
# på skärm (beskuren till A4) och i tryck (med utfall). Punkterna skrivs av bygg_tidskrift.py (bilder/karta_punkter.json).
# Ingen text i bilden: rubrik, teckenförklaring och kredit sätts i tidskriftens HTML på båda språken.
#   Rscript --vanilla utdata/tidskrift/karta_korpus.R
suppressPackageStartupMessages({ library(sf); library(ggplot2); library(jsonlite) })
sf_use_s2(FALSE)
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
root <- normalizePath(file.path(here, "..", ".."))
ne <- file.path(root, "data", "cache", "r", "naturalearth")
P <- fromJSON(file.path(here, "bilder", "karta_punkter.json"))
box <- st_as_sfc(st_bbox(c(xmin = 4, ymin = 52, xmax = 30, ymax = 68), crs = st_crs(4326)))
layer <- function(name) {
  f <- list.files(file.path(ne, name), pattern = "\\.shp$", full.names = TRUE)[1]
  x <- st_make_valid(st_zm(st_read(f, quiet = TRUE)))
  st_transform(suppressWarnings(suppressMessages(st_intersection(st_geometry(x), box))), 3006)
}
land <- layer("land"); lakes <- c(layer("lakes"), layer("lakes_europe"))
pts <- st_transform(st_as_sf(P, coords = c("lon", "lat"), crs = 4326), 3006)
pts <- pts[order(pts$lost), ]  # försvunna överst
# Utsnittet: 216 x 303 mm. Höjden 6 080–7 070 km norr (Skåne till Jämtland); bredden följer sidans format.
y0 <- 6080000; y1 <- 7070000; w <- (y1 - y0) * 216 / 303; x0 <- 250000; x1 <- x0 + w
SEA <- "#e4e9ec"; LAND <- "#fbfaf7"; INK <- "#1d2226"; RUST <- "#b7410e"
p <- ggplot() +
  geom_sf(data = land, fill = LAND, colour = "#b9c2c8", linewidth = 0.2) +
  geom_sf(data = lakes, fill = SEA, colour = "#c9d2d8", linewidth = 0.12) +
  geom_sf(data = pts[!pts$lost & !pts$dk, ], colour = INK, size = 1.05, alpha = 0.7, stroke = 0) +
  geom_sf(data = pts[pts$lost & !pts$dk, ], colour = RUST, size = 1.25, alpha = 0.95, stroke = 0) +
  # Stenar i dagens Sverige med danska signum (Skåne, Blekinge): ringar, räknas inte i korpusen.
  geom_sf(data = pts[pts$dk, ], shape = 21, fill = NA, colour = INK, size = 1.5, stroke = 0.45) +
  coord_sf(xlim = c(x0, x1), ylim = c(y0, y1), expand = FALSE, datum = NA) +
  theme_void() + theme(plot.background = element_rect(fill = SEA, colour = NA),
                       panel.background = element_rect(fill = SEA, colour = NA), plot.margin = margin(0, 0, 0, 0))
ggsave(file.path(here, "bilder", "karta_alla.png"), p, width = 216, height = 303, units = "mm", dpi = 320, bg = SEA,
       device = ragg::agg_png)
cat("karta_alla.png:", sum(!pts$dk), "svenska stenar,", sum(pts$lost & !pts$dk), "försvunna,", sum(pts$dk), "danska ringar\n")
