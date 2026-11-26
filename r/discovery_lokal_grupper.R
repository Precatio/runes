# þennsa kring södra Mälaren med stenarna i grupp som enhet (analysplaner/2026-11-26-thennsa-grupper.md).
# Samma data, halvor, cirkel och modell som r/discovery_lokal.R; enheten är 1 km-grupper innanför cirkeln.
#   Rscript r/discovery_lokal_grupper.R
suppressPackageStartupMessages({ library(jsonlite); library(dplyr); library(sf) })
sf_use_s2(FALSE)
plan <- "analysplaner/2026-11-26-thennsa-grupper.md"
stopifnot(sub(" .*", "", system2("shasum", c("-a", "256", plan), stdout = TRUE)) == readLines(paste0(plan, ".sha256")))
d <- read.csv("utdata/upptackt_v2/drag.csv", stringsAsFactors = FALSE, na.strings = "")
L <- fromJSON("utdata/upptackt_v2/lokala.json", simplifyVector = FALSE)
cc <- Filter(function(x) x$feature == "ord_þennsa", L$confirmed)[[1]]
f <- "ord_þennsa"
# samma tidsskikt, halvor och koordinater som discovery_lokal.R
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
d$period <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$period <- factor(ifelse(is.na(d$period), "odaterad", as.character(d$period)),
                   levels = c("odaterad", "–1010", "1010–1040", "1040–1070", "1070–"))
d$lw <- log1p(d$n_words)
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
xy <- st_coordinates(st_transform(st_as_sf(d[!is.na(d$lat), ], coords = c("lon", "lat"), crs = 4326), 3006))
d$x <- NA; d$y <- NA; d$x[!is.na(d$lat)] <- xy[, 1]; d$y[!is.na(d$lat)] <- xy[, 2]
loc <- d[d$lokal == 1 & !is.na(d$x), ]
link_groups <- function(x, y, r = 1000) {
  n <- length(x); g <- seq_len(n)
  find <- function(i) { while (g[i] != i) i <- g[i]; i }
  D <- as.matrix(dist(cbind(x, y)))
  for (i in seq_len(n - 1)) for (j in (i + 1):n) if (D[i, j] <= r) { a <- find(i); b <- find(j); if (a != b) g[b] <- a }
  vapply(seq_len(n), find, 1L)
}
set.seed(20261126)
test_half <- function(h, nsim = 9999) {
  x <- loc[loc$half == h & !is.na(loc[[f]]), ]
  m <- suppressWarnings(glm(reformulate(c(if (length(unique(x$province)) > 1) "province", "period", "lw"), f),
                            family = binomial, data = droplevels(x)))
  p <- fitted(m)
  inside <- sqrt((x$x - cc$cx)^2 + (x$y - cc$cy)^2) <= cc$radius
  xi <- x[inside, ]; pi <- p[inside]
  g <- link_groups(xi$x, xi$y)
  obs_st <- sum(xi[[f]]); obs_gr <- length(unique(g[xi[[f]] == 1]))
  sims <- replicate(nsim, { yy <- rbinom(length(pi), 1, pi); length(unique(g[yy == 1])) })
  e_gr <- sum(vapply(split(pi, g), function(v) 1 - prod(1 - v), 0))
  list(stenar_inne = nrow(xi), grupper_inne = length(unique(g)), stenar_med_formen = obs_st,
       grupper_med_formen = obs_gr, vantat_grupper = e_gr, p = (1 + sum(sims >= obs_gr)) / (nsim + 1),
       grupper_storlek_max = max(table(g)))
}
B <- test_half("B"); A <- test_half("A")
res <- list(plan = basename(plan), cirkel = list(centrum = cc$center, radie_m = cc$radius),
            TG_halva_B = B, TG_haller = B$p < 0.05, beskrivande_halva_A = A)
write_json(res, "utdata/upptackt_v2/thennsa_grupper.json", auto_unbox = TRUE, digits = 6, pretty = TRUE)
print(toJSON(res, auto_unbox = TRUE, pretty = TRUE, digits = 4))
