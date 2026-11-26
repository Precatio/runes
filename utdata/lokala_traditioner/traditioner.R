# Lokala ornamenttraditioner (analysplaner/2026-11-26-lokala-ornamenttraditioner.md).
# glmer(drag ~ stilgrupp + landskap + (1|härad) + (1|härad:socken)); ICC för häradet; LRT för häradets slumpeffekt
# (p halverat), Holm över de prövade dragen; ICC-intervall med parametrisk bootstrap (200, frö 20261126).
suppressMessages({library(lme4); library(jsonlite)})
here <- "utdata/lokala_traditioner"
plan <- "analysplaner/2026-11-26-lokala-ornamenttraditioner.md"
stopifnot(sub(" .*", "", system2("shasum", c("-a", "256", plan), stdout = TRUE)) == readLines(paste0(plan, ".sha256")))
d <- read.csv(file.path(here, "data.csv"), stringsAsFactors = FALSE)
d$stil <- factor(d$stil); d$landskap <- factor(d$landskap)
ctl <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
icc_of <- function(m) {
  v <- as.data.frame(VarCorr(m)); vh <- v$vcov[v$grp == "harad"]; vs <- sum(v$vcov[v$grp == "harad:socken"])
  vh / (vh + vs + pi^2 / 3)
}
fit <- function(y, boot = FALSE) {
  x <- d[!is.na(d[[y]]), ]
  x$stil <- droplevels(x$stil); x$landskap <- droplevels(x$landskap)
  fe <- c(if (nlevels(x$stil) > 1) "stil", if (nlevels(x$landskap) > 1) "landskap")
  if (nrow(x) < 100 || length(unique(x$harad)) < 20) return(list(n = nrow(x), provad = FALSE))
  full_f <- reformulate(c(fe, "(1 | harad)", "(1 | harad:socken)"), y)
  red_f <- reformulate(c(fe, "(1 | harad:socken)"), y)
  m <- glmer(full_f, data = x, family = binomial, control = ctl)
  socken <- TRUE
  if (!is.null(m@optinfo$conv$lme4$messages) || isSingular(m)) {
    m2 <- glmer(reformulate(c(fe, "(1 | harad)"), y), data = x, family = binomial, control = ctl)
    if (is.null(m2@optinfo$conv$lme4$messages)) { m <- m2; socken <- FALSE; red_f <- reformulate(fe, y) }
  }
  red <- if (socken) glmer(red_f, data = x, family = binomial, control = ctl) else glm(red_f, data = x, family = binomial)
  lrt <- as.numeric(2 * (logLik(m) - logLik(red)))
  p <- 0.5 * pchisq(max(lrt, 0), 1, lower.tail = FALSE)
  out <- list(n = nrow(x), harader = length(unique(x$harad)), andel = mean(x[[y]]), icc = icc_of(m), lrt = lrt,
              p = p, sockenterm = socken, provad = TRUE)
  if (boot) {
    set.seed(20261126)
    b <- tryCatch(bootMer(m, icc_of, nsim = 200, type = "parametric")$t, error = function(e) NULL)
    if (!is.null(b)) out$icc_95 <- unname(quantile(b, c(0.025, 0.975), na.rm = TRUE))
    re <- ranef(m)$harad
    o <- order(-abs(re[, 1]))[1:min(5, nrow(re))]
    out$avvikande_harader <- setNames(as.list(round(re[o, 1], 2)), rownames(re)[o])
  }
  out
}
D <- paste0("D", 1:8)
res <- lapply(setNames(D, D), fit)
tested <- names(res)[sapply(res, `[[`, "provad")]
ph <- p.adjust(sapply(res[tested], `[[`, "p"), "holm")
for (k in tested) { res[[k]]$p_holm <- unname(ph[k]); res[[k]]$lokal_tradition <- unname(ph[k] < 0.05) }
for (k in tested) if (isTRUE(res[[k]]$lokal_tradition)) res[[k]] <- c(res[[k]], fit(k, boot = TRUE)[c("icc_95", "avvikande_harader")])
S <- grep("^S_", names(d), value = TRUE)
sprak <- lapply(setNames(S, S), fit)
out <- list(plan = basename(plan), stenar = nrow(d), harader = length(unique(d$harad)),
            drag = list(D1 = "koppel", D2 = "huvud ovanifrån", D3 = "mandelöga", D4 = "flätverk", D5 = "extra orm",
                        D6 = "kors", D7 = "två eller fler djur", D8 = "svans i spiral"),
            ornamentik = res, sprakdrag_jamforelse = sprak)
write_json(out, file.path(here, "resultat.json"), auto_unbox = TRUE, digits = 5, pretty = TRUE)
for (k in names(res)) with(res[[k]], if (isTRUE(provad)) cat(sprintf("%s %-18s n=%d icc=%.3f p=%.2g holm=%.2g %s\n", k,
  out$drag[[k]], n, icc, p, p_holm, if (lokal_tradition) "LOKAL" else "")) else cat(k, "ej prövad n=", n, "\n"))
for (k in names(sprak)) with(sprak[[k]], if (isTRUE(provad)) cat(sprintf("%-16s n=%d icc=%.3f p=%.2g\n", k, n, icc, p)))
