# LDA som oberoende kontroll av de handkodade inskriftskategorierna (src/inscription_types.py).
# Maskinens teman lärs utan kännedom om reglerna; sedan prövas om stenarna i varje tema är
# överrepresenterade i någon handkategori (Fisher, BH). Återfinner LDA bön/färd/bro själv?
# Kör: Rscript lda_kontroll.R  (i utdata/lda_kategorier). Utdata: lda_kontroll_resultat.json.
suppressPackageStartupMessages({ library(topicmodels); library(quanteda); library(jsonlite) })
set.seed(2)

d <- read.csv("stenar.csv", stringsAsFactors = FALSE, encoding = "UTF-8")
tok <- tokens(d$ord, what = "fastestword")
dfmat <- dfm(tok)
dfmat <- dfm_remove(dfmat, "NN")                       # namnen bär inget tema
dfmat <- dfm_trim(dfmat, min_docfreq = 5)
behall <- rowSums(dfmat) >= 3
dfmat <- dfmat[behall, ]; d <- d[behall, ]

K <- 8
lda <- LDA(convert(dfmat, to = "topicmodels"), k = K, method = "Gibbs",
           control = list(seed = 2, iter = 1500, burnin = 300))
term <- terms(lda, 10)
topptema <- topics(lda)
gamma <- lda@gamma

kat <- strsplit(d$kategorier, "|", fixed = TRUE)
alla_kat <- sort(unique(unlist(kat)))
bas <- sapply(alla_kat, function(k) mean(sapply(kat, function(x) k %in% x)))

rader <- list(); pv <- c()
for (t in 1:K) {
  i_t <- which(topptema == t)
  for (k in alla_kat) {
    i_k <- sapply(kat, function(x) k %in% x)
    M <- matrix(c(sum(i_k[i_t]), length(i_t) - sum(i_k[i_t]),
                  sum(i_k[-i_t]), length(i_k) - length(i_t) - sum(i_k[-i_t])), 2)
    p <- fisher.test(M, alternative = "greater")$p.value
    rader[[paste(t, k)]] <- list(tema = t, kategori = k, n_tema = length(i_t),
                                 andel_i_tema = round(mean(i_k[i_t]), 3),
                                 basniva = round(bas[[k]], 3), p = p)
    pv <- c(pv, p)
  }
}
q <- p.adjust(pv, "BH")
for (i in seq_along(rader)) rader[[i]]$q <- round(q[i], 5)
sign <- rader[sapply(rader, function(r) r$q < 0.05 && r$andel_i_tema > r$basniva * 1.5)]

ut <- list(stenar = nrow(d), k = K,
           teman = lapply(1:K, function(t) list(tema = t, n = sum(topptema == t),
                                                ord = as.character(term[, t]))),
           traffar = sign[order(sapply(sign, `[[`, "p"))])
write_json(ut, "lda_kontroll_resultat.json", auto_unbox = TRUE, pretty = TRUE)
for (t in 1:K) cat(sprintf("tema %d (%d stenar): %s\n", t, sum(topptema == t),
                           paste(term[1:7, t], collapse = " ")))
cat("\nsignifikanta tema-kategori-par (q<0,05, minst 1,5x bas):\n")
for (r in sign) cat(sprintf("  tema %d ↔ %s: %.0f%% mot bas %.0f%% (q=%.4f)\n",
                            r$tema, r$kategori, 100 * r$andel_i_tema, 100 * r$basniva, r$q))
