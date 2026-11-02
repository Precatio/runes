# Karta till "De gamla landen: Sotholm": ön Tören omkring år 1000 (SGU:s strandförskjutningsmodell), gränsen mellan
# Övre Tör (Svartlösa härad) och Yttre Tör (Sotholms härad) och runstenarna med och utan bön. Svensk och engelsk version.
#   Rscript utdata/sotholm/karta_toren.R <hav1000.gpkg> <utmapp>
# Häradsgränserna är ungefärliga: varje ISOF-socken får området närmast sin kyrkpunkt (som kartlagret Små land).
suppressPackageStartupMessages({ library(sf); library(ggplot2); library(jsonlite) })
sf_use_s2(FALSE)
a <- commandArgs(TRUE); hav <- a[1]; out <- a[2]
ISOF <- "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/"
view <- st_bbox(c(xmin = 17.45, ymin = 58.83, xmax = 18.55, ymax = 59.38), crs = st_crs(4326))
vb <- st_bbox(st_transform(st_as_sfc(view), 3006))
frame <- st_as_sfc(vb)
sea <- st_union(st_make_valid(st_geometry(st_read(hav, quiet = TRUE))))
sea <- st_intersection(sea, st_buffer(frame, 30000))
land <- st_difference(st_buffer(frame, 20000), sea)

dist <- fromJSON(file.path(ISOF, "districts.json"))
par <- fromJSON(file.path(ISOF, "parishes.json"))
par <- par[!is.na(par$latitude) & !is.na(par$district_id), ]
par$harad <- dist$name[match(par$district_id, dist$id)]
par <- par[par$longitude > 16.9 & par$longitude < 19.2 & par$latitude > 58.6 & par$latitude < 59.6, ]
pp <- st_transform(st_as_sf(par, coords = c("longitude", "latitude"), crs = 4326), 3006)
vor <- st_collection_extract(st_voronoi(st_union(pp), st_buffer(frame, 60000)))
vor <- st_sf(geometry = vor)
vor$harad <- pp$harad[unlist(st_intersects(vor, pp))]
har <- aggregate(vor, by = list(harad = vor$harad), FUN = function(x) x[1])
har0 <- st_make_valid(har[, "harad"])
# the border between Upper and Outer Tör: the shared edge of the two hundreds, on land only
border <- st_intersection(st_intersection(st_boundary(st_union(har0[har0$harad == "Sotholms hd", ])),
                                          st_boundary(st_union(har0[har0$harad == "Svartlösa hd", ]))), land)
har <- st_intersection(st_make_valid(har[, "harad"]), land)
toren <- har[har$harad %in% c("Svartlösa hd", "Sotholms hd"), ]
toren$del <- ifelse(toren$harad == "Sotholms hd", "yttre", "ovre")

st <- read.csv("utdata/sotholm/sotholm_stenar.csv", stringsAsFactors = FALSE)
co <- read.csv("data/cache/r/corpus/7b9061c9a1c12c73/corpus.csv", stringsAsFactors = FALSE)[, c("signum", "lat", "lon")]
st <- merge(st[st$harad %in% c("Svartlösa hd", "Sotholms hd"), ], co, by = "signum")
st <- st[!is.na(st$lat), ]
st$bon <- ifelse(is.na(st$cat_kristen), "okand", ifelse(st$cat_kristen == 1, "ja", "nej"))
sp <- st_transform(st_as_sf(st, coords = c("lon", "lat"), crs = 4326), 3006)
sp <- sp[order(sp$bon == "ja"), ]
s269 <- sp[sp$signum == "Sö 269", ]
lab <- st_transform(st_as_sf(data.frame(del = c("ovre", "yttre"), lon = c(17.91, 18.38), lat = c(59.26, 59.03)),
                             coords = c("lon", "lat"), crs = 4326), 3006)
talje <- st_transform(st_as_sf(data.frame(lon = 17.465, lat = 59.195), coords = c("lon", "lat"), crs = 4326), 3006)

draw <- function(lang) {
  sv <- lang == "sv"
  L <- if (sv) list(ja = "bön för själen", nej = "ingen bön", ovre = "Övre Tör\n(Svartlösa härad)", yttre = "Yttre Tör\n(Sotholms härad)", talje = "sundet vid Tälje →",
                    t = "Tören omkring år 1000",
                    s = "Södertörn var en ö. Havet enligt SGU:s modell för år 1000. Streckad linje: gränsen mellan häraderna\n(ungefärlig, efter sockenkyrkornas lägen). Punkterna: runstenar där det går att avgöra om de har en bön.",
                    c = "Karta: Vitki, efter SGU (strandförskjutning år 1000), ISOF:s ortnamnsregister och Rundata (ODbL).")
       else list(ja = "prayer for the soul", nej = "no prayer", ovre = "Upper Tör\n(Svartlösa hundred)", yttre = "Outer Tör\n(Sotholm hundred)", talje = "the strait at Tälje →",
                 t = "Tören around AD 1000",
                 s = "Södertörn was an island. The sea after the Geological Survey of Sweden's model for AD 1000. Dashed line: the border\nbetween the hundreds (approximate, after the parish churches). Points: runestones where a prayer can be decided.",
                 c = "Map: Vitki, after SGU (shore displacement AD 1000), ISOF place-name register and Rundata (ODbL).")
  sp$b <- factor(sp$bon, levels = c("ja", "nej", "okand"))
  pts <- sp[sp$bon != "okand", ]
  ggplot() +
    geom_sf(data = st_as_sfc(st_bbox(st_buffer(frame, 20000))), fill = "#dbe7ef", colour = NA) +
    geom_sf(data = land, fill = "#f4f1ea", colour = "#9fb3c2", linewidth = 0.25) +
    geom_sf(data = toren, aes(fill = del), colour = NA, alpha = 0.9) +
    geom_sf(data = border, colour = "#7c2d12", linewidth = 0.8, linetype = "22") +
    geom_sf(data = pts, aes(colour = b, size = b), alpha = 0.95) +
    geom_sf(data = s269, shape = 21, fill = NA, colour = "#0f172a", size = 4.4, stroke = 0.7) +
    geom_sf_text(data = s269, label = "Sö 269", nudge_x = 5200, nudge_y = 1800, size = 3, colour = "#0f172a") +
    geom_sf_label(data = lab, aes(label = unlist(L[del])), size = 3.3, fontface = "bold", colour = "#44403c", lineheight = 0.95,
                  fill = "#ffffffcc", label.size = 0, label.padding = unit(0.25, "lines")) +
    geom_sf_text(data = talje, label = L$talje, size = 2.9, fontface = "italic", colour = "#335c7a", hjust = 0) +
    scale_fill_manual(values = c(ovre = "#e7e1d3", yttre = "#efd9c9"), guide = "none") +
    scale_colour_manual(values = c(ja = "#b7410e", nej = "#475569"), labels = c(ja = L$ja, nej = L$nej), name = NULL) +
    scale_size_manual(values = c(ja = 3.2, nej = 1.8), labels = c(ja = L$ja, nej = L$nej), name = NULL) +
    coord_sf(xlim = c(vb["xmin"], vb["xmax"]), ylim = c(vb["ymin"], vb["ymax"]), expand = FALSE, datum = NA) +
    labs(title = L$t, subtitle = L$s, caption = L$c) +
    theme_void(base_size = 11) +
    theme(plot.background = element_rect(fill = "white", colour = NA),
          plot.title = element_text(face = "bold", colour = "#0f172a", margin = margin(b = 4)),
          plot.subtitle = element_text(colour = "#475569", size = 9, lineheight = 1.15, margin = margin(b = 8)),
          plot.caption = element_text(colour = "#64748b", size = 8, hjust = 0),
          legend.position = "bottom", plot.margin = margin(12, 12, 10, 12))
}
for (lang in c("sv", "en")) ggsave(file.path(out, sprintf("karta_toren_%s.png", lang)), draw(lang), width = 7.5, height = 7.6, dpi = 200)
cat("härader i bilden:", paste(sort(unique(har$harad)), collapse = ", "), "\n")
cat("stenar:", nrow(sp), "med bön:", sum(sp$bon == "ja"), "\n")
