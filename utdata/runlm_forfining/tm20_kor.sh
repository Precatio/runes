#!/bin/zsh
# Variantkvoten (analysplan_tm20.md): kontrollen med kvoten 0, sedan veck 0 för kvoterna 10, 20 och 40 (urvalsvecket).
# En process åt gången (minnet). Veck 1–4 körs först när kvoten är vald (tm20_veck.sh).
cd "$(dirname "$0")/../.."  # projektmappen
export PYTHONPATH=.
F=utdata/runlm_forfining; L=/Volumes/2TB/Antigrvity/Runes/logs
BASE=(--own_d --name_cands 40 --tolerance 0.02)
.venv/bin/python -m scripts.runlm_restore_test --folds 0 $BASE --var_cands 0 --out $F/vq0_f0.json > $L/tm20_vq0_f0.log 2>&1
.venv/bin/python - <<'EOF'
import json
a = json.load(open("utdata/runlm_forfining/tol02_f0.json"))["rows"]
b = json.load(open("utdata/runlm_forfining/vq0_f0.json"))["rows"]
same = len(a) == len(b) and all(x == y for x, y in zip(a, b))
print("kontroll: kvoten 0 ger samma rader som textmodel-19:", same, len(a), len(b))
if not same:
    raise SystemExit(1)
EOF
[ $? -eq 0 ] || { echo "kontrollen föll – avbryter"; exit 1; }
for q in 10 20 40; do
  .venv/bin/python -m scripts.runlm_restore_test --folds 0 $BASE --var_cands $q --out $F/vq${q}_f0.json > $L/tm20_vq${q}_f0.log 2>&1
  .venv/bin/python $F/tm19_ab.py vq$q --folds 0 --base tol02 | head -6
done
