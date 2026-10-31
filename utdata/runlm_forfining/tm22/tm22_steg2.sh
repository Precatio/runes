#!/bin/zsh
# textmodel-22, steg 2: den på veck 0 valda kombinationen (tm22_sammanfattning.json → val) på veck 1–4 mot app_f1–4,
# två veck åt gången. Sedan tm22_jamfor.py --steg2.
cd "$(dirname "$0")/../../.."
export PYTHONPATH=.
F=utdata/runlm_forfining/tm22; L=/Volumes/2TB/Antigrvity/Runes/logs
APP=(--contexts --lam_class 0.2 --tolerance 0.02 --window -1 --char_fills 15 --context_cands --n_cands 100 --by_word
     --near 0.1 --near_km 10 --own_d --name_cands 40)
LIT=$(.venv/bin/python -c "import json; print(json.load(open('$F/tm22_sammanfattning.json'))['val']['lit'])")
LEX=$(.venv/bin/python -c "import json; print(json.load(open('$F/tm22_sammanfattning.json'))['val']['lex'])")
echo "$(date '+%F %T') steg 2: lit $LIT lex $LEX + Petersons namn"
run() { .venv/bin/python -m scripts.runlm_restore_test --folds $1 $APP --lit $LIT --lex $LEX --names_lit --out $F/vald_f$1.json > $L/tm22_vald_f$1.log 2>&1; echo "$(date '+%F %T') veck $1 klart"; }
run 1 & run 2 & wait
run 3 & run 4 & wait
.venv/bin/python $F/tm22_jamfor.py --steg2
echo "$(date '+%F %T') steg 2 klart"
