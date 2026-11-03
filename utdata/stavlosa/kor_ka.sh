#!/bin/zsh
# Runindelningen längs slingan på vanliga stenar: de 37 KÅ-skanningarna (Södermanland, ritade slingor), vanligt läge och
# indelning längs slingan (--stavlost), en process per körning. Resultat i utdata/stavlosa/resultat/<stem>__{vanligt,stavlost}.json
cd /Volumes/2TB/Antigrvity/Runes/aagaard-research
for j in /Volumes/2TB/cache/runmodell/djup/sodermanland/*.json; do
  stem=$(basename $j .json)
  for mode in vanligt stavlost; do
    out=utdata/stavlosa/resultat/${stem}__${mode}.json
    [ -f $out ] && continue
    if [ $mode = stavlost ]; then flag=--stavlost; else flag=; fi
    PYTHONPATH=. .venv/bin/python -m utdata.stavlosa.matning sodermanland $stem $flag 2>&1 | tail -1
  done
done
