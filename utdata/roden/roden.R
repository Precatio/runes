# Roden (låst plan analysplaner/2026-11-02-roden.md, sha 59ea6d58): T1 robusthet, T2 kusten eller landet, T3 färderna.
#   Rscript utdata/roden/roden.R <hav1000_U.gpkg>
suppressPackageStartupMessages({ library(lme4); library(jsonlite); library(sf) })
sf_use_s2(FALSE)
hav <- commandArgs(TRUE)[1]
d <- read.csv("utdata/roden/roden_stenar.csv", stringsAsFactors = FALSE)
d$ro <- as.integer(d$region == "roden")
d$period <- relevel(factor(d$period), ref = "1010–1040")
base <- function(x) trimws(gsub("[0-9 ]+$", "", trimws(x)))
d$ck <- ifelse(d$carver == "" | is.na(d$carver), paste0("_", d$signum), base(d$carver))
# distance to the sea of AD 1000
sea <- st_union(st_make_valid(st_geometry(st_read(hav, quiet = TRUE))))
pts <- st_transform(st_as_sf(d, coords = c("lon", "lat"), crs = 4326), 3006)
d$km <- as.numeric(st_distance(pts, sea)) / 1000
d$lkm <- log(d$km + 0.1)
fit <- function(z, y, x = "ro", re = FALSE, extra = "") {
  z <- z[!is.na(z[[y]]), ]
  f <- as.formula(paste(y, "~ period +", x, extra, if (re) "+ (1|ck)" else ""))
  m <- if (re) glmer(f, z, family = binomial, control = glmerControl(optimizer = "bobyqa")) else glm(f, z, family = binomial)
  m0 <- update(m, as.formula(paste(". ~ . -", x)))
  co <- if (re) fixef(m)[[x]] else coef(m)[[x]]
  list(n = nrow(z), k_in = sum(z[[y]][z[[x]] == 1]), n_in = sum(z[[x]] == 1), share_in = mean(z[[y]][z[[x]] == 1]),
       share_out = mean(z[[y]][z[[x]] == 0]), or = exp(co), p = pchisq(as.numeric(2 * (logLik(m) - logLik(m0))), 1, lower.tail = FALSE))
}
ro_carvers <- names(which(table(unlist(lapply(strsplit(d$carvers_all[d$ro == 1], ";"), base))) >= 5))
T1 <- list()
for (y in c("pm_kors", "cat_kristen")) {
  r <- list(grund = fit(d, y), a_ristare_slump = fit(d, y, re = TRUE), b_pa_plats = fit(d[d$moved == 0, ], y),
            c_daterade = fit(d[d$period != "odaterad", ], y), d_utan_forlorade = fit(d[d$lost == 0, ], y),
            e_utan_rodens_ristare = fit(d[!sapply(strsplit(d$carvers_all, ";"), function(v) any(base(v) %in% ro_carvers)), ], y))
  T1[[y]] <- lapply(r, function(x) c(x, holds = x$p < 0.05 && x$or < 1))
}
T2 <- lapply(c(pm_kors = "pm_kors", cat_kristen = "cat_kristen"), function(y) {
  w <- fit(d, y, extra = "+ lkm")
  c(w, holds = w$p < 0.05 && w$or < 1, dist_only = list(fit(d[d$ro == 0, ], y, x = "lkm")))
})
T3 <- lapply(c(cat_fard = "cat_fard", msg_dod_borta = "msg_dod_borta"), function(y) fit(d, y))
ps <- c(T2_kors = T2$pm_kors$p, T2_kristen = T2$cat_kristen$p, T3_fard = T3$cat_fard$p, T3_borta = T3$msg_dod_borta$p)
holm <- p.adjust(ps, "holm")
desc <- list(km_median_roden = median(d$km[d$ro == 1]), km_median_rest = median(d$km[d$ro == 0]),
             ro_carvers = ro_carvers, n_roden = sum(d$ro), n_tby = sum(d$ro == 1 & d$parish == "Täby sn"))
out <- list(plan = "analysplaner/2026-11-02-roden.md", plan_sha = "59ea6d58", T1 = T1, T2 = T2, T3 = T3, holm = as.list(holm), desc = desc)
write_json(out, "utdata/roden/roden.json", auto_unbox = TRUE, digits = 6, pretty = TRUE)
for (y in names(T1)) { cat("T1", y, "\n"); for (k in names(T1[[y]])) with(T1[[y]][[k]], cat(sprintf("  %-24s %d/%d %.0f%% mot %.0f%%  OR %.2f p %.4f %s\n", k, k_in, n_in, 100*share_in, 100*share_out, or, p, holds))) }
for (y in names(T2)) with(T2[[y]], cat(sprintf("T2 %s Roden med avstånd: OR %.2f p %.4f håller %s | avstånd inom resten: OR %.2f p %.4f\n", y, or, p, holds, dist_only$or, dist_only$p)))
for (y in names(T3)) with(T3[[y]], cat(sprintf("T3 %s %d/%d %.0f%% mot %.0f%% OR %.2f p %.4f\n", y, k_in, n_in, 100*share_in, 100*share_out, or, p)))
print(holm); str(desc)
