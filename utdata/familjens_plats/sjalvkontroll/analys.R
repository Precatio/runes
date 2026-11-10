# Självkontrollen, analysplaner/2026-11-10-sjalvkontroll-gravfalt.md: K1, K2, K3a, K3b med originalets modell
# (utdata/familjens_plats/analys.R, funktionen fit): utfall ~ i grupp + landskap/län + tidsskikt + lokal täthet [+ gfdens].
#   Rscript utdata/familjens_plats/sjalvkontroll/analys.R
suppressMessages({library(dplyr); library(jsonlite)})
dir <- "utdata/familjens_plats/sjalvkontroll"
d <- read.csv(file.path(dir, "stenar_sk.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
# Halvorna exakt som i originalet (socken för socken inom landskapet, efter tid)
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]

# Som originalets fit, men med valfri fast effekt (landskap eller län) och valfri extra kovariat
fit <- function(y, dd, fe = "province", extra = NULL) {
  dd <- dd[!is.na(dd$grupp) & !is.na(dd[[y]]), ]
  dd$g <- dd$grupp
  small <- names(which(table(dd[[fe]]) < 10))
  dd$prov <- factor(ifelse(dd[[fe]] %in% small, "övriga", dd[[fe]]))
  rhs <- c("g", if (nlevels(dd$prov) > 1) "prov", if (nlevels(droplevels(dd$period)) > 1) "period", "lt", extra)
  m <- suppressWarnings(glm(reformulate(rhs, y), family = binomial, data = droplevels(dd)))
  s <- summary(m)$coefficients
  cnt <- list(grupp_med = sum(dd[[y]][dd$g == 1]), grupp_utan = sum(1 - dd[[y]][dd$g == 1]),
              ensam_med = sum(dd[[y]][dd$g == 0]), ensam_utan = sum(1 - dd[[y]][dd$g == 0]))
  if (!"g" %in% rownames(s)) return(c(list(n = nrow(dd), events = sum(dd[[y]])), cnt))
  b <- s["g", 1]; se <- s["g", 2]
  c(list(n = nrow(dd), events = sum(dd[[y]]), share_grupp = mean(dd[[y]][dd$g == 1]),
         share_ensam = mean(dd[[y]][dd$g == 0]), or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se),
         p = s["g", 4]), cnt)
}

TESTS <- list(
  K1 = list(label = "K1 (a) granskat gravfält (V) inom 500 m", y = "y_V", fe = "province", extra = NULL),
  K2 = list(label = "K2 (b) gravfält med yngre järnålderns former (Y) inom 500 m", y = "y_Y", fe = "province", extra = NULL),
  K3a = list(label = "K3a (c) alla gravfält, län som fast effekt", y = "y_alla", fe = "lan", extra = NULL),
  K3b = list(label = "K3b (c) som K3a + registrets gravfältstäthet 1–5 km", y = "y_alla", fe = "lan", extra = "gfdens"))

res <- lapply(TESTS, function(t) {
  main <- fit(t$y, d, t$fe, t$extra)
  list(label = t$label, utfall = t$y, fast_effekt = t$fe, extra = t$extra, main = main,
       halves = list(A = fit(t$y, d[d$half == "A", ], t$fe, t$extra), B = fit(t$y, d[d$half == "B", ], t$fe, t$extra)),
       U_So = fit(t$y, d[d$province %in% c("U", "Sö"), ], t$fe, t$extra))
})
p_main <- sapply(res, function(r) if (is.null(r$main$p)) NA else r$main$p)
holm <- p.adjust(p_main, "holm")
ok_half <- function(h) !is.null(h$p) && h$or > 1 && h$p < 0.05
for (k in names(res)) {
  m <- res[[k]]$main
  res[[k]]$p_holm <- holm[[k]]
  too_few <- min(m$grupp_med, m$grupp_utan, m$ensam_med, m$ensam_utan) < 20
  res[[k]]$bedomning <-
    if (too_few || is.null(m$or)) "kan inte prövas" else
    if (m$or > 1 && holm[[k]] < 0.05 && ok_half(res[[k]]$halves$A) && ok_half(res[[k]]$halves$B)) "står sig" else
    if (m$or > 1 && m$p < 0.05) "försvagas" else "faller"
}
k3 <- c(res$K1$bedomning, res$K3a$bedomning, res$K3b$bedomning)
helhet <- if (all(k3 == "står sig")) "står sig" else if (any(k3 %in% c("faller", "kan inte prövas"))) "faller" else
  "försvagas"
if (any(k3 == "kan inte prövas")) helhet <- "kan inte avgöras (minst ett prov kan inte prövas)"

rob <- list(
  K1_utan_block = fit("y_V_utan_block", d),
  K1_250m = fit("y_V250", d),
  K1_med_lan_och_tathet = fit("y_V", d, "lan", "gfdens"),
  K2_med_lan_och_tathet = fit("y_Y", d, "lan", "gfdens"))
lanfordelning <- as.list(table(d$lan[!is.na(d$grupp)]))
lanhur <- as.list(table(d$lan_hur[!is.na(d$grupp)]))
orig <- fit("y_alla", d)
out <- list(plan = "analysplaner/2026-11-10-sjalvkontroll-gravfalt.md", original_omkord = orig, tests = res,
            holm_over = names(TESTS), helhet = helhet, robusthet = rob, stenarnas_lan = lanfordelning,
            lan_hur = lanhur)
write_json(out, file.path(dir, "resultat.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE, null = "null")
sg <- function(x, k = 3) if (is.null(x)) "–" else formatC(x, digits = k, format = "g")
line <- function(lab, m) cat(sprintf("%-62s grupp %.3f ensam %.3f OR %s [%s, %s] p %s  (n %d; grupp %d/%d, ensam %d/%d)\n",
  lab, m$share_grupp, m$share_ensam, sg(m$or), sg(m$lo, 2), sg(m$hi, 2), sg(m$p, 2), m$n,
  m$grupp_med, m$grupp_med + m$grupp_utan, m$ensam_med, m$ensam_med + m$ensam_utan))
line("Original (alla gravfält, landskap)", orig)
for (r in res) {
  line(r$label, r$main)
  cat(sprintf("   holm %s | A OR %s p %s | B OR %s p %s | U+Sö OR %s p %s  => %s\n", sg(r$p_holm, 2),
              sg(r$halves$A$or, 2), sg(r$halves$A$p, 2), sg(r$halves$B$or, 2), sg(r$halves$B$p, 2),
              sg(r$U_So$or, 2), sg(r$U_So$p, 2), r$bedomning))
}
for (k in names(rob)) line(paste("Robusthet:", k), rob[[k]])
cat("Helhet:", helhet, "\n")
