# Gemensamma hjälpfunktioner för R-modulerna. Varje modul körs som
#   Rscript --vanilla r/<modul>.R params.json utmapp
# och skriver <modul>.json och figurer (PNG) i utmappen.
suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(tidyr)
  library(stringr)
  library(ggplot2)
})
options(warn = 1, dplyr.summarise.inform = FALSE, stringsAsFactors = FALSE)

# Svenskt decimalkomma i figurtexter. OutDec sätts bara när figuren ritas (GDAL/terra tål det inte);
# sprintf() följer inte OutDec och får kommat här
sprintf <- function(fmt, ...) {
  out <- base::sprintf(fmt, ...)
  if (identical(LANG, "en")) out else gsub("(\\d)\\.(\\d)", "\\1,\\2", out)
}

# Färger: samma neutrala toner och accent som stenrapporten; högst tre kategorifärger i samma bild
INK <- "#1e293b"
MUTED <- "#64748b"
FAINT <- "#cbd5e1"
GRID <- "#e2e8f0"
ACCENT <- "#b7410e"
WATER <- "#7aa6d8"
SERIES <- c("#2a78d6", "#eb6834", "#1baf7a")
SEQ <- c("#eef4fc", "#2a78d6", "#0f3d75")
SWEREF <- 3006 # SWEREF 99 TM, meter

LANG <- "sv"
CLEAN <- FALSE # print version for journals: no titles or captions in the image, also a 600 dpi TIFF

cli_args <- function() {
  a <- commandArgs(trailingOnly = TRUE)
  if (length(a) < 2) stop("Användning: Rscript modul.R params.json utmapp")
  dir.create(a[2], showWarnings = FALSE, recursive = TRUE)
  params <- fromJSON(a[1], simplifyVector = TRUE)
  if (!is.null(params$lang)) LANG <<- params$lang
  if (isTRUE(params$clean)) CLEAN <<- TRUE
  list(params = params, out = a[2])
}

# Figure text in the report's language (sv or en)
tr <- function(sv, en) if (identical(LANG, "en")) en else sv

read_corpus <- function(path) {
  d <- read.csv(path, encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "", check.names = FALSE)
  for (col in c("words", "pairs", "normalization", "carver", "style", "carvers_all", "material")) {
    if (col %in% names(d)) d[[col]] <- as.character(d[[col]])
  }
  d
}

trait_cols <- function(d) grep("^trait_", names(d), value = TRUE)
cat_cols <- function(d) grep("^cat_", names(d), value = TRUE)

TRAIT_LABELS <- c(
  trait_ai_sten = "Diftongen ai i 'sten'", trait_au_och = "Diftongen au i 'och'",
  trait_nasal = "Nasal före konsonant", trait_h_bortfall = "h-bortfall", trait_stungna = "Stungna runor",
  trait_efter = "Stavning av 'efter'", trait_denna = "Stavning av 'denna'", trait_bon = "Kristen bön",
  trait_sjal = "Själsbön", trait_signatur = "Ristarsignatur", trait_runor = "Skrivningen av 'runor'"
)
CAT_LABELS <- c(
  cat_minne = "Minnesinskrift", cat_sjalvminne = "Självminne", cat_bro_vag = "Bro- och vägbygge",
  cat_kristen = "Kristen bön eller formel", cat_fard = "Utlandsfärd", cat_arv = "Arv och ägande",
  cat_ting = "Ting och offentlighet", cat_magisk = "Magisk eller rituell", cat_grans = "Gränsmärke"
)

theme_runor <- function(base = 10) {
  theme_minimal(base_size = base) +
    theme(
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(colour = GRID, linewidth = 0.3),
      plot.title = element_text(face = "bold", colour = INK, size = base + 1),
      plot.subtitle = element_text(colour = MUTED, size = base - 1),
      plot.caption = element_text(colour = MUTED, hjust = 0, size = base - 2),
      axis.text = element_text(colour = MUTED, size = base - 2),
      axis.title = element_text(colour = INK, size = base - 1),
      legend.position = "bottom",
      legend.title = element_text(colour = INK, size = base - 1),
      legend.text = element_text(colour = INK, size = base - 2),
      strip.text = element_text(face = "bold", colour = INK, hjust = 0, size = base - 1),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
}

theme_map <- function(base = 10) {
  theme_runor(base) + theme(axis.text = element_blank(), axis.title = element_blank(),
                            panel.grid.major = element_blank())
}

save_fig <- function(p, out, name, width = 7, height = 5) {
  op <- options(OutDec = if (identical(LANG, "en")) "." else ",")
  on.exit(options(op))
  if (CLEAN) p <- p + labs(title = NULL, subtitle = NULL, caption = NULL)
  suppressWarnings(ggsave(file.path(out, name), p, width = width, height = height, dpi = if (CLEAN) 300 else 200, bg = "white"))
  if (CLEAN) suppressWarnings(ggsave(file.path(out, sub("\\.png$", ".tif", name)), p, width = width, height = height,
                                     dpi = 600, bg = "white", device = ragg::agg_tiff, compression = "lzw"))
  name
}

write_result <- function(x, out, module) {
  write_json(x, file.path(out, paste0(module, ".json")), auto_unbox = TRUE, digits = NA,
             null = "null", na = "null", pretty = FALSE)
}

r3 <- function(x) round(x, 3)
r1 <- function(x) round(x, 1)

cramers_v <- function(tab) {
  tab <- tab[rowSums(tab) > 0, colSums(tab) > 0, drop = FALSE]
  if (min(dim(tab)) < 2) return(NA_real_)
  chi <- suppressWarnings(chisq.test(tab, correct = FALSE)$statistic)
  as.numeric(sqrt(chi / (sum(tab) * (min(dim(tab)) - 1))))
}

# Simulerat p-värde (Monte Carlo) för tabeller med små förväntade värden
chisq_p <- function(tab, B = 2000) {
  tab <- tab[rowSums(tab) > 0, colSums(tab) > 0, drop = FALSE]
  if (min(dim(tab)) < 2) return(NA_real_)
  suppressWarnings(chisq.test(tab, simulate.p.value = TRUE, B = B)$p.value)
}

# Justerat Rand-index (Hubert & Arabie 1985)
adjusted_rand <- function(a, b) {
  tab <- table(a, b)
  comb <- function(n) n * (n - 1) / 2
  s_ij <- sum(comb(tab)); s_a <- sum(comb(rowSums(tab))); s_b <- sum(comb(colSums(tab)))
  expected <- s_a * s_b / comb(sum(tab))
  (s_ij - expected) / ((s_a + s_b) / 2 - expected)
}

# Natural Earth-lager (vatten och land) beskurna till Sverige, i SWEREF 99 TM
read_water <- function(dir) {
  if (is.null(dir) || !dir.exists(dir)) return(NULL)
  suppressPackageStartupMessages(library(sf))
  sf_use_s2(FALSE)
  box <- st_as_sfc(st_bbox(c(xmin = 9, ymin = 54.5, xmax = 25, ymax = 69.5), crs = st_crs(4326)))
  layer <- function(name) {
    f <- list.files(file.path(dir, name), pattern = "\\.shp$", full.names = TRUE)
    if (!length(f)) return(NULL)
    x <- tryCatch(st_read(f[1], quiet = TRUE), error = function(e) NULL)
    if (is.null(x)) return(NULL)
    x <- st_make_valid(st_zm(x))
    x <- suppressWarnings(suppressMessages(st_intersection(st_geometry(x), box)))
    if (!length(x)) return(NULL)
    st_transform(x, SWEREF)
  }
  as_lines <- function(g) {
    if (is.null(g)) return(NULL)
    g <- g[!st_is_empty(g)]
    poly <- st_is(g, c("POLYGON", "MULTIPOLYGON"))
    out <- list()
    if (any(poly)) out[[1]] <- suppressWarnings(st_cast(st_cast(g[poly], "MULTIPOLYGON"), "MULTILINESTRING"))
    lin <- st_is(g, c("LINESTRING", "MULTILINESTRING"))
    if (any(lin)) out[[length(out) + 1]] <- suppressWarnings(st_cast(g[lin], "MULTILINESTRING"))
    if (!length(out)) return(NULL)
    do.call(c, out)
  }
  lakes <- c(layer("lakes"), layer("lakes_europe"))
  lines <- c(as_lines(layer("coastline")), as_lines(lakes), as_lines(layer("rivers")), as_lines(layer("rivers_europe")))
  land <- layer("land")
  if (is.null(lines) || !length(lines)) return(NULL)
  list(lines = st_union(lines), lakes = if (length(lakes)) st_union(lakes) else NULL,
       land = if (!is.null(land)) st_union(land) else NULL, coast = layer("coastline"))
}

WATER_NOTE <- paste(
  "Avståndet är räknat till dagens strandlinjer, sjöar och större vattendrag i Natural Earth (skala 1:10 miljoner);",
  "mindre åar och bäckar saknas. Landhöjningen sedan vikingatiden (upp till omkring 5 m i Mälardalen) har flyttat",
  "stränderna, så avstånden är en grov skattning av närheten till vatten då stenarna restes."
)
