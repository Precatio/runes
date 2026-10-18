# Ordförrådet: vilka ord på runstenarna som bär regional och tidslig signal, räknat ur Rundatas normalisering.
#
# Orden plockas med samma regler som appens ordmoln (api/routers/rundata.py): citattecken märker namn (namn ingår
# inte i proven – de följer familjer, inte dialekt), utgivarnas återställningar tas med, ord med kvarstående
# skade- eller osäkerhetsmärkning hoppas över liksom lösa enbokstavsfragment (a, i och ø är riktiga ord).
# Ett ord räknas per sten (står det på stenen eller inte), precis som i molnet.
#
# För varje ord med belägg på minst MIN_STONES stenar skattas EN logistisk modell på de daterade stenarna:
#   ord på stenen ~ landskap (sum-kontraster: varje landskap mot genomsnittet) + tid (stilgruppens mittår)
#                   + log(antal ord i texten) + ristaren som slumpeffekt
# Textlängden måste med eftersom långa texter rymmer fler ord, och ristaren som slumpeffekt så att en flitig
# ristares vanor inte räknas som landskapets (samma upplägg som change.R; stenar utan säker ristare grupperas
# per socken). Landskap med färre än MIN_PROV daterade stenar läggs i "övriga". P-värdena BH-justeras (q) över
# alla ord × landskap respektive alla ords tidslutningar. Varje signifikant ord–landskapssignal prövas dessutom
# i två halvor: socknarna delas varannan inom landskapet, och signalen ska ha samma riktning och p < 0,05 i båda.
#
# Korrespondensanalysen (paketet ca) görs på tabellen landskap × ord (antal stenar med ordet) och visar vilka
# landskap som skriver mest lika; närheten mäts också som chi²-avstånd mellan landskapens ordprofiler.
# Tiden kommer ur stilgrupperna, så proven täcker i praktiken ca 980–1130; odaterade stenar ingår bara i CA:n.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "common.R"))
suppressPackageStartupMessages({ library(mgcv); library(ca) })

a <- cli_args(); P <- a$params; out <- a$out
seed <- if (is.null(P$seed)) 2026 else P$seed
set.seed(seed)
MIN_STONES <- 20   # stenar med ordet för att ordet ska prövas
MAX_WORDS <- 120   # de vanligaste orden räcker; fler ger mest brus och långsammare körning
MIN_PROV <- 40     # daterade stenar för att ett landskap ska prövas för sig
MIN_LEGIBLE <- 3   # kärnord i texten för att stenen ska räknas (fragment säger inget om ordval)
CA_WORDS <- 60     # ord i korrespondensanalysen

d <- read_corpus(P$corpus)
d$normalization[is.na(d$normalization)] <- ""
if (is.null(d$n_words_core)) d$n_words_core <- d$n_words  # äldre korpusfiler saknar kärnordskolumnen
d$n_words_core[is.na(d$n_words_core)] <- 0
d <- d[d$n_words_core >= MIN_LEGIBLE, ]

# ---- orden ur normaliseringen (samma regler som appens ordmoln) ---------------------------------
tokenize <- function(norm) {
  raw <- strsplit(norm, "\\s+")[[1]]
  is_name <- grepl("\"", raw)
  t <- gsub("[\"\\[\\]()<>{}«»]", "", raw, perl = TRUE)
  t <- gsub("^[.,;:!?+·×=§|/\\\\'’]+|[.,;:!?+·×=§|/\\\\'’]+$", "", t)
  keep <- nzchar(t) & !grepl("\\.\\.\\.|[-?…]", t) & !is_name & (nchar(t) > 1 | tolower(t) %in% c("a", "i", "ø"))
  t <- t[keep]
  # första bokstaven liten, inre R (palatalt ʀ) behålls som i normaliseringen
  t <- paste0(tolower(substr(t, 1, 1)), substring(t, 2))
  unique(t[grepl("^[a-zåäöæøǫœęþðáéíóúýūōR]+$", t)])
}
tokens <- lapply(d$normalization, tokenize)
counts <- sort(table(unlist(tokens)), decreasing = TRUE)
words <- names(counts)[counts >= MIN_STONES]
words <- head(words, MAX_WORDS)
has <- sapply(words, function(w) vapply(tokens, function(ts) w %in% ts, logical(1)))

# ---- modellens underlag -------------------------------------------------------------------------
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$log_words <- log(d$n_words_core)
d$carver_f <- factor(ifelse(!is.na(d$carver) & d$carver != "", d$carver,
                            paste0("_", d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish))))
dated <- !is.na(d$year)
prov_n <- table(d$province[dated])
big <- names(prov_n)[prov_n >= MIN_PROV]
d$prov_f <- ifelse(d$province %in% big, d$province, "övriga")
dd <- d[dated, ]
hh <- has[dated, , drop = FALSE]
# "övriga" läggs sist: sum-kontrasterna ger då p-värden för alla riktiga landskap, och övriga – som ändå inte
# redovisas som fynd – är den utelämnade nivån
dd$prov_f <- factor(dd$prov_f, levels = c(sort(big), "övriga"))
contrasts(dd$prov_f) <- contr.sum(nlevels(dd$prov_f))
prov_levels <- levels(dd$prov_f)

# ---- en modell per ord: landskap mot genomsnittet och tidslutningen, i samma skattning ----------
fit_word <- function(w) {
  dd$y <- hh[, w]
  n1 <- sum(dd$y)
  if (n1 < 10 || n1 > nrow(dd) - 10) return(NULL)
  m <- tryCatch(bam(y ~ prov_f + t50 + log_words + s(carver_f, bs = "re"), data = dd, family = binomial,
                    method = "fREML", discrete = TRUE),
                error = function(e) NULL)
  if (is.null(m)) return(NULL)
  s <- summary(m)
  pt <- s$p.table
  k <- nlevels(dd$prov_f)
  # sum-kontraster: koefficient 2..k är landskap 1..k-1 mot genomsnittet; det sista är minus summan av de andra
  pc <- pt[grep("^prov_f", rownames(pt)), , drop = FALSE]
  est <- c(pc[, 1], -sum(pc[, 1]))
  prov <- data.frame(word = w, province = prov_levels,
                     logodds = as.numeric(est),
                     p = c(pc[, 4], NA_real_), stringsAsFactors = FALSE)  # "övriga" (sist) prövas inte
  time <- data.frame(word = w, slope = pt["t50", 1], p = pt["t50", 4], stringsAsFactors = FALSE)
  list(prov = prov, time = time)
}
fits <- lapply(words, fit_word)
names(fits) <- words
fits <- fits[!vapply(fits, is.null, logical(1))]

prov_tests <- bind_rows(lapply(fits, `[[`, "prov"))
time_tests <- bind_rows(lapply(fits, `[[`, "time"))
prov_tests$q <- p.adjust(prov_tests$p, method = "BH")
time_tests$q <- p.adjust(time_tests$p, method = "BH")

# observerade andelar som läsaren kan kontrollera för hand
share <- function(w, rows) { x <- has[rows, w]; c(sum(x), length(x)) }
prov_tests <- prov_tests %>% rowwise() %>% mutate(
  k_in = share(word, which(d$prov_f == province))[1], n_in = share(word, which(d$prov_f == province))[2],
  k_out = sum(has[, word]) - k_in, n_out = nrow(d) - n_in) %>% ungroup()

# ---- halvprovet för de signifikanta landskapssignalerna -----------------------------------------
# socknarna delas varannan (sorterade, inom landskapet), så att båda halvorna täcker samma trakter
parish_half <- local({
  key <- paste0(d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish))
  u <- sort(unique(key))
  h <- setNames(seq_along(u) %% 2, u)
  h[key]
})
holds_both <- function(w, prov) {
  ok <- TRUE
  for (half in 0:1) {
    rows <- dated & parish_half == half
    df <- data.frame(y = has[rows, w], inprov = d$prov_f[rows] == prov, t50 = d$t50[rows], lw = d$log_words[rows])
    m <- tryCatch(glm(y ~ inprov + t50 + lw, df, family = binomial), error = function(e) NULL)
    if (is.null(m) || !"inprovTRUE" %in% rownames(summary(m)$coefficients)) return(FALSE)
    co <- summary(m)$coefficients["inprovTRUE", ]
    full <- prov_tests$logodds[prov_tests$word == w & prov_tests$province == prov]
    if (is.na(co[4]) || co[4] >= 0.05 || sign(co[1]) != sign(full)) ok <- FALSE
  }
  ok
}
sig <- prov_tests %>% filter(q < 0.05, province != "övriga")
sig$holds <- mapply(holds_both, sig$word, sig$province)

# ---- andelar per epok för tidstrenderna ---------------------------------------------------------
EPOCHS <- list("980–1015" = c(0, 1015), "1015–1050" = c(1015, 1050), "1050–1080" = c(1050, 1080),
               "1080–1130" = c(1080, 9999))
epoch_shares <- function(w) {
  lapply(names(EPOCHS), function(e) {
    rows <- dated & d$year > EPOCHS[[e]][1] & d$year <= EPOCHS[[e]][2]
    list(epoch = e, k = sum(has[rows, w]), n = sum(rows))
  })
}
time_top <- time_tests %>% filter(q < 0.05) %>% arrange(q)
time_out <- lapply(seq_len(nrow(time_top)), function(i) {
  w <- time_top$word[i]
  list(word = w, slope = r3(time_top$slope[i]), q = time_top$q[i], shares = epoch_shares(w))
})

# ---- korrespondensanalys: landskap × ord --------------------------------------------------------
ca_words <- head(words, CA_WORDS)
tab <- t(sapply(sort(big), function(p) colSums(has[d$prov_f == p, ca_words, drop = FALSE])))
tab <- tab[rowSums(tab) > 0, colSums(tab) > 0, drop = FALSE]
fit_ca <- ca(tab)
inertia <- fit_ca$sv^2 / sum(fit_ca$sv^2)
# chi²-avstånd mellan landskapens ordprofiler (radprofiler mot genomsnittsprofilen)
prof <- tab / rowSums(tab)
avg <- colSums(tab) / sum(tab)
chi_dist <- as.matrix(dist(sweep(prof, 2, sqrt(avg), "/")))
pairs <- which(upper.tri(chi_dist), arr.ind = TRUE)
near <- data.frame(a = rownames(chi_dist)[pairs[, 1]], b = rownames(chi_dist)[pairs[, 2]],
                   dist = chi_dist[pairs]) %>% arrange(dist) %>% head(5)

# ---- resultatet ---------------------------------------------------------------------------------
region_out <- sig %>% arrange(q) %>% head(60) %>% rowwise() %>% mutate(
  rate_in = r3(k_in / n_in), rate_out = r3(k_out / n_out)) %>% ungroup()
result <- list(
  version = 1, seed = seed,
  method = tr(paste0("En logistisk modell per ord på de daterade runstenarna: landskap (sum-kontraster mot ",
                     "genomsnittet) + stilgruppens mittår + log(textens längd), med ristaren som slumpeffekt ",
                     "(stenar utan säker ristare grupperas per socken). P-värdena BH-justeras över alla ord × ",
                     "landskap respektive alla tidslutningar, och varje signifikant landskapssignal prövas i två ",
                     "sockenhalvor med krav på samma riktning och p < 0,05 i båda. Korrespondensanalysen görs på ",
                     "tabellen landskap × ord (antal stenar med ordet). Namn ingår inte; orden plockas med samma ",
                     "regler som appens ordmoln."),
              paste0("One logistic model per word on the dated runestones: province (sum contrasts against the ",
                     "mean) + style mid-year + log(text length), with the carver as a random effect (stones ",
                     "without a certain carver grouped by parish). P-values are BH-adjusted across all word × ",
                     "province tests and all time slopes, and every significant province signal is re-tested in ",
                     "two parish halves, requiring the same direction and p < 0.05 in both. The correspondence ",
                     "analysis uses the province × word table (stones carrying the word). Names are excluded; ",
                     "words are picked with the same rules as the app's word cloud.")),
  n_stones = nrow(d), n_dated = nrow(dd), n_words_tested = length(fits),
  min_stones = MIN_STONES, provinces_tested = setdiff(prov_levels, "övriga"),
  region = lapply(seq_len(nrow(region_out)), function(i) as.list(region_out[i, c(
    "word", "province", "logodds", "q", "k_in", "n_in", "k_out", "n_out", "rate_in", "rate_out", "holds")])),
  n_region_tests = nrow(prov_tests),
  time = time_out, n_time_tests = nrow(time_tests),
  ca = list(inertia = r3(inertia[1:2]),
            provinces = lapply(seq_len(nrow(tab)), function(i) list(
              code = rownames(tab)[i], x = r3(fit_ca$rowcoord[i, 1] * fit_ca$sv[1]),
              y = r3(fit_ca$rowcoord[i, 2] * fit_ca$sv[2]), n = as.integer(rowSums(tab)[i]))),
            words = lapply(seq_len(ncol(tab)), function(j) list(
              w = colnames(tab)[j], x = r3(fit_ca$colcoord[j, 1] * fit_ca$sv[1]),
              y = r3(fit_ca$colcoord[j, 2] * fit_ca$sv[2]), n = as.integer(colSums(tab)[j])))),
  neighbors = lapply(seq_len(nrow(near)), function(i) list(a = near$a[i], b = near$b[i], dist = r3(near$dist[i])))
)
write_result(result, out, "words")
