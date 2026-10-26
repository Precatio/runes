#!/bin/zsh
# Kör matning.py för varje fil i filer.txt, en i taget (minnet). Argument skickas vidare (--stavlost osv).
cd "$(dirname $0)/../.."
while read series stem; do
  .venv/bin/python -W ignore -m utdata.stavlosa.matning $series $stem "$@" 2>&1 | grep -v Warning | tail -1
done < utdata/stavlosa/filer.txt
