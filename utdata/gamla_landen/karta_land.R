# Gemensam karta för delarna i serien "De gamla landen" som bygger på kartlagret Små land (web/public/geo/land.geojson):
# kusten omkring år 1000 (SGU:s strandförskjutningsmodell), landet rostfärgat och grannlanden ljust, gränserna streckade,
# landets runstenar (web/public/geo/sten_land.json + Rundata) och artikelns platser (sockenkyrkornas punkter ur ISOF).
#   Rscript utdata/gamla_landen/karta_land.R <hav1000.gpkg> <config.json> <utmapp>
# config: {"id": "gotland", "focus": ["nordertredingen", ...], "bbox": [xmin, ymin, xmax, ymax], "w": 7.5, "h": 8,
#          "title_sv": …, "title_en": …, "sub_sv": …, "sub_en": …, "labels": [{"id": …, "lon": …, "lat": …, "sv": …, "en": …}],
#          "places": [{"parish": "Fröjels sn", "province": 3, "sv": "Fröjel", "en": "Fröjel", "dx": 0, "dy": 3000}],
#          "stones": "utdata/gamla_landen/<id>_stenar.csv"}
suppressPackageStartupMessages({ library(sf); library(ggplot2); library(jsonlite) })
sf_use_s2(FALSE)
a <- commandArgs(TRUE); hav <- a[1]; cfg <- fromJSON(a[2]); out <- a[3]
view <- st_bbox(c(xmin = cfg$bbox[1], ymin = cfg$bbox[2], xmax = cfg$bbox[3], ymax = cfg$bbox[4]), crs = st_crs(4326))
vb <- st_bbox(st_transform(st_as_sfc(view), 3006)); frame <- st_as_sfc(vb)
sea <- st_intersection(st_union(st_make_valid(st_geometry(st_read(hav, quiet = TRUE)))), st_buffer(frame, 30000))
land <- st_difference(st_buffer(frame, 20000), sea)
fl <- st_make_valid(st_transform(st_read("web/public/geo/land.geojson", quiet = TRUE), 3006))
fl <- fl[lengths(st_intersects(fl, st_buffer(frame, 20000))) > 0, ]
pairs <- if (nrow(fl) > 1) combn(seq_len(nrow(fl)), 2, simplify = FALSE) else list()
edges <- do.call(c, lapply(pairs, function(ij) st_intersection(st_boundary(st_geometry(fl)[ij[1]]), st_boundary(st_geometry(fl)[ij[2]]))))
edges <- if (length(edges)) st_intersection(st_union(st_collection_extract(st_sfc(edges, crs = 3006), "LINESTRING")),
                                             st_buffer(st_union(land), -300)) else NULL
fl <- st_intersection(fl, land)
fl$here <- fl$id %in% cfg$focus
d <- read.csv(cfg$stones, stringsAsFactors = FALSE)
p <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), 3006)
ISOF <- "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/"
par <- fromJSON(file.path(ISOF, "parishes.json"))
PL <- cfg$places
pl <- do.call(rbind, lapply(seq_len(nrow(PL)), function(i) {
  m <- par[par$name == PL$parish[i] & par$province_id == PL$province[i] & !is.na(par$latitude), ]
  stopifnot(nrow(m) == 1)
  data.frame(sv = PL$sv[i], en = PL$en[i], dx = PL$dx[i], dy = PL$dy[i], lon = m$longitude, lat = m$latitude)
}))
places <- st_transform(st_as_sf(pl, coords = c("lon", "lat"), crs = 4326), 3006)
xy <- cbind(as.data.frame(st_coordinates(places)), pl[, c("sv", "en", "dx", "dy")])
LB <- cfg$labels
lab <- st_transform(st_as_sf(LB, coords = c("lon", "lat"), crs = 4326), 3006)
lxy <- cbind(as.data.frame(st_coordinates(lab)), LB[, c("sv", "en")])
draw <- function(lang) {
  sv <- lang == "sv"
  xy$n <- if (sv) xy$sv else xy$en
  lxy$n <- if (sv) lxy$sv else lxy$en
  cap <- if (sv) "Karta: Vitki, efter SGU (strandförskjutning år 1000), ISOF:s ortnamnsregister och Rundata (ODbL)."
         else "Map: Vitki, after SGU (shore displacement AD 1000), ISOF place-name register and Rundata (ODbL)."
  g <- ggplot() +
    geom_sf(data = st_as_sfc(st_bbox(st_buffer(frame, 20000))), fill = "#dbe7ef", colour = NA) +
    geom_sf(data = land, fill = "#f4f1ea", colour = "#9fb3c2", linewidth = 0.2) +
    geom_sf(data = fl, aes(fill = here), colour = NA, alpha = 0.85)
  if (!is.null(edges)) g <- g + geom_sf(data = edges, colour = "#7c2d12", linewidth = 0.55, linetype = "22")
  g + geom_sf(data = p, colour = "#475569", size = 1.0, alpha = 0.8) +
    geom_sf(data = places, shape = 21, size = 2.4, fill = "white", colour = "#0f172a", stroke = 0.75) +
    geom_text(data = xy, aes(X + dx, Y + dy, label = n), size = 3.0, fontface = "italic", colour = "#0f172a") +
    geom_label(data = lxy, aes(X, Y, label = n), size = 3.4, fontface = "bold", colour = "#44403c",
               fill = "#ffffffcc", linewidth = 0, label.padding = unit(0.25, "lines")) +
    scale_fill_manual(values = c(`TRUE` = "#ebc4aa", `FALSE` = "#ece8de"), guide = "none") +
    coord_sf(xlim = c(vb["xmin"], vb["xmax"]), ylim = c(vb["ymin"], vb["ymax"]), expand = FALSE, datum = NA) +
    labs(title = if (sv) cfg$title_sv else cfg$title_en, subtitle = if (sv) cfg$sub_sv else cfg$sub_en, caption = cap) +
    theme_void(base_size = 11) +
    theme(plot.background = element_rect(fill = "white", colour = NA),
          plot.title = element_text(face = "bold", colour = "#0f172a", margin = margin(b = 4)),
          plot.subtitle = element_text(colour = "#475569", size = 8.6, lineheight = 1.15, margin = margin(b = 8)),
          plot.caption = element_text(colour = "#64748b", size = 8, hjust = 0),
          plot.margin = margin(12, 12, 10, 12))
}
for (lang in c("sv", "en")) ggsave(file.path(out, sprintf("karta_%s_%s.png", cfg$id, lang)), draw(lang), width = cfg$w, height = cfg$h, dpi = 200)
cat(cfg$id, "stenar i kartan:", nrow(p), " platser:", nrow(pl), "\n")
