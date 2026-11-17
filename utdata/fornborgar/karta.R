# Karta till fornborgsartikeln: Mälardalen med vattnet omkring år 450 (SGU, issjohav_1500, hav och sjö) och i dag
# (issjohav_1), och fornborgarna ur Kulturmiljöregistret. Sparar karta_malardalen_<sv|en>.png.
#   Rscript utdata/fornborgar/karta.R
suppressPackageStartupMessages({library(sf); library(ggplot2)})
sf_use_s2(FALSE)
here <- local({f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)); dirname(normalizePath(f[1]))})
SW <- "EPSG:3006"
bb <- c(xmin = 560000, ymin = 6530000, xmax = 720000, ymax = 6660000)
win <- st_as_sfc(st_bbox(bb, crs = st_crs(SW)))
rd <- function(f, l) {w <- st_read(f, l, wkt_filter = st_as_text(win), quiet = TRUE); w <- w[w$code %in% c(1, 4), ]; st_crs(w) <- SW; st_intersection(st_union(w), win)}
then <- rd("/Volumes/2TB/cache/strand/sgu/strandforskjutning_1000_1900.gpkg", "issjohav_1500")
now <- rd("/Volumes/2TB/cache/strand/sgu/strandforskjutning_1_900.gpkg", "issjohav_1")
f <- read.csv("/Volumes/2TB/Antigrvity/Runes/downloads/fornborgar/fornborgar.csv", fileEncoding = "UTF-8")
f <- f[!is.na(f$lat), ]
fp <- st_transform(st_as_sf(f, coords = c("lon", "lat"), crs = 4326), SW)
fp <- fp[lengths(st_intersects(fp, win)) > 0, ]
for (lang in c("sv", "en")) {
  sv <- lang == "sv"
  g <- ggplot() +
    geom_sf(data = win, fill = "#f1ede4", colour = NA) +
    geom_sf(data = then, fill = "#bcd3e6", colour = NA) +
    geom_sf(data = now, fill = "#7fa7c9", colour = NA) +
    geom_sf(data = fp, colour = "white", fill = "#b7410e", shape = 21, size = 1.6, stroke = 0.3) +
    coord_sf(expand = FALSE, datum = NA) +
    labs(title = if (sv) "Fornborgarna i Mälardalen och vattnet omkring år 450" else "The hillforts of the Mälar valley and the water around AD 450",
         caption = if (sv) paste0("Ljusblått: vatten omkring år 450 som är land i dag. Mörkblått: vatten i dag. Röda prickar: ", nrow(fp),
                                  " fornborgar.\nKälla: SGU, strandförskjutningsmodellen (CC BY 4.0); Riksantikvarieämbetet, Kulturmiljöregistret. Bild: Vitki.")
                    else paste0("Light blue: water around AD 450 that is land today. Dark blue: water today. Red dots: ", nrow(fp),
                                " hillforts.\nSource: SGU shoreline displacement model (CC BY 4.0); Swedish National Heritage Board, Kulturmiljöregistret. Image: Vitki.")) +
    theme_void(base_family = "DejaVu Sans") +
    theme(plot.title = element_text(size = 12, colour = "#0f172a", margin = margin(b = 6)),
          plot.caption = element_text(size = 7, colour = "#475569", hjust = 0, lineheight = 1.1),
          plot.background = element_rect(fill = "white", colour = NA), plot.margin = margin(10, 10, 10, 10))
  ggsave(file.path(here, paste0("karta_malardalen_", lang, ".png")), g, width = 8, height = 7, dpi = 200)
}
cat(nrow(fp), "borgar på kartan\n")
