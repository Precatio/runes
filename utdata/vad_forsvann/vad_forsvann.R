# Vad försvann? (analysplaner/2026-11-26-vad-forsvann.md) – förlorade mot bevarade runstenar, båda kodade ur teckningar.
# glmer(utfall ~ förlorad + teckningens typ + Uppland + (1|socken)); tvåsidigt Wald-p för förlorad, Holm över U1–U3.
suppressMessages({library(lme4); library(jsonlite); library(sandwich); library(lmtest)})
here <- "utdata/vad_forsvann"
plan <- "analysplaner/2026-11-26-vad-forsvann.md"
stopifnot(sub(" .*", "", system2("shasum", c("-a", "256", plan), stdout = TRUE)) == readLines(paste0(plan, ".sha256")))
d <- read.csv(file.path(here, "data.csv"), stringsAsFactors = FALSE)
d$typ <- factor(d$typ, levels = c("Bautil", "Rhezelius", "Peringskiöld", "övrig"))
fit1 <- function(y, data) {
  x <- data[!is.na(data[[y]]), ]
  f <- reformulate(c("forlorad", "typ", "uppland", "(1 | socken)"), y)
  m <- tryCatch(glmer(f, data = x, family = binomial, control = glmerControl(optimizer = "bobyqa")), error = function(e) NULL)
  conv <- !is.null(m) && is.null(m@optinfo$conv$lme4$messages)
  if (conv) {
    s <- summary(m)$coefficients["forlorad", ]
    est <- s["Estimate"]; se <- s["Std. Error"]; p <- s["Pr(>|z|)"]; metod <- "glmer"
  } else {
    g <- glm(reformulate(c("forlorad", "typ", "uppland"), y), data = x, family = binomial)
    ct <- coeftest(g, vcov = vcovCL(g, cluster = ~socken))["forlorad", ]
    est <- ct[1]; se <- ct[2]; p <- ct[4]; metod <- "glm + klusterrobust (socken)"
  }
  list(n = nrow(x), n_forlorade = sum(x$forlorad == 1), n_bevarade = sum(x$forlorad == 0),
       andel_forlorade = mean(x[[y]][x$forlorad == 1]), andel_bevarade = mean(x[[y]][x$forlorad == 0]),
       or = unname(exp(est)), ci = unname(exp(est + c(-1.96, 1.96) * se)), p = unname(p), metod = metod)
}
res <- lapply(c(U1 = "U1", U2 = "U2", U3 = "U3"), fit1, data = d)
ps <- p.adjust(sapply(res, `[[`, "p"), "holm")
for (k in names(res)) { res[[k]]$p_holm <- unname(ps[k]); res[[k]]$skiljer <- ps[k] < 0.05 }
upp <- lapply(c(U1 = "U1", U2 = "U2", U3 = "U3"), fit1, data = d[d$uppland == 1, ])
# beskrivande: förlorade (teckning) mot bevarade planschstenar (foto) i samma socknar – andelar
f <- read.csv(file.path(here, "data_foto.csv"), stringsAsFactors = FALSE)
foto <- lapply(c(U1 = "U1", U2 = "U2", U3 = "U3"), function(y) {
  x <- f[!is.na(f[[y]]), ]
  list(forlorade_teckning = mean(x[[y]][x$forlorad == 1]), n_f = sum(x$forlorad == 1),
       bevarade_foto = mean(x[[y]][x$forlorad == 0]), n_b = sum(x$forlorad == 0))
})
typer <- lapply(split(d, d$typ), function(x) sapply(c("U1", "U2", "U3"), function(y)
  c(forlorade = mean(x[[y]][x$forlorad == 1], na.rm = TRUE), bevarade = mean(x[[y]][x$forlorad == 0], na.rm = TRUE))))
out <- list(plan = basename(plan), huvudprov = res, uppland = upp, beskrivande_foto = foto, per_typ = typer)
write_json(out, file.path(here, "resultat.json"), auto_unbox = TRUE, digits = 5, pretty = TRUE)
print(toJSON(out[c("huvudprov", "uppland", "beskrivande_foto")], auto_unbox = TRUE, pretty = TRUE, digits = 3))
