# Namn och släkt (IMPLEMENTATIONSPLAN 5.4) enligt den låsta planen analysplaner/2026-11-02-namn-och-slakt.md (sha bf6e080a).
#   Rscript r/names.R params.json utmapp
# params: names_pairs (förälder–barn- och syskonpar med namnled, src/names_data.py), names_stones (en rad per runsten med
# namnnycklar), names_family (släktlänkarna sammanfattade), seed.
#   1 namnled i arv: delat namnled mot omblandning av partnern inom den gamla regionen; båda halvorna
#   2 grannar delar namn: andelen stenpar i samma region som delar ett ovanligt namn, per avståndsband; < 1 km mot
#     omblandning av namnlistorna inom regionen
#   3 namnens geografi: namn (≥ 10 stenar) × region (≥ 30 stenar), Fisher, BH, båda halvorna
#   4 namnskicket per region: överskottet av delat namnled per region (≥ 40 par), skillnaden prövad med omblandning
#   5 släktmönster: beskrivande, ur länkarna
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(dplyr); library(Matrix) })

a <- cli_args(); P <- a$params; out <- a$out
set.seed(if (is.null(P$seed)) 2026 else P$seed)
NPERM <- 9999
MIN_NAME <- 10; MIN_REGION <- 30; MIN_PAIRS <- 40
BANDS <- c(0, 1, 5, 20, 50)

if (is.null(P$names_pairs) || !file.exists(P$names_pairs)) {
  write_result(list(available = FALSE, note = "Namnunderlaget saknas (src/names_data.py)."), out, "names")
  quit(save = "no")
}
pr <- read.csv(P$names_pairs, encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
st <- read.csv(P$names_stones, encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
fam <- if (!is.null(P$names_family) && file.exists(P$names_family)) jsonlite::fromJSON(P$names_family, simplifyVector = FALSE) else NULL

# ---- 1 namnled i arv ----------------------------------------------------------------------------------------------
# every name in a pair as an index; a name × name matrix of "shares an element or is the same name"
nm <- sort(unique(c(pr$a, pr$b)))
parts <- strsplit(setNames(c(pr$a_parts, pr$b_parts), c(pr$a, pr$b))[nm], "\\|")
allp <- sort(unique(unlist(parts)))
I <- sparseMatrix(i = rep(seq_along(nm), lengths(parts)), j = match(unlist(parts), allp), x = 1,
                  dims = c(length(nm), length(allp)))
M <- as.matrix(tcrossprod(I) > 0); diag(M) <- TRUE
pr$ia <- match(pr$a, nm); pr$ib <- match(pr$b, nm)
pr$obs <- M[cbind(pr$ia, pr$ib)]
perm_within <- function(g) { idx <- seq_along(g); for (ix in split(idx, g)) idx[ix] <- ix[sample.int(length(ix))]; idx }
inherit <- function(x, nperm = NPERM) {
  if (nrow(x) < 10) return(list(pairs = nrow(x)))
  obs <- mean(x$obs)
  sims <- vapply(seq_len(nperm), function(i) mean(M[cbind(x$ia, x$ib[perm_within(x$region)])]), 0)
  list(pairs = nrow(x), share = r3(obs), expected = r3(mean(sims)), ratio = r3(obs / mean(sims)),
       p = signif((1 + sum(sims >= obs)) / (nperm + 1), 3))
}
s1 <- lapply(c(pc = "pc", sib = "sib"), function(k) {
  x <- pr[pr$kind == k, ]
  c(inherit(x), list(halves = lapply(c(A = "A", B = "B"), function(h) inherit(x[x$half == h, ]))))
})
for (k in names(s1)) s1[[k]]$holds <- isTRUE(s1[[k]]$p < 0.05) && all(vapply(s1[[k]]$halves, function(h) isTRUE(h$p < 0.05), TRUE))

# ---- 4 namnskicket per region (expected per pair from permutations within the region) --------------------------------
pc <- pr[pr$kind == "pc", ]
acc <- numeric(nrow(pc))
for (i in seq_len(1999)) acc <- acc + M[cbind(pc$ia, pc$ib[perm_within(pc$region)])]
pc$excess <- pc$obs - acc / 1999
big_pc <- names(which(table(pc$region) >= MIN_PAIRS))
pcb <- pc[pc$region %in% big_pc, ]
by_reg <- pcb %>% group_by(region) %>% summarise(pairs = n(), share = r3(mean(obs)), excess = r3(mean(excess)), .groups = "drop")
het <- function(r) { m <- tapply(pcb$excess, r, mean); var(m) }
h_obs <- het(pcb$region)
h_sims <- vapply(seq_len(NPERM), function(i) het(sample(pcb$region)), 0)
s4 <- list(regions = by_reg, var = signif(h_obs, 3), p = signif((1 + sum(h_sims >= h_obs)) / (NPERM + 1), 3))

# ---- 2 grannar delar namn ------------------------------------------------------------------------------------------
stn <- st[!is.na(st$lat) & !is.na(st$lon) & !is.na(st$names) & st$names != "", ]
keys <- strsplit(stn$names, "\\|")
common <- names(sort(table(unlist(keys)), decreasing = TRUE))[seq_len(min(60, length(unique(unlist(keys)))))]
keys <- lapply(keys, function(k) setdiff(unique(k), common))
ok <- lengths(keys) > 0
stn <- stn[ok, ]; keys <- keys[ok]
uk <- sort(unique(unlist(keys)))
S <- sparseMatrix(i = rep(seq_len(nrow(stn)), lengths(keys)), j = match(unlist(keys), uk), x = 1, dims = c(nrow(stn), length(uk)))
xy <- cbind(stn$lon * 111.2 * cos(stn$lat * pi / 180), stn$lat * 111.2)
pairs <- do.call(rbind, lapply(split(seq_len(nrow(stn)), stn$region), function(ix) {
  if (length(ix) < 2) return(NULL)
  cmb <- t(combn(ix, 2))
  d <- sqrt(rowSums((xy[cmb[, 1], , drop = FALSE] - xy[cmb[, 2], , drop = FALSE])^2))
  keep <- d < max(BANDS)
  data.frame(i = cmb[keep, 1], j = cmb[keep, 2], km = d[keep])
}))
pairs$band <- cut(pairs$km, BANDS, right = FALSE, labels = c("<1", "1–5", "5–20", "20–50"))
shared <- function(Sm, i, j) rowSums(Sm[i, , drop = FALSE] * Sm[j, , drop = FALSE]) > 0
pairs$sh <- shared(S, pairs$i, pairs$j)
bands <- pairs %>% group_by(band) %>% summarise(pairs = n(), share = r3(mean(sh)), .groups = "drop")
base <- bands$share[bands$band == "20–50"]
bands$ratio <- r3(bands$share / base)
near_test <- function(rows) {
  pn <- pairs[pairs$band == "<1" & rows[pairs$i] & rows[pairs$j], ]
  if (nrow(pn) < 10) return(list(pairs = nrow(pn)))
  obs <- mean(pn$sh)
  sims <- vapply(seq_len(NPERM), function(k) { o <- perm_within(stn$region); mean(shared(S[o, , drop = FALSE], pn$i, pn$j)) }, 0)
  list(pairs = nrow(pn), share = r3(obs), expected = r3(mean(sims)), ratio = r3(obs / mean(sims)),
       p = signif((1 + sum(sims >= obs)) / (NPERM + 1), 3))
}
s2 <- c(near_test(rep(TRUE, nrow(stn))), list(bands = bands,
        halves = lapply(c(A = "A", B = "B"), function(h) near_test(stn$half == h))))
s2$holds <- isTRUE(s2$p < 0.05) && all(vapply(s2$halves, function(h) isTRUE(h$p < 0.05), TRUE))

# ---- 3 namnens geografi -------------------------------------------------------------------------------------------
allkeys <- strsplit(ifelse(is.na(st$names), "", st$names), "\\|")
regs <- names(which(table(st$region) >= MIN_REGION))
cnt <- table(unlist(lapply(allkeys, unique)))
cand <- names(cnt[cnt >= MIN_NAME])
has <- function(nm_, rows) vapply(allkeys[rows], function(k) nm_ %in% k, TRUE)
geo <- do.call(rbind, lapply(cand, function(n_) {
  h <- has(n_, seq_len(nrow(st)))
  do.call(rbind, lapply(regs, function(r) {
    inr <- st$region == r
    t <- matrix(c(sum(h & inr), sum(!h & inr), sum(h & !inr), sum(!h & !inr)), 2)
    f <- fisher.test(t)
    data.frame(name = n_, region = r, k_in = t[1, 1], n_in = sum(inr), k_out = t[1, 2], n_out = sum(!inr),
               or = unname(f$estimate), p = f$p.value)
  }))
}))
geo$q <- p.adjust(geo$p, "BH")
sig <- geo[geo$q < 0.05 & geo$or > 1, ]
half_p <- function(n_, r, hh) {
  rows <- st$half == hh
  h <- has(n_, which(rows)); inr <- st$region[rows] == r
  t <- matrix(c(sum(h & inr), sum(!h & inr), sum(h & !inr), sum(!h & !inr)), 2)
  f <- fisher.test(t, alternative = "greater"); f$p.value
}
if (nrow(sig)) {
  sig$pA <- mapply(half_p, sig$name, sig$region, "A"); sig$pB <- mapply(half_p, sig$name, sig$region, "B")
  sig$holds <- sig$pA < 0.05 & sig$pB < 0.05
}
s3 <- list(n_tests = nrow(geo), n_names = length(cand), regions = regs, n_sig = nrow(sig),
           n_holds = if (nrow(sig)) sum(sig$holds) else 0,
           rows = if (nrow(sig)) lapply(seq_len(nrow(sig)), function(i) list(
             name = sig$name[i], region = sig$region[i], k_in = sig$k_in[i], n_in = sig$n_in[i], k_out = sig$k_out[i],
             n_out = sig$n_out[i], or = r3(sig$or[i]), q = signif(sig$q[i], 3), holds = isTRUE(sig$holds[i]))) else list())

write_result(list(available = TRUE, plan = "analysplaner/2026-11-02-namn-och-slakt.md", n_pairs = nrow(pr),
                  n_stones = nrow(st), inheritance = s1, neighbours = s2, geography = s3, custom = s4, family = fam),
             out, "names")
