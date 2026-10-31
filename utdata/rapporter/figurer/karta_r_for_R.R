# Figur 1 i rapporten om r för ʀ: varje runsten där draget kan avgöras (flyttade stenar räknas inte), r eller ʀ, och
# klustret ur Kulldorffs scanstatistik. Svensk och engelsk version.
#   Rscript utdata/rapporter/figurer/karta_r_for_R.R <korpusmapp> <utmapp>
suppressPackageStartupMessages({ library(sf); library(ggplot2); library(jsonlite) })
sf_use_s2(FALSE)
a <- commandArgs(TRUE); cdir <- a[1]; out <- a[2]
ne <- file.path(dirname(dirname(cdir)), "naturalearth")
d <- read.csv(file.path(cdir, "corpus.csv"))
d <- d[!is.na(d$pm_r_for_R) & !is.na(d$lat) & !is.na(d$lon) & (is.na(d$moved) | d$moved == 0), ]
h <- fromJSON(file.path(cdir, "hotspots.json"), simplifyVector = FALSE)
pat <- Filter(function(p) p$key == "r_for_R", h$patterns)[[1]]
cl <- pat$clusters[[1]]
box <- st_as_sfc(st_bbox(c(xmin = 4, ymin = 52, xmax = 26, ymax = 66), crs = st_crs(4326)))  # clip wide, frame with coord_sf
view <- st_as_sfc(st_bbox(c(xmin = 10.9, ymin = 55.25, xmax = 19.6, ymax = 61.2), crs = st_crs(4326)))
zoom <- st_as_sfc(st_bbox(c(xmin = 16.25, ymin = 59.45, xmax = 18.05, ymax = 60.35), crs = st_crs(4326)))
layer <- function(name) {
  f <- list.files(file.path(ne, name), pattern = "\\.shp$", full.names = TRUE)[1]
  x <- st_make_valid(st_zm(st_read(f, quiet = TRUE)))
  st_transform(suppressWarnings(suppressMessages(st_intersection(st_geometry(x), box))), 3006)
}
land <- layer("land"); lakes <- c(layer("lakes"), layer("lakes_europe"))  # the big lakes (Vänern, Mälaren) are only in "lakes"
pts <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), 3006)
pts$val <- factor(ifelse(pts$pm_r_for_R == 1, "r", "R"), levels = c("r", "R"))
pts <- pts[order(pts$val, decreasing = TRUE), ]   # r on top
circ <- st_buffer(st_transform(st_sfc(st_point(c(cl$lon, cl$lat)), crs = 4326), 3006), cl$radius_km * 1000)
bb <- st_bbox(st_transform(view, 3006)); bz <- st_bbox(st_transform(zoom, 3006))
erik <- pts[pts$carver %in% "Erik" & pts$carvers_uncertain %in% 0, ]
draw <- function(lang, z = FALSE, art = FALSE) {
  sv <- lang == "sv"
  b <- if (z) bz else bb
  tr <- function(x) if (!art) x else {
    for (pr in list(c("r för ʀ", "r i stället för yr-runan"), c("r for ʀ", "r instead of the yr-rune"), c("bara ʀ-runan", "bara yr-runan"),
                    c("the ʀ-rune only", "the yr-rune only"), c("ʀ skrivet med r-runan", "r i stället för yr-runan"),
                    c("ʀ written with the r-rune", "r instead of the yr-rune"))) x <- gsub(pr[1], pr[2], x, fixed = TRUE)
    x }
  lab <- tr(if (sv) c(r = "r för ʀ (minst en gång)", R = "bara ʀ-runan") else c(r = "r for ʀ (at least once)", R = "the ʀ-rune only"))
  ggplot() +
    geom_sf(data = land, fill = "#f4f4f2", colour = "#94a3b8", linewidth = 0.25) +
    geom_sf(data = lakes, fill = "white", colour = "#cbd5e1", linewidth = 0.15) +
    geom_sf(data = circ, fill = NA, colour = "#1e293b", linewidth = 0.6, linetype = "22") +
    geom_sf(data = pts, aes(colour = val, size = val), alpha = 0.9) +
    (if (z) geom_sf(data = erik, shape = 21, fill = NA, colour = "#0f172a", size = 4.2, stroke = 0.7) else NULL) +
    scale_colour_manual(values = c(r = "#b7410e", R = "#94a3b8"), labels = lab, name = NULL) +
    scale_size_manual(values = if (z) c(r = 2.8, R = 1.8) else c(r = 1.5, R = 0.9), labels = lab, name = NULL) +
    coord_sf(xlim = c(b["xmin"], b["xmax"]), ylim = c(b["ymin"], b["ymax"]), expand = FALSE, datum = NA) +
    labs(title = tr(if (z) (if (sv) "Klustret i västra Uppland" else "The cluster in western Uppland") else
                   (if (sv) "ʀ skrivet med r-runan: stenarna och klustret" else "ʀ written with the r-rune: the stones and the cluster")),
         subtitle = tr(if (z) sprintf(if (sv) "Ringen: %.0f km runt %s; %d av %d stenar inom den har r för ʀ.\nSvart ring runt punkten: en av ristaren Eriks %d säkert attribuerade stenar." else
                                     "The ring: %.0f km around %s; %d of %d stones within it have r for ʀ.\nBlack ring around a point: one of the carver Erik's %d securely attributed stones.",
                                   cl$radius_km, cl$center, cl$cases, cl$n, nrow(erik)) else
                    sprintf(if (sv) "Varje punkt är en runsten där draget kan avgöras (%d stenar; flyttade stenar ingår inte).\nRingen: klustret, %.0f km runt %s, där %d av %d stenar har r för ʀ." else
                              "Each point is a runestone where the trait can be decided (%d stones; moved stones excluded).\nThe ring: the cluster, %.0f km around %s, where %d of %d stones have r for ʀ.",
                            nrow(pts), cl$radius_km, cl$center, cl$cases, cl$n)),
         caption = if (sv) "Källa: Samnordisk runtextdatabas (Rundata, ODbL). Kustlinjer och sjöar: Natural Earth." else
                     "Source: Scandinavian Runic-text Database (Rundata, ODbL). Coastlines and lakes: Natural Earth.") +
    theme_void(base_size = 11) +
    theme(plot.background = element_rect(fill = "white", colour = NA),
          plot.title = element_text(face = "bold", colour = "#0f172a", margin = margin(b = 4)),
          plot.subtitle = element_text(colour = "#475569", size = 9.5, lineheight = 1.15, margin = margin(b = 8)),
          plot.caption = element_text(colour = "#64748b", size = 8, hjust = 0),
          legend.position = "top", legend.justification = "left", legend.text = element_text(size = 9.5, colour = "#0f172a"),
          plot.margin = margin(14, 14, 10, 14)) +
    guides(colour = guide_legend(override.aes = list(size = 2.6)), size = "none")
}
for (lang in c("sv", "en")) {
  ggsave(file.path(out, sprintf("karta_r_for_R_%s.png", lang)), draw(lang), width = 6.4, height = 7.6, dpi = 220, device = ragg::agg_png, bg = "white")
  ggsave(file.path(out, sprintf("karta_r_for_R_zoom_%s.png", lang)), draw(lang, TRUE), width = 6.8, height = 5.6, dpi = 220, device = ragg::agg_png, bg = "white")
  ggsave(file.path(out, sprintf("artikel_r_for_R_%s.png", lang)), draw(lang, FALSE, TRUE), width = 6.4, height = 7.6, dpi = 220, device = ragg::agg_png, bg = "white")
  ggsave(file.path(out, sprintf("artikel_r_for_R_zoom_%s.png", lang)), draw(lang, TRUE, TRUE), width = 6.8, height = 5.6, dpi = 220, device = ragg::agg_png, bg = "white")
}
cat("Erik:", nrow(erik), "stenar på kartan\n")
cat("klart", nrow(pts), "stenar\n")
