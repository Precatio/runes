# Upptäcktsmotorn, version 5: drag som ändrades olika fort på olika håll (rums-tidsmodell), enligt den låsta planen
# analysplaner/2026-11-04-upptacktsmotorn-v5-spridning.md.
#   Rscript r/discovery_v5.R steg1 A UTMAPP     halva A upptäcker; kandidaterna och A-modellerna fryses (SHA-256)
#   Rscript r/discovery_v5.R steg2 A UTMAPP     halva B bekräftar A:s kandidater (+ stegpinnen)
#   Rscript r/discovery_v5.R steg1 B UTMAPP / steg2 B UTMAPP   halvorna bytta
#   Rscript r/discovery_v5.R rapport UTMAPP     kartor för bekräftade drag + rimlighetskontrollen
.args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({ library(mgcv); library(jsonlite); library(dplyr) })
cmd <- .args[1]
if (cmd == "rapport") { out <- .args[2] } else { H <- .args[2]; out <- .args[3] }
dir.create(out, showWarnings = FALSE, recursive = TRUE)
MIN_N <- 30; Q <- 0.05; MAX_CAND <- 20
T_EARLY <- 1010; T_LATE <- 1100

d <- read.csv(file.path(out, "drag.csv"), stringsAsFactors = FALSE, na.strings = "")
meta <- c("signum", "province", "parish", "carver", "style_from", "style_to", "n_words", "lat", "lon", "pa_plats", "lokal")
feats <- setdiff(names(d), meta)
d <- d[!is.na(d$style_from) & !is.na(d$style_to) & !is.na(d$lat) & !is.na(d$lon), ]
d$year <- (d$style_from + d$style_to) / 2
d$t50 <- (d$year - 1050) / 50
d$x <- d$lon * 111.32 * cos(59 * pi / 180)
d$y <- d$lat * 110.57
d$lw <- log1p(d$n_words)
d$carver_f <- factor(ifelse(!is.na(d$carver) & d$carver != "", d$carver,
                            paste0("_", d$province, ":", ifelse(is.na(d$parish), d$signum, d$parish))))
# Halvorna som i version 2: socken för socken, växelvis inom varje landskap i sockenmedeldateringens ordning
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = mean(t), n = n(), .groups = "drop") %>%
  arrange(province, mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
other <- function(h) if (h == "A") "B" else "A"

usable <- function(x, f) { v <- x[[f]][!is.na(x[[f]])]; sum(v == 1) >= MIN_N && sum(v == 0) >= MIN_N }
fit0 <- function(f, x) gam(as.formula(paste(f, "~ s(t50, k = 4) + s(x, y, k = 30) + lw")), family = binomial,
                           data = x, method = "REML")
fit1 <- function(f, x) gam(as.formula(paste(f, "~ s(t50, k = 4) + s(x, y, k = 30) + lw +",
                                            "ti(x, y, t50, d = c(2, 1), k = c(20, 4))")),
                           family = binomial, data = x, method = "REML")
# A-modellens lokala förändring 1010 → 1100 (logit), vid medelordlängden
local_change <- function(m, at, lw) {
  e <- data.frame(x = at$x, y = at$y, lw = lw, t50 = (T_EARLY - 1050) / 50)
  l <- e; l$t50 <- (T_LATE - 1050) / 50
  as.numeric(predict(m, l, type = "link") - predict(m, e, type = "link"))
}
sha <- function(p) system2("shasum", c("-a", "256", shQuote(p)), stdout = TRUE)

if (cmd == "steg1") {
  x <- d[d$half == H, ]
  res <- lapply(feats, function(f) {
    y <- x[!is.na(x[[f]]), ]
    if (!usable(y, f)) return(NULL)
    m0 <- tryCatch(suppressWarnings(fit0(f, y)), error = function(e) NULL)
    m1 <- tryCatch(suppressWarnings(fit1(f, y)), error = function(e) NULL)
    if (is.null(m0) || is.null(m1)) return(NULL)
    a <- anova(m0, m1, test = "Chisq")
    p <- a[2, "Pr(>Chi)"]; if (is.na(p)) p <- 1
    cat(f, nrow(y), sum(y[[f]] == 1), signif(p, 3), "\n")
    saveRDS(m1, file.path(out, sprintf("m1_%s_%s.rds", H, f)))
    data.frame(drag = f, n = nrow(y), k = sum(y[[f]] == 1), dev = a[2, "Deviance"], df = a[2, "Df"], p = p,
               lw_mean = mean(y$lw))
  })
  res <- do.call(rbind, res)
  res$q <- p.adjust(res$p, "BH")
  res <- res[order(res$p), ]
  cand <- head(res[res$q < Q, ], MAX_CAND)
  keep <- file.path(out, sprintf("m1_%s_%s.rds", H, cand$drag))
  for (f in setdiff(list.files(out, sprintf("^m1_%s_.*\\.rds$", H), full.names = TRUE), keep)) file.remove(f)
  cand$modell_sha256 <- vapply(keep, function(p) strsplit(sha(p), " ")[[1]][1], "")
  write_json(list(halva = H, provade = res, kandidater = cand), file.path(out, sprintf("kandidater_%s.json", H)),
             auto_unbox = TRUE, digits = NA, pretty = TRUE)
  writeLines(sha(file.path(out, sprintf("kandidater_%s.json", H))), file.path(out, sprintf("kandidater_%s.sha256", H)))
  cat(nrow(res), "drag prövade,", nrow(cand), "kandidater (halva", H, ")\n")
}

if (cmd == "steg2") {
  k <- fromJSON(file.path(out, sprintf("kandidater_%s.json", H)))
  stopifnot(identical(strsplit(readLines(file.path(out, sprintf("kandidater_%s.sha256", H))), " ")[[1]][1],
                      strsplit(sha(file.path(out, sprintf("kandidater_%s.json", H))), " ")[[1]][1]))
  cand <- k$kandidater
  x <- d[d$half == other(H), ]
  confirm <- function(f, y, mA, lwA) {
    y <- y[!is.na(y[[f]]), ]
    if (sum(y[[f]] == 1) < 10 || sum(y[[f]] == 0) < 10) return(NULL)
    y$z <- local_change(mA, y, lwA); y$z <- y$z - mean(y$z)
    y$carver_f <- droplevels(y$carver_f)
    m <- tryCatch(suppressWarnings(gam(as.formula(paste(f, "~ s(t50, k = 4) + s(x, y, k = 30) + lw + t50:z +",
                                                        "s(carver_f, bs = 're')")),
                                       family = binomial, data = y, method = "REML")), error = function(e) NULL)
    if (is.null(m)) return(NULL)
    s <- summary(m)$p.table
    if (!"t50:z" %in% rownames(s)) return(NULL)
    list(n = nrow(y), k = sum(y[[f]] == 1), b = s["t50:z", 1], se = s["t50:z", 2],
         p1 = pnorm(s["t50:z", 3], lower.tail = FALSE))
  }
  rows <- lapply(seq_len(nrow(cand)), function(i) {
    f <- cand$drag[i]; p <- file.path(out, sprintf("m1_%s_%s.rds", H, f))
    stopifnot(identical(strsplit(sha(p), " ")[[1]][1], cand$modell_sha256[i]))
    mA <- readRDS(p)
    main <- confirm(f, x, mA, cand$lw_mean[i])
    if (is.null(main)) return(data.frame(drag = f, n = NA, k = NA, b = NA, se = NA, p1 = 1))
    cat(f, round(main$b, 3), signif(main$p1, 3), "\n")
    data.frame(drag = f, n = main$n, k = main$k, b = main$b, se = main$se, p1 = main$p1)
  })
  r <- do.call(rbind, rows)
  r$holm <- p.adjust(r$p1, "holm"); r$q <- p.adjust(r$p1, "BH")
  r$status <- ifelse(r$holm < Q, "bekräftad", ifelse(r$q < Q, "mönster att pröva", "inte bekräftad"))
  # Stegpinnen för bekräftade
  ladder <- lapply(r$drag[r$status == "bekräftad"], function(f) {
    i <- match(f, cand$drag); mA <- readRDS(file.path(out, sprintf("m1_%s_%s.rds", H, f)))
    sub <- list(pa_plats = x[!is.na(x$pa_plats) & x$pa_plats == 1, ], uppland = x[x$province == "U", ],
                utan_uppland = x[x$province != "U", ])
    rr <- lapply(names(sub), function(nm) {
      y <- sub[[nm]]; v <- y[[f]][!is.na(y[[f]])]
      if (nm == "utan_uppland" && (sum(v == 1) < MIN_N || sum(v == 0) < MIN_N)) return(NULL)
      c_ <- confirm(f, y, mA, cand$lw_mean[i]); if (is.null(c_)) return(NULL)
      data.frame(drag = f, steg = nm, n = c_$n, k = c_$k, b = c_$b, p1 = c_$p1)
    })
    do.call(rbind, rr)
  })
  ladder <- do.call(rbind, ladder)
  write_json(list(upptackt_i = H, bekraftat_i = other(H), resultat = r, stegpinne = ladder),
             file.path(out, sprintf("bekraftelse_%s_till_%s.json", H, other(H))), auto_unbox = TRUE, digits = NA,
             pretty = TRUE)
  print(r)
  if (!is.null(ladder)) print(ladder)
}

if (cmd == "rapport") {
  b <- fromJSON(file.path(out, "bekraftelse_A_till_B.json"))
  conf <- b$resultat$drag[b$resultat$status == "bekräftad"]
  b2 <- file.path(out, "bekraftelse_B_till_A.json")  # bekräftade med halvorna bytta: beskrivs också
  if (file.exists(b2)) { b2 <- fromJSON(b2); conf <- unique(c(conf, b2$resultat$drag[b2$resultat$status == "bekräftad"])) }
  known <- c("pm_kors", "pm_bon", "pm_sjal", "ord_hialpi")
  # Kartdata: M1 på hela datan, rutnät 10 km, bara rutor med en sten inom 20 km
  gx <- seq(floor(min(d$x)), ceiling(max(d$x)), 10); gy <- seq(floor(min(d$y)), ceiling(max(d$y)), 10)
  g <- expand.grid(x = gx, y = gy)
  near <- vapply(seq_len(nrow(g)), function(i) min((d$x - g$x[i])^2 + (d$y - g$y[i])^2) <= 400, TRUE)
  g <- g[near, ]
  maps <- list(); trend <- list()
  for (f in unique(c(conf, known))) {
    y <- d[!is.na(d[[f]]), ]
    m <- tryCatch(suppressWarnings(fit1(f, y)), error = function(e) NULL)
    if (is.null(m)) next
    pe <- predict(m, cbind(g, lw = mean(y$lw), t50 = (T_EARLY - 1050) / 50), type = "response")
    pl <- predict(m, cbind(g, lw = mean(y$lw), t50 = (T_LATE - 1050) / 50), type = "response")
    maps[[f]] <- data.frame(x = g$x, y = g$y, lat = g$y / 110.57, lon = g$x / (111.32 * cos(59 * pi / 180)),
                            p_tidig = as.numeric(pe), p_sen = as.numeric(pl))
    trend[[f]] <- y %>% group_by(year) %>% summarise(n = n(), andel = mean(.data[[f]] == 1), .groups = "drop")
  }
  write_json(list(bekraftade = conf, kartor = maps, tidstrend = trend), file.path(out, "kartor.json"),
             auto_unbox = TRUE, digits = 4)
  cat("kartor för", length(maps), "drag\n")
}
