# Gården, gravfältet och vägen: H1–H4 enligt den låsta planen analysplaner/2026-10-29-gard-gravfalt-vag.md.
#   .venv/bin/python utdata/gard_vag/data.py && Rscript utdata/gard_vag/analys.R
suppressMessages({library(dplyr); library(jsonlite)})
dir <- "utdata/gard_vag"
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

fit <- function(dd, y, x, tat, family = binomial, inv = TRUE) {
  dd <- dd[!is.na(dd[[x]]) & !is.na(dd[[y]]), ]
  small <- names(which(table(dd$province) < 10))
  dd$prov <- factor(ifelse(dd$province %in% small, "övriga", dd$province))
  rhs <- c(x, if (nlevels(dd$prov) > 1) "prov", "period", "lt", if (inv) tat)
  m <- suppressWarnings(glm(reformulate(rhs, y), family = family, data = droplevels(dd)))
  s <- summary(m)$coefficients
  b <- s[x, 1]; se <- s[x, 2]
  r <- list(n = nrow(dd), k_x = sum(dd[[x]] == 1), p = s[x, 4],
            andel_x1 = mean(dd[[y]][dd[[x]] == 1]), andel_x0 = mean(dd[[y]][dd[[x]] == 0]))
  if (identical(family, binomial)) c(r, or = exp(b), lo = exp(b - 1.96 * se), hi = exp(b + 1.96 * se)) else c(r, beta = b)
}
T <- list(H1 = list(y = "bytomt500", x = "grupp", tat = "tat_bytomt"),
          H2 = list(y = "boplats500", x = "grupp", tat = "tat_boplats"),
          H3 = list(y = "bytomt500", x = "arv", tat = "tat_bytomt"),
          H4 = list(y = "vag200", x = "bro", tat = "tat_vag"))
res <- lapply(T, function(t) list(alla = fit(d, t$y, t$x, t$tat), A = fit(d[d$half == "A", ], t$y, t$x, t$tat),
                                  B = fit(d[d$half == "B", ], t$y, t$x, t$tat)))
holm <- p.adjust(sapply(res, function(r) r$alla$p), "holm")
for (k in names(res)) {
  up <- res[[k]]$alla$or > 1
  both <- all(sapply(c("A", "B"), function(h) res[[k]][[h]]$p < 0.05 && (res[[k]][[h]]$or > 1) == up))
  res[[k]]$holm <- holm[[k]]
  res[[k]]$status <- if (holm[[k]] < 0.05 && both) "håller" else if (holm[[k]] < 0.05 || res[[k]]$alla$p < 0.05)
    "antydan" else "ingen skillnad påvisad"
}
U <- d[d$province %in% c("U", "Sö"), ]
rob <- list(H1_250 = fit(d, "bytomt250", "grupp", "tat_bytomt"), H1_1000 = fit(d, "bytomt1000", "grupp", "tat_bytomt"),
            H1_utan_inv = fit(d, "bytomt500", "grupp", "tat_bytomt", inv = FALSE), H1_U_So = fit(U, "bytomt500", "grupp", "tat_bytomt"),
            H1_ensam2km = fit(transform(d, grupp = ensam2km), "bytomt500", "grupp", "tat_bytomt"),
            H1_logavst = fit(d, "log_d_bytomt", "grupp", "tat_bytomt", family = gaussian),
            H2_250 = fit(d, "boplats250", "grupp", "tat_boplats"), H2_1000 = fit(d, "boplats1000", "grupp", "tat_boplats"),
            H2_utan_inv = fit(d, "boplats500", "grupp", "tat_boplats", inv = FALSE), H2_U_So = fit(U, "boplats500", "grupp", "tat_boplats"),
            H3_250 = fit(d, "bytomt250", "arv", "tat_bytomt"), H3_1000 = fit(d, "bytomt1000", "arv", "tat_bytomt"),
            H3_logavst = fit(d, "log_d_bytomt", "arv", "tat_bytomt", family = gaussian),
            H4_100 = fit(d, "vag100", "bro", "tat_vag"), H4_400 = fit(d, "vag400", "bro", "tat_vag"),
            H4_utan_inv = fit(d, "vag200", "bro", "tat_vag", inv = FALSE), H4_U_So = fit(U, "vag200", "bro", "tat_vag"))
write_json(list(plan = "analysplaner/2026-10-29-gard-gravfalt-vag.md", tests = res, robustness = rob),
           file.path(dir, "gard_vag.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
sg <- function(x, k = 3) if (is.null(x)) "–" else formatC(x, digits = k, format = "g")
for (k in names(res)) { r <- res[[k]]
  cat(sprintf("%s %-22s %s/%s  OR %s [%s, %s] p %s holm %s | A %s (%s) B %s (%s) | n=%d k=%d\n", k, r$status,
    sg(r$alla$andel_x1, 2), sg(r$alla$andel_x0, 2), sg(r$alla$or), sg(r$alla$lo, 2), sg(r$alla$hi, 2), sg(r$alla$p, 2),
    sg(r$holm, 2), sg(r$A$or, 2), sg(r$A$p, 2), sg(r$B$or, 2), sg(r$B$p, 2), r$alla$n, r$alla$k_x)) }
for (k in names(rob)) cat(sprintf("  %-12s %s p %s\n", k, if (!is.null(rob[[k]]$or)) paste("OR", sg(rob[[k]]$or)) else paste("beta", sg(rob[[k]]$beta)), sg(rob[[k]]$p, 2)))
