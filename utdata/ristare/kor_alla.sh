#!/bin/bash
# Ristarprofiler för alla ristare med minst sex säkra stenar (r/carver_profile.R), plus Balle utan Röd-Balles två.
cd /Volumes/2TB/Antigrvity/Runes/aagaard-research
C=data/cache/r/corpus/7b9061c9a1c12c73; D=utdata/upptackt_v5/drag.csv; O=utdata/ristare/profiler
mkdir -p $O
Rscript -e 'd<-read.csv("'$C'/corpus.csv",stringsAsFactors=F); x<-table(d$carver[!is.na(d$carver)&d$carver!=""]); writeLines(names(sort(x[x>=6],decreasing=TRUE)))' > $O/ristare.txt
while IFS= read -r who; do
  f=$(echo "$who" | tr ' ' '_' | tr -d '-')
  line=$(Rscript r/carver_profile.R $C $D "$who" "$O/$f.json" 2>&1 | head -1)
  n=$(echo "$line" | sed -E 's/.*signaturdrag ([0-9]+).*/\1/')
  if [ "$(python3 -c "import json;print(json.load(open('$O/$f.json'))['profil'])")" = "signerade" ] && [ "$n" -lt 8 ]; then
    line="$(MODE="alla säkra" Rscript r/carver_profile.R $C $D "$who" "$O/$f.json" 2>&1 | head -1) (signerade gav bara $n drag)"
  fi
  echo "$line"
done < $O/ristare.txt
SKIP="Vs 15;Vs 24" Rscript r/carver_profile.R $C $D Balle $O/Balle__utan_rodballe.json 2>&1 | head -1
