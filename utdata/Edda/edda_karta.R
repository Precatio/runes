# Eddans stilometriska karta: Burrows' Delta över alla texter (≥600 ord) med Hávamál i fyra delar,
# plus Hugsvinnsmál – första beräkningsmässiga prövningen av von See-tesen (Hávamál ~ Disticha Catonis
# via Hugsvinnsmál). Kör: Rscript edda_karta.R  (i utdata/Edda). Utdata: edda_karta_resultat.json,
# fig_karta_dendrogram.png, fig_karta_pca.png.
library(jsonlite)

d <- read.csv("edda_karta_texter.csv", stringsAsFactors = FALSE, encoding = "UTF-8")
tokl <- strsplit(d$text, " ", fixed = TRUE)
names(tokl) <- d$namn

# relativ frekvens per text; MFW = de 100 ord som har högst MEDELfrekvens över texterna,
# så att de två långa prosatexterna inte ensamma väljer ordlistan
frek <- lapply(tokl, function(w) table(w) / length(w))
alla <- sort(unique(unlist(lapply(frek, names))))
M0 <- sapply(frek, function(f) { v <- as.numeric(f[alla]); v[is.na(v)] <- 0; v })
rownames(M0) <- alla
mfw <- names(sort(rowMeans(M0), decreasing = TRUE))[1:100]
M <- t(M0[mfw, ])                                  # texter x ord

Z <- scale(M)
delta <- as.matrix(dist(Z, method = "manhattan")) / ncol(Z)
sd2 <- as.matrix(stylo::dist.delta(M))
stylo_ok <- cor(as.dist(delta), as.dist(sd2[rownames(delta), rownames(delta)])) > 0.99

hc <- hclust(as.dist(delta), method = "ward.D2")
grupp <- function(n) ifelse(grepl("^Hávamál_", n), "Hávamál-del",
                     ifelse(n %in% c("Sólarljóð", "Hugsvinnsmál"), "visdom, kristen tid",
                     ifelse(n %in% c("Gylfaginning", "Skáldskaparmál"), "prosa (Snorra-Edda)",
                     ifelse(d$ljodahattr[match(n, d$namn)] == 1, "ljóðaháttr övrig", "övrig dikt"))))

png("fig_karta_dendrogram.png", 1600, 1100, res = 110)
par(mar = c(1, 4, 2, 12))
dend <- as.dendrogram(hc)
farg <- c("Hávamál-del" = "#b7410e", "visdom, kristen tid" = "#1d4ed8", "prosa (Snorra-Edda)" = "#6b7280",
          "ljóðaháttr övrig" = "#047857", "övrig dikt" = "#111827")
dend <- dendrapply(dend, function(nod) {
  if (is.leaf(nod)) { attr(nod, "nodePar") <- list(lab.col = farg[grupp(attr(nod, "label"))], pch = NA) }
  nod })
plot(dend, horiz = TRUE, main = "Eddans stilkarta: Burrows' Delta, 100 vanligaste orden")
legend("topleft", legend = names(farg), text.col = farg, bty = "n", cex = 0.95)
dev.off()

p <- prcomp(Z)
png("fig_karta_pca.png", 1500, 1100, res = 110)
par(mar = c(4, 4, 2, 1))
plot(p$x[, 1], p$x[, 2], type = "n", xlab = "PC1", ylab = "PC2",
     main = "Eddatexterna i stilrummet (PCA på samma 100 ord)")
text(p$x[, 1], p$x[, 2], labels = rownames(Z), col = farg[sapply(rownames(Z), grupp)], cex = 0.75)
dev.off()

grannar <- function(n, k = 6) {
  v <- sort(delta[n, setdiff(rownames(delta), n)])[1:k]
  mapply(function(nn, dd) list(namn = nn, delta = round(dd, 3)), names(v), v, SIMPLIFY = FALSE, USE.NAMES = FALSE)
}
rang <- function(fran, till) which(names(sort(delta[fran, setdiff(rownames(delta), fran)])) == till)

lj <- d$namn[d$ljodahattr == 1]
delta_lj <- delta[lj, lj]
rang_lj <- function(fran, till) which(names(sort(delta_lj[fran, setdiff(lj, fran)])) == till)

ut <- list(
  texter = nrow(d), mfw = 100, stylo_kontroll = stylo_ok,
  grannar = list(Hugsvinnsmal = grannar("Hugsvinnsmál"), Solarljod = grannar("Sólarljóð"),
                 Havamal_gnomisk = grannar("Hávamál_gnomisk")),
  von_see = list(
    delta_hugsvinn_havgnom = round(delta["Hugsvinnsmál", "Hávamál_gnomisk"], 3),
    delta_hugsvinn_solarljod = round(delta["Hugsvinnsmál", "Sólarljóð"], 3),
    delta_hugsvinn_median = round(median(delta["Hugsvinnsmál", setdiff(rownames(delta), "Hugsvinnsmál")]), 3),
    rang_havgnom_hos_hugsvinn = rang("Hugsvinnsmál", "Hávamál_gnomisk"),
    rang_solarljod_hos_hugsvinn = rang("Hugsvinnsmál", "Sólarljóð"),
    rang_havgnom_hos_hugsvinn_ljodahattr = rang_lj("Hugsvinnsmál", "Hávamál_gnomisk"),
    rang_solarljod_hos_hugsvinn_ljodahattr = rang_lj("Hugsvinnsmál", "Sólarljóð"),
    antal_ljodahattr = length(lj)),
  havamal_ihop = list(
    inbordes = round(mean(delta[grep("^Hávamál_", rownames(delta)),
                                grep("^Hávamál_", rownames(delta))][upper.tri(matrix(0, 4, 4))]), 3),
    mot_andra = round(mean(delta[grep("^Hávamál_", rownames(delta)),
                                 grep("^Hávamál_", rownames(delta), invert = TRUE)]), 3)),
  kluster4 = split(hc$labels, cutree(hc, 4))
)
write_json(ut, "edda_karta_resultat.json", auto_unbox = TRUE, pretty = TRUE)
cat("stylo-kontroll:", stylo_ok, "\n")
cat("Hugsvinnsmáls grannar:", paste(sapply(ut$grannar$Hugsvinnsmal, `[[`, "namn"), collapse = ", "), "\n")
cat("von See:", toJSON(ut$von_see, auto_unbox = TRUE), "\n")
