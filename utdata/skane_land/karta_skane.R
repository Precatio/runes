# Karta till "De gamla landen: Skåne": Skåne omkring år 1000 (SGU:s strandförskjutningsmodell), häraderna (varje ISOF-socken
# får området närmast sin kyrkpunkt, som i utdata/sotholm/karta_toren.R), Skånes vikingatida runstenar (utdata/skane/skane.json)
# och artikelns platser (sockenkyrkornas punkter ur ISOF). Svensk och engelsk version.
#   Rscript utdata/skane_land/karta_skane.R <hav1000_Sk.gpkg> <utmapp>
suppressPackageStartupMessages({ library(sf); library(ggplot2); library(jsonlite) })
sf_use_s2(FALSE)
a <- commandArgs(TRUE); hav <- a[1]; out <- a[2]
view <- st_bbox(c(xmin = 12.35, ymin = 55.3, xmax = 14.62, ymax = 56.48), crs = st_crs(4326))
vb <- st_bbox(st_transform(st_as_sfc(view), 3006)); frame <- st_as_sfc(vb)
sea <- st_intersection(st_union(st_make_valid(st_geometry(st_read(hav, quiet = TRUE)))), st_buffer(frame, 30000))
land <- st_difference(st_buffer(frame, 20000), sea)
ISOF <- "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/"
dist <- fromJSON(file.path(ISOF, "districts.json"))
par <- fromJSON(file.path(ISOF, "parishes.json"))
par <- par[!is.na(par$latitude) & !is.na(par$district_id) & par$longitude > 11.5 & par$longitude < 15.5 &
           par$latitude > 55.0 & par$latitude < 57.2, ]
par$harad <- dist$name[match(par$district_id, dist$id)]
par$skane <- par$province_id == 1
pp <- st_transform(st_as_sf(par, coords = c("longitude", "latitude"), crs = 4326), 3006)
vor <- st_sf(geometry = st_collection_extract(st_voronoi(st_union(pp), st_buffer(frame, 80000))))
hit <- sapply(st_intersects(vor, pp), function(i) if (length(i)) i[1] else NA_integer_)
vor$harad <- pp$harad[hit]; vor$skane <- pp$skane[hit]
sk <- st_make_valid(st_union(vor[vor$skane %in% TRUE, ]))
har <- aggregate(vor[vor$skane %in% TRUE, "harad"], by = list(h = vor$harad[vor$skane %in% TRUE]), FUN = function(x) x[1])
inner <- st_intersection(st_union(st_boundary(st_make_valid(har))), st_buffer(sk, -500))
inner <- st_intersection(inner, st_buffer(st_union(land), -300))
outer <- st_intersection(st_boundary(sk), st_buffer(st_union(land), -300))
sk <- st_intersection(sk, land)
rest <- st_difference(st_intersection(st_buffer(frame, 20000), land), sk)
d <- read.csv("utdata/skane_land/stenar_kartan.csv", stringsAsFactors = FALSE)
p <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), 3006)
PL <- read.csv("utdata/skane_land/platser.csv", stringsAsFactors = FALSE)   # n_sv, n_en, parish, dx, dy
pl <- merge(PL, par[par$province_id == 1, c("name", "latitude", "longitude")], by.x = "parish", by.y = "name")
stopifnot(nrow(pl) == nrow(PL))
places <- st_transform(st_as_sf(pl, coords = c("longitude", "latitude"), crs = 4326), 3006)
xy <- cbind(as.data.frame(st_coordinates(places)), pl[, c("n_sv", "n_en", "dx", "dy")])
draw <- function(lang) {
  sv <- lang == "sv"
  xy$n <- if (sv) xy$n_sv else xy$n_en
  L <- if (sv) list(t = "Skåne omkring år 1000",
                    s = "Kusten enligt SGU:s modell för år 1000. Rostfärgat: Skåne; streckat: häradsgränserna, ungefärliga (varje socken har fått\nområdet närmast sin kyrka). Grå punkter: Skånes vikingatida runstenar. Ringar: platser i texten.",
                    c = "Karta: Vitki, efter SGU (strandförskjutning år 1000), ISOF:s ortnamnsregister och Rundata (ODbL).")
       else list(t = "Skåne around AD 1000",
                 s = "The coast after the Geological Survey of Sweden's model for AD 1000. Rust: Skåne; dashed: the hundreds, approximate\n(each parish given the area nearest its church). Grey points: Skåne's Viking-age runestones. Rings: places in the text.",
                 c = "Map: Vitki, after SGU (shore displacement AD 1000), ISOF place-name register and Rundata (ODbL).")
  ggplot() +
    geom_sf(data = st_as_sfc(st_bbox(st_buffer(frame, 20000))), fill = "#dbe7ef", colour = NA) +
    geom_sf(data = rest, fill = "#f4f1ea", colour = NA) +
    geom_sf(data = sk, fill = "#ebc4aa", colour = NA, alpha = 0.85) +
    geom_sf(data = inner, colour = "#9a6b52", linewidth = 0.25, linetype = "22") +
    geom_sf(data = outer, colour = "#7c2d12", linewidth = 0.6, linetype = "22") +
    geom_sf(data = p, colour = "#475569", size = 1.3, alpha = 0.85) +
    geom_sf(data = places, shape = 21, size = 2.4, fill = "white", colour = "#0f172a", stroke = 0.75) +
    geom_text(data = xy, aes(X + dx, Y + dy, label = n), size = 3.0, fontface = "italic", colour = "#0f172a") +
    coord_sf(xlim = c(vb["xmin"], vb["xmax"]), ylim = c(vb["ymin"], vb["ymax"]), expand = FALSE, datum = NA) +
    labs(title = L$t, subtitle = L$s, caption = L$c) +
    theme_void(base_size = 11) +
    theme(plot.background = element_rect(fill = "white", colour = NA),
          plot.title = element_text(face = "bold", colour = "#0f172a", margin = margin(b = 4)),
          plot.subtitle = element_text(colour = "#475569", size = 8.6, lineheight = 1.15, margin = margin(b = 8)),
          plot.caption = element_text(colour = "#64748b", size = 8, hjust = 0),
          plot.margin = margin(12, 12, 10, 12))
}
for (lang in c("sv", "en")) ggsave(file.path(out, sprintf("karta_skane_%s.png", lang)), draw(lang), width = 8.2, height = 6.8, dpi = 200)
cat("stenar i kartan:", nrow(p), " platser:", nrow(pl), "\n")
