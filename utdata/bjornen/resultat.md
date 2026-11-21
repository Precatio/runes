# Björnen – resultat (fördjupning 4 i serien Nordiska väsen)

Enligt `analysplaner/2026-11-21-bjornen.md` (låst 1779c2e) med den frysta ordlistan `ordlista.csv` (sha256 6f79caee…).
Räknat 2026-11-21 med `analys.py`, `analys_t2.R` och SHM-sammanställningen `b4_shm.json`. Siffrorna finns i `matt.json` och
`t2.csv`.

## Kvalitetsgrinden (klarad)
- **Stickprovet:** 71 träffar, stratifierade efter term och textgrupp, med 92 % riktiga viktat (krav ≥ 90 %).
- **Fel:**
  - *björn* och *bersi* som kenningar för skepp (Skáldskaparmál);
  - *húnn* som spelpjäs i hnefatafl och som "mina söner" (Völundarkviða);
  - *björnuna* om kung Olav.
- **Utan test:** cellen björn i Eddan (6 av 8) ligger under 80 % och tas ur testerna. T1 använder den inte ändå.
- **Förvandlingsfönstren:** alla 5 står i fornaldarsagorna. Tre är björnfylgjor i drömmar och två är falska (*dreka hamr*,
  drakens ham, i Hrómundar saga). Bödvar Bjarkes *bjarnarhamrinn* i Hrólfs saga kraka fångas inte, eftersom ordet står
  inne i en sammansättning.

## B1 Björnen i litteraturen
- **Antal:** bara 137 träffar i hela korpusen.
- **Täthet per 10 000 ord:** eddadikterna 2,1, Skáldskaparmál 3,7, fornaldarsagornas prosa 1,1, islänningasagornas prosa
  0,75, Heimskringla 0,1.
- **Jämförelse:** björnen är alltså ett ovanligt ord jämfört med jättarna, som har 54 i eddadikterna.

## B2 Isbjörnarna
18 träffar på *hvítabjörn*:
- **Króka-Refs saga (6):** isbjörnar från Grönland, bland annat en *fulltíði* (fullvuxen) isbjörn som gåva till kung
  Harald och fem isbjörnar i en last.
- **Hrólfs saga Gautrekssonar (5)** och **Örvar-Odds saga (2):** isbjörnar som fylgjor och i drömmar.
- **Övriga:** Svarfdæla saga, Harðar saga, Þorsteins saga Síðu-Hallssonar och Ketils saga hængs har en var, och Völsunga
  saga och Atlamál har var sin i en dröm.

## B3 Björnnamnen på runstenarna
- **Antal:** 375 av 2 321 svenska vikingatida runstenar (**16 %**) har minst ett namn med *björn*. Vargnamn finns på 189
  (8 %).
- **De vanligaste:** Bjôrn 101, Þorbjôrn 50, Ásbjôrn 35, Vébjôrn 21, Geirbjôrn 15, Ígulbjôrn 15, Ketilbjôrn 15, Sigbjôrn
  14, Gunnbjôrn 11 och Styrbjôrn 9.
- **Per landskap (stenar med björnnamn):** Västmanland 21 %, Uppland 20 %, Gästrikland 19 %, Södermanland 16 %,
  Västergötland 11 %, Öland 10 %, Gotland 10 %, Östergötland 9 % och Småland 5 %.

## B4 Björnklorna i gravarna (Statens historiska museer)
- **Antal:** 84 poster med 323 föremål (björnklor, tåben och tänder). 68 kommer ur gravar, 9 från boplatser och 7 är okända.
- **Period:**
  - äldre järnålder till folkvandringstid 31;
  - bara "Järnålder" 16;
  - vendeltid 9;
  - yngre järnålder 7;
  - vikingatid 14 (helt eller delvis);
  - medeltid 5.
- **Landskap:** Uppland 33, Gotland 19, Östergötland 11, Södermanland 9 och Hälsingland 4.
- **Läsning:** björnskinnet i graven är framför allt en sed från tiden före vikingatiden.
- **Förbehåll:** det här är SHM:s samlingar, inte hela Sverige, och brända ben registreras ofta inte art för art. Antalet
  är ett minimum.

## Testerna (Holm över T1 och T2)
- **T1 förvandlingen: håller inte.**
  - Förvandlingssammanhang finns hos 12,2 % av björnarna i fornaldarsagorna (5 av 41, i 10 sagor) och 0 % i
    islänningasagorna (0 av 71).
  - Skillnaden är +12,2 procentenheter, med 95 % intervall 0,0–28,6, p 0,051.
  - Med fönstret ± 10 ord: 4,9 % mot 0.
  - Två av de fem fönstren var dessutom falska. Underlaget är för litet för att avgöra frågan.
- **T2 björnnamnen och skogen: håller formellt.**
  - Björnnamn finns på 11,5 % av stenarna i skogslandskapen (21 av 183) och 19,1 % i Mälarlandskapen (302 av 1 584).
  - Kvot 0,49 (0,30–0,81), p 0,006, Holm-justerat 0,011.
  - **Men känsligheten** visar att skillnaden bärs av Småland (5 %). Utan Småland blir kvoten 1,18 (0,60–2,32).
  - Läsning: björnnamnen är inte vanligare där björnarna levde, och de är vanligast i Mälardalen. Att de är *ovanligare*
    i skogsbygderna gäller bara Småland.

## Vad det betyder och inte betyder
- Björnen är sällsynt i litteraturen men vanlig i namnen. Var sjätte runsten bär ett björnnamn, dubbelt så ofta som ett
  vargnamn.
- I sagorna är björnen mest ett djur som jagas eller skänks bort. I fornaldarsagorna är den också en fylgja i drömmar, men
  underlaget räcker inte för att säga att det skiljer dem från islänningasagorna.
- Björnklorna i gravarna är mest äldre än runstenarna.
- Ett namn är inte en tro: namnleden ärvdes och kombinerades.
