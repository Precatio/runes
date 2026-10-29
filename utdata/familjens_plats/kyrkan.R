# Tog kyrkan över efter gravfältet? Fyra test enligt den låsta planen analysplaner/2026-10-29-kyrkan-tog-over.md.
#   .venv/bin/python utdata/familjens_plats/kyrkan_data.py && Rscript utdata/familjens_plats/kyrkan.R
suppressMessages({library(dplyr); library(jsonlite)})
set.seed(2026)
dir <- "utdata/familjens_plats"
NPERM <- 9999
STYLES <- c("RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5")
d <- read.csv(file.path(dir, "kyrkan.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d$dated <- d$style %in% STYLES
d$year <- ifelse(d$dated, (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$rank <- match(d$style, STYLES)
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
d$pk <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = d$pk, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, d$pk), paste(pinfo$province, pinfo$pk))]

lfit <- function(dd, y, x, ctrl) {
  dd <- dd[!is.na(dd[[y]]) & !is.na(dd[[x]]), ]
  small <- names(which(table(dd$province) < 10))   # som i Familjens plats: små landskap slås ihop
  dd$prov <- factor(ifelse(dd$province %in% small, "övriga", dd$province))
  rhs <- c(x, if (nlevels(dd$prov) > 1) "prov", ctrl)
  m <- suppressWarnings(glm(reformulate(rhs, y), family = binomial, data = droplevels(dd)))
  s <- summary(m)$coefficients
  b <- s[x, 1]; se <- s[x, 2]
  list(n = nrow(dd), events = sum(dd[[y]]), or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se), p = s[x, 4])
}
fp <- d[d$pa_plats == 1, ]
t1 <- function(dd, y = "gravfalt") lfit(dd[!is.na(dd$t50), ], y, "t50", "lt")
t2 <- function(dd, y = "gravfalt") lfit(dd, y, "cat_kristen", c("period", "lt"))
ck <- d[d$kyrka == 1 | d$pa_plats == 1, ]
t4 <- function(dd) lfit(dd, "cat_kristen", "kyrka", "period")

t3 <- function(dd, v = "year") {
  dd <- dd[!is.na(dd[[v]]), ]
  both <- dd %>% group_by(pk) %>% filter(any(kyrka == 1) & any(kyrka == 0)) %>% ungroup()
  if (nrow(both) == 0) return(list(parishes = 0))
  idx <- split(seq_len(nrow(both)), both$pk)
  w <- sapply(idx, length)
  val <- both[[v]]
  stat <- function(lab) sum(w * sapply(idx, function(i) mean(val[i][lab[i] == 1]) - mean(val[i][lab[i] == 0]))) / sum(w)
  obs <- stat(both$kyrka)
  sims <- replicate(NPERM, { lab <- both$kyrka; for (i in idx) lab[i] <- lab[i][sample.int(length(i))]; stat(lab) })
  lo <- (1 + sum(sims <= obs)) / (NPERM + 1); hi <- (1 + sum(sims >= obs)) / (NPERM + 1)
  list(parishes = length(idx), church = sum(both$kyrka == 1), field = sum(both$kyrka == 0), diff = obs,
       mean_church = mean(val[both$kyrka == 1]), mean_field = mean(val[both$kyrka == 0]),
       p = min(1, 2 * min(lo, hi)))
}
# riktningen uttryckt som för de andra: "upp" = det förväntade hållet
expected_up <- c(t1 = FALSE, t2 = FALSE, t3 = TRUE, t4 = TRUE)
eff <- function(r, k) if (k == "t3") r$diff > 0 else r$or > 1

run <- list(
  t1 = list(f = function(x) t1(x), data = fp, label = "Gravfält och tid (per 50 år)"),
  t2 = list(f = function(x) t2(x), data = fp, label = "Kristna stenar vid gravfält"),
  t3 = list(f = function(x) t3(x), data = d[d$dated & (d$kyrka == 1 | d$pa_plats == 1), ], label = "Kyrkans stenar senare (år)"),
  t4 = list(f = function(x) t4(x), data = ck, label = "Kyrkans stenar kristna"))
res <- lapply(names(run), function(k) {
  r <- run[[k]]
  list(key = k, label = r$label, main = r$f(r$data),
       halves = list(A = r$f(r$data[r$data$half == "A", ]), B = r$f(r$data[r$data$half == "B", ])))
})
names(res) <- names(run)
holm <- p.adjust(sapply(res, function(r) r$main$p), "holm")
for (k in names(res)) {
  r <- res[[k]]; up <- eff(r$main, k)
  ok <- function(h) !is.null(h$p) && h$p < 0.05 && eff(h, k) == up
  both <- ok(r$halves$A) && ok(r$halves$B)
  st <- if (holm[[k]] < 0.05 && both) "håller" else if (holm[[k]] < 0.05 || r$main$p < 0.05) "antydan" else
    "ingen skillnad påvisad"
  if (st != "ingen skillnad påvisad" && up != expected_up[[k]]) st <- paste(st, "(motsatt riktning)")
  res[[k]]$p_holm <- holm[[k]]; res[[k]]$status <- st
}
U <- function(x) x[x$province == "U", ]
plac <- d[d$dated & ((d$kyrka_plac == 1) | d$pa_plats == 1), ]; plac$kyrka <- plac$kyrka_plac
rob <- list(
  t1_U = t1(U(fp)), t1_250 = t1(fp, "gravfalt250"), t2_U = t2(U(fp)), t2_250 = t2(fp, "gravfalt250"),
  t3_U = t3(U(run$t3$data)), t3_placering = t3(plac), t3_rang = t3(run$t3$data, "rank"),
  t4_U = t4(U(ck)), t4_placering = { x <- d[d$kyrka_plac == 1 | d$pa_plats == 1, ]; x$kyrka <- x$kyrka_plac; t4(x) })
desc <- d[d$dated, ] %>% mutate(grupp = ifelse(inmurad == 1, "inmurad", ifelse(kyrka == 1, "vid kyrkan övrigt",
                                                ifelse(pa_plats == 1, "på sin plats", "annan")))) %>%
  filter(grupp != "annan") %>% count(grupp, style) %>% group_by(grupp) %>% mutate(share = n / sum(n)) %>% ungroup()
write_json(list(plan = "analysplaner/2026-10-29-kyrkan-tog-over.md", tests = unname(res), robustness = rob,
                styles = desc), file.path(dir, "kyrkan.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
sg <- function(x, k = 3) if (is.null(x)) "–" else formatC(x, digits = k, format = "g")
show <- function(r) if (!is.null(r$or)) sprintf("OR %s [%s, %s] p %s n %d", sg(r$or), sg(r$lo, 2), sg(r$hi, 2),
  sg(r$p, 2), r$n) else sprintf("diff %s (kyrka %s, fält %s) p %s, %d socknar %d/%d", sg(r$diff), sg(r$mean_church, 5),
  sg(r$mean_field, 5), sg(r$p, 2), r$parishes, r$church, r$field)
for (r in res) cat(sprintf("%-30s %s | Holm %s | A: %s | B: %s | %s\n", r$label, show(r$main), sg(r$p_holm, 2),
                           show(r$halves$A), show(r$halves$B), r$status))
for (k in names(rob)) cat(sprintf("  %-14s %s\n", k, show(rob[[k]])))
print(as.data.frame(tidyr::pivot_wider(desc[, c("grupp", "style", "n")], names_from = style, values_from = n)))
