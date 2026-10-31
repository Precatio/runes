#!/bin/zsh
# textmodel-22 (analysplaner/2026-10-30-litteraturlexikon.md), steg 1: veck 0 – kontroll (vikt 0 = app_f0 exakt),
# litteraturvikter {0,01; 0,03; 0,1}, lexikonvikter {0,003; 0,01}, Petersons namn i alla kandidater (+ en körning med
# bara namnen, beskrivande). Två körningar åt gången (modellen med listorna tar 3,2 GB; 16 GB-regeln).
cd "$(dirname "$0")/../../.."  # projektmappen
export PYTHONPATH=.
F=utdata/runlm_forfining/tm22; L=/Volumes/2TB/Antigrvity/Runes/logs
APP=(--contexts --lam_class 0.2 --tolerance 0.02 --window -1 --char_fills 15 --context_cands --n_cands 100 --by_word
     --near 0.1 --near_km 10 --own_d --name_cands 40)
run1() {  # $1 = namn, rest = extra flaggor; veck 0
  local pre=$1; shift
  .venv/bin/python -m scripts.runlm_restore_test --folds 0 $APP "$@" --out $F/${pre}_f0.json > $L/tm22_${pre}_f0.log 2>&1
  [ -s $F/${pre}_f0.json ] && echo "$(date '+%F %T') klart $pre" || echo "$(date '+%F %T') $pre SAKNAS – se $L/tm22_${pre}_f0.log"
}
echo "$(date '+%F %T') start steg 1 (veck 0)"
run1 kontroll & run1 lit001 --lit 0.01 --names_lit & wait
.venv/bin/python $F/tm22_jamfor.py --kontroll || { echo "KONTROLLEN AVVIKER – stopp"; exit 1; }
run1 lit003 --lit 0.03 --names_lit & run1 lit01 --lit 0.1 --names_lit & wait
run1 lex0003 --lex 0.003 --names_lit & run1 lex001 --lex 0.01 --names_lit & wait
run1 namn --names_lit & wait
.venv/bin/python $F/tm22_jamfor.py --steg1
echo "$(date '+%F %T') steg 1 klart"
