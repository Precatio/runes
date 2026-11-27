#!/bin/zsh
# textmodel-24 (analysplaner/2026-11-27-bojningsmodellen-tm24.md, sha 1656a0bf): valet på veck 0. Böjningslagret med
# appens flaggor (som tm23), rutnätet λ_böj ∈ {0,003, 0,01, 0,03} × tröskel ∈ {0,02, 0,05} × μ ∈ {0, 0,5}, tolv körningar,
# två åt gången (16 GB). Sist tm24_jamfor.py --val, som väljer mot app_f0 och skriver val_val.json (committas före veck 1–4).
cd "$(dirname "$0")/../../.."
export PYTHONPATH=.
F=utdata/runlm_forfining/tm24; L=/Volumes/2TB/Antigrvity/Runes/logs
mkdir -p $L
APP=(--contexts --lam_class 0.2 --tolerance 0.02 --window -1 --char_fills 15 --context_cands --n_cands 100 --by_word
     --near 0.1 --near_km 10 --own_d --name_cands 40)
run() {  # $1 = λ_böj, $2 = tröskel, $3 = μ
  local n=val_$1_$2_$3_f0
  if [ -s $F/$n.json ]; then echo "$(date '+%F %T') $n finns redan"; return; fi
  .venv/bin/python -m scripts.runlm_restore_test --folds 0 $APP --infl $1 --infl_min $2 --infl_mu $3 --out $F/$n.json > $L/tm24_$n.log 2>&1
  [ -s $F/$n.json ] && echo "$(date '+%F %T') klart $n" || echo "$(date '+%F %T') $n SAKNAS – se $L/tm24_$n.log"
}
echo "$(date '+%F %T') start"
i=0
for lam in 0.003 0.01 0.03; do
  for t in 0.02 0.05; do
    for mu in 0 0.5; do
      run $lam $t $mu &
      i=$((i + 1))
      (( i % 2 == 0 )) && wait
    done
  done
done
wait
.venv/bin/python $F/tm24_jamfor.py --val
echo "$(date '+%F %T') klart"
