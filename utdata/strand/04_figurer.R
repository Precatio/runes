# Steg 4: figurerna, på svenska och engelska.  Rscript --vanilla utdata/strand/04_figurer.R
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "config.R"))
R <- jsonlite::fromJSON(file.path(OUT, "resultat.json"), simplifyVector = FALSE)
S <- load_stones()

SRC_SV <- "Källor: SGU, Strandförskjutningsmodell (öppna data, CC BY 4.0; Påsse & Daniels 2015); Rundata (Samnordisk runtextdatabas); Vitki."
SRC_EN <- "Sources: Geological Survey of Sweden (SGU), shore displacement model (open data, CC BY 4.0; Påsse & Daniels 2015); Rundata (Scandinavian Runic-text Database); Vitki."

# (a) Mälardalen: today's water and the water of AD 1050 (SGU), the runestones that are not moved
mx <- c(500000, 730000, 6480000, 6740000)
t100 <- rast(ext(mx), resolution = 100, crs = "EPSG:3006")
w49 <- water_mask(NOW, t100); w1050 <- water_mask(MAIN, t100)
cls <- ifelse(!is.na(values(w49)[, 1]), 2L, ifelse(!is.na(values(w1050)[, 1]), 1L, 0L))
cdf <- as.data.frame(xyFromCell(t100, seq_len(ncell(t100)))); cdf$cls <- cls
rm(w49, w1050, cls); gc(verbose = FALSE)
mal <- S$all %>% filter(province %in% c("U", "Sö", "Vs"), moved == 0)
mxy <- st_coordinates(st_transform(st_as_sf(mal, coords = c("lon", "lat"), crs = 4326), SWEREF))
mal <- data.frame(x = mxy[, 1], y = mxy[, 2])
mal <- mal[mal$x > mx[1] & mal$x < mx[2] & mal$y > mx[3] & mal$y < mx[4], ]
map_fig <- function(lang) {
  LANG <<- lang
  labs_cls <- c(tr("Land", "Land"), tr("Vatten omkring år 1050, land i dag", "Water c. AD 1050, land today"),
                tr("Vatten i dag (modellens år 1949)", "Water today (the model's year 1949)"))
  cdf$f <- factor(labs_cls[cdf$cls + 1], levels = labs_cls)
  stone_lab <- tr(sprintf("Runstenar som inte är flyttade (%d)", nrow(mal)), sprintf("Runestones not moved (%d)", nrow(mal)))
  p <- ggplot() +
    geom_raster(data = cdf, aes(x, y, fill = f)) +
    scale_fill_manual(values = setNames(c("#f4f1ea", "#bcd6ee", "#5b8fc9"), labs_cls), name = NULL) +
    geom_point(data = mal, aes(x, y, colour = stone_lab), size = 1.1, shape = 21, fill = ACCENT, stroke = 0.3) +
    scale_colour_manual(values = setNames("white", stone_lab), name = NULL) +
    guides(fill = guide_legend(order = 1, nrow = 3),
           colour = guide_legend(order = 2, override.aes = list(size = 2.6, colour = INK))) +
    coord_equal(xlim = mx[1:2], ylim = mx[3:4], expand = FALSE) +
    labs(title = tr("Mälardalen omkring år 1050 och i dag", "The Lake Mälaren region c. AD 1050 and today"),
         subtitle = tr("Ljusblått: vatten då men land i dag. Mälaren var en vik av Östersjön.",
                       "Light blue: water then, land today. Lake Mälaren was an inlet of the Baltic."),
         caption = paste(strwrap(tr(paste(SRC_SV, "Uppland, Södermanland och Västmanland; stenar vid kyrkor, i murar och museer är inte med. Strandlinjen år 1050 är modellerad och osäker med upp till några sekel."),
                                    paste(SRC_EN, "Uppland, Södermanland and Västmanland; stones at churches, in walls and museums are left out. The shoreline of AD 1050 is modelled and uncertain by up to a few centuries.")), 125),
                         collapse = "\n")) +
    theme_map() + theme(legend.position = "bottom", legend.box = "vertical", legend.key.size = unit(0.45, "cm"))
  save_fig(p, OUT, paste0("karta_malardalen_", lang, ".png"), 8, 9)
}
fig_map <- c(sv = map_fig("sv"), en = map_fig("en"))

# (b) shares within 1 km of the water of AD 1050, per province and all six
bar_fig <- function(lang) {
  LANG <<- lang
  g <- c(tr("Runstenar", "Runestones"), tr("Slumpvisa punkter inom 5 km", "Random points within 5 km"))
  rows <- c(list(c(list(province = "Alla"), R$H1$overall)), R$H1$provinces)
  df <- bind_rows(lapply(rows, function(r) {
    nm <- if (r$province == "Alla") tr("Alla sex", "All six") else PROV_NAME[[r$province]]
    data.frame(lab = sprintf("%s (%d)", nm, r$n_stones), group = g, share = c(r$within_1000_stones, r$within_1000_random))
  }))
  df$lab <- factor(df$lab, levels = rev(unique(df$lab)))
  df$group <- factor(df$group, levels = rev(g))
  p <- ggplot(df, aes(share, lab, fill = group)) +
    geom_col(position = position_dodge(width = 0.8), width = 0.72, colour = "white", linewidth = 0.5) +
    geom_text(aes(label = paste0(round(share * 100), " %")), position = position_dodge(width = 0.8),
              hjust = -0.15, size = 3, colour = INK) +
    scale_fill_manual(values = setNames(c("#b9b9b9", SERIES[1]), rev(g)), breaks = g, name = NULL) +
    scale_x_continuous(labels = function(x) paste0(round(x * 100), " %"), limits = c(0, 1.08), breaks = seq(0, 1, 0.25),
                       expand = c(0, 0)) +
    labs(x = tr("Andel inom 1 km från vatten omkring år 1050", "Share within 1 km of water c. AD 1050"), y = NULL,
         title = tr("Hur många står nära sin tids vatten?", "How many stand near the water of their time?"),
         subtitle = tr("Runstenar som inte är flyttade, mot slumpvisa punkter på land i samma trakter (antal stenar inom parentes)",
                       "Runestones not moved, against random points on land in the same areas (number of stones in brackets)"),
         caption = paste(strwrap(tr(paste(SRC_SV, "Vattnet = hav och sjöar i SGU:s modell för år 1050."),
                                    paste(SRC_EN, "Water = sea and lakes in SGU's model for AD 1050.")), 120), collapse = "\n")) +
    theme_runor() + theme(panel.grid.major.y = element_blank())
  save_fig(p, OUT, paste0("andel_nara_vatten_", lang, ".png"), 7.5, 5)
}
fig_bar <- c(sv = bar_fig("sv"), en = bar_fig("en"))
say("figurer: ", paste(c(fig_map, fig_bar), collapse = ", "))
