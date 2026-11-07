# Tilläggsplanen analysplaner/2026-11-01-folkland-at-ristare.md (sha c4c4f5ba): prepositionen at vid gränsen
# Tiundaland–Attundaland med ristaren som slumpeffekt, och samma ristare på båda sidor.
#   Rscript utdata/folkland/at_ristare.R
suppressPackageStartupMessages({ library(lme4); library(jsonlite) })
here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
d <- read.csv(file.path(here, "at_rader.csv"), stringsAsFactors = FALSE, na.strings = "")
d$sida <- factor(ifelse(d$land == "tiundaland", "tiundaland", "attundaland"), levels = c("attundaland", "tiundaland"))
d$named <- !is.na(d$carver) & d$carver != ""
d$ristare <- factor(ifelse(d$named, d$carver, paste0("_", d$parish)))
d$period <- factor(d$period)
fit <- function(x) {
  m <- tryCatch(glmer(prep_at ~ sida + period + (1 | ristare), family = binomial, data = droplevels(x),
                      control = glmerControl(optimizer = "bobyqa")), error = function(e) NULL)
  if (is.null(m)) return(list(error = TRUE))
  s <- summary(m)$coefficients
  list(n = nrow(x), beta = s["sidatiundaland", 1], se = s["sidatiundaland", 2], or = exp(s["sidatiundaland", 1]),
       p = s["sidatiundaland", 4], p1 = pnorm(s["sidatiundaland", 3], lower.tail = FALSE),
       ristare_sd = as.data.frame(VarCorr(m))$sdcor[1])
}
s1 <- list(border = fit(d[d$border == 1, ]), all = fit(d))
# 2: named carvers with ≥ 2 stones on each side
nm <- d[d$named, ]
tab <- do.call(rbind, lapply(split(nm, nm$carver), function(x) {
  t <- x[x$land == "tiundaland", ]; a <- x[x$land == "attundaland", ]
  data.frame(carver = x$carver[1], n_t = nrow(t), at_t = sum(t$prep_at), n_a = nrow(a), at_a = sum(a$prep_at))
}))
both <- tab[tab$n_t >= 2 & tab$n_a >= 2, ]
both$share_t <- both$at_t / both$n_t; both$share_a <- both$at_a / both$n_a
nt <- sum(both$share_t > both$share_a); na <- sum(both$share_t < both$share_a)
sign_p <- if (nt + na > 0) binom.test(nt, nt + na, alternative = "greater")$p.value else NA
# 3: how many named stones belong to carvers with stones on both sides
any_both <- tab$carver[tab$n_t >= 1 & tab$n_a >= 1]
s3 <- list(named_stones = nrow(nm), carvers = nrow(tab), carvers_both_sides = length(any_both),
           stones_by_both_side_carvers = sum(nm$carver %in% any_both))
# descriptive: the named carvers with most stones, per side
top <- tab[order(-(tab$n_t + tab$n_a)), ][1:min(15, nrow(tab)), ]
res <- list(plan = "analysplaner/2026-11-01-folkland-at-ristare.md", n = nrow(d), n_border = sum(d$border),
            step1 = s1, holds_with_carvers = isTRUE(s1$border$p1 < 0.05),
            step2 = list(carvers = both, tiund_higher = nt, attund_higher = na, ties = nrow(both) - nt - na, sign_p = sign_p),
            step3 = s3, top_carvers = top)
write_json(res, file.path(here, "at_ristare.json"), digits = NA, pretty = TRUE, auto_unbox = TRUE, na = "null")
str(s1); print(both); cat("teckentest", nt, "mot", na, "p", sign_p, "\n"); str(s3); print(top)
