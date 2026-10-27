# Kontroll i R av alla statistiska påståenden i artikeln "Vad berättar runskrifterna på de brittiska öarna?"
# (build_brittiska.py räknar dem i Python; här räknas de om oberoende, med intervall och känslighetsprov).
#   .venv/bin/python utdata/brittiska/statistik_data.py && Rscript utdata/brittiska/statistik.R
library(jsonlite)
here <- "utdata/brittiska"
a <- fromJSON(file.path(here, "analys.json"))
W <- a$women_commemorated
cat("\n== 1. Kvinnor bland de minnade (när släktskapen anges) ==\n")
man <- c(W$`Isle of Man`$women, W$`Isle of Man`$men)
bt <- binom.test(man[1], sum(man))
cat(sprintf("Isle of Man %d/%d = %.0f %%, 95 %% KI %.0f–%.0f %%\n", man[1], sum(man), 100*man[1]/sum(man), 100*bt$conf.int[1], 100*bt$conf.int[2]))
for (land in c("Norge", "Danmark", "Sverige")) {
  o <- c(W[[land]]$women, W[[land]]$men)
  ft <- fisher.test(rbind(man, o))
  cat(sprintf("  mot %-8s %d/%d = %4.1f %%   oddskvot %.1f (95 %% KI %.1f–%.1f)   p = %.2g\n", land, o[1], sum(o), 100*o[1]/sum(o),
              ft$estimate, ft$conf.int[1], ft$conf.int[2], ft$p.value))
}
nor <- c(W$Norge$women, W$Norge$men)
cat("  Känslighet: utan fostermodern på MM 130 (osäker läsning) och utan fragmentet Andreas VIII:\n")
for (k in list(c(8, 4), c(7, 4))) cat(sprintf("    Man %d/%d mot Norge: p = %.3f\n", k[1], sum(k), fisher.test(rbind(k, nor))$p.value))

cat("\n== 2. Englandsstenar per land ==\n")
st <- a$scandinavian_stones; en <- a$naming_islands
sv <- c(en$`Sverige|England`, st$Sverige); no <- c(en$`Norge|England`, st$Norge)
ft <- fisher.test(rbind(c(sv[1], sv[2]-sv[1]), c(no[1], no[2]-no[1])))
cat(sprintf("Sverige 1 av %.0f, Norge 1 av %.0f: oddskvot %.2f (95 %% KI %.2f–%.1f), p = %.2f\n", sv[2]/sv[1], no[2]/no[1],
            ft$estimate, ft$conf.int[1], ft$conf.int[2], ft$p.value))

cat("\n== 3. Namnpar på båda sidor ==\n")
h <- fromJSON(file.path(here, "hemma.json"))
cat(sprintf("%d par prövade, %.1f väntade av slump, %d funna: P(minst %d) = %.2f\n", h$pairs_tested, h$pairs_expected,
            length(h$pairs_found$isles), length(h$pairs_found$isles), ppois(length(h$pairs_found$isles) - 1, h$pairs_expected, lower.tail = FALSE)))

cat("\n== 4. Götaland mot Svealand: dog i väster ==\n")
d <- read.csv(file.path(here, "hemma_tabell.csv"))
d <- subset(d, utfall != "utesluten" & region != "övrigt")
d$dog <- as.integer(d$utfall == "dog"); d$region <- factor(d$region, c("Svealand", "Götaland"))
show <- function(x, namn) {
  t <- table(x$region, x$dog)
  ft <- fisher.test(t)
  s <- subset(x, stil != "")
  mh <- mantelhaen.test(xtabs(~ region + dog + stil, s), exact = TRUE)
  cat(sprintf("%-46s Götaland %2d/%2d, Svealand %2d/%2d   Fisher p = %.4f   inom stilgrupp p = %.4f\n", namn,
              t["Götaland", "1"], sum(t["Götaland", ]), t["Svealand", "1"], sum(t["Svealand", ]), ft$p.value, mh$p.value))
}
show(d, "Huvudanalysen")
show(subset(d, !signum %in% c("Vs 5", "Vg 197")), "Utan de två osäkra kodningarna (Vs 5, Vg 197)")
show(subset(d, england == 1), "Bara stenar som nämner England, London, Bath")
show(subset(d, utfall != "resa"), "Bara dog mot kom hem (utan 'bara resan')")
m <- glm(dog ~ region + stil, binomial, subset(d, stil != ""))
ci <- exp(suppressMessages(confint(m)))
cat(sprintf("Logistisk regression, dog ~ region + stilgrupp: oddskvot Götaland %.1f (95 %% profil-KI %.1f–%.0f)\n",
            exp(coef(m)["regionGötaland"]), ci["regionGötaland", 1], ci["regionGötaland", 2]))
cat(sprintf("\nAntal test i artikeln: 3 huvudtest. Bonferroni-gräns 0,05/3 = %.3f\n", 0.05/3))
