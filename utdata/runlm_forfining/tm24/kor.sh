#!/bin/zsh
# textmodel-24 (analysplaner/2026-11-20-grannstenarnas-namn-narhet.md, sha fe998288). Steg 1: kontroll (förvalet, ska ge
# samma val som app_f0) och fem kombinationer på veck 0; val. Steg 2: valet på veck 1–4. Två körningar åt gången.
cd "$(dirname "$0")/../../.."
export PYTHONPATH=.
F=utdata/runlm_forfining/tm24; L=/Volumes/2TB/Antigrvity/Runes/logs
APP=(--contexts --lam_class 0.2 --tolerance 0.02 --window -1 --char_fills 15 --context_cands --n_cands 100 --by_word
     --near_km 10 --own_d --name_cands 40)
run() {  # $1 veck, $2 namn, $3 skala, $4 lam
  .venv/bin/python -m scripts.runlm_restore_test --folds $1 $APP --near $4 --near_scale $3 --out $F/$2_f$1.json > $L/tm24_$2_f$1.log 2>&1
  [ -s $F/$2_f$1.json ] && echo "$(date '+%F %T') klart $2 veck $1" || echo "$(date '+%F %T') $2 veck $1 SAKNAS"
}
echo "$(date '+%F %T') steg 1"
run 0 kontroll 5 0.1 & run 0 s5_l02 5 0.2 & wait
.venv/bin/python $F/jamfor.py --kontroll || { echo "KONTROLLEN AVVIKER – stopp"; exit 1; }
run 0 s1_l01 1 0.1 & run 0 s1_l02 1 0.2 & wait
run 0 s025_l01 0.25 0.1 & run 0 s025_l02 0.25 0.2 & wait
.venv/bin/python $F/jamfor.py --steg1 || { echo "ingen kombination med positivt netto – stopp (negativt)"; exit 0; }
VAL=$(.venv/bin/python -c "import json; v=json.load(open('$F/sammanfattning.json'))['val']; print(v['namn'], v['s'], v['lam'])")
set -- ${=VAL}
echo "$(date '+%F %T') steg 2 med $1 (skala $2, lam $3)"
run 1 vald $2 $3 & run 2 vald $2 $3 & wait
run 3 vald $2 $3 & run 4 vald $2 $3 & wait
.venv/bin/python $F/jamfor.py --steg2
echo "$(date '+%F %T') klart"
