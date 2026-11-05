# Kontroll till rapportversion 2 (2026-11-05): vilka stenar ligger i olika halva i huvudtestet (r/change.R) och i
# känslighetsanalyserna (src/robustness.py via src/question.py)? Regeln är densamma – hela socknar växelvis inom varje
# landskap i ordning efter socknens medeldatering – men den räknas fram två gånger. Halvorna i huvudtestet återskapas här
# med exakt koden i r/change.R (avsnittet split-half replication); känslighetsanalysernas halvor läses ur deras indata.
#   Rscript --vanilla utdata/monoftong/halvor.R          (från projektets rot)
suppressPackageStartupMessages({ library(dplyr); library(jsonlite) })
source("r/common.R")
FP <- "e83202e01a5e6d27"
C <- file.path("data/cache/r/corpus", FP)
d <- read_corpus(file.path(C, "corpus.csv"))
d <- d[!is.na(d$lat) & !is.na(d$lon), ]
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
# ---- som i r/change.R ----
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
# ---- monoftongdragets stenar i huvudtestet: draget avgjort och daterade ----
s <- d[!is.na(d$trait_ai_alla) & !is.na(d$t50), c("signum", "parish", "half")]
r <- read.csv(file.path(C, "robustness", "data.csv"), stringsAsFactors = FALSE, na.strings = "", check.names = FALSE)
r <- r[r$pattern == "Förändring|ai_alla", c("signum", "half")]
m <- merge(s, r, by = "signum", suffixes = c("_main", "_ladder"))
stopifnot(nrow(m) == nrow(s), nrow(m) == nrow(r))
sw <- m[m$half_main != m$half_ladder, ]
sw <- sw[order(sw$signum), ]
out <- list(
  corpus = FP, n = nrow(m),
  main = as.list(table(m$half_main)), ladder = as.list(table(m$half_ladder)),
  switched = nrow(sw), a_to_b = sum(sw$half_main == "A"), b_to_a = sum(sw$half_main == "B"),
  parishes = sort(unique(sw$parish)),
  stones = lapply(seq_len(nrow(sw)), function(i) list(signum = sw$signum[i], parish = sw$parish[i],
                                                      main = sw$half_main[i], ladder = sw$half_ladder[i])),
  note = paste("Samma regel, två implementationer: i känslighetsanalysernas halvor (src/question.py) får en socken",
               "(Viksta) medeldateringen 0,6999999999999998 i stället för 0,7 genom avrundning i flyttal och hamnar",
               "före de andra socknarna med samma medeldatering, så att några uppländska socknar byter halva.")
)
write_json(out, "utdata/monoftong/halvor.json", auto_unbox = TRUE, pretty = TRUE)
cat("huvudtestet", unlist(out$main), "känslighetsanalyserna", unlist(out$ladder), "olika halva:", out$switched, "\n")
