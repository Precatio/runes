# Fjädrundaland (låst plan analysplaner/2026-11-02-fjadrundaland.md, sha 6088f2af): T1 robusthet för sex drag, T2 ristaren
# eller landet.   Rscript utdata/fjadrundaland/fjadrundaland.R
suppressPackageStartupMessages({ library(lme4); library(jsonlite) })
d <- read.csv("utdata/fjadrundaland/fjadrundaland_stenar.csv", stringsAsFactors = FALSE)
d$fj <- as.integer(d$region == "fjadrundaland")
d$period <- relevel(factor(d$period), ref = "1010–1040")
base <- function(x) trimws(gsub("[0-9 ]+$", "", trimws(x)))
d$ck <- ifelse(d$carver == "" | is.na(d$carver), paste0("_", d$signum), base(d$carver))
fit <- function(z, y, x = "fj", re = FALSE) {
  z <- z[!is.na(z[[y]]), ]
  f <- as.formula(paste(y, "~ period +", x, if (re) "+ (1|ck)" else ""))
  m <- if (re) glmer(f, z, family = binomial, control = glmerControl(optimizer = "bobyqa")) else glm(f, z, family = binomial)
  m0 <- update(m, as.formula(paste(". ~ . -", x)))
  co <- if (re) fixef(m)[[x]] else coef(m)[[x]]
  list(n = nrow(z), k_in = sum(z[[y]][z[[x]] == 1]), n_in = sum(z[[x]] == 1), share_in = mean(z[[y]][z[[x]] == 1]),
       share_out = mean(z[[y]][z[[x]] == 0]), or = exp(co), p = pchisq(as.numeric(2 * (logLik(m) - logLik(m0))), 1, lower.tail = FALSE))
}
fj_carvers <- names(which(table(unlist(lapply(strsplit(d$carvers_all[d$fj == 1], ";"), base))) >= 5))
Y <- c("pm_kors", "r_for_R", "skilj_plus", "ord_ræisti", "i_grupp", "flera_resare")
T1 <- list()
for (y in Y) {
  g <- fit(d, y); up <- g$or > 1
  r <- list(grund = g, a_ristare_slump = tryCatch(fit(d, y, re = TRUE), error = function(e) list(p = NA, or = NA)),
            b_pa_plats = fit(d[d$moved == 0, ], y), c_daterade = fit(d[d$period != "odaterad", ], y),
            d_utan_forlorade = fit(d[d$lost == 0, ], y),
            e_utan_fjadrundalands_ristare = fit(d[!sapply(strsplit(d$carvers_all, ";"), function(v) any(base(v) %in% fj_carvers)), ], y))
  T1[[y]] <- lapply(r, function(x) c(x, holds = isTRUE(x$p < 0.05) && isTRUE((x$or > 1) == up)))
}
# T2: the same carver inside and outside Fjädrundaland
d$cb <- sapply(strsplit(d$carvers_all, ";"), function(v) if (length(v) == 1 && v != "") base(v) else NA)
T2 <- list(); ps <- c()
for (cv in names(which(table(d$cb[d$fj == 1]) >= 5))) {
  if (sum(d$cb == cv & d$fj == 0, na.rm = TRUE) < 5) next
  for (y in c("pm_kors", "r_for_R")) {
    z <- d[!is.na(d$cb) & d$cb == cv & !is.na(d[[y]]), ]
    tb <- table(factor(z$fj, levels = c(1, 0)), factor(z[[y]], levels = c(1, 0)))
    if (min(rowSums(tb)) < 5) next
    p <- fisher.test(tb)$p.value
    T2[[paste(cv, y)]] <- list(carver = cv, trait = y, in_k = tb[1, 1], in_n = sum(tb[1, ]), out_k = tb[2, 1], out_n = sum(tb[2, ]), p = p)
    ps[paste(cv, y)] <- p
  }
}
holm <- if (length(ps)) as.list(p.adjust(ps, "holm")) else list()
out <- list(plan = "analysplaner/2026-11-02-fjadrundaland.md", plan_sha = "6088f2af", fj_carvers = fj_carvers, T1 = T1, T2 = T2, holm = holm)
write_json(out, "utdata/fjadrundaland/fjadrundaland.json", auto_unbox = TRUE, digits = 6, pretty = TRUE, na = "null")
for (y in names(T1)) { cat("T1", y, "\n"); for (k in names(T1[[y]])) with(T1[[y]][[k]], cat(sprintf("  %-32s %s/%s  %s mot %s  OR %.2f p %.4f %s\n", k, k_in, n_in, round(100*share_in), round(100*share_out), or, p, holds))) }
for (k in names(T2)) with(T2[[k]], cat(sprintf("T2 %-22s i %d/%d  utanför %d/%d  p %.4f holm %.4f\n", k, in_k, in_n, out_k, out_n, p, holm[[k]])))
cat("ristare >=5:", fj_carvers, "\n")
