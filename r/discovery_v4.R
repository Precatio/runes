# Upptäcktsmotorn, version 4: beroendenätverket enligt den låsta planen analysplaner/2026-11-01-upptacktsmotorn-v4-natverk.md
# (sha c43e65b7).
#   Rscript r/discovery_v4.R utdata/upptackt_v3 utdata/upptackt_v4
# Halva A: bnlearn boot.strength (hc/BIC, 200 dragningar), kanter ≥ 0,85 mellan drag ur olika familjer fryses; halva B:
# glm med kantens grannar, ensidigt, Holm. Sekundärt bytta halvor. De 15 kända paren ur v1/v2: direkta eller förklarade.
.args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({ library(bnlearn); library(jsonlite); library(dplyr); library(digest); library(parallel) })
src <- .args[1]; dir <- .args[2]
SEED <- 2026; R_BOOT <- 200; THR <- 0.85
BG <- c("landskap", "tidsskikt", "langd")

d <- read.csv(file.path(src, "drag.csv"), stringsAsFactors = FALSE, na.strings = "")
fam <- fromJSON(file.path(src, "drag_familjer.json"))
meta <- c("signum", "province", "parish", "carver", "style_from", "style_to", "n_words", "lat", "lon", "pa_plats", "lokal")
feats <- setdiff(names(d), meta)
feats <- feats[vapply(feats, function(f) all(d[[f]] %in% c(0, 1, NA)), TRUE)]
famof <- function(f) if (!is.null(fam[[f]])) fam[[f]] else f
forbid <- vapply(fromJSON(file.path(src, "drag_forbjudna.json"), simplifyVector = FALSE),
                 function(p) paste(sort(unlist(p)), collapse = "|"), "")
okpair <- function(a, b) famof(a) != famof(b) && !(paste(sort(c(famof(a), famof(b))), collapse = "|") %in% forbid)

# --- halves and period as in v2/v3 ---
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
per <- cut(d$year, c(-Inf, 1010, 1040, 1070, Inf), labels = c("–1010", "1010–1040", "1040–1070", "1070–"))
d$tidsskikt <- factor(ifelse(is.na(per), "odaterad", as.character(per)))
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
big <- names(which(table(d$province) >= 20))
d$landskap <- factor(ifelse(d$province %in% big, d$province, "övrigt"))
q <- quantile(d$n_words, c(1 / 3, 2 / 3), na.rm = TRUE)
d$langd <- factor(cut(d$n_words, c(-Inf, q, Inf), labels = c("kort", "mellan", "lång")))
asfac <- function(x) factor(ifelse(is.na(x), "na", as.character(x)))

learn <- function(H) {
  x <- d[d$half == H, ]
  X <- data.frame(lapply(x[, feats], asfac), check.names = FALSE)
  keep <- names(X)[vapply(X, function(v) nlevels(droplevels(v)) >= 2, TRUE)]
  X <- data.frame(lapply(X[, keep], droplevels), landskap = droplevels(x$landskap), tidsskikt = droplevels(x$tidsskikt),
                  langd = x$langd, check.names = FALSE)
  bl <- expand.grid(from = names(X), to = BG, stringsAsFactors = FALSE)
  bl <- bl[bl$from != bl$to, ]
  cl <- makeCluster(4); clusterSetRNGStream(cl, SEED); set.seed(SEED)
  bs <- boot.strength(X, R = R_BOOT, algorithm = "hc", algorithm.args = list(score = "bic", blacklist = bl), cluster = cl)
  stopCluster(cl)
  e <- bs[bs$strength >= THR, ]
  e$key <- mapply(function(a, b) paste(sort(c(a, b)), collapse = "~"), e$from, e$to)
  e <- e[!duplicated(e$key), c("from", "to", "strength", "key")]
  list(edges = e, dropped = setdiff(feats, keep), n = nrow(X))
}

neigh <- function(edges, v) unique(c(edges$to[edges$from == v], edges$from[edges$to == v]))

fit_edge <- function(x, a, b, G) {
  z <- x[!is.na(x[[a]]) & !is.na(x[[b]]), ]
  G <- setdiff(intersect(G, feats), c(a, b))
  for (g in G) z[[g]] <- asfac(z[[g]])
  rhs <- paste(c(a, G, "landskap", "tidsskikt", "langd"), collapse = " + ")
  fit <- tryCatch(suppressWarnings(glm(as.formula(paste(b, "~", rhs)), family = binomial, data = droplevels(z))), error = function(e) NULL)
  if (is.null(fit)) return(c(beta = NA, z = NA, n = nrow(z)))
  s <- summary(fit)$coefficients
  if (!a %in% rownames(s)) return(c(beta = NA, z = NA, n = nrow(z)))
  c(beta = s[a, 1], z = s[a, 3], n = nrow(z))
}

run <- function(Hfind, Htest) {
  L <- learn(Hfind)
  e <- L$edges
  isfeat <- e$from %in% feats & e$to %in% feats
  e$kind <- ifelse(!isfeat, "bakgrund", ifelse(mapply(okpair, e$from, e$to), "kandidat", "familj"))
  cand <- e[e$kind == "kandidat", ]
  xa <- d[d$half == Hfind, ]; xb <- d[d$half == Htest, ]
  res <- do.call(rbind, lapply(seq_len(nrow(cand)), function(i) {
    a <- cand$from[i]; b <- cand$to[i]
    G <- union(neigh(e, a), neigh(e, b))
    fa <- fit_edge(xa, a, b, G); fb <- fit_edge(xb, a, b, G)
    p1 <- if (is.na(fa["beta"]) || is.na(fb["z"])) NA else if (fa["beta"] > 0) pnorm(fb["z"], lower.tail = FALSE) else pnorm(fb["z"])
    data.frame(a = a, b = b, strength = cand$strength[i], n_G = length(setdiff(intersect(G, feats), c(a, b))),
               beta_find = unname(fa["beta"]), beta_test = unname(fb["beta"]), n_test = unname(fb["n"]), p1 = unname(p1))
  }))
  if (!is.null(res) && nrow(res)) {
    res$holm <- p.adjust(res$p1, "holm")
    res$utslag <- ifelse(!is.na(res$holm) & res$holm < 0.05, "bekräftad", "höll inte")
  }
  list(learn = L, edges = e, cand = cand, res = res)
}

fa <- file.path(dir, "natverk_A.rds")
M <- if (file.exists(fa)) readRDS(fa) else run("A", "B")  # same seed: reuse a finished run
saveRDS(M, fa)
write_json(M$cand[, c("from", "to", "strength")], file.path(dir, "kandidater.json"), digits = NA, pretty = TRUE)
writeLines(paste(digest(file = file.path(dir, "kandidater.json"), algo = "sha256"), " kandidater.json"), file.path(dir, "kandidater.sha256"))
fb <- file.path(dir, "natverk_B.rds")
S <- if (file.exists(fb)) readRDS(fb) else run("B", "A")
saveRDS(S, fb)

# --- the 15 known pairs ---
known <- list(c("kvinna_ensam", "rel_make"), c("flera_resare", "rel_barn"), c("kvinna_resare", "rel_make"),
              c("flera_resare", "rel_foralder"), c("kvinna_resare", "rel_barn"), c("kvinna_ensam", "rel_barn"),
              c("o_runa", "rel_barn"), c("msg_dod_uppgift", "rel_foralder"), c("kvinna_resare", "rel_foralder"),
              c("msg_resa", "flera_resare"), c("kvinna_ensam", "rel_foralder"), c("pm_kors", "skilj_apostrof"),
              c("msg_dod_borta", "rel_foralder"), c("cat_fard", "flera_resare"), c("msg_resa", "rel_foralder"))
path <- function(edges, a, b) {
  prev <- setNames(list(NULL), a); frontier <- a; seen <- a
  while (length(frontier)) {
    nxt <- c()
    for (v in frontier) for (w in neigh(edges, v)) if (!w %in% seen) { prev[[w]] <- v; seen <- c(seen, w); nxt <- c(nxt, w) }
    if (b %in% seen) { p <- b; while (p[1] != a) p <- c(prev[[p[1]]], p); return(p) }
    frontier <- nxt
  }
  NULL
}
K <- do.call(rbind, lapply(known, function(p) {
  key <- paste(sort(p), collapse = "~")
  inA <- key %in% M$edges$key
  r <- if (!is.null(M$res)) M$res[mapply(function(a, b) paste(sort(c(a, b)), collapse = "~"), M$res$a, M$res$b) == key, ] else NULL
  status <- if (!is.null(r) && nrow(r) && r$utslag[1] == "bekräftad") "direkt, bekräftad" else if (inA) {
    if (M$edges$kind[M$edges$key == key][1] != "kandidat") "kant inom familj (inte prövad)" else "kant i A, inte bekräftad"
  } else "ingen direkt kant"
  pth <- if (!inA) path(M$edges, p[1], p[2]) else NULL
  data.frame(a = p[1], b = p[2], status = status, via = if (is.null(pth)) "" else paste(pth, collapse = " – "))
}))

out <- list(plan = "analysplaner/2026-11-01-upptacktsmotorn-v4-natverk.md", n_stones = nrow(d),
            A = list(n = M$learn$n, dropped = M$learn$dropped, edges = as.list(table(M$edges$kind)), n_cand = nrow(M$cand), res = M$res),
            swapped = list(n = S$learn$n, edges = as.list(table(S$edges$kind)), n_cand = nrow(S$cand), res = S$res),
            known = K, edges_A = M$edges)
write_json(out, file.path(dir, "resultat.json"), digits = NA, pretty = TRUE, auto_unbox = TRUE, na = "null")
cat("A: kanter", nrow(M$edges), "| typer:", paste(names(table(M$edges$kind)), table(M$edges$kind), collapse = ", "), "\n")
print(M$res[order(M$res$holm), ])
cat("\nBytta: kanter", nrow(S$edges), "kandidater", nrow(S$cand), "bekräftade", sum(S$res$utslag == "bekräftad", na.rm = TRUE), "\n")
print(S$res[S$res$utslag == "bekräftad", c("a", "b", "beta_find", "beta_test", "holm")])
cat("\nKända par:\n"); print(K)
