# T2 enligt tillägg 1 (analysplaner/2026-11-21-torshammare-tillagg-1-kultplatser.md, låst 5b64d88).
# Läser data/cache/torshammare/socknar.csv (analys_t2.py), skriver utdata/torshammare/t2.csv.
suppressMessages(library(lme4))
d0 <- read.csv("data/cache/torshammare/socknar.csv", fileEncoding = "UTF-8")
fit <- function(d, y, kult, label, graves = TRUE) {
  d$y <- d[[y]]; d$k <- d[[kult]]
  f <- if (graves) y ~ k + log1p(gravfalt) + log1p(hog) + offset(log(exponering)) + (1 | landskap) + (1 | harad) + (1 | socken)
       else y ~ k + offset(log(exponering)) + (1 | landskap) + (1 | harad) + (1 | socken)
  r <- tryCatch({
    m <- glmer(f, data = d, family = poisson, control = glmerControl(optimizer = "bobyqa"))
    b <- fixef(m)["k"]; se <- sqrt(diag(vcov(m)))[2]
    c(exp(b), exp(b - 1.96 * se), exp(b + 1.96 * se), 2 * pnorm(-abs(b / se)), isSingular(m))
  }, error = function(e) c(NA, NA, NA, NA, NA))
  data.frame(modell = label, socknar = nrow(d), kultsocknar = sum(d$k), hammare = sum(d$y),
             hammare_i_kult = sum(d$y[d$k == 1]), kvot = r[1], lag = r[2], hog = r[3], p = r[4], singular = r[5])
}
out <- rbind(fit(d0, "hammare", "kult", "huvud"),
             fit(subset(d0, adelso == 0), "hammare", "kult", "utan Adelsö"),
             fit(d0, "hammare", "kult_saker", "bara säkra namn"),
             fit(d0, "ringar", "kult", "sekundär: ringar"),
             fit(d0, "hangen", "kult", "sekundär: hängen"),
             fit(d0, "hammare", "kult", "sekundär: utan gravkontroller", graves = FALSE))
print(out, digits = 3, row.names = FALSE)
write.csv(out, "utdata/torshammare/t2.csv", row.names = FALSE)
