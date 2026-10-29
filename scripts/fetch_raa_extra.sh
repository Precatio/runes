#!/bin/zsh
# Hämtar fler lämningstyper ur KMR, en typ per fil, efter att KMR-runristningshämtningen är klar.
cd "$(dirname "$0")/.."

for t in "bytomt/gårdstomt" "boplats" "husgrund, förhistorisk/medeltida" "fossil åker" "vägmärke" "samlingsplats" \
         "brunn/kallkälla" "källa med tradition" "offerplats" "offerkast" "stensättning" "röse" "stenkrets/stenrad" \
         "minnesmärke" "begravningsplats"; do
  f="data/raa/lamningar_extra/$(echo "$t" | tr '/ ,' '___').csv"
  [ -s "$f" ] && continue
  RAA_REMAINS="$f" .venv/bin/python scripts/fetch_raa_remains.py "$t" 2>&1 | tail -2
done
echo KLART
