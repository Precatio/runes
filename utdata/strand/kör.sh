#!/bin/zsh
# Kör analysen steg för steg, en R-process i taget (minnet): planen analysplaner/2026-10-23-strand-och-gravfalt.md
set -e
cd "$(dirname "$0")/../.."  # projektmappen
LOG=/Volumes/2TB/cache/strand
for p in U Sö Ög Sm Vg Öl; do Rscript --vanilla utdata/strand/01_avstand.R $p >> $LOG/steg1.log 2>&1; done
for p in U Sö Ög Sm Vg Öl; do Rscript --vanilla utdata/strand/01b_marginal.R $p >> $LOG/steg1b.log 2>&1; done
for p in U Sö Ög Sm Vg Öl; do Rscript --vanilla utdata/strand/02_r6.R $p >> $LOG/steg2.log 2>&1; done
Rscript --vanilla utdata/strand/03_statistik.R >> $LOG/steg3.log 2>&1
Rscript --vanilla utdata/strand/04_figurer.R >> $LOG/steg4.log 2>&1
