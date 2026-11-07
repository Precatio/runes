#!/bin/zsh
# Skala av vittringen på tio skanningar ur sex serier, en process per skanning (minnet). Logg i /Volumes/2TB/Antigrvity/Runes/logs/skala_av.log
cd /Volumes/2TB/Antigrvity/Runes/aagaard-research
for pair in "sodermanland So_206_thin03_closed_holes" "sodermanland So_113_1_4_thin_closed_holes" "sodermanland So_162_1_4_closed_holes" \
            "sodermanland So_128_1_4_thin_closed_holes" "asmund Gs_11_1_4_thin05" "asmund U_1144_thin05_closed_holes" \
            "medelpad M_3_Berga_thin02" "vastergotland Vg_103_thin03_closed" "gravmonument_og_sm Og_2_thin03" \
            "halsingland HS_14_1mm_complete_thin03"; do
  set -- ${=pair}
  [ -f utdata/skala_av/$2.json ] && continue
  PYTHONPATH=. .venv/bin/python -W ignore utdata/skala_av/prova.py $1 $2 2>&1 | tail -1
done
echo KLAR
