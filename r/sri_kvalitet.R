# Datakvalitet: SRI:s fyndhistorik mot appens egna fält (scripts/sri_kvalitet.py). Bara överensstämmelse,
# inga prov på A1:s frågor. Cohens kappa med 95 % bootstrapintervall (2 000 dragningar, slumpfrö 2026).
#   Rscript --vanilla r/sri_kvalitet.R stenar.csv utmapp
suppressPackageStartupMessages({ library(jsonlite) })
args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1], stringsAsFactors = FALSE, encoding = "UTF-8")
ut <- args[2]
set.seed(2026)

kappa <- function(a, b) {
  t <- table(factor(a, levels = 0:1), factor(b, levels = 0:1))
  n <- sum(t); po <- sum(diag(t)) / n
  pe <- sum(rowSums(t) * colSums(t)) / n^2
  if (pe == 1) return(NA_real_)
  (po - pe) / (1 - pe)
}
jamfor <- function(a, b, namn_a, namn_b) {
  ok <- !is.na(a) & !is.na(b)
  a <- a[ok]; b <- b[ok]
  t <- table(factor(a, levels = 0:1, labels = paste(namn_a, c("nej", "ja"))),
             factor(b, levels = 0:1, labels = paste(namn_b, c("nej", "ja"))))
  k <- kappa(a, b)
  bs <- replicate(2000, { i <- sample.int(length(a), replace = TRUE); kappa(a[i], b[i]) })
  list(n = length(a), tabell = as.data.frame.matrix(t), overens = round(mean(a == b), 4),
       kappa = round(k, 3), kappa95 = round(unname(quantile(bs, c(.025, .975), na.rm = TRUE)), 3))
}

# 1. SRI:s läge (flyttad = 1, ursprunglig plats = 0; okänt och försvunnen räknas inte) mot is_moved
l <- d[d$sri_lage %in% c("flyttad", "ursprunglig plats"), ]
l$sri_flyttad <- as.integer(l$sri_lage == "flyttad")
res <- list()
res$lage_mot_is_moved <- jamfor(l$sri_flyttad, l$is_moved, "SRI flyttad", "is_moved")
res$lage_mot_is_moved_per_landskap <- lapply(split(l, l$province), function(x)
  if (nrow(x) >= 20) jamfor(x$sri_flyttad, x$is_moved, "SRI flyttad", "is_moved") else list(n = nrow(x)))
# 2. SRI "försvunnen när bandet skrevs" mot Rundatas flags.lost (alla stenar med SRI-artikel)
res$forsvunnen_mot_rundata <- jamfor(d$sri_lost_at_edition, d$rundata_lost, "SRI försvunnen", "Rundata försvunnen")
# 3. SRI:s läge mot Runor 2020:s original (original sant = ursprunglig plats)
r <- l[l$runor_original %in% c("0", "1", 0, 1), ]
r$runor_flyttad <- 1L - as.integer(r$runor_original)
res$lage_mot_runor <- jamfor(r$sri_flyttad, r$runor_flyttad, "SRI flyttad", "Runor flyttad")
res$lage_fordelning <- as.list(table(d$sri_lage))
res$n_stenar <- nrow(d)

write_json(res, file.path(ut, "sri_kvalitet.json"), auto_unbox = TRUE, pretty = TRUE, digits = NA)
# oenigheterna med is_moved, som förslag till Viktor (tillägg 1)
o <- l[l$sri_flyttad != l$is_moved, c("signum", "province", "checked_by", "sri_lage", "is_moved", "sri_inmurad", "place", "placement")]
o$riktning <- ifelse(o$sri_lage == "flyttad", "SRI flyttad, appen orörd", "SRI ursprunglig plats, appen flyttad")
write.csv(o[order(o$riktning, o$province, o$signum), ], file.path(ut, "oenigheter_is_moved.csv"), row.names = FALSE)
cat(toJSON(res[c("n_stenar", "lage_mot_is_moved", "forsvunnen_mot_rundata", "lage_mot_runor")], auto_unbox = TRUE, pretty = TRUE), "\n")
