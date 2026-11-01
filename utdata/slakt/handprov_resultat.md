# Resultat: släktnätverket, steg 1b – blint handprov (2026-11-01)

Plan: `analysplaner/2026-11-01-slaktnatverket-steg1b.md` (SHA-256 f3ba7e78…, låst innan paren drogs). Bedömare: Viktor Kvant, i webbsidan https://claude.ai/artifact/2fWEqUNXQjv5unG8FqjbNj utan signum. Svaren frystes i versionshanteringen (dee7598) innan nyckeln öppnades; nyckelns SHA-256 (471e769c3c45acfd…) stämmer med den som checkades in före bedömningen (b5fa5f0).

## Utfall: inte avgörande – appen behåller M0

- De nya länkarna: 5 av 5 bedömda som samma släkt (J).
- De kända länkarna (Williams 1990): 3 av 5 J, övriga ?. Planen krävde minst 4 av 5.
- Namnparen: 3 av 15 J, 6 ?, 6 N.
- Fishers exakta test, J bland de nya mot bland namnparen, ensidigt: p = 0,0036.
- Villkoren: minst hälften av de nya J – ja; Fisher p < 0,05 – ja; minst 4 av 5 kända J – nej. Enligt planen är provet därför inte avgörande, och M2 införs inte.
- Känslighet (J och ? sammanslagna): nya 5 av 5, kända 5 av 5, namnpar 9 av 15, Fisher p = 0,13.

I klartext: alla fem länkar som modellen ensam hittade bedömdes blint som samma släkt, mot var femte av de namnpar den inte länkar. Men bedömaren kände bara säkert igen tre av fem kända släktlänkar ur texterna, och då säger planen att provet inte kan avgöra.

## Varför de kända länkarna fick ? (ur bedömarens kommentarer)

- U 136 och U 147: Eftersom stenarna står i Täby rör det sig mycket sannolikt om den kända Jarlabankeätten. Som vi såg i det förra exempel (Par 8) hade Östen (nämns på Sten 1) en son vid namn Ingefast (nämns på Sten 2). Det är därför historiskt högst troligt att det är samma släkt.Inga gemensamma namn: På Sten 1 är det Estrid (Æstriðr) som reser stenen efter sin make Östen (Øystæin). På Sten 2 är det Jorunn ([I]orun
- Ög 81 och Ög 84: Namnet Torkel (Þorkell) finns på båda stenarna. På Sten 1 agerar han dock uttryckligen som runristare ("Þorkell ræist runaR"), det vill säga hantverkaren som högg stenen åt Torgärd, utan att någon familjerelation till den omskrivna släkten (Gulle och hans fem söner) anges. På Sten 2 är Torkel istället den som låter resa stenen tillsammans med Helga ("Þorkell ok Hælga, þau ræistu stæin"). Inskrifte

Det ena paret (Ög 81 och Ög 84) står i Williams grupp 81+82+83+84+165, men det gemensamma namnet, Þorkell, är ristare på den ena stenen; sambandet hos Williams vilar alltså inte bara på släktskap i texterna. Det andra (U 136 och U 147, Jarlabankeätten) kräver kunskap om släkten utöver de två texterna. Kontrollvillkoret mätte därför också vad Williams lista bygger på, inte bara bedömaren.

## Namnpar som bedömdes som samma släkt (modellen länkar dem inte)

- U 315 och U 871: å Sten 1 reser paret Gunnar (Gunnarr) och Holmdis (Holmdis) minnesmärket efter sin son. På Sten 2 agerar exakt samma namnkombination, Gunnar och Holmdis, som medresare till stenen.
- U 643 och U 678: Den äldre generationen (Sten 2): Bröderna Andvett (Andvettr) och Gulleiv (GullæifR) är, tillsammans med tre andra bröder, uppresare av stenen till minne av sin far Tord (Þorð). Den yngre generationen (Sten 1): Här agerar en Gulleiv (GullæifR) och Kåre (Karr) resare efter sin far Andvett Röde (Andvet
- U 808 och U Fv1973;146: Utöver namnmönstret stämmer kronologin perfekt. Sten 1 (när Gisl är i livet) är i den äldre stilen Pr3, och Sten 2 (när Gisl är död och sönerna vuxna) är i den yngre stilen Pr4. Avståndet på 21,1 km i Uppland knyter ihop det hela geografiskt.

De är kandidater till länkar som modellen missar, inte fynd; de kan prövas i nästa steg.

## Avvikelser från planen
- Planen anger 270 säkra par hos Williams; det är 270 rader och 266 unika par (stenar som står i två grupper). Kontrollparen drogs bland de 266.
- Bedömningen gjordes i en webbsida i stället för i markdownformuläret; paren, ordningen och texterna är desamma (`handprov_sida.py` läser formuläret).
- I övrigt inga.
