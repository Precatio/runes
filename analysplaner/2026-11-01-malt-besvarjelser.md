# Analysplan: Maltstenen mot besvärjelser – formen och tolkningarnas ord

Skriven och låst 2026-11-01, innan något av måtten nedan har räknats. Viktor 2026-11-01: "jag tror inte vi ska försöka
förstå den som något logiskt budskap likt de svenska stenarna. Besvärjelse eller magi uttrycker sig förmodligen
annorlunda", "kan du hitta fler danska besvärjelser från tidig vikingatid", "lås planen och kör". Uppföljning till
`analysplaner/2026-11-01-malt-runmasteri.md` (88a546f). Ingen läsning av Malt läggs till.

## Vad som är känt före låsningen
- Antal texter med minst 24 runor enligt urvalsregeln nedan (utan dværg/værki): vikingatida besvärjelser 14, medeltida 77;
  vikingatida runstenar 1 814.
- Vi har läst de tidiga danska texterna Ribeskallen (DR EM85;151B), Hedebypinnen (DR EM85;371B), Ribepinnen med runrad
  (DR EM85;371A), Hemdruppinnen (DR EM85;350), DR Schl3, DR DKSJy76 och DR EM85;463B.
- En oplanerad jämförelse: med `runlm.similarity` liknar Malts grupp *tuRraki* Ribeskallens *tuirk* ("dvärg") mest av
  Malts grupper (0,67). Den räknas inte som resultat; del B prövar frågan från början.
- Eddan: *Billingr* står i Völuspás dvärgatal (str. 13) och i Skáldskaparmál (*Billings burar full*).

## Del A – liknar Malts form besvärjelser eller minnesstenar?
**Urval (regel):** besvärjelser = inskrifter som inte är runstenar och där Rundatas objekt innehåller *amulett* eller
*bleck*, eller anteckningen innehåller *besvärj*, *magisk*, *trollformel* eller *amulett*, eller normaliseringen
innehåller *þurs*, *galdr*, *agla*, *sárþvara*/*sarþvara*, *gyrill*, *þistil*, *dværg*, *dverg* eller ordet *værki*.
Vikingatid (`runlm.viking`) och medeltid för sig. Minnesstenar = vikingatida runstenar. Alla med minst 24 runor, Malt
utesluten. Runföljden som i `utdata/Malt/runrad_dubblering.stretches`; Malt som `utdata/Malt/upprepning.malt_stream`
med modellens bästa val.
**Avsnitt:** varje inskrift delas i på varandra följande avsnitt om 24 runor inom obrutna följder (resten kastas), så att
längden inte styr. Malt ger fem avsnitt.
**Mått per avsnitt:** (1) bitar per runa i en trigrammodell tränad på vikingatida runstenar (`runlm_sprakprov.train`;
för runstenarna själva femfaldig korsvalidering per inskrift); (2) koincidensindex; (3) andelen vokaler (a e i o u y æ ø);
(4) andelen trerunsföljder som återkommer inom avsnittet; (5) om samma runa står tre gånger i rad; (6) skiljetecken per
runa; (7) andelen grupper om en eller två runor bland grupperna helt inom avsnittet.
**Modell:** logistisk regression på standardiserade mått, minnesstenar mot vikingatida besvärjelser (balanserade vikter);
femfaldig korsvalidering grupperad per inskrift ger AUC. Sedan anpassad på allt och tillämpad på Malts avsnitt.
**Gräns:** om AUC ≥ 0,75 sägs Malts form **likna besvärjelser mer än minnesstenar** när medelsannolikheten för besvärjelse
över Malts fem avsnitt är över 0,5, och **minnesstenar** när den är under 0,5. Om AUC < 0,75 skiljer formen inte
genrerna, och ingen slutsats dras. Samma sak med medeltida besvärjelser (beskrivande), utan mått (1) (känslighet), och
med bara danska runstenar som minnesstenar (känslighet). Beskrivande: avståndet i måtten mellan Malts avsnitt och
Hedebypinnens och Ribeskallens.

## Del B – liknar Malts grupper de ord tolkningarna läser in?
**Målord** (ur tolkningarna i `tolkningar.json`): *dvärg* (Heltoft *tuRraki*), *Billing* (Thuesen, Heltoft, Fridell,
*bilikikR*), *Tyr* (Thuesen, Fridell) och *ut* (Thuesen, Heltoft, *utu*). **Former:** alla normaliserade ordformer i
Rundata (alla perioder) som börjar på *dværg*/*dverg*, *billing*/*billi*, är *týr*/*tyr*, eller är *út*/*ut*.
**Mått:** S = den högsta `runlm.similarity` mellan någon av textens skiljeteckengrupper och någon av målordets former.
**Jämförelse:** samma S för de 163 vikingatida runstenarna med 91–204 runor från upprepningsplanen. Malts S är
**ovanligt hög** för ett målord om den ligger över 95:e percentilen. **Kontroll:** samma prov för 50 slumpvis valda
normaliserade ord ur Rundata med 3–8 bokstäver (frö 2026), för att se hur ofta ett godtyckligt ord når samma nivå. Når
mer än 10 av 50 kontrollord gränsen, skiljer måttet inte, och inget målord sägs ha stöd i ristningen.

## Vad som inte får göras
Urvalsregeln, avsnittslängden, måtten, målorden och gränserna ändras inte efter körningen. Inga läsningar läggs till.

## Redovisning
`utdata/Malt/besvarjelser.py`, `besvarjelser.json`, `besvarjelser_resultat.md`.
