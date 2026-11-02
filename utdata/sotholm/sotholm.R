# Sotholms härad (låst plan analysplaner/2026-11-02-sotholm.md, sha 9fa481d3): T1–T4.
#   Rscript utdata/sotholm/sotholm.R
suppressPackageStartupMessages({ library(lme4); library(jsonlite) })
d <- read.csv("utdata/sotholm/sotholm_stenar.csv", stringsAsFactors = FALSE)
d$so <- as.integer(d$harad == "Sotholms hd")
d$period <- relevel(factor(d$period), ref = "1010–1040")
base <- function(x) trimws(gsub("[0-9 ]+$", "", trimws(x)))
fit <- function(z, y = "cat_kristen", x = "so", re = FALSE) {
  z <- z[!is.na(z[[y]]), ]
  f <- as.formula(paste(y, "~ period +", x, if (re) "+ (1|ck)" else ""))
  m <- if (re) glmer(f, z, family = binomial, control = glmerControl(optimizer = "bobyqa")) else glm(f, z, family = binomial)
  m0 <- update(m, as.formula(paste(". ~ . -", x)))
  lr <- as.numeric(2 * (logLik(m) - logLik(m0)))
  co <- if (re) fixef(m)[[x]] else coef(m)[[x]]
  list(n = nrow(z), n_in = sum(z[[x]] == 1), k_in = sum(z[[y]][z[[x]] == 1]), share_in = mean(z[[y]][z[[x]] == 1]),
       share_out = mean(z[[y]][z[[x]] == 0]), log_or = co, or = exp(co), p = pchisq(lr, 1, lower.tail = FALSE))
}
d$ck <- ifelse(d$carver == "" | is.na(d$carver), paste0("_", d$signum), base(d$carver))
so_carvers <- names(which(table(unlist(lapply(strsplit(d$carvers_all[d$so == 1], ";"), base))) >= 5))
T1 <- list(
  grund = fit(d),
  a_ristare_slump = fit(d, re = TRUE),
  b_pa_plats = fit(d[d$moved == 0, ]),
  c_daterade = fit(d[d$period != "odaterad", ]),
  d_utan_forlorade = fit(d[d$lost == 0, ]),
  e_utan_sotholms_ristare = fit(d[!sapply(strsplit(d$carvers_all, ";"), function(v) any(base(v) %in% so_carvers)), ])
)
T1 <- lapply(T1, function(r) c(r, holds = r$p < 0.05 && r$log_or < 0))
T2 <- fit(d, y = "pm_kors")
d$sv <- as.integer(d$harad %in% c("Svartlösa hd", "Öknebo hd"))
T3 <- fit(d[d$so == 0, ], x = "sv")
yr <- suppressWarnings(as.numeric(d$year))
mw <- wilcox.test(yr[d$so == 1], yr[d$so == 0])
T4 <- list(median_so = median(yr[d$so == 1], na.rm = TRUE), median_rest = median(yr[d$so == 0], na.rm = TRUE),
           mean_so = mean(yr[d$so == 1], na.rm = TRUE), mean_rest = mean(yr[d$so == 0], na.rm = TRUE), p = mw$p.value,
           per_period = lapply(split(d, d$period), function(z) list(
             so = c(sum(z$cat_kristen[z$so == 1], na.rm = TRUE), sum(z$so == 1 & !is.na(z$cat_kristen))),
             rest = c(sum(z$cat_kristen[z$so == 0], na.rm = TRUE), sum(z$so == 0 & !is.na(z$cat_kristen))))))
ps <- c(T2 = T2$p, T3 = T3$p, T4 = T4$p)
holm <- p.adjust(ps, "holm")
out <- list(plan = "analysplaner/2026-11-02-sotholm.md", plan_sha = "9fa481d3", so_carvers = so_carvers,
            T1 = T1, T1_all_hold = all(sapply(T1, `[[`, "holds")), T2 = T2, T3 = T3, T4 = T4, holm = as.list(holm))
write_json(out, "utdata/sotholm/sotholm.json", auto_unbox = TRUE, digits = 6, pretty = TRUE)
str(lapply(T1, function(r) round(unlist(r[c("n", "k_in", "n_in", "share_in", "share_out", "or", "p")]), 4)))
cat("T2 kors", round(unlist(T2[c("k_in","n_in","share_in","share_out","or","p")]),4), "\n")
cat("T3 Svartlösa+Öknebo", round(unlist(T3[c("k_in","n_in","share_in","share_out","or","p")]),4), "\n")
cat("T4 år", round(unlist(T4[c("median_so","median_rest","mean_so","mean_rest","p")]),4), "\n"); print(holm)
