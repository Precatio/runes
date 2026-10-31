# Seriationen i Upplands halvor och i Södermanland enligt den låsta planen
# analysplaner/2026-10-31-seriation-halvor-sodermanland.md. Metoden är exakt r/chronology.R (incidensmatris, ca, första
# dimensionen, Spearman mot stilgruppens mittår, riktningen vänd så att rho blir positiv, partiell korrelation med
# latituden konstant), körd på olika urval.
#   Rscript utdata/seriation/replikering.R kontroll   # provkörningen: hela Uppland, ska ge rho 0,543
#   Rscript utdata/seriation/replikering.R            # prövningarna
.args <- commandArgs(trailingOnly = TRUE)
source("r/common.R")
suppressPackageStartupMessages({library(ca); library(dplyr); library(jsonlite)})
C <- "data/cache/r/corpus/e83202e01a5e6d27"
MIN_ATTR <- 15; MIN_PER_STONE <- 4
d0 <- read_corpus(file.path(C, "corpus.csv"))
tc <- trait_cols(d0); cc <- cat_cols(d0)
txt <- read.csv(file.path(C, "text_features.csv"), encoding = "UTF-8", check.names = FALSE)
fcols <- grep("^formula_", names(txt), value = TRUE)
d0 <- d0 %>% left_join(txt[, c("signum", fcols)], by = "signum")
FL <- c(formula_raising = "Resarformel", formula_monument = "Monument", formula_order = "Ordföljd",
        formula_signature = "Ristarsignatur", formula_prayer = "Bön")
TL <- TRAIT_LABELS; CL <- CAT_LABELS
levels_of <- function(col, labels, d) {
  v <- d[[col]]
  ok <- !is.na(v) & !(v %in% c("ingen", "ej bestämbar"))
  out <- matrix(0L, nrow(d), 0)
  for (lv in sort(unique(v[ok]))) {
    m <- matrix(as.integer(ok & v == lv), ncol = 1, dimnames = list(NULL, paste0(labels[[col]], ": ", trv(lv))))
    out <- cbind(out, m)
  }
  out
}
incidence <- function(d) {
  I <- do.call(cbind, c(lapply(tc, levels_of, labels = TL, d = d), lapply(fcols, levels_of, labels = FL, d = d)))
  extra <- cbind(d$cross, d$short_twig); colnames(extra) <- c("Kors", "Kortkvistrunor")
  I <- cbind(I, extra)
  CI <- as.matrix(d[, cc]); colnames(CI) <- unname(CL[cc])
  I <- cbind(I, CI)
  I <- I[, colSums(I) >= MIN_ATTR, drop = FALSE]
  keep <- rowSums(I) >= MIN_PER_STONE
  I <- I[keep, , drop = FALSE]
  list(I = I[, colSums(I) > 0, drop = FALSE], keep = keep)
}
seriate <- function(d) {
  inc <- incidence(d); dd <- d[inc$keep, ]
  fit <- ca(inc$I, nd = 3)
  score <- fit$rowcoord[, 1]
  dd$mid <- ifelse(!is.na(dd$style_from), (dd$style_from + dd$style_to) / 2, NA)
  dated <- !is.na(dd$mid)
  rho0 <- suppressWarnings(cor(score[dated], dd$mid[dated], method = "spearman"))
  if (!is.na(rho0) && rho0 < 0) score <- -score
  ct <- suppressWarnings(cor.test(score[dated], dd$mid[dated], method = "spearman", exact = FALSE))
  ok <- dated & !is.na(dd$lat)
  r_sm <- rank(score[ok]); r_t <- rank(dd$mid[ok]); r_l <- rank(dd$lat[ok])
  partial <- cor(resid(lm(r_sm ~ r_l)), resid(lm(r_t ~ r_l)))
  g <- dd$district[dated]; keepg <- !is.na(g) & g != "" & g %in% names(which(table(g) >= 5))
  rs <- rank(score[dated][keepg]); rt <- rank(dd$mid[dated][keepg]); gg <- g[keepg]
  within <- if (sum(keepg) >= 30) cor(rs - ave(rs, gg), rt - ave(rt, gg)) else NA
  list(n_stones = nrow(dd), n_dated = sum(dated), n_attributes = ncol(inc$I), rho = unname(ct$estimate), p = ct$p.value,
       partial_rho = partial, within_district = within, n_districts = length(unique(gg)),
       inertia_pct = 100 * fit$sv[1]^2 / sum(fit$sv^2))
}
U <- d0 %>% filter(province == "U")
if (length(.args) && .args[1] == "kontroll") {
  r <- seriate(U); cat(sprintf("KONTROLL hela Uppland: rho %.3f (väntat 0,543), daterade %d (väntat 501)\n", r$rho, r$n_dated))
  quit(save = "no")
}
# The halves, the rule of r/change.R: parishes ordered by mean dating within the province, alternating A/B
d0$t50 <- ifelse(!is.na(d0$style_from), ((d0$style_from + d0$style_to) / 2 - 1050) / 50, NA)
pkey <- ifelse(is.na(d0$parish) | d0$parish == "", paste0("_", d0$signum), d0$parish)
pinfo <- data.frame(province = d0$province, pk = pkey, t = d0$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d0$half <- pinfo$half[match(paste(d0$province, pkey), paste(pinfo$province, pinfo$pk))]
U <- d0 %>% filter(province == "U")
res <- list(plan = "analysplaner/2026-10-31-seriation-halvor-sodermanland.md", corpus = "e83202e01a5e6d27",
            uppland = seriate(U), half_A = seriate(U %>% filter(half == "A")), half_B = seriate(U %>% filter(half == "B")),
            sodermanland = seriate(d0 %>% filter(province == "Sö")))
ps <- c(res$half_A$p, res$half_B$p, res$sodermanland$p)
holm <- p.adjust(ps, "holm")
res$half_A$p_holm <- holm[1]; res$half_B$p_holm <- holm[2]; res$sodermanland$p_holm <- holm[3]
ok <- function(r) r$p_holm < 0.05 && r$rho >= 0.3
res$halves_hold <- ok(res$half_A) && ok(res$half_B)
s <- res$sodermanland
res$sodermanland_status <- if (s$p_holm < 0.05 && s$rho >= 0.3) "replikerat" else if (s$p_holm < 0.05) "delvis replikerat" else "inte replikerat"
res$sodermanland_geografi <- s$rho >= 0.3 && s$partial_rho < 0.3
write_json(res, "utdata/seriation/replikering.json", auto_unbox = TRUE, digits = 8, pretty = TRUE)
for (k in c("uppland", "half_A", "half_B", "sodermanland")) { r <- res[[k]]
  cat(sprintf("%-13s stenar %4d daterade %4d drag %3d rho %.3f p %.2g Holm %s partiell %.3f inom härad %s (%d)\n", k,
              r$n_stones, r$n_dated, r$n_attributes, r$rho, r$p, if (is.null(r$p_holm)) "–" else signif(r$p_holm, 2),
              r$partial_rho, if (is.na(r$within_district)) "–" else sprintf("%.3f", r$within_district), r$n_districts)) }
cat("HALVORNA:", if (res$halves_hold) "håller" else "håller inte", " SÖDERMANLAND:", res$sodermanland_status,
    if (res$sodermanland_geografi) "(kan vara geografiskt)" else "", "\n")
