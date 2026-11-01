# Steg 6 (illustration, inget prov): två kartor som visar vad studien mätte, på svenska och engelska.
# (a) Översikt över Mälardalen: vattnet år 1050 och i dag (SGU), de prövade stenarna och rutan för (b).
# (b) Detalj kring Vassunda, Håtuna och Haga (Uppland): vattnet då och nu i 25 m upplösning, stenarna, slumppunkterna
#     och strecken till närmaste vatten år 1050, alltså de avstånd som mättes. Rutan valdes som den 12 km-ruta i
#     Mälardalen med flest stenar gånger andelen mark som var vatten år 1050 men är land i dag.
#   Rscript --vanilla utdata/strand/06_illustration.R
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "config.R"))
S <- load_stones()
st <- read.csv(file.path(OUT, "stenar.csv"), fileEncoding = "UTF-8", stringsAsFactors = FALSE)
d <- S$all6[S$all6$signum %in% st$signum, c("signum", "province", "x", "y")]
d$then <- st$then[match(d$signum, st$signum)]
rnd <- bind_rows(lapply(c("U", "Sö"), function(pv) readRDS(file.path(WORK, paste0(pv_key(pv), "_avstand.rds")))$rnd$main))

SRC_SV <- "Karta: Vitki. Källor: SGU, Strandförskjutningsmodell (öppna data, CC BY 4.0; Påsse & Daniels 2015); Rundata (Samnordisk runtextdatabas)."
SRC_EN <- "Map: Vitki. Sources: Geological Survey of Sweden (SGU), shore displacement model (open data, CC BY 4.0; Påsse & Daniels 2015); Rundata (Scandinavian Runic-text Database)."
FILL <- c("#f4f1ea", "#bcd6ee", "#5b8fc9")
classes <- function(tmpl) {
  w49 <- water_mask(NOW, tmpl); w1050 <- water_mask(MAIN, tmpl)
  cdf <- as.data.frame(xyFromCell(tmpl, seq_len(ncell(tmpl))))
  cdf$cls <- ifelse(!is.na(values(w49)[, 1]), 2L, ifelse(!is.na(values(w1050)[, 1]), 1L, 0L))
  cdf
}
cls_labels <- function() c(tr("Land", "Land"), tr("Vatten år 1050, land i dag", "Water in AD 1050, land today"),
                           tr("Vatten i dag", "Water today"))

# ---- (b) the detail window ----------------------------------------------------------------------------------------
W <- 12000; X0 <- 644000; Y0 <- 6610000
win <- c(X0, X0 + W, Y0, Y0 + W)
inwin <- function(z) z$x > win[1] & z$x < win[2] & z$y > win[3] & z$y < win[4]
ds <- d[inwin(d), ]; rs <- rnd[inwin(rnd), ]
cd <- classes(rast(ext(win), resolution = 25, crs = "EPSG:3006"))
# Lines to the nearest water of AD 1050 (sea and lakes), from the polygons; points in the water get none
wp <- read_slice(MAIN, win + c(-4000, 4000, -4000, 4000))
wp <- st_union(st_crop(st_make_valid(wp), st_bbox(c(xmin = win[1] - 4000, ymin = win[3] - 4000, xmax = win[2] + 4000,
                                                   ymax = win[4] + 4000), crs = st_crs(SWEREF))))
seg <- function(z) {
  z <- z[z$then > 0, ]
  p <- st_as_sf(z, coords = c("x", "y"), crs = SWEREF)
  l <- st_nearest_points(p, wp)
  xy <- lapply(l, function(g) st_coordinates(g)[, 1:2])
  data.frame(x = sapply(xy, `[`, 1, 1), y = sapply(xy, `[`, 1, 2), xend = sapply(xy, `[`, 2, 1), yend = sapply(xy, `[`, 2, 2),
             len = as.numeric(st_length(l)), then = z$then)
}
ls <- seg(ds); lr <- seg(rs)
# The drawn lines are the measured distances (polygon against 25 m cells): they agree to within a cell or two
stopifnot(median(abs(ls$len - ls$then)) < 50, median(abs(lr$len - lr$then)) < 50)
med_s <- round(median(ds$then)); med_r <- round(median(rs$then))
say("detalj: ", nrow(ds), " stenar (median ", med_s, " m), ", nrow(rs), " punkter (median ", med_r, " m); andel vatten då men land nu ",
    round(mean(cd$cls == 1), 3))

detail_fig <- function(lang) {
  LANG <<- lang
  lab <- cls_labels(); cd$f <- factor(lab[cd$cls + 1], levels = lab)
  ks <- tr(sprintf("Runsten som står kvar (%d)", nrow(ds)), sprintf("Runestone still in place (%d)", nrow(ds)))
  kr <- tr(sprintf("Slumpvis punkt i samma bygd (%d)", nrow(rs)), sprintf("Random point in the same district (%d)", nrow(rs)))
  pts <- rbind(data.frame(x = rs$x, y = rs$y, k = kr), data.frame(x = ds$x, y = ds$y, k = ks))
  pts$k <- factor(pts$k, levels = c(ks, kr))
  sb <- c(win[1] + 600, win[3] + 600)
  p <- ggplot() +
    geom_raster(data = cd, aes(x, y, fill = f)) +
    scale_fill_manual(values = setNames(FILL, lab), name = NULL) +
    geom_segment(data = lr, aes(x, y, xend = xend, yend = yend), colour = "#6b7280", linewidth = 0.25, alpha = 0.8) +
    geom_segment(data = ls, aes(x, y, xend = xend, yend = yend), colour = ACCENT, linewidth = 0.6) +
    geom_point(data = pts[pts$k == kr, ], aes(x, y, shape = k), size = 0.8, colour = "#4b5563") +
    geom_point(data = pts[pts$k == ks, ], aes(x, y, shape = k), size = 2.4, colour = "white", fill = ACCENT, stroke = 0.5) +
    scale_shape_manual(values = setNames(c(21, 16), c(ks, kr)), name = NULL, drop = FALSE) +
    annotate("segment", x = sb[1], xend = sb[1] + 2000, y = sb[2], yend = sb[2], colour = INK, linewidth = 0.8) +
    annotate("text", x = sb[1] + 1000, y = sb[2] + 280, label = "2 km", colour = INK, size = 3) +
    guides(fill = guide_legend(order = 1, ncol = 1),
           shape = guide_legend(order = 2, ncol = 1, override.aes = list(size = c(3, 1.4), fill = c(ACCENT, NA),
                                                                         colour = c("white", "#4b5563")))) +
    coord_equal(xlim = win[1:2], ylim = win[3:4], expand = FALSE) +
    labs(title = tr("Vad som mättes: avståndet till vattnet år 1050", "What was measured: the distance to the water of AD 1050"),
         subtitle = tr(sprintf("Vassunda, Håtuna och Haga i Uppland. Strecken går till närmaste vatten år 1050. Median: stenarna %d m, punkterna %d m.",
                               med_s, med_r),
                       sprintf("Vassunda, Håtuna and Haga in Uppland. The lines run to the nearest water of AD 1050. Median: stones %d m, points %d m.",
                               med_s, med_r)),
         caption = paste(strwrap(tr(paste(SRC_SV, "Vattnet är hav och sjöar i modellen; strandlinjen år 1050 är osäker med upp till några sekel. Punkterna är studiens egna slumppunkter i rutan."),
                                    paste(SRC_EN, "Water is sea and lakes in the model; the shoreline of AD 1050 is uncertain by up to a few centuries. The points are the study's own random points in the window.")), 115),
                         collapse = "\n")) +
    theme_map() + theme(legend.position = "bottom", legend.box = "horizontal", legend.key.size = unit(0.45, "cm"),
                        plot.subtitle = element_text(size = 8.5))
  save_fig(p, OUT, paste0("karta_detalj_", lang, ".png"), 8, 8.6)
}
fig_d <- c(detail_fig("sv"), detail_fig("en"))
rm(cd); gc(verbose = FALSE)

# ---- (a) the overview ------------------------------------------------------------------------------------------------
mx <- c(500000, 730000, 6480000, 6740000)
co <- classes(rast(ext(mx), resolution = 100, crs = "EPSG:3006"))
dm <- d[d$x > mx[1] & d$x < mx[2] & d$y > mx[3] & d$y < mx[4], ]
over_fig <- function(lang) {
  LANG <<- lang
  lab <- cls_labels(); co$f <- factor(lab[co$cls + 1], levels = lab)
  ks <- tr(sprintf("Runstenar som står kvar och ingår i studien (%d)", nrow(dm)),
           sprintf("Runestones still in place and in the study (%d)", nrow(dm)))
  p <- ggplot() +
    geom_raster(data = co, aes(x, y, fill = f)) +
    scale_fill_manual(values = setNames(FILL, lab), name = NULL) +
    geom_point(data = dm, aes(x, y, colour = ks), size = 1.1, shape = 21, fill = ACCENT, stroke = 0.3) +
    scale_colour_manual(values = setNames("white", ks), name = NULL) +
    annotate("rect", xmin = win[1], xmax = win[2], ymin = win[3], ymax = win[4], fill = NA, colour = INK, linewidth = 0.7) +
    annotate("label", x = win[2] + 1500, y = win[4] + 1500, label = tr("Detaljkartan", "Detail map"), hjust = 0, vjust = 0,
             size = 3, colour = INK, fill = "white") +
    guides(fill = guide_legend(order = 1, nrow = 3), colour = guide_legend(order = 2, override.aes = list(size = 2.6, colour = INK))) +
    coord_equal(xlim = mx[1:2], ylim = mx[3:4], expand = FALSE) +
    labs(title = tr("Mälardalen år 1050 och i dag", "The Lake Mälaren region in AD 1050 and today"),
         subtitle = tr("Ljusblått: vatten då men land i dag. Mälaren var en vik av Östersjön.",
                       "Light blue: water then, land today. Lake Mälaren was an inlet of the Baltic."),
         caption = paste(strwrap(tr(paste(SRC_SV, "Stenar vid kyrkor, i murar och museer är inte med. Strandlinjen år 1050 är modellerad och osäker med upp till några sekel."),
                                    paste(SRC_EN, "Stones at churches, in walls and museums are left out. The shoreline of AD 1050 is modelled and uncertain by up to a few centuries.")), 125),
                         collapse = "\n")) +
    theme_map() + theme(legend.position = "bottom", legend.box = "vertical", legend.key.size = unit(0.45, "cm"))
  save_fig(p, OUT, paste0("karta_oversikt_", lang, ".png"), 8, 9)
}
fig_o <- c(over_fig("sv"), over_fig("en"))
jsonlite::write_json(list(window = win, n_stones = nrow(ds), n_random = nrow(rs), median_stones_m = med_s, median_random_m = med_r,
                          n_overview = nrow(dm)), file.path(OUT, "illustration.json"), auto_unbox = TRUE, pretty = TRUE)
say("figurer: ", paste(c(fig_d, fig_o), collapse = ", "))
