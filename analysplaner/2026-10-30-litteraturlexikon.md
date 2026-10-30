# Analysplan: litteraturlexikonet (textmodel-22-kandidat)

Skriven och låst 2026-10-30 innan några resultat tagits fram. Viktor: "jag vill att vi lär modellen all fornnordisk
litteratur också som vi har tillgänglig." Bakgrund: Rökstenen (utdata/Rok) och Maltstenen visar att modellen läser
formelorden och faller på varje ord som inte står på någon annan runsten; *alistiąsa* finns i ingen text, men delarna
*list* och *ása* finns i Eddan och sagorna.

## 1. Fråga
Blir modellen bättre på att läsa och fylla luckor om dess ordförråd utökas från Rundata + Eddan till all normaliserad
fornnordisk litteratur vi har, inlagd på samma sätt som Eddan i dag (ett ordförråd vars runstavningar härleds med
stavningsreglerna, med egen låg vikt) – utan att säkra fel ökar? Och hur många av Maltstenens och Rökstenens okända
runföljder når modellen då?

## 2. Källor (nivåer; varje nivå en egen ordlista med källa och antal)
- **N0 (finns):** Eddan (`src/runlm.edda_tokens`, utdata/Edda), vikt 0,03.
- **N1 normaliserad fornvästnordisk prosa:** Heimskringla (heimskringla.no, Linder & Haggson), fornaldarsagorna
  (Guðni Jónsson), samtidssagorna – `utdata/varlden/korpus/`, redan hämtade. Skaldeverserna ur dem.
- **N2 islänningasagorna** (sagadb.org) – nutida isländsk stavning. Tas med bara om stavningen kan föras tillbaka till
  fornvästnordisk form med en regeluppsättning som prövas på N1 (modernisera N1 med samma regler baklänges och mät
  hur stor del som kommer tillbaka rätt; gräns 95 % av ordformerna). Annars utesluts N2 och det redovisas.
- **N3 fornsvenska och forndanska lagar** (Fornsvenska textbanken, Skånelagen) – närmast runsvenskan i tid och språk.
  Tas med om de går att hämta; annars redovisas det.
- **N4 lexikon:** Zoëga (A Concise Dictionary of Old Icelandic, public domain) uppslagsord; Nordiskt runnamnslexikon
  (Peterson 2007, PDF) för namnleden i namnmodellen.
Alla ordformer normaliseras till den form Rundatas normalisering använder (samma `normtok`), med ǫ/ö, æ/ę och R/r
behandlade som i dag för Eddan. Inga egna ord läggs till för hand.

## 3. Mekanism (bestämd nu)
Som Eddan: en unigramlista per nivå med vikt λ_nivå, och stavningarna härledda med `Spelling.expand(edda=True)`-vägen.
Vikterna väljs på **veck 0 enbart** bland {0,01; 0,03; 0,1} för "litteratur" (N1–N3 som en lista) och {0,003; 0,01}
för "lexikon" (N4), var för sig; den kombination som ger störst netto utan fler säkra fel; vid lika netto den minsta.
Namnleden (N4 namn) läggs in i `NameModel` som ytterligare namnled med samma vikt som dagens.

## 4. Underlag och jämförelse
Maskeringsprovet med **appens inställning** (analysplan_tm21.md, filerna app_f0–4) på exakt samma luckor; jämförelse
parvis per lucka, bara runstenar. Dokumenterade luckor dok5 (361) som i tm19/tm20. Bas = app (textmodel-19 med appens
inställning). Rundatas normalisering av provstenarna används aldrig som källa (lexikonet byggs av litteraturen, inte
av Rundata; Rundata-ord som redan finns i modellen ändras inte).

## 5. Mått och gränser
- Håller om: fler vunna än förlorade ord i båda slagen (inne i ord, hela ord) över veck 1–4 med vikterna valda på
  veck 0, OCH fel bland svar ≥ 95 % (tm19:s kalibrering) inte fler, OCH dok5 inte sämre än 252 av 361 med inte fler
  ≥ 95 %-fel än 2.
- Beskrivande, oavsett utfall: Malt (`scripts/malt_decode.py`) och Rök (`utdata/Rok/jamfor.py`) läses om med lexikonet:
  antal okända runföljder före/efter, om Vífrøðr nås, ord samma som Rundata på Rök (före: 50 av 147), och vilka
  litteraturord modellen föreslår för Malts okända följder (titul, alisti, afr, utu) med sannolikhet.
- Känslighet: hur många **nya fel** lexikonet ger på korta luckor (1–2 runor), där kandidatexplosion är risken.

## 6. Vad som INTE får göras
Inga ordlistor ändras efter att veck 1–4 setts. Ingen vikt utanför punkt 3. Rundatas normalisering av Malt och Rök
ingår aldrig. Inga ord läggs till för att "nå" ett visst ord på Malt. Håller punkt 5 inte, förblir lexikonet av och
utfallet redovisas som negativt; de beskrivande Malt/Rök-måtten redovisas ändå.

## 7. Redovisning
`utdata/runlm_forfining/tm22_resultat.md`, METHODS.md 8.1 (versionsnot) bara om det införs, CHANGELOG, bristlistan,
news.json. Körs efter att tm21 är klar (ett tungt jobb i taget).
