# T2 enligt analysplaner/2026-11-21-bjornen.md (låst 1779c2e): björnnamn ~ skog + log(namn + 1) + (1 | härad).
suppressMessages(library(lme4))
d0 <- read.csv("data/cache/bjornen/stenar.csv", fileEncoding = "UTF-8")
fit <- function(d, label) {
  d <- subset(d, grupp %in% c("skog", "malar"))
  d$skog <- as.integer(d$grupp == "skog")
  m <- tryCatch(glmer(bjorn ~ skog + log(namn + 1) + (1 | harad), data = d, family = binomial,
                      control = glmerControl(optimizer = "bobyqa")), error = function(e) NULL)
  if (is.null(m)) return(data.frame(modell = label, stenar = nrow(d), kvot = NA, lag = NA, hog = NA, p = NA, konvergerade = FALSE))
  b <- fixef(m)["skog"]; se <- sqrt(diag(vcov(m)))[2]
  data.frame(modell = label, stenar = nrow(d), skog_stenar = sum(d$skog), kvot = exp(b), lag = exp(b - 1.96 * se),
             hog = exp(b + 1.96 * se), p = 2 * pnorm(-abs(b / se)), konvergerade = is.null(m@optinfo$conv$lme4$messages))
}
out <- rbind(fit(d0, "huvud"), fit(subset(d0, landskap != "Sm"), "utan Småland"))
print(out, digits = 3, row.names = FALSE)
write.csv(out, "utdata/bjornen/t2.csv", row.names = FALSE)
