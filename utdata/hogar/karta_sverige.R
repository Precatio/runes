# Karta: Sveriges fristående gravhögar i Kulturmiljöregistret, de minst 20 m breda framhävda, mot dagens hav och sjöar
# (SGU:s strandförskjutningsmodell, lagret issjohav_1). Beskuren till södra och mellersta Sverige, där nästan alla
# högarna ligger (16 av 17 531 ligger norr om 64° N). Ersätter karta_sverige.py. Sparar karta_sverige_<sv|en>.png.
#   Rscript utdata/hogar/karta_sverige.R
suppressPackageStartupMessages({library(sf); library(ggplot2)})
sf_use_s2(FALSE)
here <- local({f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)); dirname(normalizePath(f[1]))})
SW <- "EPSG:3006"
bb <- c(xmin = 255000, ymin = 6125000, xmax = 760000, ymax = 7030000)
win <- st_as_sfc(st_bbox(bb, crs = st_crs(SW)))
w <- st_read("/Volumes/2TB/cache/strand/sgu/strandforskjutning_1_900.gpkg", "issjohav_1", wkt_filter = st_as_text(win), quiet = TRUE)
w <- w[w$code %in% c(1, 4), ]
st_crs(w) <- SW
w <- suppressWarnings(st_intersection(st_geometry(w), win))
H <- read.csv("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv", fileEncoding = "UTF-8")
txt <- gsub("\\s+", " ", ifelse(is.na(H$beskrivning), "", H$beskrivning))
m <- regmatches(txt, regexec("(\\d+(?:[.,]\\d+)?)\\s*m\\s*(?:i\\s*)?diam", txt, ignore.case = TRUE, perl = TRUE))
d <- suppressWarnings(as.numeric(sub(",", ".", sapply(m, function(v) if (length(v) > 1) v[2] else NA))))
H$big <- !is.na(d) & d >= 20
stopifnot(nrow(H) == 17531, sum(H$big) == 2017)
P <- st_transform(st_as_sf(H, coords = c("lon", "lat"), crs = 4326), SW)
outside <- sum(lengths(st_intersects(P, win)) == 0)
P <- P[lengths(st_intersects(P, win)) > 0, ]
small <- P[!P$big, ]; big <- P[P$big, ]
fmt <- function(n, sv) format(n, big.mark = if (sv) " " else ",")
for (lang in c("sv", "en")) {
  sv <- lang == "sv"
  g <- ggplot() +
    geom_sf(data = win, fill = "#f1ede4", colour = NA) +
    geom_sf(data = w, fill = "#9dbbd6", colour = NA) +
    geom_sf(data = small, aes(colour = "s"), size = 0.45, alpha = 0.75, stroke = 0) +
    geom_sf(data = big, aes(colour = "b"), size = 1.15, stroke = 0) +
    scale_colour_manual(values = c(s = "#334155", b = "#b7410e"), breaks = c("b", "s"),
                        labels = if (sv) c(paste0("minst 20 m breda (", fmt(nrow(big), TRUE), ")"), paste0("övriga högar (", fmt(nrow(small), TRUE), ")"))
                                 else c(paste0("at least 20 m across (", fmt(nrow(big), FALSE), ")"), paste0("other mounds (", fmt(nrow(small), FALSE), ")")),
                        name = NULL) +
    guides(colour = guide_legend(override.aes = list(size = 3, alpha = 1))) +
    coord_sf(expand = FALSE, datum = NA) +
    labs(title = if (sv) "Sveriges fristående gravhögar" else "Sweden's free-standing burial mounds",
         caption = if (sv) paste0("Högarna i gravfälten ingår inte. Kartan visar södra och mellersta Sverige; ", outside,
                                  " högar ligger norr om kartan.\nKälla: Riksantikvarieämbetet, Kulturmiljöregistret; SGU, dagens hav och sjöar ur strandförskjutningsmodellen (CC BY 4.0). Bild: Vitki.")
                    else paste0("Mounds inside grave fields are not included. The map shows southern and central Sweden; ", outside,
                                " mounds lie north of the map.\nSource: Swedish National Heritage Board, Kulturmiljöregistret; SGU, today's sea and lakes from the shoreline displacement model (CC BY 4.0). Image: Vitki.")) +
    theme_void(base_family = "DejaVu Sans") +
    theme(plot.title = element_text(size = 13, colour = "#0f172a", margin = margin(b = 6)),
          plot.caption = element_text(size = 7, colour = "#475569", hjust = 0, lineheight = 1.1),
          legend.position = c(0.02, 0.97), legend.justification = c(0, 1), legend.text = element_text(size = 9),
          legend.background = element_rect(fill = alpha("white", 0.8), colour = NA),
          plot.background = element_rect(fill = "white", colour = NA), plot.margin = margin(10, 10, 10, 10))
  ggsave(file.path(here, paste0("karta_sverige_", lang, ".png")), g, width = 7, height = 11.6, dpi = 200)
}
cat(nrow(big), "stora,", nrow(small), "övriga,", outside, "utanför kartan\n")
