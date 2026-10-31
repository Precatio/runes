# Kodningskontroll: samma modeller som robusthetsstegen (rå, justerad för landskap, ristaren som slumpeffekt, halvorna)
# med projektets regel och med den stränga kodningen (kodning.py). Tid = stilgruppens mittår i 50-årssteg.
#   Rscript utdata/monoftong/kodning.R
suppressMessages({library(lme4); library(jsonlite)})
d <- read.csv("utdata/monoftong/stenar.csv", stringsAsFactors = FALSE)
fit <- function(dd, y, rhs, re = FALSE) {
  small <- names(which(table(dd$province) < 10))
  dd$prov <- factor(ifelse(dd$province %in% small, "övriga", dd$province))
  f <- as.formula(paste(y, "~", rhs, if (re) "+ (1 | hand)"))
  m <- if (re) glmer(f, family = binomial, data = dd, control = glmerControl(optimizer = "bobyqa")) else glm(f, family = binomial, data = dd)
  s <- summary(m)$coefficients["t50", ]
  list(or = unname(exp(s[1])), lo = unname(exp(s[1] - 1.96 * s[2])), hi = unname(exp(s[1] + 1.96 * s[2])), p = unname(s[4]), n = nrow(dd))
}
out <- list()
for (y in c("y_rule", "y_strict")) {
  dd <- d[!is.na(d[[y]]), ]
  out[[y]] <- list(raw = fit(dd, y, "t50"), adjusted = fit(dd, y, "t50 + prov"), carver = fit(dd, y, "t50 + prov", TRUE),
                   half_A = fit(dd[dd$half == "A", ], y, "t50 + prov"), half_B = fit(dd[dd$half == "B", ], y, "t50 + prov"),
                   uppland = fit(dd[dd$province == "U", ], y, "t50"))
}
write_json(out, "utdata/monoftong/kodning_modeller.json", auto_unbox = TRUE, digits = 8, pretty = TRUE)
for (y in names(out)) for (k in names(out[[y]])) { r <- out[[y]][[k]]
  cat(sprintf("%-8s %-9s OR %.3f [%.3f, %.3f] p %.2g n %d\n", y, k, r$or, r$lo, r$hi, r$p, r$n)) }
