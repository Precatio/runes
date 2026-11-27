#!/bin/zsh
# textmodel-24 (analysplaner/2026-11-27-bojningsmodellen-tm24.md, sha 1656a0bf): provet på veck 1–4 med inställningen som
# valdes på veck 0 (val_val.json, som måste vara committad först), två körningar åt gången. Sist tm24_jamfor.py --prov.
cd "$(dirname "$0")/../../.."
export PYTHONPATH=.
F=utdata/runlm_forfining/tm24; L=/Volumes/2TB/Antigrvity/Runes/logs
mkdir -p $L
[ -s $F/val_val.json ] || { echo "val_val.json saknas – kör tm24_kor_val.sh först"; exit 1; }
git ls-files --error-unmatch $F/val_val.json > /dev/null 2>&1 && git diff --quiet HEAD -- $F/val_val.json ||
  { echo "val_val.json är inte committad (planen: valet committas innan veck 1–4 körs) – stopp"; exit 1; }
SET=($(.venv/bin/python -c "
import json, sys
v = json.load(open('$F/val_val.json'))['vald']
if not v:
    sys.exit(1)
print(v['lam'], v['min'], v['mu'])")) || { echo "ingen inställning vald på veck 0 (negativt) – stopp"; exit 1; }
echo "$(date '+%F %T') start: λ_böj ${SET[1]}, tröskel ${SET[2]}, μ ${SET[3]}"
APP=(--contexts --lam_class 0.2 --tolerance 0.02 --window -1 --char_fills 15 --context_cands --n_cands 100 --by_word
     --near 0.1 --near_km 10 --own_d --name_cands 40)
run() {  # $1 = veck
  local n=prov_f$1
  .venv/bin/python -m scripts.runlm_restore_test --folds $1 $APP --infl ${SET[1]} --infl_min ${SET[2]} --infl_mu ${SET[3]} \
    --out $F/$n.json > $L/tm24_$n.log 2>&1
  [ -s $F/$n.json ] && echo "$(date '+%F %T') klart $n" || echo "$(date '+%F %T') $n SAKNAS – se $L/tm24_$n.log"
}
run 1 & run 2 & wait
run 3 & run 4 & wait
.venv/bin/python $F/tm24_jamfor.py --prov
echo "$(date '+%F %T') klart"
