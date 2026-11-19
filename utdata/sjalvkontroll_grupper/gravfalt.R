# Tilläggsplanen analysplaner/2026-11-19-sjalvkontroll-tillagg-grupper.md (låst, SHA-256 c1e3d2ab…), prov G: gravfälten
# med stenar i grupp som en enhet. Samma data, halvor och modell som utdata/familjens_plats/sjalvkontroll/analys.R
# (funktionen fit, kopierad oförändrad nedan); bara osäkerheten räknas om: klusterrobust kovarians per 1 km-grupp
# (sandwich::vcovCL, HC1), standardfelet aldrig under modellens eget, p tvåsidigt mot t med (grupper på den mindre
# sidan − 1) frihetsgrader. Grupperna ur gravfalt_grupper.csv (grupper.py).
#   Rscript utdata/sjalvkontroll_grupper/gravfalt.R
suppressMessages({library(dplyr); library(jsonlite); library(sandwich)})
src <- "utdata/familjens_plats/sjalvkontroll"
here <- "utdata/sjalvkontroll_grupper"
d <- read.csv(file.path(src, "stenar_sk.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
# Halvorna exakt som i den låsta planens analys.R (socken för socken inom landskapet, efter tid)
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
gr <- read.csv(file.path(here, "gravfalt_grupper.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
d$sgroup <- gr$sgroup[match(d$signum, gr$signum)]
stopifnot(sum(!is.na(d$grupp)) == 657, all(!is.na(d$sgroup[!is.na(d$grupp)])))

# fit som i analys.R, med den klusterrobusta osäkerheten tillagd
fit <- function(y, dd, fe = "province", extra = NULL) {
  dd <- dd[!is.na(dd$grupp) & !is.na(dd[[y]]), ]
  dd$g <- dd$grupp
  small <- names(which(table(dd[[fe]]) < 10))
  dd$prov <- factor(ifelse(dd[[fe]] %in% small, "övriga", dd[[fe]]))
  rhs <- c("g", if (nlevels(dd$prov) > 1) "prov", if (nlevels(droplevels(dd$period)) > 1) "period", "lt", extra)
  dd <- droplevels(dd)
  m <- suppressWarnings(glm(reformulate(rhs, y), family = binomial, data = dd))
  s <- summary(m)$coefficients
  cnt <- list(grupp_med = sum(dd[[y]][dd$g == 1]), grupp_utan = sum(1 - dd[[y]][dd$g == 1]),
              ensam_med = sum(dd[[y]][dd$g == 0]), ensam_utan = sum(1 - dd[[y]][dd$g == 0]))
  G1 <- length(unique(dd$sgroup[dd$g == 1])); G0 <- length(unique(dd$sgroup[dd$g == 0]))
  if (!"g" %in% rownames(s)) return(c(list(n = nrow(dd), events = sum(dd[[y]]), grupper_i_grupp = G1, grupper_ensamma = G0), cnt))
  b <- s["g", 1]; se_m <- s["g", 2]
  V <- vcovCL(m, cluster = ~sgroup, type = "HC1")
  se_cl <- sqrt(V["g", "g"])
  se <- max(se_cl, se_m)
  df <- min(G1, G0) - 1
  tt <- b / se
  c(list(n = nrow(dd), events = sum(dd[[y]]), share_grupp = mean(dd[[y]][dd$g == 1]),
         share_ensam = mean(dd[[y]][dd$g == 0]), or = exp(b),
         p_modell = s["g", 4], se_modell = se_m, se_klusterrobust = se_cl, se = se,
         designeffekt = se_cl^2 / se_m^2, grupper_i_grupp = G1, grupper_ensamma = G0, df = df,
         lo = exp(b - qt(0.975, df) * se), hi = exp(b + qt(0.975, df) * se),
         p = if (df >= 1) 2 * pt(-abs(tt), df) else NA_real_,
         kan_provas = min(G1, G0) >= 5), cnt)
}

TESTS <- list(
  K1 = list(y = "y_V", fe = "province", extra = NULL),
  K2 = list(y = "y_Y", fe = "province", extra = NULL),
  K3a = list(y = "y_alla", fe = "lan", extra = NULL),
  K3b = list(y = "y_alla", fe = "lan", extra = "gfdens"))
ok_half <- function(h) !is.null(h$p) && !is.na(h$p) && h$or > 1 && h$p < 0.05 && isTRUE(h$kan_provas)
too_few <- function(m) min(m$grupp_med, m$grupp_utan, m$ensam_med, m$ensam_utan) < 20 || !isTRUE(m$kan_provas)

res <- lapply(TESTS, function(t) {
  list(utfall = t$y, fast_effekt = t$fe, extra = t$extra, main = fit(t$y, d, t$fe, t$extra),
       halves = list(A = fit(t$y, d[d$half == "A", ], t$fe, t$extra), B = fit(t$y, d[d$half == "B", ], t$fe, t$extra)))
})
p_main <- sapply(res, function(r) if (is.null(r$main$p)) NA else r$main$p)
holm <- p.adjust(p_main, "holm")
for (k in names(res)) {
  m <- res[[k]]$main
  res[[k]]$p_holm <- holm[[k]]
  res[[k]]$bedomning <-
    if (too_few(m) || is.null(m$or)) "kan inte prövas" else
    if (m$or > 1 && holm[[k]] < 0.05 && ok_half(res[[k]]$halves$A) && ok_half(res[[k]]$halves$B)) "står sig" else
    if (m$or > 1 && m$p < 0.05) "försvagas" else "faller"
}
k3 <- c(res$K1$bedomning, res$K3a$bedomning, res$K3b$bedomning)
helhet <- if (all(k3 == "står sig")) "står sig" else if (any(k3 %in% c("faller", "kan inte prövas"))) "faller" else "försvagas"
if (any(k3 == "kan inte prövas")) helhet <- "kan inte avgöras (minst ett prov kan inte prövas)"

g0 <- list(main = fit("y_alla", d), halves = list(A = fit("y_alla", d[d$half == "A", ]), B = fit("y_alla", d[d$half == "B", ])))
g0$haller <- with(g0, main$or > 1 && main$p < 0.05 && ok_half(halves$A) && ok_half(halves$B))
g0$bedomning <- if (g0$haller) "håller" else if (g0$main$or > 1 && g0$main$p < 0.05) "försvagas" else "faller"

out <- list(plan = "analysplaner/2026-11-19-sjalvkontroll-tillagg-grupper.md", G0 = g0, tests = res,
            holm_over = names(TESTS), helhet = helhet,
            grupper_per_halva = lapply(c(A = "A", B = "B"), function(h) {
              x <- d[!is.na(d$grupp) & d$half == h, ]
              list(stenar = nrow(x), grupper_i_grupp = length(unique(x$sgroup[x$grupp == 1])),
                   grupper_ensamma = length(unique(x$sgroup[x$grupp == 0])))
            }))
write_json(out, file.path(here, "gravfalt.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE, null = "null")
pr <- function(lab, m) cat(sprintf("%-8s OR %.2f [%.2f–%.2f] p %.2g (modell %.2g) DE %.2f df %d  grupper %d/%d\n",
                                   lab, m$or, m$lo, m$hi, m$p, m$p_modell, m$designeffekt, m$df, m$grupper_i_grupp, m$grupper_ensamma))
pr("G0", g0$main); pr("G0 A", g0$halves$A); pr("G0 B", g0$halves$B); cat("G0:", g0$bedomning, "\n")
for (k in names(res)) {
  pr(k, res[[k]]$main); pr(paste(k, "A"), res[[k]]$halves$A); pr(paste(k, "B"), res[[k]]$halves$B)
  cat(sprintf("  Holm %.2g → %s\n", res[[k]]$p_holm, res[[k]]$bedomning))
}
cat("helhet:", helhet, "\n")
