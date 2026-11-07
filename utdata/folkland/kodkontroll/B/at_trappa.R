# Tilläggsplan 2 (analysplaner/2026-11-01-folkland-at-trappa.md, sha 1ffcb5c6): at vid gränsen Tiundaland–Attundaland mot
# utrymmet (runor, namn), med socken, ett härad i taget och utan flyttade stenar.
#   Rscript utdata/folkland/at_trappa.R
suppressPackageStartupMessages({ library(lme4); library(jsonlite) })
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
d <- read.csv(file.path(here, "at_rader2.csv"), stringsAsFactors = FALSE, na.strings = "")
d$sida <- factor(ifelse(d$land == "tiundaland", "tiundaland", "attundaland"), levels = c("attundaland", "tiundaland"))
d$ristare <- factor(ifelse(!is.na(d$carver) & d$carver != "", d$carver, paste0("_", d$parish)))
d$socken <- factor(d$parish); d$period <- factor(d$period)
d$lruner <- log(pmax(d$runes, 1))
ctl <- glmerControl(optimizer = "bobyqa")
term <- function(m, t = "sidatiundaland") {
  if (is.null(m)) return(list(error = TRUE))
  s <- summary(m)$coefficients
  list(beta = s[t, 1], or = exp(s[t, 1]), z = s[t, 3], p1 = pnorm(s[t, 3], lower.tail = FALSE))
}
g <- function(f, x) tryCatch(glmer(f, family = binomial, data = droplevels(x), control = ctl), error = function(e) NULL)
B <- d[d$border == 1, ]
# 1 space
m1 <- g(prep_at ~ sida + lruner + names + period + (1 | ristare), B)
m1a <- g(prep_at ~ sida + lruner + names + period + (1 | ristare), d)
s1 <- list(border = c(term(m1), list(runes = term(m1, "lruner"), names = term(m1, "names"))),
           all = c(term(m1a), list(runes = term(m1a, "lruner"), names = term(m1a, "names"))))
s1$holds <- isTRUE(s1$border$p1 < 0.05)
# 2 parish
m2 <- g(prep_at ~ sida + period + (1 | ristare) + (1 | socken), B)
s2 <- c(term(m2)); s2$holds <- isTRUE(s2$p1 < 0.05)
# 3 one hundred at a time
big <- names(which(table(d$district) >= 15))
s3 <- lapply(big, function(h) {
  x <- d[is.na(d$district) | d$district != h, ]
  r <- term(g(prep_at ~ sida + period + (1 | ristare), x))
  c(list(harad = h, n_left = nrow(x), share_left = nrow(x) / nrow(d)), r)
})
ok3 <- all(vapply(s3, function(r) isTRUE(r$beta > 0), TRUE)) &&
  all(vapply(s3, function(r) r$share_left < 2 / 3 || isTRUE(r$p1 < 0.05), TRUE))
# 4 not moved
m4 <- g(prep_at ~ sida + period + (1 | ristare), B[is.na(B$moved) | B$moved != 1, ])
s4 <- c(term(m4), list(n = sum(is.na(B$moved) | B$moved != 1))); s4$holds <- isTRUE(s4$p1 < 0.05)
res <- list(plan = "analysplaner/2026-11-01-folkland-at-trappa.md", n = nrow(d), n_border = nrow(B),
            space = s1, parish = s2, hundreds = list(rows = s3, holds = ok3), unmoved = s4,
            all_hold = s1$holds && s2$holds && ok3 && s4$holds)
write_json(res, file.path(here, "at_trappa.json"), digits = NA, pretty = TRUE, auto_unbox = TRUE, na = "null")
str(s1, max.level = 2); str(s2); for (r in s3) cat(sprintf("utan %-28s n %3d  OR %.2f  p1 %.4f\n", r$harad, r$n_left, r$or, r$p1))
cat("härader håller:", ok3, "\n"); str(s4); cat("ALLA:", res$all_hold, "\n")
