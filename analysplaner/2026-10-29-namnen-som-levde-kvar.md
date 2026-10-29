# Analysplan: Namnen som levde kvar – runstenarnas namn i de medeltida breven

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-namnen-som-levde-kvar.sha256`.
Kod `utdata/namnarv/` (`hamta.py` hämtar, `lexikon.csv` klassar namnen, `analys.py` prövar), resultat `resultat.md` där.

## Bakgrund
Skriften och lagen gick över till latinska bokstäver när kyrkan tog över, men namnen bar fornnordiskan vidare
(Viktor 2026-10-29). Frågan: hur länge, hur mycket och i vilka familjer? Källa: Svenskt diplomatariums huvudkartotek
(SDHK), de svenskspråkiga breven i Språkbankens Korp (`SDHK-SVENSKA`, cirka 970 000 ord, mest 1350–1450, med datum
och utfärdandeort). Sett före låsningen: frekvenslistan över ord med versal i hela samlingen och fördelningen av ord
per halvsekel; inga namn har klassats, inga andelar räknats över tid, kön, generation eller plats.

## Material
- **Namnbelägg:** förnamn i breven = ord med versal som står i namnlexikonet nedan (inte i början av en mening om
  ordet också är ett vanligt ord). Ett belägg per förekomst; breven är klustret.
- **Fader–barn-par:** ett förnamn följt direkt av ett patronymikon (namn + -son/-sson/-sun/-dotter/-dottir/-dotir i
  någon stavning); fadern = patronymikonets förled. Kön: -dotter-formerna och lexikonets kön.
- **Tid:** brevets år (`text_datefrom`); perioder 1250–1349, 1350–1399, 1400–1449, 1450–.
- **Plats:** utfärdandeorten (`text_place`) läggs till landskap för orter med minst 20 namnbelägg; övriga utan
  landskap.

## Namnlexikonet (byggs före räkningen, låses i `lexikon.csv` med SHA-256)
Alla ord med versal som förekommer minst 5 gånger i samlingen klassas för hand till: **förnamn** (med normalform,
t.ex. Niclis/Nicles/Niels/Nisse → Nils, och kön), **ej namn** (ord, ortnamn, latin). Varje förnamn får **ursprung**:
- **nordiskt** – fornnordiskt/germanskt ursprung i Norden (Sven, Björn, Torsten, Ingeborg, Karl, Erik …);
- **kristet/utländskt** – bibliska namn, helgonnamn, latinska, grekiska och kontinentala namn (Johannes/Jöns, Nils,
  Lars, Peder, Anders, Katarina, Margareta, Magnus …).
Magnus klassas som utländskt (latin) men redovisas också för sig. Namn vars ursprung är osäkert märks och räknas bort.
Varje nordiskt namn får också **på runsten**: om namnet finns som personnamn på svenska vikingatida runstenar
(korpus 3f58e9339191761e, entitetsmodellens namnnyckel). **Kontroll:** ursprunget prövas mot ordboken Sveriges
medeltida personnamn (ISOF, häfte 1–17, A–J) för alla klassade namn A–J; andelen överensstämmande redovisas, och
klassningen ändras där SMP säger annat innan lexikonet låses.

## Test (Holm över H1–H4, α = 0,05)
- **H1 Tiden:** andelen nordiska förnamn sjunker med året. Logistisk regression nordiskt ~ år (per 50 år), med
  brevet som kluster (klusterrobusta medelfel). Förväntat: oddskvot under 1.
- **H2 Generationen:** i fader–barn-paren har barnet mer sällan ett nordiskt namn än fadern. McNemar på de oeniga
  paren (barn nordiskt/fader inte mot tvärtom). Förväntat: barnen mindre nordiska.
- **H3 Vilka namn överlevde:** bland de 100 vanligaste mansnamnen på vikingatida runstenar: finns namnet i breven?
  Jämförelse namn med gudanamn som förled (Tor-, Ås-, Frö-/Frey-, Ing-, Gud-) mot övriga, Fishers exakta test,
  tvåsidigt.
- **H4 Kvinnor och män:** andelen nordiska namn bland kvinnor mot män (logistisk, år som kontroll, brevet som
  kluster). Tvåsidigt.
**Håller:** Holm-p < 0,05 och samma riktning med p < 0,05 i båda halvorna (breven delade efter jämnt/udda
brevnummer; H3 har inga halvor och redovisas utan). **Antydan:** Holm-p < 0,05 utan halvorna, eller okorrigerat p < 0,05.

## Beskrivning (prövas inte)
Andelen nordiska namn per halvsekel och per landskap; de vanligaste namnen per period; vilka runstensnamn som
lever kvar och vilka som försvann; andelen nordiska namn bland fäderna jämfört med barnen per period.

## Robusthet
Bara säkra namn (de 150 vanligaste förnamnen); Magnus räknat som nordiskt; utan brev utfärdade i Stockholm (stadens
tyska inslag).

## Förbehåll
Breven gäller mest frälse, präster och bönder med jord – inte alla. Svenskspråkiga brev blir vanliga först efter
1350; latinska brev ingår inte. Ett namn i ett brev kan räknas flera gånger (samma person); brevet som kluster tar
hand om en del. Patronymikon är inte alltid faderns namn (ibland redan ett släktnamn). Utfärdandeorten är inte alltid
där människorna bodde.
