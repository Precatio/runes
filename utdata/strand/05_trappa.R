# Steg 5: robusthetsstegen enligt den låsta tilläggsplanen analysplaner/2026-11-01-strand-trappan.md, för H1 (vattnet
# år 1050) och H3 (gravfälten). Samma stenar, punkter och mått som 03_statistik.R.
#   Rscript --vanilla utdata/strand/05_trappa.R      Skriver trappan.json.
.here <- dirname(normalizePath(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])))
source(file.path(.here, "config.R"))
suppressPackageStartupMessages(library(lme4))
S <- load_stones()
all6 <- S$all6
A <- lapply(PROVS, function(pv) readRDS(file.path(WORK, paste0(pv_key(pv), "_avstand.rds")))); names(A) <- PROVS
dist_st <- bind_rows(lapply(A, function(a) a$stones))
all6$then <- dist_st$then[match(all6$signum, dist_st$signum)]
rnd <- bind_rows(lapply(A, function(a) a$rnd[["main"]]))
d <- all6[all6$moved == 0, ]

# Halves exactly as in 03_statistik.R; every random point belongs to the nearest stone in the same province
d$pk <- ifelse(is.na(d$parish) | d$parish == "", paste0("_", d$signum), d$parish)
pinfo <- data.frame(province = d$province, pk = d$pk, t = d$t50) %>% group_by(province, pk) %>%
  summarise(mt = if (all(is.na(t))) NA_real_ else mean(t, na.rm = TRUE), n = n(), .groups = "drop") %>%
  arrange(province, is.na(mt), mt, desc(n)) %>% group_by(province) %>%
  mutate(half = ifelse(row_number() %% 2 == 1, "A", "B")) %>% ungroup()
d$half <- pinfo$half[match(paste(d$province, d$pk), paste(pinfo$province, pinfo$pk))]
rnd$owner <- NA_character_
for (pv in PROVS) {
  ri <- which(rnd$province == pv); si <- which(d$province == pv)
  nn <- st_nearest_feature(st_as_sf(rnd[ri, ], coords = c("x", "y"), crs = SWEREF),
                           st_as_sf(d[si, ], coords = c("x", "y"), crs = SWEREF))
  rnd$owner[ri] <- d$signum[si][nn]
}
rnd$half <- d$half[match(rnd$owner, d$signum)]
rnd$pk <- d$pk[match(rnd$owner, d$signum)]
rem <- read.csv(REMAINS, fileEncoding = "UTF-8", stringsAsFactors = FALSE) %>% filter(!is.na(lat), !is.na(lon))
gf <- st_transform(st_as_sf(rem[rem$type == "gravfält", ], coords = c("lon", "lat"), crs = 4326), SWEREF)
nearest_m <- function(df) {
  p <- st_as_sf(df, coords = c("x", "y"), crs = SWEREF)
  as.numeric(st_distance(p, gf[st_nearest_feature(p, gf), ], by_element = TRUE))
}
d$grave <- nearest_m(d); rnd$grave <- nearest_m(rnd)

# The same stones and distances as the run of 03_statistik.R, or stop
st <- read.csv(file.path(OUT, "stenar.csv"), fileEncoding = "UTF-8", stringsAsFactors = FALSE)
res <- jsonlite::fromJSON(file.path(OUT, "resultat.json"), simplifyVector = FALSE)
m <- match(d$signum, st$signum)
stopifnot(nrow(d) == nrow(st), !anyNA(m), isTRUE(all.equal(d$then, st$then[m])), isTRUE(all.equal(d$grave, st$grave[m])),
          identical(d$half, st$half[m]), nrow(rnd) == res$population$n_random,
          round(median(rnd$then)) == res$H1$overall$median_random_m, round(median(rnd$grave)) == res$H3$overall$median_random_m)
say("samma stenar och avstånd som 03_statistik.R: ", nrow(d), " stenar, ", nrow(rnd), " punkter")

# Flags for the steps
now_c <- read_corpus(file.path(REPO, "data/cache/r/corpus/e83202e01a5e6d27/corpus.csv"))
mc <- match(d$signum, now_c$signum)
d$carver_sure <- ifelse(!is.na(mc) & !is.na(now_c$carvers_uncertain[mc]) & now_c$carvers_uncertain[mc] == 0 &
                          !is.na(now_c$carver[mc]) & now_c$carver[mc] != "", now_c$carver[mc], NA_character_)
d$stays_now <- !is.na(mc) & !is.na(now_c$moved[mc]) & now_c$moved[mc] == 0 & !is.na(now_c$lost[mc]) & now_c$lost[mc] == 0
runor <- jsonlite::fromJSON(file.path(REPO, "data/raa/runor_2020.json"), simplifyVector = TRUE)
runor <- if (is.data.frame(runor)) runor else runor$inscriptions
d$moved_runor <- d$signum %in% runor$signum[!is.na(runor$original) & runor$original == FALSE]
REERECT <- "återrest|återupprest|rest upp|restes upp|uppsatt|uppställd|lagad|lagades|lagats|reparerad"
txt <- setNames(rep("", nrow(d)), d$signum)
for (r in jsonlite::fromJSON(file.path(REPO, "data/raa/kmr_runstenar.json"), simplifyVector = FALSE)$records) {
  t <- paste(sapply(c("Beskrivning", "Placering", "Skadestatus", "Orientering"),
                    function(k) paste(unlist(r$fields[[k]]), collapse = " ")), collapse = " ")
  for (s in intersect(unlist(r$signa), d$signum)) txt[[s]] <- paste(txt[[s]], t)
}
for (r in jsonlite::fromJSON(file.path(REPO, "data/rundata.json"), simplifyVector = FALSE)$inscriptions) {
  if (r$signum %in% d$signum) txt[[r$signum]] <- paste(txt[[r$signum]], if (is.null(r$placement)) "" else r$placement,
                                                       if (is.null(r$other)) "" else r$other)
}
d$reerected <- grepl(REERECT, tolower(txt[d$signum]))

# ---- the tests ----------------------------------------------------------------------------------------------------
auc <- function(s, r) {
  n1 <- length(s); n2 <- length(r)
  rk <- rank(c(s, r))
  1 - (sum(rk[seq_len(n1)]) - n1 * (n1 + 1) / 2) / (n1 * n2)
}
summ <- function(s, r) {
  s <- s[!is.na(s)]; r <- r[!is.na(r)]
  w <- suppressWarnings(wilcox.test(s, r, alternative = "less", exact = FALSE))
  list(n_stones = length(s), n_random = length(r), median_stones_m = round(median(s)), median_random_m = round(median(r)),
       auc = r3(auc(s, r)), p = signif(w$p.value, 3), within_500_stones = r3(mean(s < 500)),
       within_500_random = r3(mean(r < 500)))
}
ok <- function(r) r$p < 0.05 && r$auc > 0.5
sub_test <- function(keep, col) {
  c(summ(d[[col]][keep], rnd[[col]][rnd$owner %in% d$signum[keep]]), list(removed = sum(!keep)))
}
mixed <- function(col) {
  both <- rbind(data.frame(y = 1, province = d$province, pk = d$pk, v = d[[col]]),
                data.frame(y = 0, province = rnd$province, pk = rnd$pk, v = rnd[[col]]))
  both$closer <- -log2(both$v + 250)
  warn <- character(0)
  fit <- withCallingHandlers(glmer(y ~ closer + factor(province) + (1 | pk), data = both, family = binomial,
                                   control = glmerControl(optimizer = "bobyqa")),
                             warning = function(w) { warn <<- c(warn, conditionMessage(w)); invokeRestart("muffleWarning") })
  cf <- coef(summary(fit))["closer", ]
  p1 <- pnorm(cf[["z value"]], lower.tail = FALSE)
  list(n = nrow(both), n_parishes = length(unique(both$pk)), or = r3(exp(cf[["Estimate"]])),
       lo = r3(exp(cf[["Estimate"]] - 1.96 * cf[["Std. Error"]])), hi = r3(exp(cf[["Estimate"]] + 1.96 * cf[["Std. Error"]])),
       p = signif(p1, 3), sd_parish = r3(sqrt(as.numeric(VarCorr(fit)$pk))), warnings = warn,
       holds = cf[["Estimate"]] > 0 && p1 < 0.05)
}
first_carver <- d[!is.na(d$carver_sure), ]
first_carver <- first_carver[order(first_carver$signum, method = "radix"), ]
first_carver <- first_carver$signum[!duplicated(first_carver$carver_sure)]
keep_carver <- is.na(d$carver_sure) | d$signum %in% first_carver
dated <- !is.na(d$year)

ladder <- function(col) {
  R <- list()
  R$huvud <- c(summ(d[[col]], rnd[[col]]), list(removed = 0L))
  R$halva_A <- sub_test(d$half == "A", col)
  R$halva_B <- sub_test(d$half == "B", col)
  pm <- tapply(d[[col]], d$pk, median)
  R$socken <- c(summ(as.numeric(pm), rnd[[col]]), list(n_parishes = length(pm)))
  R$en_per_ristare <- c(sub_test(keep_carver, col), list(n_carvers = length(first_carver)))
  R$utan_aterresta <- sub_test(!d$reerected, col)
  R$utan_flyttade_runor <- sub_test(!d$moved_runor, col)
  R$dagens_flyttregel <- sub_test(d$stays_now, col)
  R$tidiga <- sub_test(dated & d$year < 1050, col)
  R$sena <- sub_test(dated & d$year >= 1050, col)
  for (k in names(R)) R[[k]]$holds <- ok(R[[k]])
  R$socken_slumpeffekt <- mixed(col)
  lopo <- lapply(PROVS, function(pv) {
    r <- sub_test(d$province != pv, col); r$share_kept <- r3(r$n_stones / nrow(d))
    r$holds <- r$auc > 0.5 && (r$share_kept < 2 / 3 || r$p < 0.05); r
  })
  names(lopo) <- PROVS
  steps <- c(halvorna = R$halva_A$holds && R$halva_B$holds, utan_ett_landskap = all(sapply(lopo, `[[`, "holds")),
             socken = R$socken$holds, socken_slumpeffekt = R$socken_slumpeffekt$holds,
             en_per_ristare = R$en_per_ristare$holds, utan_aterresta = R$utan_aterresta$holds,
             utan_flyttade_runor = R$utan_flyttade_runor$holds, dagens_flyttregel = R$dagens_flyttregel$holds,
             tiden = R$tidiga$holds && R$sena$holds)
  list(rungs = R, lopo = lopo, steps = as.list(steps), all_hold = all(steps))
}
out <- list(plan = "analysplaner/2026-11-01-strand-trappan.md",
            plan_sha256 = trimws(sub(" .*", "", readLines(file.path(REPO, "analysplaner/2026-11-01-strand-trappan.sha256"))[1])),
            computed_at = format(Sys.time(), "%Y-%m-%d %H:%M"), r_version = R.version.string,
            counts = list(n = nrow(d), reerected = sum(d$reerected), moved_runor = sum(d$moved_runor),
                          not_staying_now = sum(!d$stays_now), sure_carver_stones = sum(!is.na(d$carver_sure)),
                          carvers = length(first_carver), dated = sum(dated), early = sum(dated & d$year < 1050),
                          late = sum(dated & d$year >= 1050)),
            H1 = ladder("then"), H3 = ladder("grave"),
            T1 = list(water_holds = res$T1$water_holds, grave_holds = res$T1$grave_holds, n = res$T1$n))
write_json(out, file.path(OUT, "trappan.json"), auto_unbox = TRUE, digits = NA, null = "null", na = "null", pretty = TRUE)
for (h in c("H1", "H3")) {
  for (k in names(out[[h]]$rungs)) {
    r <- out[[h]]$rungs[[k]]
    if (!is.null(r$auc)) say(h, " ", k, ": n ", r$n_stones, ", median ", r$median_stones_m, " mot ", r$median_random_m,
                             " m, AUC ", r$auc, ", p ", r$p, if (r$holds) " HÅLLER" else " HÅLLER INTE")
    else say(h, " ", k, ": OR ", r$or, " (", r$lo, "–", r$hi, "), p ", r$p, if (r$holds) " HÅLLER" else " HÅLLER INTE",
             if (length(r$warnings)) paste0(" [", paste(r$warnings, collapse = "; "), "]") else "")
  }
  for (pv in PROVS) { r <- out[[h]]$lopo[[pv]]
    say(h, " utan ", pv, ": kvar ", r$share_kept, ", AUC ", r$auc, ", p ", r$p, if (r$holds) " HÅLLER" else " HÅLLER INTE") }
  say(h, ": ", if (out[[h]]$all_hold) "ALLA STEG HÅLLER" else paste("faller:", paste(names(which(!unlist(out[[h]]$steps))), collapse = ", ")))
}
say("återresta ", out$counts$reerected, ", Runor-flyttade ", out$counts$moved_runor, ", inte kvar enligt dagens regel ",
    out$counts$not_staying_now, ", ristare ", out$counts$carvers, " (", out$counts$sure_carver_stones, " stenar), tidiga ",
    out$counts$early, ", sena ", out$counts$late)
