# Ristarprofil: hur väl följer varje sten en ristares drag? Profilen byggs BARA av ristarens signerade stenar (de
# attribuerade har forskningen tillskrivit just efter dragen – annars cirkelresonemang) och jämförs med samtida
# grannstenar som ristaren inte gjort.
#   Rscript r/carver_profile.R KORPUSMAPP DRAG.csv RISTARE UTFIL.json
# Grannar: andra ristares och osignerade stenar inom NEAR_KM km från någon av ristarens stenar, med stil Pr3–Pr5 eller
# Fp eller stildatering som överlappar ristarens (de odaterade tas inte med).
# Drag: de binära dragen i upptäcktsmotorns dragtabell (src/discovery_v2.py) plus stil och korsets form ur korpusen;
# drag som bara säger att stenen är signerad tas bort. Signaturdrag: Fishers test p < P_SIG och minst dubbla eller
# halva oddsen mot grannarna, bland drag som går att avläsa på minst MIN_OBS signerade stenar. Värdet per sten:
# medelvärdet av log-kvoten (ristaren mot grannarna) över signaturdragen som går att avläsa på stenen. Signerade stenar
# räknas med sig själva utelämnade, också i valet av signaturdrag.
.args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({ library(jsonlite); library(dplyr) })
cdir <- .args[1]; drag_path <- .args[2]; who <- .args[3]; out <- .args[4]
NEAR_KM <- 30; P_SIG <- 0.10; MIN_OBS <- 8; MIN_LOR <- log(2); MAX_PHI <- 0.6

d <- read.csv(file.path(cdir, "corpus.csv"), stringsAsFactors = FALSE, na.strings = c("", "NA"))
f <- read.csv(drag_path, stringsAsFactors = FALSE, na.strings = "")
fam <- fromJSON(sub("drag\\.csv$", "drag_familjer.json", drag_path))
oof <- tryCatch(read.csv(file.path(cdir, "attribution_oof.csv"), check.names = FALSE), error = function(e) NULL)

meta <- c("signum", "province", "parish", "carver", "style_from", "style_to", "n_words", "lat", "lon", "pa_plats", "lokal")
drop <- c("has_carver", "pm_signatur", "ord_risti", "ord_hiogg", "ord_runaR", "ord_retta")  # signaturens egna ord
feats <- setdiff(names(f), c(meta, drop))
st <- d %>% transmute(signum, style = ifelse(is.na(style), "", style))
for (s in c("Pr1", "Pr2", "Pr3", "Pr4", "Pr5", "Fp", "KB", "RAK")) st[[paste0("stil_", s)]] <- ifelse(st$style == "", NA, as.integer(st$style == s))
st$style <- NULL
x <- f[, c("signum", feats)] %>% full_join(st, by = "signum")
feats <- setdiff(names(x), "signum")
family <- function(t) {
  if (startsWith(t, "stil_")) return("stil")
  g <- fam[[t]]; if (is.null(g)) "övrigt" else g
}

all_c <- ifelse(is.na(d$carvers_all), "", d$carvers_all)
mine <- d$carver %in% who & !is.na(d$carver)
shared <- !mine & grepl(who, all_c, fixed = TRUE)
grp <- data.frame(signum = d$signum, province = d$province, place = d$place, parish = d$parish, lat = d$lat, lon = d$lon,
                  style = d$style, style_from = d$style_from, style_to = d$style_to, material = d$material,
                  signed = d$signed, stringsAsFactors = FALSE)
grp$set <- ifelse(mine & d$signed == 1, "signerad", ifelse(mine, "attribuerad", ifelse(shared, "osäker", NA)))
# Signerade stenar som hålls utanför profilen (t.ex. Röd-Balles två, vars identitet med Balle är omstridd): env SKIP
skip <- strsplit(Sys.getenv("SKIP", ""), ";")[[1]]
grp$set[grp$signum %in% skip & grp$set %in% "signerad"] <- "signerad utanför profilen"
km <- function(la1, lo1, la2, lo2) 6371 * acos(pmin(1, sin(la1 * pi / 180) * sin(la2 * pi / 180) +
                                                cos(la1 * pi / 180) * cos(la2 * pi / 180) * cos((lo2 - lo1) * pi / 180)))
own <- grp[!is.na(grp$set) & !is.na(grp$lat), ]
y0 <- min(own$style_from, na.rm = TRUE); y1 <- max(own$style_to, na.rm = TRUE)
cand <- is.na(grp$set) & !is.na(grp$lat) & !grepl(who, all_c, fixed = TRUE)
near <- vapply(which(cand), function(i) min(km(grp$lat[i], grp$lon[i], own$lat, own$lon)) <= NEAR_KM, TRUE)
cand[which(cand)] <- near
late <- grp$style %in% c("Pr3", "Pr4", "Pr5", "Fp") |
  (!is.na(grp$style_from) & grp$style_to >= y0 & grp$style_from <= y1)
grp$set[cand & late] <- "granne"
grp <- grp[!is.na(grp$set), ]
X <- x[match(grp$signum, x$signum), feats]

jeff <- function(k, n) (k + 0.5) / (n + 1)
profile <- function(rows_s, rows_b) {
  res <- lapply(feats, function(t) {
    a <- X[rows_s, t]; b <- X[rows_b, t]; a <- a[!is.na(a)]; b <- b[!is.na(b)]
    if (length(a) < MIN_OBS || length(b) < 20) return(NULL)
    ka <- sum(a == 1); kb <- sum(b == 1)
    if (ka + kb == 0 || ka + kb == length(a) + length(b)) return(NULL)
    pa <- jeff(ka, length(a)); pb <- jeff(kb, length(b))
    p <- fisher.test(matrix(c(ka, length(a) - ka, kb, length(b) - kb), 2))$p.value
    data.frame(drag = t, familj = family(t), n_ristare = length(a), k_ristare = ka, n_grannar = length(b),
               k_grannar = kb, p_ristare = pa, p_grannar = pb,
               lor = log(pa / (1 - pa)) - log(pb / (1 - pb)), p = p, stringsAsFactors = FALSE)
  })
  r <- do.call(rbind, res)
  r$signatur <- r$p < P_SIG & abs(r$lor) >= MIN_LOR
  # Dubbletter: drag som nästan alltid följs åt (|phi| >= MAX_PHI på alla stenar) räknas en gång, det starkaste
  r$dubblett_av <- NA_character_
  keep <- character(0)
  for (t in r$drag[r$signatur][order(-abs(r$lor[r$signatur]))]) {
    hit <- NA_character_
    for (k in keep) {
      ok <- !is.na(X[[t]]) & !is.na(X[[k]])
      if (sum(ok) > 30 && sd(X[[t]][ok]) > 0 && sd(X[[k]][ok]) > 0 &&
          abs(cor(X[[t]][ok], X[[k]][ok])) >= MAX_PHI) { hit <- k; break }
    }
    if (is.na(hit)) keep <- c(keep, t) else { r$signatur[r$drag == t] <- FALSE; r$dubblett_av[r$drag == t] <- hit }
  }
  r
}
score <- function(i, pr) {
  s <- pr[pr$signatur, ]; v <- unlist(X[i, s$drag]); ok <- !is.na(v)
  if (!any(ok)) return(c(score = NA, n = 0, follows = NA))
  l1 <- ifelse(v[ok] == 1, log(s$p_ristare[ok] / s$p_grannar[ok]), log((1 - s$p_ristare[ok]) / (1 - s$p_grannar[ok])))
  c(score = mean(l1), n = sum(ok), follows = mean(l1 > 0))
}
S <- which(grp$set == "signerad"); B <- which(grp$set == "granne")
pr <- profile(S, B)
sc <- t(vapply(seq_len(nrow(grp)), function(i) {
  if (grp$set[i] == "signerad") score(i, profile(setdiff(S, i), B)) else score(i, pr)
}, c(score = 0, n = 0, follows = 0)))
grp <- cbind(grp, sc)
sig_s <- grp$score[grp$set == "signerad"]; sig_b <- grp$score[grp$set == "granne"]
cut_core <- median(sig_s, na.rm = TRUE); cut_span <- quantile(sig_s, 0.10, na.rm = TRUE)
cut_out <- quantile(sig_b, 0.90, na.rm = TRUE)
# kärna: minst som den mittersta signerade; inom spannet: mer lik ristaren än 90 % av grannarna; ytterkant: inom de
# signerades spann (över deras tiondel) men inte skild från grannarna; som grannarna: under de signerades tiondel
grp$klass <- ifelse(is.na(grp$score) | grp$n < 5, "kan inte avgöras",
              ifelse(grp$score >= cut_core, "kärna", ifelse(grp$score > cut_out, "inom spannet",
              ifelse(grp$score >= cut_span, "ytterkant", "som grannarna"))))
if (!is.null(oof)) {
  col <- paste0(".pred_", who)
  if (col %in% names(oof)) grp$modell <- oof[[col]][match(grp$signum, oof$signum)]
}
sig <- pr[pr$signatur, ]
cells <- X[, sig$drag, drop = FALSE]
write_json(list(ristare = who, grannar_km = NEAR_KM, period = c(y0, y1),
                n = as.list(table(grp$set)), granser = list(karna = cut_core, spann = unname(cut_span),
                                                         grannar_p90 = unname(cut_out)),
                drag = pr, signatur = sig$drag, stenar = grp,
                celler = lapply(seq_len(nrow(grp)), function(i) unname(unlist(cells[i, ])))),
           out, auto_unbox = TRUE, digits = 4, na = "null", pretty = FALSE)
cat(who, ": ", paste(names(table(grp$set)), table(grp$set), collapse = ", "), "; signaturdrag ", nrow(sig), "\n", sep = "")
print(sig[order(-abs(sig$lor)), c("drag", "k_ristare", "n_ristare", "k_grannar", "n_grannar", "lor", "p")])
print(table(grp$set, grp$klass))
