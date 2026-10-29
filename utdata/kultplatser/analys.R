# Bönen vid den gamla kultplatsen: H1–H4 enligt den låsta planen analysplaner/2026-10-29-bon-vid-kultplatsen.md.
#   .venv/bin/python utdata/kultplatser/data.py && Rscript utdata/kultplatser/analys.R
suppressMessages({library(dplyr); library(jsonlite); library(lme4)})
dir <- "utdata/kultplatser"
d <- read.csv(file.path(dir, "stenar.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
nm <- read.csv(file.path(dir, "namn.csv"), encoding = "UTF-8", stringsAsFactors = FALSE, na.strings = "")
d$year <- ifelse(!is.na(d$style_from), (d$style_from + d$style_to) / 2, NA)
d$t50 <- (d$year - 1050) / 50
# Halves as in r/change.R: whole parishes alternately within the province, ordered by the parish's mean dating
pkey <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = pkey, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, pkey), paste(pinfo$province, pinfo$pk))]
d$hand <- ifelse(!is.na(d$carver) & d$carver != "", d$carver, paste0("_", d$province, ":", pkey))
FLOOR <- 0.05  # km: a stone in the churchyard is not infinitely near the church
d$l2_early <- log2(pmax(d$km_church_early, FLOOR))
d$l2_late <- log2(pmax(d$km_church_late, FLOOR))
d$near <- as.integer(d$km_cult < 2)
d$near_spring <- as.integer(d$km_spring < 2)

# One-sided p in the hypothesis' direction (sign = +1: coefficient > 0)
one <- function(z, sign) if (sign > 0) pnorm(z, lower.tail = FALSE) else pnorm(z)
logit <- function(dd, f, term, sign = 1) {
  m <- tryCatch(suppressWarnings(glm(f, data = droplevels(dd), family = binomial)), error = function(e) NULL)
  if (is.null(m) || !term %in% rownames(coef(summary(m)))) return(NULL)
  s <- coef(summary(m))[term, ]
  list(n = nrow(dd), or = exp(s[[1]]), lo = exp(s[[1]] - 1.96 * s[[2]]), hi = exp(s[[1]] + 1.96 * s[[2]]),
       p_two = s[[4]], p = one(s[[3]], sign))
}
halves <- function(dd, f, term, sign = 1) {
  h <- lapply(c(A = "A", B = "B"), function(x) logit(dd[dd$half == x, ], f, term, sign))
  ok <- function(r) !is.null(r) && r$p < 0.05
  c(h, list(replicated = ok(h$A) && ok(h$B)))
}
share <- function(x) mean(x, na.rm = TRUE)
P <- "+ factor(province)"

res <- list(n = nrow(d), n_near = sum(d$near), n_names_near = length(unique(d$cult_name[d$near == 1])))
res$base <- c(logit(d, as.formula(paste("bon ~ near", P)), "near"),
              list(share_near = share(d$bon[d$near == 1]), share_far = share(d$bon[d$near == 0])))

# H1: among dated prayer stones, are those near a theophoric name earlier?
pr <- d[d$bon == 1 & !is.na(d$year), ]
m1 <- lm(as.formula(paste("year ~ near", P)), data = droplevels(pr))
s1 <- coef(summary(m1))["near", ]
res$H1 <- list(n = nrow(pr), n_near = sum(pr$near), years = s1[[1]],
               ci = s1[[1]] + c(-1.96, 1.96) * s1[[2]], p = pt(s1[[3]], m1$df.residual),
               mean_near = mean(pr$year[pr$near == 1]), mean_far = mean(pr$year[pr$near == 0]))
dt <- d[!is.na(d$year), ]; dt$late <- as.integer(dt$year >= 1050)
res$H1$robust_interaction <- logit(dt, as.formula(paste("bon ~ near * late", P)), "near:late", sign = -1)
res$H1$robust_early <- logit(dt[dt$late == 0, ], as.formula(paste("bon ~ near", P)), "near")
res$H1$robust_late <- logit(dt[dt$late == 1, ], as.formula(paste("bon ~ near", P)), "near")

# H2: near a name, do prayer stones stand nearer the name, relative to the nearest farm, than other stones?
nr <- d[d$near == 1 & !is.na(d$km_farm), ]
nr$lr <- log2(pmax(nr$km_cult, FLOOR) / pmax(nr$km_farm, FLOOR))
small <- names(which(table(nr$province) < 5))
nr$prov2 <- ifelse(nr$province %in% small, "övriga", nr$province)
res$H2 <- c(logit(nr, bon ~ lr + factor(prov2), "lr", sign = -1),
            list(median_lr_bon = median(nr$lr[nr$bon == 1]), median_lr_other = median(nr$lr[nr$bon == 0]),
                 n_bon = sum(nr$bon), prov_collapsed = small))
ft <- fisher.test(table(factor(nr$km_cult < nr$km_farm, c(TRUE, FALSE)), factor(nr$bon, c(1, 0))), alternative = "greater")
res$H2$robust_fisher <- list(p = ft$p.value, or = unname(ft$estimate),
                             share_nearer_bon = share(nr$km_cult[nr$bon == 1] < nr$km_farm[nr$bon == 1]),
                             share_nearer_other = share(nr$km_cult[nr$bon == 0] < nr$km_farm[nr$bon == 0]))

# H3: with nearness to early and late churches held constant
f3 <- as.formula(paste("bon ~ near + l2_early + l2_late", P))
res$H3 <- c(logit(d, f3, "near"), list(halves = halves(d, f3, "near")))
res$H3$church_terms <- list(early = logit(d, f3, "l2_early", sign = -1), late = logit(d, f3, "l2_late", sign = -1))
rob3 <- list()
for (km in c(1, 3)) { dd <- d; dd$near <- as.integer(dd$km_cult < km); rob3[[paste0("km", km)]] <- c(logit(dd, f3, "near"), list(n_near = sum(dd$near))) }
rob3$time <- logit(dt, as.formula(paste("bon ~ near + l2_early + l2_late + t50", P)), "near")
rob3$carver <- tryCatch({
  m <- glmer(as.formula(paste("bon ~ near + l2_early + l2_late", P, "+ (1 | hand)")), data = d, family = binomial,
             control = glmerControl(optimizer = "bobyqa"))
  s <- coef(summary(m))["near", ]; list(or = exp(s[[1]]), p = one(s[[3]], 1))
}, error = function(e) list(error = conditionMessage(e)))
rob3$U_So <- logit(d[d$province %in% c("U", "Sö"), ], f3, "near")
rob3$runor <- logit(d[d$moved_runor == 0, ], f3, "near")
loo <- sapply(unique(d$cult_name[d$near == 1]), function(n) {
  r <- logit(d[!(d$near == 1 & d$cult_name == n), ], f3, "near"); if (is.null(r)) NA else r$or })
rob3$loo <- list(min_or = min(loo, na.rm = TRUE), max_or = max(loo, na.rm = TRUE), min_name = names(which.min(loo)))
res$H3$robust <- rob3

# H4: prayer near springs with tradition
f4 <- as.formula(paste("bon ~ near_spring", P))
res$H4 <- c(logit(d, f4, "near_spring"), list(halves = halves(d, f4, "near_spring"), n_near = sum(d$near_spring),
            share_near = share(d$bon[d$near_spring == 1]), share_far = share(d$bon[d$near_spring == 0])))
rob4 <- list()
for (km in c(1, 3)) { dd <- d; dd$near_spring <- as.integer(dd$km_spring < km); rob4[[paste0("km", km)]] <- c(logit(dd, f4, "near_spring"), list(n_near = sum(dd$near_spring))) }
rob4$time <- logit(dt, as.formula(paste("bon ~ near_spring + t50", P)), "near_spring")
rob4$carver <- tryCatch({
  m <- glmer(as.formula(paste("bon ~ near_spring", P, "+ (1 | hand)")), data = d, family = binomial,
             control = glmerControl(optimizer = "bobyqa"))
  s <- coef(summary(m))["near_spring", ]; list(or = exp(s[[1]]), p = one(s[[3]], 1))
}, error = function(e) list(error = conditionMessage(e)))
rob4$U_So <- logit(d[d$province %in% c("U", "Sö"), ], f4, "near_spring")
rob4$runor <- logit(d[d$moved_runor == 0, ], f4, "near_spring")
res$H4$robust <- rob4

ps <- c(H1 = res$H1$p, H2 = res$H2$p, H3 = res$H3$p, H4 = res$H4$p)
holm <- p.adjust(ps, "holm")
verdict <- function(h) {
  p <- ps[[h]]; ph <- holm[[h]]
  if (is.na(p) || p >= 0.05) return("faller")
  if (h %in% c("H3", "H4")) {
    if (ph < 0.05 && isTRUE(res[[h]]$halves$replicated)) return("håller")
  } else if (ph < 0.05) return("stöder")
  "antydan"
}
res$holm <- as.list(holm)
res$verdicts <- lapply(setNames(names(ps), names(ps)), verdict)

# Description: the names with stones within 2 km
near <- d[d$near == 1, ]
res$names <- lapply(split(near, near$cult_name), function(x) {
  n <- nm[nm$name == x$cult_name[1], ][1, ]
  list(name = x$cult_name[1], god = x$cult_god[1], province = paste(unique(x$province), collapse = "/"),
       stones = nrow(x), bon = sum(x$bon), bon_signa = x$signum[x$bon == 1],
       km_church_early = n$km_church_early, km_offerplats = n$km_offerplats)
})
write_json(res, file.path(dir, "kultplatser.json"), auto_unbox = TRUE, digits = NA, pretty = TRUE)
cat(toJSON(res[c("n", "n_near", "base", "holm", "verdicts")], auto_unbox = TRUE, digits = 4), "\n")
