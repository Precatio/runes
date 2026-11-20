# Analysplan: Rundatas ifyllningar som sannolikhetsmodellen starkt ifrågasätter

Skriven och låst 2026-11-20, innan listan nedan har tagits fram eller lästs. Viktor 2026-11-20: "gör dessa: De
ifyllningar i Rundata som modellen starkt ifrågasätter … varje fall går att pröva mot läsningen i Sveriges
runinskrifter."

## Känt före låsningen
- Benchmarken dok5 (utdata/runlm_forfining/dok5_f0–f4.json, textmodel-19, appens inställning): utgivarnas ifyllda luckor
  maskeras och fylls av en modell som inte har lärt sig av stenen (fem delar). Runstenar: 361 luckor med ord; i
  intervallet 0,8–0,95 sade modellen 0,89 och hade rätt mot Rundata i 0,89 av 46; vid 0,95 och över sade den 0,99 och hade
  rätt i 0,976 av 166. Ungefär nio luckor på runstenar är alltså säkra men säger något annat än Rundata. Vilka de är har
  inte lästs.
- Blindprovet 2026-10-17: alla 13 påståenden ≥ 95 % höll.
- textmodel-value (2026-10-28): förslaget att lista ifyllningar modellen starkt ifrågasätter gjordes aldrig.

## Listan
Alla rader i dok5_f0–f4 (runstenar och andra stenar, redovisade var för sig) där modellens kalibrerade sannolikhet p ≥ 0,8
och modellens ord inte är Rundatas ord (word_ok = false). Ingen annan gräns, inga undantag. För varje fall: signum, de
bevarade runorna, Rundatas ifyllning och ord, modellens ifyllning, ord och p, och modellens tre närmaste alternativ.

## Prövningen mot källorna (för varje fall, innan modellen bedöms)
1. **Sveriges runinskrifter:** artikeln om stenen (SRI:s text, src/sri_text.py / downloads/sri_artiklar). Vad säger
   utgivaren om de runor som Rundata fyller i? Kodas i en av fyra klasser, med kort citat och tryckt sida:
   - **sett:** runorna eller delar av dem syns eller sågs på stenen;
   - **äldre avbildning:** ifyllt efter en äldre avbildning eller läsning (till exempel Bautil, Peringskiöld, Dybeck);
   - **utgivarens förslag:** ifyllt utan stöd på stenen, som förslag eller med förbehåll ("torde", "förmodligen",
     "kompletteras");
   - **framgår inte:** artikeln säger inget om just dessa runor.
2. **Runor 2020:** samma ställe i Riksantikvarieämbetets Runor (data/raa/runor_2020.json): samma ifyllning, en annan eller
   ingen.
3. **Modellens alternativ:** står modellens ord någon annanstans i korpusen i samma ställning (ordklass, formel), och är
   det språkligt möjligt med de bevarade runorna? Bara beskrivet, med exempel.
Kodningen görs av en läsare som ser SRI-texten och Rundatas ifyllning men inte modellens förslag (punkt 1), därefter
punkt 2 och 3. Läsaren är en körning av Anthropics språkmodell Claude med fast instruktion; varje kodning har citatet
med, och Viktor kan kontrollera det.

## Vad listan får sägas visa
- Ett fall där SRI anger **utgivarens förslag** eller **framgår inte** och modellens alternativ är språkligt möjligt är
  ett **ställe värt att pröva igen**, inte ett fel i Rundata.
- Ett fall där SRI anger **sett** räknas som modellens fel och redovisas som sådant.
- Antalen redovisas per klass. Inget prov av skillnader görs; antalet fall är för litet.

## Vad som inte skrivs
Modellen läser inte stenen. Att den är säker betyder att texten i sammanhanget pekar åt ett annat ord, inte att runorna
på stenen gör det.

## Utdata
`utdata/ifragasatta_ifyllningar/lista.py` → `lista.json`, `kodning.json` och `resultat.md`.
