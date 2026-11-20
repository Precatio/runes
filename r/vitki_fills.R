# Vitkis ifyllningar av förlorade runor i R – bara som valbar robusthetskontroll (METHODS 8.1, beslut 2026-11-20).
# Ligger utanför common.R så att korpusmodulernas versioner (src/r_bridge.module_hashes) inte ändras. Används så:
#   source(file.path(.here, "vitki_fills.R"))
#   d <- with_vitki_fills(read_corpus(P$corpus), read_vitki_fills(P$vitki_fills), "words")

# Korpusen är Rundatas text. Vitkis bekräftade ifyllningar av förlorade runor (data/vitki_ifyllningar.csv) räknas aldrig
# som förval och läggs aldrig i corpus.csv. De får slås på som ett extra steg ("håller resultatet också med
# ifyllningarna?"), men inte i prov som mäter det som sannolikhetsmodellen själv bygger sina ifyllningar på – namn och
# namnens geografi, formler och ordföljd, ristarnas vanor och stavning – för där skulle ifyllningarna bekräfta sig själva.
VITKI_FILLS_FORBIDDEN <- c(
  "names", "people", "network", "text", "messages", "dialect", "chronology",
  "attribution", "attribution_audit", "attribution_bygd", "attribution_candidates", "attribution_v2", "attribution_v3",
  "attribution_v4", "anonymous", "carver_profile",
  "discovery", "discovery_lokal", "discovery_v2", "discovery_v3", "discovery_v4", "discovery_v5")

read_vitki_fills <- function(path) {
  if (is.null(path) || !nzchar(path) || !file.exists(path)) stop("Vitkis ifyllningar saknas (data/vitki_ifyllningar.csv).")
  f <- read.csv(path, encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "", colClasses = "character")
  f[f$status == "bekräftad" & !is.na(f$word) & nzchar(f$word), , drop = FALSE]  # förslag räknas aldrig
}

# Lägger orden i de bekräftade ifyllningarna sist i stenens normalisering (namn med citattecken, som i Rundata).
# Bara ord som stenen inte redan har läggs till, så att en lucka som Rundata redan fyllt med samma ord inte räknas två
# gånger. Dragen (trait_*), kategorierna och mönstren är Rundatas och ändras inte. module: modulens namn, för spärren.
with_vitki_fills <- function(d, fills, module) {
  if (missing(module) || !nzchar(module)) stop("with_vitki_fills() kräver modulens namn.")
  if (module %in% VITKI_FILLS_FORBIDDEN)
    stop(sprintf("Vitkis ifyllningar får inte användas i %s.R: provet mäter det som modellen bygger ifyllningarna på.", module))
  d$vitki_filled <- 0L
  norm <- ifelse(is.na(d$normalization), "", d$normalization)
  low <- function(x) tolower(gsub('["\\[\\]()?]', "", x, perl = TRUE))
  for (i in seq_len(nrow(fills))) {
    k <- match(fills$signum[i], d$signum)
    if (is.na(k)) next
    w <- fills$word[i]
    tok <- if (identical(fills$name[i], "1")) paste0('"', toupper(substr(w, 1, 1)), substr(w, 2, nchar(w))) else w
    if (low(w) %in% low(strsplit(norm[k], "\\s+")[[1]])) next
    norm[k] <- trimws(paste(norm[k], tok))
    d$vitki_filled[k] <- d$vitki_filled[k] + 1L
  }
  d$normalization <- ifelse(nzchar(norm), norm, NA_character_)
  attr(d, "vitki_fills") <- sprintf("Med Vitkis bekräftade ifyllningar (%d ord på %d sten(ar)); förvalt är Rundata ensamt.",
                                    sum(d$vitki_filled), sum(d$vitki_filled > 0))
  d
}
