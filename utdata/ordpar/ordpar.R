# Ordpar och ordnätverk på vikingatida runstenar (quanteda + igraph).
# Fråga 1: finns ordpar vars ORDNING skiljer sig mellan regionerna (goðan dræng mot dræng goðan)?
#   Test per oordnat par: region x ordning, chi-två (simulerat p vid gles tabell), BH-justering;
#   kontroll mot epokförväxling: samma test inom epok 900 resp. 1000.
# Fråga 2: hur ser ordens grannskap ut per region? Samförekomst inom sats, igraph, louvain-kluster.
# Kör: Rscript ordpar.R  (i utdata/ordpar). Utdata: ordpar_resultat.json, fig_natverk_*.png.
suppressPackageStartupMessages({ library(quanteda); library(igraph); library(jsonlite) })
set.seed(1)

d <- read.csv("ordpar_satser.csv", stringsAsFactors = FALSE, encoding = "UTF-8")
REGIONER <- c("Danmark", "Svealand", "Götaland")   # tillräckligt stora för test
d <- d[d$region %in% REGIONER, ]
satser <- strsplit(d$ord, " ", fixed = TRUE)

# --- fråga 1: ordningstest -------------------------------------------------------------------------
bigram <- function(ix) {
  ut <- new.env()
  for (i in ix) {
    w <- satser[[i]]
    if (length(w) < 2) next
    for (j in seq_len(length(w) - 1)) {
      nyck <- paste(w[j], w[j + 1], sep = "|")
      ut[[nyck]] <- (if (is.null(ut[[nyck]])) 0 else ut[[nyck]]) + 1
    }
  }
  as.list(ut)
}
ordningstabell <- function(delmangd) {
  per <- lapply(REGIONER, function(rg) bigram(which(delmangd & d$region == rg)))
  names(per) <- REGIONER
  alla <- unique(unlist(lapply(per, names)))
  split_par <- strsplit(alla, "|", fixed = TRUE)
  opar <- sapply(split_par, function(p) paste(sort(p), collapse = "|"))
  rader <- list()
  for (op in unique(opar)) {
    p <- strsplit(op, "|", fixed = TRUE)[[1]]
    if (p[1] == p[2]) next
    ab <- paste(p[1], p[2], sep = "|"); ba <- paste(p[2], p[1], sep = "|")
    M <- sapply(REGIONER, function(rg) c(ab = if (is.null(per[[rg]][[ab]])) 0 else per[[rg]][[ab]],
                                         ba = if (is.null(per[[rg]][[ba]])) 0 else per[[rg]][[ba]]))
    tot <- sum(M)
    if (tot < 30 || min(rowSums(M)) < 3 || sum(colSums(M) > 0) < 2) next
    pv <- tryCatch(chisq.test(t(M), simulate.p.value = TRUE, B = 5000)$p.value, error = function(e) NA)
    rader[[op]] <- list(par = op, n = tot, p = pv,
                        andel_ab = round(M["ab", ] / pmax(colSums(M), 1), 2),
                        n_region = colSums(M))
  }
  rader
}

alla_rader <- ordningstabell(rep(TRUE, nrow(d)))
pv <- sapply(alla_rader, `[[`, "p")
q <- p.adjust(pv, "BH")
for (i in seq_along(alla_rader)) alla_rader[[i]]$q <- round(q[i], 4)
ok <- !is.na(q) & q < 0.1
sign_par <- alla_rader[ok]
sign_par <- sign_par[order(sapply(sign_par, `[[`, "q"))]

# riktade fraspar: samma fras i båda ordningarna (possessiv, demonstrativ, adjektiv) - här är
# ordningsjämförelsen ren; NN-paren ovan kan blanda olika konstruktioner och läses med försiktighet
FRASPAR <- c("broþur|sin", "faþur|sin", "sun|sin", "bonda|sin", "moþur|sina", "systur|sina",
             "sten|þena", "sten|þensi", "sten|þansi", "sten|þensa", "goþan|dreng", "goþan|þegn",
             "bro|þesa", "kumbl|þesi")
per_rg <- lapply(REGIONER, function(rg) bigram(which(d$region == rg)))
names(per_rg) <- REGIONER
glob <- bigram(seq_len(nrow(d)))
cat("-- vanligaste bigram (nyckelformer):\n")
print(head(sort(unlist(glob), decreasing = TRUE), 40))
riktat <- list()
for (op in FRASPAR) {
  p <- strsplit(op, "|", fixed = TRUE)[[1]]
  ab <- paste(p[1], p[2], sep = "|"); ba <- paste(p[2], p[1], sep = "|")
  M <- sapply(REGIONER, function(rg) c(ab = if (is.null(per_rg[[rg]][[ab]])) 0 else per_rg[[rg]][[ab]],
                                       ba = if (is.null(per_rg[[rg]][[ba]])) 0 else per_rg[[rg]][[ba]]))
  if (sum(M) < 10) next
  pv <- tryCatch(chisq.test(t(M), simulate.p.value = TRUE, B = 5000)$p.value, error = function(e) NA)
  riktat[[op]] <- list(n = sum(M), p = round(pv, 4), n_ab = M["ab", ], n_ba = M["ba", ])
}


# poolat adjektivtest: goþan före/efter sitt huvudord (dreng + þegn), per region och inom epok
adjtest <- function(ix) {
  M <- sapply(REGIONER, function(rg) {
    b <- bigram(intersect(ix, which(d$region == rg)))
    fore <- sum(unlist(b[c("goþan|dreng", "goþan|þegn")]), na.rm = TRUE)
    efter <- sum(unlist(b[c("dreng|goþan", "þegn|goþan")]), na.rm = TRUE)
    c(fore = fore, efter = efter)
  })
  list(tabell = M, p = tryCatch(round(fisher.test(t(M))$p.value, 4), error = function(e) NA))
}
adj <- list(alla = adjtest(seq_len(nrow(d))),
            epok900 = adjtest(which(d$epok == "900")),
            epok1000 = adjtest(which(d$epok == "1000")))
cat("goþan före/efter per region:\n"); print(adj$alla$tabell); cat("Fisher p:", adj$alla$p, "\n")
cat("inom epok 900:\n"); print(adj$epok900$tabell); cat("p:", adj$epok900$p, "\n")
cat("inom epok 1000:\n"); print(adj$epok1000$tabell); cat("p:", adj$epok1000$p, "\n")

# epokkontroll för de signifikanta paren
for (ep in c("900", "1000")) {
  inom <- ordningstabell(d$epok == ep)
  for (i in seq_along(sign_par)) {
    op <- sign_par[[i]]$par
    sign_par[[i]][[paste0("epok", ep)]] <- if (!is.null(inom[[op]]))
      list(p = round(inom[[op]]$p, 4), andel_ab = inom[[op]]$andel_ab, n = inom[[op]]$n) else NULL
  }
}

# --- fråga 2: nätverk per region -------------------------------------------------------------------
natverk <- list()
for (rg in REGIONER) {
  kant <- new.env()
  for (i in which(d$region == rg)) {
    w <- setdiff(unique(satser[[i]]), "NN")
    if (length(w) < 2) next
    for (par in combn(sort(w), 2, simplify = FALSE)) {
      nyck <- paste(par, collapse = "|")
      kant[[nyck]] <- (if (is.null(kant[[nyck]])) 0 else kant[[nyck]]) + 1
    }
  }
  kl <- as.list(kant); vikt <- unlist(kl)
  behall <- vikt >= 4
  if (!any(behall)) next
  em <- do.call(rbind, strsplit(names(kl)[behall], "|", fixed = TRUE))
  g <- graph_from_data_frame(data.frame(em, weight = vikt[behall]), directed = FALSE)
  comm <- cluster_louvain(g)
  grad <- sort(strength(g), decreasing = TRUE)
  natverk[[rg]] <- list(noder = vcount(g), kanter = ecount(g),
                        modularitet = round(modularity(comm), 3),
                        topp = as.list(round(grad[1:12])),
                        kluster = lapply(split(V(g)$name, membership(comm)),
                                         function(x) head(x[order(-strength(g)[x])], 8)))
  png(sprintf("fig_natverk_%s.png", tolower(rg)), 1400, 1100, res = 110)
  beh <- names(grad)[1:min(40, length(grad))]
  g2 <- induced_subgraph(g, beh)
  plot(g2, vertex.size = 3 + sqrt(strength(g2)), vertex.label.cex = 0.8,
       vertex.label.color = "#111827", vertex.color = "#f4c7ad",
       edge.width = 0.5 + log1p(E(g2)$weight), layout = layout_with_fr,
       main = sprintf("Ordens grannskap, %s (samförekomst inom sats, vikt ≥ 4)", rg))
  dev.off()
}

ut <- list(satser = nrow(d), regioner = as.list(table(d$region)),
           ordning = list(testade_par = length(alla_rader), q_under_10 = length(sign_par),
                          par = sign_par, riktade_fraspar = riktat,
                          adjektiv_goþan = lapply(adj, function(x) list(tabell = as.list(as.data.frame(x$tabell)), p = x$p))),
           natverk = natverk)
write_json(ut, "ordpar_resultat.json", auto_unbox = TRUE, pretty = TRUE)
cat("testade par:", length(alla_rader), "| q<0,1:", length(sign_par), "\n")
for (x in sign_par) cat(sprintf("%s  n=%d  q=%.3f  andel_ab: %s\n", x$par, x$n, x$q,
                                paste(names(x$andel_ab), x$andel_ab, collapse = " ")))
