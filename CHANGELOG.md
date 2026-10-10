# Ändringslogg

Versionsnumren följer [semantisk versionering](https://semver.org/lang/sv/). Mätmetodens version (`groove-N`)
anges separat, eftersom den avgör vilka mätningar som är jämförbara (METHODS.md, avsnitt 1).

## [Ej släppt]

### Mätmetod `groove-5`
- Den automatiska spåranalysen mäter bara spår som känns igen som runor; slinglinjer, ornamentik och möjliga
  sprickor sorteras bort med skäl (METHODS.md 1c, steg 5).
- Rättat: slingband som stängdes av runstavar fylldes och räknades som en enda för bred yta.
- Stenens medelvärden med runan som enhet (ICC); riktvärden 10 runor för att beskriva en sten och 20 för att
  jämföra stenar (`scripts/rune_sample_size.py`).

### Rapporter
- Elva publiceringsformer för stenrapporten: tidskriftsartikel, uppsats, avhandlingskapitel, runologisk utgåva,
  konferensabstract, poster, blogginlägg, pressmeddelande, antikvarisk rapport och dataartikel (METHODS.md 14e).

### Validering av huggspårsanalysen
- Facit-läge i 3D-vyn: alla spår mäts, inget förmärks, forskaren märker runor; `scripts/evaluate_rune_detection.py`
  mäter runigenkänningens precision och träffsäkerhet mot facit.
- `scripts/groove_robustness.py`: samma skanning mätt med ändrat rutnät, lutad normal, annan känslighet och
  förenklad skanning (METHODS.md 1e).
- Antalet igenkända runor jämfört med Rundatas translitterering (METHODS.md 1c).

### Statistik
- Attribueringsmodellen i R korsvalideras också grupperat per socken och härad (rätt ristare 72 % slumpvis,
  68 % på ny socken, 57 % i nytt härad), visat på sidan Statistik (R) och i fynden.

### Protokoll och dokumentation
- Vitki-protokollet för automatisk huggspårsmätning (`PROTOCOL.md`, `src/protocol.py`), utkast: fasta parametrar,
  krav på skanningen, arbetsgång, minsta redovisning; varje automatisk analys kontrolleras mot protokollet.
- Webbsidan Metodik och beräkningar (Dokumentation → Metodik) visar METHODS.md, protokollet och alla moduler,
  skript och R-moduler direkt från koden (`/api/docs`).

### Transparens
- Förteckning över metodens kända brister som visas under varje analyssida, står i varje rapport och sparas i
  proveniensen för varje mätning (METHODS.md 18).

## [2.0.0] – 2026-10-04
- Första versionen under namnet Vitki: 3D-huggspårsanalys, Rundata, ortografisk stilometri, syntes och
  attribuering, mätkorpus, statistik i R, forskningsluckor och rapporter. Mätmetoden har sedan ändrats
  (`groove-2` till `groove-4`, se METHODS.md 1).
