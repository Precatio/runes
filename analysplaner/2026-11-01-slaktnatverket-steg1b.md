# Analysplan: släktnätverket, steg 1b – blint handprov av länkningen med avståndsband

Skriven och låst 2026-11-01, innan några par har dragits eller bedömts. Viktor 2026-11-01 valde "Blint handprov" (med Viktor
som bedömare) sedan Petersons förteckning visat sig bygga på Williams (110 av 118 svenska släktpar finns redan där).

## Bakgrund
Steg 1 (`analysplaner/2026-11-01-slaktnatverket-steg1.md`, `utdata/slakt/steg1_resultat.md`): M1 föll på Jarlabanke. I
känsligheten gav nollmodellen inom landskapet med samma avståndsband (här **M2**) 59 säkra länkar, 39,6 % täckning och
94,7 % träffsäkerhet mot Williams 1990 och 6 av 10 Jarlabankepar. M2 valdes efter att ha sett Williams lista och kan därför
inte prövas mot den. Före låsningen är bara antalen kända: 5 av M2:s 59 säkra länkar ligger utanför Williams grupper; 312 av
kandidatlänkarna är varken säkra i M2 eller hos Williams; Williams har 270 säkra par mellan runstenar i materialet. Vilka
par det är har inte setts.

## M2
Som M1 i steg 1 men med nollmodellen inom landskapet (`level="province"`): kandidatregel, styrka, avståndsband (A ≤ 2 km,
B ≤ 10 km, C > 10 km), q per band, säker länk = q < 0,1 och ingen motsägelse. Kod: `utdata/slakt/steg1.py`, `model(ALL,
"province", (2, 10))`.

## Paren (dras en gång med fröet 2026, `utdata/slakt/handprov.py`)
- **Nya:** alla M2-länkar utanför Williams grupper (5).
- **Kända (kontroll):** 5 slumpvis valda av Williams säkra par mellan runstenar.
- **Namnpar (kontroll):** 15 slumpvis valda av kandidatlänkarna som varken är säkra i M2 eller står hos Williams – stenar
  som delar namn men som modellen inte länkar.
De 25 paren blandas i slumpvis ordning. Nyckeln (vilket par som är vilket) sparas utanför projektmappen
(`/Volumes/2TB/tmp/slakt_handprov_nyckel.json`); dess SHA-256 checkas in tillsammans med formuläret innan bedömningen.

## Bedömningen
Viktor bedömer varje par utan att veta vilken grupp det tillhör. Han ser för varje sten landskap, socken, Rundatas
normaliserade text och engelska översättning och stilgruppens datering, samt avståndet mellan stenarna, men inte signum.
Han får inte slå upp stenarna under bedömningen. Svar: **J** (samma släkt), **?** (kan inte avgöra) eller **N** (inte
samma släkt), gärna med en kort kommentar.

## Mått och gränser
p_ny, p_känd och p_namn = andelen J i respektive grupp. **M2 håller** om
1. p_ny ≥ 0,5 (minst 3 av 5),
2. J är vanligare bland de nya än bland namnparen: Fishers exakta test, ensidigt, p < 0,05, och
3. p_känd ≥ 0,7 (minst 4 av 5); annars är provet **inte avgörande** (bedömningen känner inte igen kända släktlänkar ur
   texten), och M2 införs inte.
Känslighet: samma prov med J och ? sammanslagna.

## Om M2 håller
Länkningen i appen byts mot M2 (`scripts/link_entities.py`, METHODS 1r, nyhet i `web/content/news.json`), öppet märkt som
vald efter att ha sett Williams lista och prövad blint på de nya länkarna. Steg 2 (släktträd och arvsfrågor) bygger på M2.

## Vad som inte får göras
Paren dras inte om, gränserna ändras inte och inga bedömningar ändras efter att nyckeln öppnats.

## Redovisning
`utdata/slakt/handprov.py`, formuläret `utdata/slakt/handprov_formular.md`, resultat `utdata/slakt/handprov_resultat.md`.
