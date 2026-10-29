# H1 och H4 enligt analysplaner/2026-10-29-namnen-som-levde-kvar.md: logistisk regression på förnamnsbeläggen
# (viktade med antal), klusterrobusta medelfel per brev (sandwich). Anropas av analys.py.
suppressPackageStartupMessages({ library(sandwich); library(lmtest); library(jsonlite) })
dir <- commandArgs(trailingOnly = TRUE)[1]
d <- read.csv(file.path(dir, "namn_belagg.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
d <- d[!is.na(d$ar), ]
d$t50 <- (d$ar - 1400) / 50
d$kvinna <- as.integer(d$kon == "k")
fit <- function(dd, f, term) {
  m <- suppressWarnings(glm(f, family = binomial, data = dd, weights = n))
  ct <- coeftest(m, vcov = vcovCL(m, cluster = dd$brev))
  list(n = sum(dd$n), brev = length(unique(dd$brev)), or = exp(ct[term, 1]),
       lo = exp(ct[term, 1] - 1.96 * ct[term, 2]), hi = exp(ct[term, 1] + 1.96 * ct[term, 2]), p = ct[term, 4])
}
run <- function(f, term, dd = d) list(alla = fit(dd, f, term), A = fit(dd[dd$halva == "A", ], f, term),
                                      B = fit(dd[dd$halva == "B", ], f, term))
H1 <- run(nordiskt ~ t50, "t50")
H4 <- run(nordiskt ~ kvinna + t50, "kvinna")
top <- names(sort(tapply(d$n, d$normalform, sum), decreasing = TRUE))[1:150]
mag <- d; mag$nordiskt[mag$normalform == "Magnus"] <- 1L
sth <- d[!grepl("(?i)stock|stok", d$ort), ]
rob <- list(H1_saekra = fit(d[d$normalform %in% top, ], nordiskt ~ t50, "t50"),
            H1_magnus_nordiskt = fit(mag, nordiskt ~ t50, "t50"),
            H1_utan_stockholm = fit(sth, nordiskt ~ t50, "t50"),
            H4_saekra = fit(d[d$normalform %in% top, ], nordiskt ~ kvinna + t50, "kvinna"),
            H4_utan_stockholm = fit(sth, nordiskt ~ kvinna + t50, "kvinna"))
write_json(list(H1 = H1, H4 = H4, robusthet = rob), file.path(dir, "modeller.json"), auto_unbox = TRUE, digits = NA)
