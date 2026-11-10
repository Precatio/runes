# P2 i analysplaner/2026-11-10-sjalvkontroll-osterled.md: förskjuts östandelen mot väster från tidiga (RAK, Fp, Pr1,
# Pr2) till sena stilgrupper (Pr3–Pr5)? glm(cbind(O, V) ~ sen + landskap, quasibinomial), en rad per sten.
# Spärr: minst 20 platser (O + V) i både tidig och sen grupp, annars "för få träffar" (modellen redovisas då bara
# beskrivande). Läser stenar_tid.csv (analys.py), skriver tid_resultat.json.
suppressPackageStartupMessages(library(jsonlite))
here <- tryCatch(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)))),
                 error = function(e) ".")
d <- read.csv(file.path(here, "stenar_tid.csv"), encoding = "UTF-8", stringsAsFactors = FALSE)
d$landskap <- factor(d$landskap, levels = c("Uppland", "Södermanland", "Östergötland", "övriga"))

fit <- function(x, sen_col = "sen", mitt_col = "mitt", adj = TRUE, trend = FALSE) {
  x <- x[!is.na(x[[sen_col]]), ]
  x$sen_ <- x[[sen_col]]
  x$mitt50 <- (x[[mitt_col]] - 1050) / 50
  hits <- c(tidig = sum(x$O[x$sen_ == 0] + x$V[x$sen_ == 0]), sen = sum(x$O[x$sen_ == 1] + x$V[x$sen_ == 1]))
  x$landskap <- droplevels(x$landskap)
  term <- if (trend) "mitt50" else "sen_"
  rhs <- paste(c(term, if (adj && nlevels(x$landskap) > 1) "landskap"), collapse = " + ")
  m <- glm(as.formula(paste("cbind(O, V) ~", rhs)), family = quasibinomial, data = x)
  s <- summary(m)$coefficients
  b <- s[term, "Estimate"]; se <- s[term, "Std. Error"]; df <- m$df.residual
  t <- b / se
  list(stenar = nrow(x), platser = as.list(hits), enough = unname(all(hits >= 20)), term = term,
       or = exp(b), ci = exp(b + c(-1, 1) * qt(0.975, df) * se),
       p_ensidig_lagre = pt(t, df), p_tvasidig = 2 * pt(-abs(t), df), dispersion = summary(m)$dispersion,
       landskap = as.list(table(x$landskap)))
}

dom <- function(r) {
  if (!r$enough) return("för få träffar")
  if (r$or < 1 && r$p_ensidig_lagre < 0.05) return("håller (förskjutning mot väster)")
  if (r$or > 1 && r$p_tvasidig < 0.05) return("motsatt riktning")
  if (r$ci[1] >= 0.5 && r$ci[2] <= 2) return("ingen förskjutning av betydelse")
  "obestämt"
}

d_wo <- d[d$ingvar == 0, ]
d_wide <- d; d_wide$sen <- d_wide$sen_vid; d_wide$mitt <- d_wide$mitt_vid
out <- list(
  huvud_med_ingvar = fit(d),
  huvud_utan_ingvar = fit(d_wo),
  rob_utan_landskap = fit(d, adj = FALSE),
  rob_trend_mittar = fit(d, trend = TRUE),
  rob_trend_mittar_utan_ingvar = fit(d_wo, trend = TRUE),
  rob_vida_stilgrupper = fit(d_wide),
  rob_vida_stilgrupper_utan_ingvar = fit(d_wide[d_wide$ingvar == 0, ]),
  rob_utan_knut = fit(d[d$knut == 0, ])
)
for (k in names(out)) out[[k]]$dom <- if (startsWith(k, "huvud")) dom(out[[k]]) else NA
for (k in names(out)) out[[k]]$not <- if (!out[[k]]$enough) "spärren (20 platser i varje grupp) nås inte: endast beskrivande" else ""
write_json(out, file.path(here, "tid_resultat.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
for (k in names(out)) with(out[[k]], cat(sprintf("%-34s n=%3d platser tidig/sen=%s/%s OR=%.2f [%.2f, %.2f] p1=%.3f p2=%.3f %s\n",
  k, stenar, platser$tidig, platser$sen, or, ci[1], ci[2], p_ensidig_lagre, p_tvasidig, ifelse(is.na(out[[k]]$dom), "", out[[k]]$dom))))
