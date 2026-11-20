# Hundra år av runfrågor III, M4 (analysplaner/2026-11-20-hundra-ar-III.md + tillägg 1): nämnd i tidskrifterna minst
# en gång ~ landskap + stilgrupp + förlorad + ristare + log(textlängd + 1) + (1 | socken), mätbara stenar.
#   Rscript utdata/hundra_ar_iii/analys_m4.R
suppressPackageStartupMessages(library(lme4))
d <- read.csv("data/cache/hundra_ar_iii/stenar.csv", encoding = "UTF-8")
d$named <- as.integer(d$n_j > 0)
small <- names(which(table(d$landskap) < 20))
d$land <- ifelse(d$landskap %in% small, "övriga", d$landskap)
d$land <- relevel(factor(d$land), ref = "U")
d$stil <- relevel(factor(d$stil), ref = "Pr4")
d$loglen <- log(d$langd + 1)
m <- glmer(named ~ land + stil + forlorad + ristare + loglen + (1 | socken), data = d, family = binomial,
           control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5)))
ci <- confint(m, parm = "beta_", method = "Wald")
out <- data.frame(term = names(fixef(m)), or = round(exp(fixef(m)), 2), lo = round(exp(ci[, 1]), 2), hi = round(exp(ci[, 2]), 2))
cat("n =", nrow(d), " socknar =", length(unique(d$socken)), " sockenvarians =", round(VarCorr(m)$socken[1], 2), "\n")
print(out, row.names = FALSE)
write.csv(out, "utdata/hundra_ar_iii/m4.csv", row.names = FALSE)
