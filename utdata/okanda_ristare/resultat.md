# Resultat: de möjliga okända ristarna mot bergart, storlek och namn (2026-10-29)

Plan: `analysplaner/2026-10-29-okanda-ristare-oberoende.md` (621ae55, SHA-256 kontrollerad före körning). Kod
`analys.py`, siffror `okanda_ristare.json`, läslista för runologen `lasning.md`. 9 999 slumpmängder per grupp ur
trakten (30 km), med samma fördelning på stilgrupp.

## Positiv kontroll: kända ristare i Uppland och Södermanland (26 ristare med minst 5 stenar)
Testet ser en ristare genom alla tre egenskaperna:
- **Bergart:** 92 % av paren delar bergart mot 65 % i trakten (median), Fisher p 2·10⁻⁹ (24 ristare).
- **Storlek:** höjdskillnad 0,40 mot 0,64 (log), Fisher p 3·10⁻⁵ (22 ristare).
- **Namn:** 8,1 % av paren delar ett personnamn mot 2,6 %, Fisher p 9·10⁻¹⁹; 12 av 26 ristare var för sig.

## Utfall för de fem kandidatgrupperna (Holm över H1–H3)
- **H1 Bergart – håller.** Fisher p 0,0008, Holm 0,0023. Bärs av Konungsund (92 % mot 77 %, p 0,0001) och Kölaby
  (56 % mot 40 %, p 0,008); Vetlanda, Leksberg och Husaby skiljer sig inte från trakten.
- **H2 Storlek – faller.** Fisher p 0,32 (bara tre grupper har höjder; ingen skiljer sig).
- **H3 Namn – håller.** Fisher p 0,017, Holm 0,035. Bärs av Kölaby (7,7 % mot 1,2 % av paren, p 0,001: Ásbjôrn tre
  gånger, Þórðr, Geiri, Gufi) och Leksberg (Þórir fyra gånger, p 0,051); Konungsund, Vetlanda och Husaby delar inte
  namn mer än trakten.

**Tolkningen enligt planen:** H3 håller, alltså *familjens beställningar möjliga*.

## Läsning
Den positiva kontrollen visar något som planen inte förutsåg: kända ristares stenar delar personnamn betydligt oftare
än trakten. En ristare gjorde ofta flera stenar åt samma släkt. Delade namn skiljer därför inte en ristare från en
familjs beställningar – båda ger samma mönster – och planens regel ("H3 håller = familj möjlig") är för grov. Det som
går att säga:
- **Konungsundsgruppen (Ög, 28 stenar)** beter sig som en känd ristares stenar i det enda oberoende drag som skiljer
  den från trakten: bergarten (nästan bara granit, oftare än traktens stenar), utan att stenarna hör till en släkt.
  Det är den starkaste kandidaten.
- **Kölabygruppen (Vg, 13)** delar både bergart och namn – en ristare som arbetade åt en släkt, eller släktens egen
  sed; går inte att skilja.
- **Leksberg (Vg, 6)** delar namn (Þórir) men inte bergart – lika gärna en släkts stenar.
- **Vetlanda (Sm, 14) och Husaby (Vg, 6)** delar ingenting utöver det de grupperats på; lokal skrivsed är lika troligt
  som en ristare.

Ingen grupp är bevisad som en okänd ristare. Konungsund är värd en runologs granskning först (läslistan: Brate, SRI
II), sedan Kölaby (Jungner & Svärdström, SRI V).

## Avvikelser
- Planen nämner `data.py` och `analys.py`; allt ligger i `analys.py`.
- Kontrollen: 26 ristare hade minst 5 stenar med koordinater (24 med bergart, 22 med höjder).
