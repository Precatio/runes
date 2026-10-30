#!/bin/zsh
# textmodel-21 (analysplan_tm21.md): A = appens inställning på maskeringsprovets luckor (app_f0–4), B = samma + trigram
# (app3_f0–4). Fem veck parallellt per steg, ett steg i taget (minnet). Sist jämförelsen (tm21_jamfor.py).
cd "$(dirname "$0")/../.."  # projektmappen
export PYTHONPATH=.
F=utdata/runlm_forfining; L=/Volumes/2TB/Antigrvity/Runes/logs
APP=(--contexts --lam_class 0.2 --tolerance 0.02 --window -1 --char_fills 15 --context_cands --n_cands 100 --by_word
     --near 0.1 --near_km 10 --own_d --name_cands 40)
run_step() {  # $1 = prefix, rest = extra flags
  local pre=$1; shift
  echo "$(date '+%F %T') start $pre"
  for k in 0 1 2 3 4; do
    .venv/bin/python -m scripts.runlm_restore_test --folds $k $APP "$@" --out $F/${pre}_f$k.json > $L/tm21_${pre}_f$k.log 2>&1 &
  done
  wait
  for k in 0 1 2 3 4; do [ -s $F/${pre}_f$k.json ] || { echo "$pre veck $k saknas – se $L/tm21_${pre}_f$k.log"; exit 1; }; done
  echo "$(date '+%F %T') klart $pre"
}
run_step app
.venv/bin/python $F/tm21_jamfor.py
run_step app3 --trigram
.venv/bin/python $F/tm21_jamfor.py
echo "$(date '+%F %T') tm21 klart"
