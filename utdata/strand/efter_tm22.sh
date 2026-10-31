#!/bin/zsh
# Kedja 2026-10-31 (Viktor: "gör alla saker du föreslår"): väntar tills textmodellens steg 1 (tm22_kor.sh) är klart,
# kör sedan strandens återstående steg enligt planen och tillägget (R6 för Sm och Vg, statistiken med T1, figurerna),
# en R-process i taget, och startar därefter textmodellens steg 2 (tm22_steg2.sh). Ett tungt jobb i taget (16 GB).
cd "$(dirname "$0")/../.."
LOG=/Volumes/2TB/cache/strand
while pgrep -f "tm22_kor.sh" >/dev/null; do sleep 120; done
echo "$(date '+%F %T') tm22 steg 1 klart; stranden startar" >> $LOG/kedja.log
for p in Sm Vg; do Rscript --vanilla utdata/strand/02_r6.R $p >> $LOG/steg2.log 2>&1; done
Rscript --vanilla utdata/strand/03_statistik.R >> $LOG/steg3.log 2>&1 && echo "$(date '+%F %T') strandens statistik klar" >> $LOG/kedja.log
Rscript --vanilla utdata/strand/04_figurer.R >> $LOG/steg4.log 2>&1
echo "$(date '+%F %T') stranden klar; tm22 steg 2 startar" >> $LOG/kedja.log
zsh utdata/runlm_forfining/tm22/tm22_steg2.sh >> /Volumes/2TB/Antigrvity/Runes/logs/tm22_steg2.log 2>&1
echo "$(date '+%F %T') tm22 steg 2 klart" >> $LOG/kedja.log
