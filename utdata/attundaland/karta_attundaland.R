# Karta till "De gamla landen: Attundaland": östra Mälaren och Upplands kust omkring år 1000 (SGU:s strandförskjutningsmodell),
# folklanden (kartlagret Små land, web/public/geo/land.geojson; öarna i Färingö tingslag, som enligt DMS 1:7 hörde till Bro
# härad, läggs till Attundaland med området närmast sina kyrkor ur ISOF), Upplands runstenar ur Rundata
# (utdata/attundaland/stenar_kartan.csv) och artikelns platser. Svensk och engelsk version.
#   Rscript utdata/attundaland/karta_attundaland.R <hav1000_U.gpkg> <utmapp>
suppressPackageStartupMessages({ library(sf); library(ggplot2); library(jsonlite) })
sf_use_s2(FALSE)
a <- commandArgs(TRUE); hav <- a[1]; out <- a[2]
view <- st_bbox(c(xmin = 17.3, ymin = 59.25, xmax = 18.95, ymax = 59.98), crs = st_crs(4326))
vb <- st_bbox(st_transform(st_as_sfc(view), 3006)); frame <- st_as_sfc(vb)
sea <- st_intersection(st_union(st_make_valid(st_geometry(st_read(hav, quiet = TRUE)))), st_buffer(frame, 30000))
land <- st_difference(st_buffer(frame, 20000), sea)
fl <- st_read("web/public/geo/land.geojson", quiet = TRUE)
fl <- st_intersection(st_make_valid(st_transform(fl[fl$realm == "folkland" & fl$id != "attundaland", ], 3006)), land)
# Attundaland itself: the eight hundreds of the six-year tithe 1314 plus the islands of Färingö tingslag (Bro härad per DMS
# 1:7), each parish getting the area nearest its church (ISOF parish points), as in utdata/sotholm/karta_toren.R
ISOF <- "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/"
dist <- fromJSON(file.path(ISOF, "districts.json"))
par <- fromJSON(file.path(ISOF, "parishes.json"))
par <- par[!is.na(par$latitude) & !is.na(par$district_id) & par$longitude > 16.6 & par$longitude < 19.4 &
           par$latitude > 59.0 & par$latitude < 60.3, ]
par$harad <- dist$name[match(par$district_id, dist$id)]
pp <- st_transform(st_as_sf(par, coords = c("longitude", "latitude"), crs = 4326), 3006)
vor <- st_sf(geometry = st_collection_extract(st_voronoi(st_union(pp), st_buffer(frame, 60000))))
hit <- sapply(st_intersects(vor, pp), function(i) if (length(i)) i[1] else NA_integer_)  # one church per cell
vor$name <- pp$name[hit]; vor$harad <- pp$harad[hit]
HUND <- c("Bro hd", "Sollentuna hd", "Vallentuna hd", "Seminghundra hd", "Långhundra hd", "Lyhundra hd", "Ärlinghundra hd", "Sjuhundra hd")
FARINGO <- c("Färentuna sn", "Hilleshögs sn", "Munsö sn", "Skå sn", "Sånga sn", "Lovö sn")
att <- st_make_valid(st_union(vor[vor$harad %in% HUND | (vor$harad == "Färentuna hd" & vor$name %in% FARINGO), ]))
edges <- st_intersection(st_boundary(att), st_buffer(st_union(land), -300))
att <- st_intersection(att, land)
d <- read.csv("utdata/attundaland/stenar_kartan.csv", stringsAsFactors = FALSE)
p <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), 3006)
lab <- st_transform(st_as_sf(data.frame(id = c("attundaland", "roden", "tiundaland", "fjadrundaland"),
                                        lon = c(18.25, 18.72, 17.75, 17.42), lat = c(59.72, 59.93, 59.94, 59.62)),
                             coords = c("lon", "lat"), crs = 4326), 3006)
pl <- data.frame(n = c("Vallentuna", "Bällsta", "Granby", "Hillersjö", "Snottsta", "Birka"),
                 lon = c(18.0737, 18.0536, 17.9272, 17.7049, 18.0362, 17.5430),
                 lat = c(59.5313, 59.5159, 59.4046, 59.3881, 59.6115, 59.3350))
places <- st_transform(st_as_sf(pl, coords = c("lon", "lat"), crs = 4326), 3006)
xy <- cbind(as.data.frame(st_coordinates(places)), n = pl$n, dy = c(2600, -2600, 2600, 2600, 2600, 2600))
draw <- function(lang) {
  sv <- lang == "sv"
  N <- c(attundaland = "Attundaland", roden = "Roden", tiundaland = "Tiundaland", fjadrundaland = "Fjädrundaland")
  L <- if (sv) list(t = "Attundaland omkring år 1000",
                    s = "Havet enligt SGU:s modell för år 1000; Mälaren var en vik av havet. Rostfärgat: Attundaland, med öarna i Färingö\ntingslag; ljust: grannlanden. Gränserna är ungefärliga. Grå punkter: runstenar. Ringar: platser i texten.",
                    c = "Karta: Vitki, efter SGU (strandförskjutning år 1000), ISOF:s ortnamnsregister och Rundata (ODbL).")
       else list(t = "Attundaland around AD 1000",
                 s = "The sea after the Geological Survey of Sweden's model for AD 1000; Lake Mälaren was a bay of the sea. Rust: Attundaland,\nwith the islands of Färingö; light: the neighbouring lands. Borders approximate. Grey points: runestones. Rings: places in the text.",
                 c = "Map: Vitki, after SGU (shore displacement AD 1000), ISOF place-name register and Rundata (ODbL).")
  ggplot() +
    geom_sf(data = st_as_sfc(st_bbox(st_buffer(frame, 20000))), fill = "#dbe7ef", colour = NA) +
    geom_sf(data = land, fill = "#f4f1ea", colour = "#9fb3c2", linewidth = 0.2) +
    geom_sf(data = fl, fill = "#ece8de", colour = NA, alpha = 0.85) +
    geom_sf(data = att, fill = "#ebc4aa", colour = NA, alpha = 0.85) +
    geom_sf(data = edges, colour = "#7c2d12", linewidth = 0.55, linetype = "22") +
    geom_sf(data = p, colour = "#475569", size = 0.75, alpha = 0.75) +
    geom_sf(data = places, shape = 21, size = 2.2, fill = "white", colour = "#0f172a", stroke = 0.7) +
    geom_text(data = xy, aes(X, Y + dy, label = n), size = 2.9, fontface = "italic", colour = "#0f172a") +
    geom_sf_label(data = lab, aes(label = N[id]), size = 3.4, fontface = "bold", colour = "#44403c",
                  fill = "#ffffffcc", label.size = 0, label.padding = unit(0.25, "lines")) +
    coord_sf(xlim = c(vb["xmin"], vb["xmax"]), ylim = c(vb["ymin"], vb["ymax"]), expand = FALSE, datum = NA) +
    labs(title = L$t, subtitle = L$s, caption = L$c) +
    theme_void(base_size = 11) +
    theme(plot.background = element_rect(fill = "white", colour = NA),
          plot.title = element_text(face = "bold", colour = "#0f172a", margin = margin(b = 4)),
          plot.subtitle = element_text(colour = "#475569", size = 8.6, lineheight = 1.15, margin = margin(b = 8)),
          plot.caption = element_text(colour = "#64748b", size = 8, hjust = 0),
          legend.position = "bottom", plot.margin = margin(12, 12, 10, 12))
}
for (lang in c("sv", "en")) ggsave(file.path(out, sprintf("karta_attundaland_%s.png", lang)), draw(lang), width = 8.2, height = 6.6, dpi = 200)
cat("stenar i kartan:", nrow(p), "\n")
