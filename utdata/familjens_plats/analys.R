# Familjens plats, test 1–13 enligt den låsta planen analysplaner/2026-10-29-familjens-plats.md.
# Logistisk regression (glm): utfall ~ i grupp + landskap + tidsskikt + lokal täthet; oddskvot för "i grupp".
# Test 14–15 räknas i data.py (inom_grupper.json) och tas in i Holm här.
#   Rscript utdata/familjens_plats/analys.R
suppressMessages({library(dplyr); library(jsonlite)})
dir <- "utdata/familjens_plats"
d <- read.csv(file.path(dir, "stenar.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]

TESTS <- c(y1_gravfalt = "Gravfält inom 500 m", y2_hog = "Gravhög inom 500 m", y3_vag = "Färdväg inom 500 m",
           y4_grans = "Gränsmärke inom 500 m", y5_kyrka = "Medeltida kyrka inom 2 km",
           y6_gammalt_namn = "Gammalt bebyggelsenamn inom 1 km", y7_ungt_namn = "Ungt bebyggelsenamn inom 1 km",
           y8_kultnamn = "Kultnamn inom 2 km", y9_centralort = "Centralortsnamn inom 5 km",
           y10_namnger_plats = "Texten nämner en plats", y11_arv_gard = "Arv eller gård",
           y12_hog_sten = "Hög sten (≥ 1,6 m)", y13_signerad = "Signerad")

fit <- function(y, dd, g = "grupp") {
  dd <- dd[!is.na(dd[[g]]) & !is.na(dd[[y]]), ]
  dd$g <- dd[[g]]
  # landskap med under 10 stenar i urvalet slås ihop (annars skattas de inte)
  small <- names(which(table(dd$province) < 10))
  dd$prov <- factor(ifelse(dd$province %in% small, "övriga", dd$province))
  rhs <- c("g", if (nlevels(dd$prov) > 1) "prov", if (nlevels(droplevels(dd$period)) > 1) "period", "lt")
  m <- suppressWarnings(glm(reformulate(rhs, y), family = binomial, data = droplevels(dd)))
  s <- summary(m)$coefficients
  if (!"g" %in% rownames(s)) return(list(n = nrow(dd), events = sum(dd[[y]])))
  b <- s["g", 1]; se <- s["g", 2]
  list(n = nrow(dd), events = sum(dd[[y]]), share_grupp = mean(dd[[y]][dd$g == 1]),
       share_ensam = mean(dd[[y]][dd$g == 0]), or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se),
       p = s["g", 4])
}

res <- lapply(names(TESTS), function(y) {
  main <- fit(y, d)
  list(key = y, label = TESTS[[y]], main = main,
       halves = list(A = fit(y, d[d$half == "A", ]), B = fit(y, d[d$half == "B", ])),
       robustness = list(ensam_2km = fit(y, d, "ensam2km"),
                         U_So = fit(y, d[d$province %in% c("U", "Sö"), ]),
                         halverade = if (paste0(y, "_halv") %in% names(d)) fit(paste0(y, "_halv"), d) else NULL))
})
names(res) <- names(TESTS)
ig <- fromJSON(file.path(dir, "inom_grupper.json"))
p_all <- c(sapply(res, function(r) r$main$p), t14 = ig$t14$p, t15 = ig$t15$p)
holm <- p.adjust(p_all, "holm")
dir_ok <- function(h, up) !is.null(h$p) && h$p < 0.05 && ((h$or > 1) == up)
status <- function(hp, p, both) if (hp < 0.05 && both) "håller" else if (hp < 0.05 || p < 0.05) "antydan" else
  "ingen skillnad påvisad"
for (k in names(res)) {
  r <- res[[k]]; up <- r$main$or > 1
  both <- dir_ok(r$halves$A, up) && dir_ok(r$halves$B, up)
  res[[k]]$p_holm <- holm[[k]]
  res[[k]]$status <- status(holm[[k]], r$main$p, both)
}
# 14 ensidigt (fler stilgrupper), 15 tvåsidigt; halvorna ska ha p < 0,05 åt samma håll
t14_both <- ig$t14_A$p < 0.05 && ig$t14_B$p < 0.05
t15_both <- ig$t15_A$p < 0.05 && ig$t15_B$p < 0.05 && ig$t15_A$direction == ig$t15$direction &&
  ig$t15_B$direction == ig$t15$direction
inom <- list(t14 = c(ig$t14, list(p_holm = holm[["t14"]], status = status(holm[["t14"]], ig$t14$p, t14_both))),
             t15 = c(ig$t15, list(p_holm = holm[["t15"]], status = status(holm[["t15"]], ig$t15$p, t15_both))))
out <- list(plan = "analysplaner/2026-10-29-familjens-plats.md", n_grupp = sum(d$grupp == 1, na.rm = TRUE),
            n_ensam = sum(d$grupp == 0, na.rm = TRUE), tests = unname(res), inom = inom, inom_raw = ig)
write_json(out, file.path(dir, "familjens_plats.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE, null = "null")
sg <- function(x, k = 3) if (is.null(x)) "–" else formatC(x, digits = k, format = "g")
for (r in res) {
  m <- r$main
  cat(sprintf("%-34s grupp %.2f ensam %.2f OR %s [%s, %s] p %s holm %s | A %s (%s) B %s (%s) | 2km %s U+Sö %s halv %s  %s\n",
              r$label, m$share_grupp, m$share_ensam, sg(m$or), sg(m$lo, 2), sg(m$hi, 2), sg(m$p, 2), sg(r$p_holm, 2),
              sg(r$halves$A$or, 2), sg(r$halves$A$p, 2), sg(r$halves$B$or, 2), sg(r$halves$B$p, 2),
              sg(r$robustness$ensam_2km$or, 2), sg(r$robustness$U_So$or, 2), sg(r$robustness$halverade$or, 2), r$status))
}
cat("t14", inom$t14$status, "holm", sg(inom$t14$p_holm), "\nt15", inom$t15$status, "holm", sg(inom$t15$p_holm), "\n")
