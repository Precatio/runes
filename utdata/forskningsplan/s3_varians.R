# Studie 3 (analysplaner/2026-10-24-skanningarna.md): hur stor del av spårmåttens variation hör till ristaren,
# bergarten och stenen? lmer(mått ~ skanner + (1|bergart) + (1|ristare) + (1|sten)), 500 parametriska bootstrap.
suppressMessages(library(lme4))
here <- "utdata/forskningsplan"
d <- read.csv(file.path(here, "s3_snitt.csv"), fileEncoding = "UTF-8", check.names = FALSE)
set.seed(1)
out <- list()
for (m in c("apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm", "bottenradie_mm")) {
  x <- d[!is.na(d[[m]]), ]
  x$y <- x[[m]]
  # Step 0a marks a measure resolution-sensitive: then the scan's point spacing enters as a covariate
  sens <- jsonlite::fromJSON(file.path(here, "s_analys.json"))$steg0a
  sensitive <- any(vapply(sens, function(s) isTRUE(s[[m]]$känsligt), logical(1)))
  fixed <- c(if (length(unique(x$skanner)) > 1) "skanner", if (sensitive) "upplosning")
  form <- as.formula(paste("y ~", paste(c(fixed, "(1 | bergart)", "(1 | ristare)", "(1 | sten)"), collapse = " + ")))
  fit <- lmer(form, data = x, REML = TRUE)
  shares <- function(f) {
    v <- as.data.frame(VarCorr(f))
    s <- setNames(v$vcov, v$grp)
    s / sum(s)
  }
  est <- shares(fit)
  bs <- bootMer(fit, shares, nsim = 500, seed = 1)
  ci <- apply(bs$t, 2, quantile, c(0.025, 0.975), na.rm = TRUE)
  cat(sprintf("\n%s (%d snitt, %d stenar, %d ristare, %d bergarter)\n", m, nrow(x), length(unique(x$sten)),
              length(unique(x$ristare)), length(unique(x$bergart))))
  for (g in names(est)) cat(sprintf("  %-9s %5.1f %%  [%5.1f, %5.1f]\n", g, 100 * est[[g]], 100 * ci[1, g], 100 * ci[2, g]))
  out[[m]] <- list(n = nrow(x), shares = as.list(est), lo = as.list(ci[1, ]), hi = as.list(ci[2, ]))
}
jsonlite::write_json(out, file.path(here, "s3_varians.json"), auto_unbox = TRUE, digits = 5, pretty = TRUE)
