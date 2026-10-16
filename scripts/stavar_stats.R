# Stavarna på runstenarna: när och i vilket sammanhang ordet staf står, och om stenarna med en rest stav skiljer
# sig från andra vikingatida runstenar (artikeln "Stenar och stavar"). Underlag: utdata/stavar/stavar_data.csv
# (scripts/stavar_data.py, Rundata 3.1). Skriver utdata/stavar/stavar_stats.json.
#   .venv/bin/python -m scripts.stavar_data && Rscript scripts/stavar_stats.R
# Grupper: "minne" = staf rest som minnesmärke (Sö 196, Vs 1, U 226, U 332, U 849; Zilmer 2005), "osaker" = Sö 56
# ("stafa marga", minnesmärke eller runor), "runor" = runorna kallas stavar (Sm 16, DR 40). Jämförelsen är alla andra
# vikingatida inskrifter. Fishers exakta test (litet underlag), p-värden justerade för de sju testen (Holm).
# thing: texten nämner ett ting; thing_mon: monumentet gör det (U 226 med U 225, som då räknas bort ur jämförelsen).
suppressMessages(library(jsonlite))
setwd(file.path(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)))), "..", "utdata", "stavar"))
d <- read.csv("stavar_data.csv", encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d$staf[is.na(d$staf)] <- ""
rest <- d[d$staf == "", ]
fisher_row <- function(g, var, base = rest, cond = NULL) {
  if (!is.null(cond)) { g <- g[cond(g), ]; base <- base[cond(base), ] }
  g <- g[!is.na(g[[var]]), ]; base <- base[!is.na(base[[var]]), ]
  tab <- matrix(c(sum(g[[var]] == 1), sum(g[[var]] == 0), sum(base[[var]] == 1), sum(base[[var]] == 0)), 2)
  ft <- fisher.test(tab)
  list(var = var, x = sum(g[[var]] == 1), n = nrow(g), share = mean(g[[var]] == 1),
       base_x = sum(base[[var]] == 1), base_n = nrow(base), base_share = mean(base[[var]] == 1),
       odds_ratio = unname(ft$estimate), p = ft$p.value)
}
run <- function(g, label) {
  tests <- list(
    malardalen = fisher_row(g, "malardalen"),
    plural = fisher_row(g, "plural"),
    early = fisher_row(g, "early", cond = function(x) x$malardalen == 1),
    signed = fisher_row(g, "signed"),
    prayer = fisher_row(g, "prayer"),
    thing = fisher_row(g, "thing"),
    thing_mon = fisher_row(g, "thing_mon"))
  p_adj <- p.adjust(sapply(tests, `[[`, "p"), method = "holm")
  for (k in names(tests)) tests[[k]]$p_holm <- unname(p_adj[k])
  cat(sprintf("\n== %s (n = %d)\n", label, nrow(g)))
  for (k in names(tests)) with(tests[[k]], cat(sprintf("  %-10s %d/%d (%.0f %%) mot %d/%d (%.1f %%)  OR %.1f  p %.3f  Holm %.3f\n",
                                                     k, x, n, 100 * share, base_x, base_n, 100 * base_share, odds_ratio, p, p_holm)))
  tests
}
minne <- d[d$staf == "minne", ]
minne6 <- d[d$staf %in% c("minne", "osaker"), ]
runor <- d[d$staf == "runor", ]
res <- list(minne = run(minne, "staf rest som minnesmärke, fem säkra"),
            minne_med_so56 = run(minne6, "med Sö 56"))
# when: the style groups' mid-years (Gräslund) for the staves against the other stones with a style group
yr <- function(x) x$year_mid[!is.na(x$year_mid)]
when <- list(minne = yr(minne), osaker = yr(d[d$staf == "osaker", ]), runor = yr(runor),
             malardalen_median = median(yr(rest[rest$malardalen == 1, ])), alla_median = median(yr(rest)))
# the rune staves: both RAK; how often is a stone with a style group RAK?
rak <- mean(rest$style[!is.na(rest$style)] == "RAK")
when$runor_bada_rak_p <- rak^2
when$rak_andel <- rak
cat(sprintf("\nnär (stilgruppens mittår): minne %s; Sö 56 %s; runor %s; median Mälardalen %.0f, alla %.0f\n",
            paste(when$minne, collapse = ", "), paste(when$osaker, collapse = ", "), paste(when$runor, collapse = ", "),
            when$malardalen_median, when$alla_median))
cat(sprintf("RAK bland stenar med stilgrupp: %.1f %%; chansen att två slumpvisa stenar båda är RAK: %.3f\n", 100 * rak, rak^2))
writeLines(toJSON(list(tests = res, when = when), auto_unbox = TRUE, digits = 6, pretty = TRUE), "stavar_stats.json")
