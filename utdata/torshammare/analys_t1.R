# T1 enligt analysplaner/2026-11-20-torshammare.md (låst 14a659e): hammare per härad ~ log2(runstenar + 1)
# + offset(log(exponering)) + (1 | landskap) + (1 | härad), poisson. Kvot per fördubbling av runstenarna, 95 % Wald.
# Läser data/cache/torshammare/harader.csv och harader_utan_adelso.csv (analys.py), skriver utdata/torshammare/t1.csv.
suppressMessages(library(lme4))
run <- function(file, y, label) {
  d <- read.csv(file, fileEncoding = "UTF-8")
  d$y <- d[[y]]
  m <- glmer(y ~ log2(runstenar + 1) + offset(log(exponering)) + (1 | landskap) + (1 | harad),
             data = d, family = poisson, control = glmerControl(optimizer = "bobyqa"))
  b <- fixef(m)[2]; se <- sqrt(diag(vcov(m)))[2]
  data.frame(modell = label, utfall = y, harader = nrow(d), hammare = sum(d$y), kvot = exp(b),
             lag = exp(b - 1.96 * se), hog = exp(b + 1.96 * se), p = 2 * pnorm(-abs(b / se)),
             singular = isSingular(m))
}
f <- "data/cache/torshammare/harader.csv"; g <- "data/cache/torshammare/harader_utan_adelso.csv"
out <- rbind(run(f, "hammare", "huvud"), run(g, "hammare", "utan Adelsö"),
             run(f, "ringar", "sekundär"), run(f, "hangen", "sekundär"))
print(out, digits = 3)
write.csv(out, "utdata/torshammare/t1.csv", row.names = FALSE)
