# Karta till "De gamla landen: Roden": Upplands kust omkring år 1000 (SGU:s strandförskjutningsmodell), folklanden
# (kartlagret Små land, web/public/geo/land.geojson) och runstenarna med och utan kors. Svensk och engelsk version.
#   Rscript utdata/roden/karta_roden.R <hav1000_U.gpkg> <utmapp>
suppressPackageStartupMessages({ library(sf); library(ggplot2) })
sf_use_s2(FALSE)
a <- commandArgs(TRUE); hav <- a[1]; out <- a[2]
view <- st_bbox(c(xmin = 17.55, ymin = 59.22, xmax = 19.25, ymax = 60.55), crs = st_crs(4326))
vb <- st_bbox(st_transform(st_as_sfc(view), 3006)); frame <- st_as_sfc(vb)
sea <- st_intersection(st_union(st_make_valid(st_geometry(st_read(hav, quiet = TRUE)))), st_buffer(frame, 30000))
land <- st_difference(st_buffer(frame, 20000), sea)
fl <- st_read("web/public/geo/land.geojson", quiet = TRUE)
fl <- st_make_valid(st_transform(fl[fl$realm == "folkland", ], 3006))
# the borders between the lands: shared edges of the polygons, on land only (not the coastlines)
pairs <- combn(seq_len(nrow(fl)), 2, simplify = FALSE)
edges <- do.call(c, lapply(pairs, function(ij) st_intersection(st_boundary(st_geometry(fl)[ij[1]]), st_boundary(st_geometry(fl)[ij[2]]))))
edges <- st_intersection(st_union(st_collection_extract(st_sfc(edges, crs = 3006), "LINESTRING")), land)
fl <- st_intersection(fl, land)
fl$roden <- fl$id == "roden"
d <- read.csv("utdata/roden/roden_stenar.csv", stringsAsFactors = FALSE)
d <- d[!is.na(d$pm_kors), ]
p <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), 3006)
p$k <- factor(ifelse(p$pm_kors == 1, "ja", "nej"), levels = c("ja", "nej"))
p <- p[order(p$k == "ja"), ]
lab <- st_transform(st_as_sf(data.frame(id = c("roden", "tiundaland", "attundaland", "fjadrundaland"),
                                        lon = c(18.95, 17.95, 18.05, 17.78), lat = c(60.02, 60.12, 59.56, 59.62)),
                             coords = c("lon", "lat"), crs = 4326), 3006)
taby <- st_transform(st_as_sf(data.frame(lon = 18.044, lat = 59.48), coords = c("lon", "lat"), crs = 4326), 3006)
draw <- function(lang) {
  sv <- lang == "sv"
  N <- if (sv) c(roden = "Roden", tiundaland = "Tiundaland", attundaland = "Attundaland", fjadrundaland = "Fjädrundaland")
       else c(roden = "Roden", tiundaland = "Tiundaland", attundaland = "Attundaland", fjadrundaland = "Fjädrundaland")
  L <- if (sv) list(ja = "kors", nej = "inget kors", t = "Roden och folklanden omkring år 1000",
                    s = "Havet enligt SGU:s modell för år 1000. Rostfärgat: Roden, kustlandet med skeppslagen; ljust: de tre folklanden.\nPunkterna: Upplands runstenar där det går att avgöra om de har ett kors. Gränserna är ungefärliga.",
                    taby = "Täby", c = "Karta: Vitki, efter SGU (strandförskjutning år 1000), ISOF:s ortnamnsregister och Rundata (ODbL).")
       else list(ja = "cross", nej = "no cross", t = "Roden and the folklands around AD 1000",
                 s = "The sea after the Geological Survey of Sweden's model for AD 1000. Rust: Roden, the coastal land of the ship districts;\nlight: the three folklands. Points: Uppland's runestones where it can be told whether they carry a cross. Borders approximate.",
                 taby = "Täby", c = "Map: Vitki, after SGU (shore displacement AD 1000), ISOF place-name register and Rundata (ODbL).")
  ggplot() +
    geom_sf(data = st_as_sfc(st_bbox(st_buffer(frame, 20000))), fill = "#dbe7ef", colour = NA) +
    geom_sf(data = land, fill = "#f4f1ea", colour = "#9fb3c2", linewidth = 0.2) +
    geom_sf(data = fl, aes(fill = roden), colour = NA, alpha = 0.85) +
    geom_sf(data = edges, colour = "#7c2d12", linewidth = 0.55, linetype = "22") +
    geom_sf(data = p, aes(colour = k, size = k), alpha = 0.9) +
    geom_sf_text(data = taby, label = L$taby, nudge_x = 11000, nudge_y = -2500, size = 3, fontface = "italic", colour = "#0f172a") +
    geom_sf_label(data = lab, aes(label = N[id]), size = 3.4, fontface = "bold", colour = "#44403c",
                  fill = "#ffffffcc", label.size = 0, label.padding = unit(0.25, "lines")) +
    scale_fill_manual(values = c(`TRUE` = "#ebc4aa", `FALSE` = "#ece8de"), guide = "none") +
    scale_colour_manual(values = c(ja = "#b7410e", nej = "#475569"), labels = c(ja = L$ja, nej = L$nej), name = NULL) +
    scale_size_manual(values = c(ja = 1.15, nej = 1.15), labels = c(ja = L$ja, nej = L$nej), name = NULL) +
    coord_sf(xlim = c(vb["xmin"], vb["xmax"]), ylim = c(vb["ymin"], vb["ymax"]), expand = FALSE, datum = NA) +
    labs(title = L$t, subtitle = L$s, caption = L$c) +
    theme_void(base_size = 11) +
    theme(plot.background = element_rect(fill = "white", colour = NA),
          plot.title = element_text(face = "bold", colour = "#0f172a", margin = margin(b = 4)),
          plot.subtitle = element_text(colour = "#475569", size = 8.6, lineheight = 1.15, margin = margin(b = 8)),
          plot.caption = element_text(colour = "#64748b", size = 8, hjust = 0),
          legend.position = "bottom", plot.margin = margin(12, 12, 10, 12))
}
for (lang in c("sv", "en")) ggsave(file.path(out, sprintf("karta_roden_%s.png", lang)), draw(lang), width = 7.5, height = 8.2, dpi = 200)
cat("stenar i kartan:", nrow(p), "\n")
