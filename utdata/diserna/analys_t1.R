# T1 enligt analysplaner/2026-11-21-diserna.md (låst 63420aa): dis ~ svealand + (1 | härad), kvinnor på runstenar.
suppressMessages(library(lme4))
d0 <- read.csv("data/cache/diserna/kvinnor.csv", fileEncoding = "UTF-8")
d0 <- subset(d0, grupp %in% c("svealand", "gotaland")); d0$sv <- as.integer(d0$grupp == "svealand")
fit <- function(d, label) {
  m <- tryCatch(glmer(dis ~ sv + (1 | harad), data = d, family = binomial, control = glmerControl(optimizer = "bobyqa")),
                error = function(e) NULL, warning = function(w) NULL)
  ft <- fisher.test(table(d$sv, d$dis))
  out <- data.frame(modell = label, kvinnor = nrow(d), dis = sum(d$dis), dis_svea = sum(d$dis[d$sv == 1]), n_svea = sum(d$sv),
                    dis_gota = sum(d$dis[d$sv == 0]), n_gota = sum(d$sv == 0), fisher_or = unname(ft$estimate),
                    fisher_lag = ft$conf.int[1], fisher_hog = ft$conf.int[2], fisher_p = ft$p.value)
  if (!is.null(m)) {
    b <- fixef(m)["sv"]; se <- sqrt(diag(vcov(m)))[2]
    out$glmer_kvot <- exp(b); out$glmer_lag <- exp(b - 1.96 * se); out$glmer_hog <- exp(b + 1.96 * se); out$glmer_p <- 2 * pnorm(-abs(b / se))
  } else { out$glmer_kvot <- NA; out$glmer_lag <- NA; out$glmer_hog <- NA; out$glmer_p <- NA }
  out
}
out <- rbind(fit(d0, "huvud"), fit(subset(d0, kon_ur_text == 1), "kön ur relation/formel"))
print(out, digits = 3, row.names = FALSE)
write.csv(out, "utdata/diserna/t1.csv", row.names = FALSE)
