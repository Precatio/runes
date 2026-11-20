#!/bin/zsh
# textmodel-23 (analysplaner/2026-11-20-petersons-namn-i-textmodellen.md, sha 321c3a6d): kontroll på veck 0 utan namnen
# (samma val som app_f0, annars stopp), sedan --names_lit på veck 0–4, två körningar åt gången. Sist tm23_jamfor.py.
cd "$(dirname "$0")/../../.."
export PYTHONPATH=.
F=utdata/runlm_forfining/tm23; L=/Volumes/2TB/Antigrvity/Runes/logs
APP=(--contexts --lam_class 0.2 --tolerance 0.02 --window -1 --char_fills 15 --context_cands --n_cands 100 --by_word
     --near 0.1 --near_km 10 --own_d --name_cands 40)
run() {  # $1 = veck, $2 = namn på utfilen, rest = extra flaggor
  local k=$1 pre=$2; shift 2
  .venv/bin/python -m scripts.runlm_restore_test --folds $k $APP "$@" --out $F/${pre}_f$k.json > $L/tm23_${pre}_f$k.log 2>&1
  [ -s $F/${pre}_f$k.json ] && echo "$(date '+%F %T') klart $pre veck $k" || echo "$(date '+%F %T') $pre veck $k SAKNAS – se $L/tm23_${pre}_f$k.log"
}
echo "$(date '+%F %T') start"
run 0 kontroll & run 0 namn --names_lit & wait
.venv/bin/python $F/tm23_jamfor.py --kontroll || { echo "KONTROLLEN AVVIKER – stopp"; exit 1; }
run 1 namn --names_lit & run 2 namn --names_lit & wait
run 3 namn --names_lit & run 4 namn --names_lit & wait
.venv/bin/python $F/tm23_jamfor.py --prov
echo "$(date '+%F %T') klart"
