# Analysplan: tre nya källor kring runstenarna

Skriven och låst 2026-10-21 innan något av måtten i punkterna A–C har räknats (METHODS.md 1x, ANALYSPLAN.md). Hash i
`analysis_plan_kallor.sha256`. Källorna är RuneS-DB (Göttingenakademien, runesdb.de, CC BY-SA 4.0), Språkbankens
Karp (Söderwalls ordbok med supplement, Schlyters ordbok och Fornsvensk lexikalisk databas) och Kiels runprojekts
material om den äldre futharken, som ingår i RuneS-DB (Kielservern avvisar krypterade anslutningar 2026-10-21).
K-samsök prövades också: Statens historiska museers 246 543 vikingatida föremål saknar fyndplats i K-samsöks index
och museets egen webbplats går inte att nå härifrån; den källan redovisas bara som en notis.

Känt innan låsningen (bara antal och en pilot): RuneS-DB har 223 inskrifter med yngre futharken i Skåne och Blekinge,
72 med graftyper, 53 av dem med DR-signum i vår Rundata och 42 i stavningsmodellens index; 27 inskrifter med äldre
futharken, med 7 (Bl 2 Gummarp), 19 (Bl 3 Stentoften), 7 (Bl 4 Istaby) och 12 (Bl 6 Björketorp) tolkningar;
ordböckerna har 22 572 + 19 172 + 10 067 + 41 958 uppslag; en pilot utan lemmatisering matchade 13 % av runsvenskans
ordformer. Inga teststorheter är räknade.

## A. Skåne: formar den som stavar lika sina runor lika?

* **Fråga.** Hänger runformerna (RuneS-DB:s graftyper) ihop med stavningen (Vitkis ortografiska jämförelse) på
  Skånes runstenar? Ja = Mantelkorrelationen (Spearman) mellan runformsavstånd och stavningsavstånd är positiv med
  p < 0,05 (ensidigt, 10 000 permutationer av stenarna) och förblir det när båda avstånden först rensats från det
  geografiska avståndet (partiell Mantel, residualer mot log-avståndet i km). Nej = inte det.
* **Stenar.** De inskrifter med yngre futharken i RuneS-DB:s landskap Skåne som har graftyper, ett DR-signum i
  Rundata 3.1 och finns i stavningsmodellens index (`api.routers.orthography.model`); 42 enligt inventeringen.
* **Runformsavstånd.** Per sten och translittereringstecken: andelen positioner med varje graftyp. *Varierande tecken*
  = tecken som i urvalet har minst två graftyper med minst fem positioner var. Avståndet mellan två stenar är
  medelvärdet över de varierande tecken som finns på båda av totalvariationsavståndet ½ Σ|p_i − p_j|; par med färre
  än tre gemensamma varierande tecken saknar värde och lämnas utanför korrelationen (permutationerna flyttar
  saknade värden med stenarna).
* **Stavningsavstånd.** 1 − cosinus mellan stavningsmodellens vektorer (`vectorize`, namn borttagna, som i modellen).
* **Beskrivande.** Antal graftyper per tecken i Skåne och vilka tecken som varierar mest.
* **Inte.** Inga egna läsningar; inga val av stenar för hand; inga ändringar av tecknen eller måtten efter resultat.

## B. Fornsvenskan: hur många av runstenarnas ord finns i de medeltida ordböckerna?

* **Fråga.** Hur stor andel av runstenarnas ord (lemman, namn uteslutna) finns som uppslagsord i de fornsvenska
  ordböckerna, och är de ord som förekommer en enda gång i korpusen (hapax) belagda mer sällan än de vanliga? Ja =
  andelen belagda hapax-lemman är lägre än andelen bland lemman med minst fem förekomster (tvåproportionstest,
  ensidigt p < 0,05). Skillnaden anger hur många av engångsorden som saknar stöd utanför runstenarna.
* **Ord.** Svenska vikingatida runstenar (`research_gaps.is_runestone`), orden ur Rundatas normalisering
  (`runlm.sections`/`norm_words`/`normtok`), namn uteslutna (citerade i Rundata), lemma ur textmodellens
  `Model.lemma` byggd på alla vikingatida inskrifter (`textmodel.MODEL`).
* **Ordböcker.** Uppslagsorden (`baseform`) i Söderwall, Söderwalls supplement, Schlyter och Fornsvensk lexikalisk
  databas, hämtade 2026-10-21 (`/Volumes/2TB/cache/kallor/karp/`), gemener.
* **Matchning.** Ett lemma räknas som belagt om någon av dess varianter är ett uppslagsord. Varianterna bildas av
  lemmat och av ordformen med en fast regellista: ʀ→r; ð→þ; þ→þ/th/dh; æi, ei→e; au→ö; øy, ey→ö; ø→ö; æ→ä/e; ǫ→o;
  längdtecken bort; slut-r i maskulina nominativer→-er eller bort; ia→iä; slutet -i/-a/-u får bytas mot -a/-e/-i/-u
  (ordbokens böjningsform). Andelarna är nedre gränser, eftersom reglerna inte fångar allt; en lista över de vanligaste
  obelagda lemmana visas så att läsaren kan bedöma. Inga ord rättas för hand efter att andelarna setts.
* **Frekvensklasser.** Hapax (1 förekomst), 2–4, minst 5.

## C. Blekinge: vad är forskarna överens om på de fyra stenarna?

* **Fråga.** Hur mycket skiljer sig tolkningarna av Gummarp (Bl 2), Stentoften (Bl 3), Istaby (Bl 4) och Björketorp
  (Bl 6) åt, och är förbannelsen den stabila delen? Ja = på Bl 6 och Bl 3 hör orden för död och förstörelse
  (engelska översättningens *death/die/dead* och *destroy/break*) till det stabila innehållet (finns i minst 80 % av
  tolkningarna), medan orden för förutsägelse/skada i Bl 6:s inledning (*prophecy/prophesy/harm*) inte gör det.
* **Data.** RuneS-DB:s tolkningssidor (`/find/N/interpretations`, hämtade 2026-10-21): per tolkning
  translitterering, normaliserad läsning, tysk och engelsk översättning, litteratur. Tjurkö-brakteaterna (IK 184,
  IK 185) bara beskrivande.
* **Mått.** (1) Antal tolkningar och årtal. (2) Per rad i inskriften: *täckning* = andelen tolkningar som
  translittererar raden, *läsningsenighet* = andelen som har majoritetens translitterering av raden (klamrar,
  diakritika och z/ʀ-skillnaden borttagna). (3) *Översättningsenighet* = medelvärdet av parvis likhet
  (`difflib.SequenceMatcher`) mellan de engelska översättningarna, och per sten de innehållsord (engelska, stoppord
  bort, stam utan böjning) som finns i minst 80 % respektive färre än 50 % av tolkningarna.
* **Inte.** Ingen egen läsning eller tolkning; tolkningarna citeras som data om oenighet (`data-before-interpretation`).

## Redovisning
`utdata/kallor/resultat.md`, resultatfiler per del (`skane_runformer.json`, `fornsvenska.json`, `blekinge.json`),
ett artikelutkast (opublicerat) om vad källorna tillför, och en notis i METHODS.md. Ett nej redovisas lika tydligt.
