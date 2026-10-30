# Resultat: de fornnordiska namnen som inte stod på runstenarna (2026-10-30)

Plan: `analysplaner/2026-10-30-namnen-utanfor-runstenarna.md` (låst 21994df, SHA-256 3a8edd…). Kod: `hamta.py`,
`hamta_en.py`, `hamta_wp.py` (hämtning), `ursprung.py` (fornnordiskt eller inte, med handgranskning), `analys.py`
(grupper och prövningar). Tabeller: `ursprung.csv` (alla 1 166 namn med etymologirad), `grupper.csv` (de fornnordiska
namnen med grupp, runform och bärare 1999/2020), `resultat.json`.

## P1 – beskrivning
193 fornnordiska namn bärs av minst 10 svenskar 1999 eller 2020, av sammanlagt 1 063 838 personer 2020.
- **runsten:** 107 namn, 710,112 bärare 2020 (1999: 1,126,231) – två tredjedelar av bärarna, men en minskning med en tredjedel på 21 år.
- **annan runtext:** 15 namn (57,891), bl.a. Vidar (medeltida N 121), Tor (namnlistan N B599), Ylva, Erling.
- **myt:** 26 namn (93,494; 1999: 76,822), bl.a. Idun 43 → 1 313, Freja 562 → 7 085, Embla 130 → 1 112, Saga 2 353 → 11 851.
- **övrigt:** 45 namn (202,341), bl.a. Leif, Gustav, Arvid, Hjalmar, Loke, Meja och kortformer av runnamn (Olle, Kalle).

## Prövningarna (Holm över P2–P4)
- **P2 – håller.** Namn utanför runtexterna (myt + övrigt, 71) har vuxit mer än runstensnamnen (107): Mann–Whitney ensidigt p 0.0083, Holm 0.017.
- **P3 – håller.** Mytnamnen (26) har vuxit mer än övriga fornnordiska namn (167): p 0.0028, Holm 0.008.
- **P4 – faller.** Kvinno- och mansnamn växer lika: p 0.24.

## Läsning
Runstenarnas namn lever av arv och åldras nu med sina bärare; de namn som växer kommer ur sagorna och myterna.
Vikingatidens människor bar gudarna i namnen (Torsten, Ingrid) men aldrig gudens eget namn: ingen säker person på en
svensk runsten heter Þórr, Freyja eller Óðinn (U 440 kan läsas Þórðr, Þórr eller Þórn). I dag heter barn Tor, Freja,
Idun och Loke.

## Avvikelser (alla före resultaten)
- Svenska Wiktionary saknade etymologi för de flesta namn; engelska Wiktionary och svenska Wikipedias namnartiklar
  lades till som källor (`hamta_en.py`, `hamta_wp.py`).
- Myt-markeringen läser också Wikipedias namnartikel (Wiktionary nämner inte mytologin för Embla, Vidar, Loke).
- Ursprung granskat för hand (`GRANSKNING` i `ursprung.py`): Johan, Kristina, Fredrik, Albrekt, Märta, Elin och
  Majvor är inte fornnordiska trots fornsvenskt led; tio Wikipedia-träffar är falska; tretton blandade är fornnordiska.
- Runformer granskade för hand (`SAME_AS_STONE` i `analys.py`): 28 nutida namn är samma namn som på en svensk runsten
  i senare ljudform (Kjell ← Ketill, Sixten ← Sigsteinn, Love ← Lófi …); kortformer och smeknamn (Olle, Kalle, Uffe)
  räknas inte. Falska runträffar: Tor ← Tárr, Tyr ← Týr (runnamnet i N B604); namnfragment (Þor-) räknas inte.
- Tyr räknas mekaniskt som "övrigt" (ingen källa nämner guden i den hämtade texten).

## Förbehåll
- Wiktionary och Wikipedia täcker inte alla namn; 291 namn har okänt ursprung och är inte med.
- Etymologierna är källornas, inte våra.
- Tillväxten mäts på tilltalsnamn med minst 10 bärare 1999 och 2020.
