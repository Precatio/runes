#!/bin/zsh
# Provet (analysplaner/2026-11-07-skala-av-provet.md) på de 95 filerna med granskade slingor, en process per fil.
cd /Volumes/2TB/Antigrvity/Runes/aagaard-research
while read series stem || [ -n "$series" ]; do
  [ -f utdata/skala_av/provet/$stem.json ] && continue
  PYTHONPATH=. .venv/bin/python -W ignore utdata/skala_av/provet.py $series $stem 2>&1 | tail -1
done < utdata/skala_av/provet_filer.txt
echo KLAR
