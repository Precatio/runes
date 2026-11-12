# Analysplan A2, tillägg 1: inventeringsåret (D4)

Skrivet 2026-11-12 och låst samma dag. Tillägget gäller analysplanen
`2027-02-A2-registret-och-namnaren.md` (låst 2026-11-11, 4eef7f6, sha256 i
`2027-02-A2-registret-och-namnaren.sha256`). Planen själv ändras inte. Där planen och tillägget säger olika saker gäller
tillägget. Viktor beslutade 2026-11-12 att tillägget skulle skrivas (”kör 2”).

## Vad som har räknats före låsningen
Bara D4-tabellens täckning, med `scripts/a2_d4_tackning.py`. Utdata ligger i `utdata/registret/d4_tackning.json` och
`d4_val.json`. Inga stenantal, gravfält, bebyggelseenheter eller andra kovariater har lästs eller lagts mot
inventeringsåret. Runstenssocknarna används bara som flagga för täckningen, som planen kräver.

- **D4-fil:** `data/raa/d4_inventeringsar_socken.csv`, sha256 `d065053ef35df31af7c2aeb0837f181e7437695a6b1f70bf647734b808728497`. Fältdatumen
  hämtades ur Fornsök 2026-11-11 (fe90511).
- **Studieområdet:** 1 953 socknar, varav 591 runstenssocknar.

| Mått | Värde |
|---|---|
| Andel av urvalets poster med fältdatum | 91,9 % |
| Runstenssocknar med minst 5 fältdatum, alla typer | 536 av 591 (90,7 %) |
| Runstenssocknar med minst 5 fältdatum, bara gravtyperna | 31 av 591 (5,2 %) |
| Planens revisionsflagga = 1 | 98,7 % av socknarna, 100 % av runstenssocknarna |
| Huvudår efter 2003 | 143 socknar (40 runstenssocknar), median 2009, 2004–2018 |
| Osäkerhet hög eller saknas | 128 socknar (34 runstenssocknar) |
| Förstagångsår ≤ 1977 i beskrivningstexten | 49 % av socknarna (61 % av runstenssocknarna) |
| Huvudårets spridning inom län (sd) | 7,8 år; 4,4 år utan socknarna efter 2003 |

## Tre problem i planen som tillägget löser
1. **Planens D4-F klarar inte sina egna krav.** Planen tar medianåret ur fältdatumen för gravtyperna (Gravfält, Hög,
   Stensättning och Röse) och kräver minst 5 poster i 80 % av runstenssocknarna. Hämtningen tog ett slumpurval av alla
   lämningstyper, upp till 6 per socken. Det ger bara 5,2 %. D4-T (årtal ur fritexten) klarar inte heller kravet,
   eftersom bara 2,4 % av posterna har ett inventeringsårtal. Följt bokstavligt skulle planen falla tillbaka på D4-H,
   och då kan P1 inte prövas.
2. **Revisionsflaggan är nästan konstant.** Fältdatumet är det senaste fältbesöket, och nästan alla socknar har besökts
   igen 1974 eller senare. En förklaring som är 1 nästan överallt kan inte skattas och kan inte blandas om i proven.
3. **Fältdatum efter 2003.** Revideringsinventeringen avslutades 2002–2003 (RAÄ, HAIK 2020). Ett huvudår efter 2003 är
   en senare inventering hos länsstyrelsen, Skog och historia (1995–2007) eller ett uppdrag. Det är inte samma sak som
   den systematiska revideringen.

## Beslut
**1. D4-variant: D4-F med alla lämningstyper.**
- Socknens inventeringsår är D4-tabellens `huvudar`, alltså året med flest fältbesök inom ±1 år i ett slumpurval av
  upp till 6 oförändrade FMIS-poster av alla typer. Det ersätter planens median över gravtyperna.
- Kraven prövas på samma sätt men över alla typer: minst 70 % av posterna med år (91,9 %) och minst 80 % av
  runstenssocknarna med år ur minst 5 poster (90,7 %). Båda klaras, och varianten är vald.
- Skälet är att gravtyperna inte längre fångar förstagångsinventeringen när fältdatumet skrivs över vid varje besök. Ett
  slumpurval av alla typer beskriver när socknens register senast sattes i fält. Det är det mått planen redan anger
  (”när registrets beskrivning i socknen senast sattes i fält”).
- **Robusthet:** gravtypernas medianår i socknar med minst 3 gravtypsdatum (191 runstenssocknar). Det ingår bara i P1.

**2. Omgången: den senaste systematiska är huvudmåttet, och förstagångsåret är bara robusthet.**
- Huvudåret ligger i revideringsinventeringen för 83 % av socknarna. Det är den omgången som bestämmer vad registret
  innehåller i dag, och därmed vad Vitkis KMR-resultat bygger på. P1, P2, K-A, K-B, K-C och P5 använder därför
  huvudåret.
- **Förstagångsåret** (`text_tidigaste` ≤ 1977) finns för 49 % av socknarna och klarar inte kraven. Det används bara i en
  robusthetsrad i P1: bara socknar med textår, förstagångsåret som extra förklaring, och omblandning inom län. Raden får
  ingen Holm-korrigering och ingen egen gräns.
- **Hyenstrands landskapsdecennier** sammanfaller med landskapets fasta effekt. De är bara beskrivande, som planen
  redan säger.
- Arkivsöks serienamn (förstagångsbok och revideringsbok per socken) hämtas inte för A2.

**3. Fältdatum efter 2003.**
- Revisionsflaggan ersätts överallt i planen (P1, P2:s M2, K-A, K-B, K-C och P5) av **efter2003** (0/1: huvudåret är
  2004 eller senare).
- Inventeringsåret går in som **min(huvudår, 2003)** i decennier, linjärt. Lutningen skattas då bara inom den
  systematiska inventeringen 1938–2003, och socknarna efter 2003 får en egen nivå.
- I P1 blandas paret (inventeringsår, efter2003) om tillsammans inom län, som planen anger för paret år och
  revisionsflagga.
- **Robusthet:** (a) utan socknarna efter 2003; (b) med deras faktiska år linjärt och utan efter2003.
- P1:s gräns gäller lutningen per decennium. Den ändras inte.

**4. Osäkerhet hög eller saknas** (128 socknar, varav 34 runstenssocknar)
- **P1:** socknarna tas bort. Utfallet modelleras direkt mot året.
- **P2, P5, K-A, K-B och K-C:** socknarna stannar kvar, eftersom de tomma platserna inte får falla bort. De får länets
  medianår (bland låg och medel) och en indikator **d4_osaker** = 1.
- **Robusthet:** utan socknarna.

**5. Styrkan, skriven nu.** Huvudåret sprider sig bara 4,4 år (sd) inom län före 2004. Ett decennium är alltså mer än
två standardavvikelser inom länet. Utfallet ”syns inte” betyder därför ”syns inte inom länen”. Rapporten ska säga
att skillnader mellan länens inventeringsepoker fångas av landskapets fasta effekt och inte prövas av P1.

## Ändras inte
Frågorna, proven, gränserna, Holm-familjerna, platserna i P2, indexet E, nämnaren, tolkningen och redovisningen. Ordningen
D4-F → D4-T → D4-H gäller som förut, med D4-F enligt beslut 1.
