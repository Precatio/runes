#!/bin/zsh
# Kön efter textmodel-23: omräkningen av dok5 (plan b18f81cd). textmodel-24 (plan fe998288) avbruten 2026-11-20 före start
# på Viktors beslut: förväntad vinst 0–10 namnluckor av ~225, inte värt två dygn.
cd "$(dirname "$0")/../.."
export PYTHONPATH=.
L=/Volumes/2TB/Antigrvity/Runes/logs
while pgrep -f tm23_kor.sh > /dev/null || pgrep -f "runlm_restore_test.*tm23/" > /dev/null; do /bin/sleep 300; done
echo "$(date '+%F %T') tm23 klar; omräkning dok5"
.venv/bin/python utdata/runlm_forfining/matt_2026_11_20/omrakna.py > $L/omrakna_dok5.log 2>&1 && echo "$(date '+%F %T') omräkning klar" || echo "omräkning MISSLYCKADES – se $L/omrakna_dok5.log"
