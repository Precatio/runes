# Analysplan: Attribueringsmodellen version 2 – nya belägg, ristarens bygd och ”samma hand”

Låst 2026-11-04, innan någon ny variant körs. SHA-256 i `analysplaner/2026-11-04-attribuering-v2.sha256`. Kod:
`src/attribution_features.py` (nya drag), `r/attribution_v2.R` (prövningen). Resultat i `utdata/attribuering_v2/`.

## Bakgrund
Provningen 2026-11-04 (`analysplaner/2026-11-04-attribuering-provad.md`, `utdata/attribuering_provad/resultat.md`) gav
utgångsläget för dagens modell (A): **71,2 %** rätt förstaval på 117 signerade stenar, grupperat per socken; **43 %**
som medel över ristarna; ECE 0,31. Den känner de stora ristarna och nästan inte de små. Viktor 2026-11-04: förbättra
attribueringen, ”prio 1 i appen”. Sett före låsningen: att Runor 2020 (RAÄ, `data/raa/runor_2020.json`) har korsform
enligt Lagers typologi (aspekt A–G, form) för 1 119 inskrifter, varav 520 med säker ristare (Öpir 73, Åsmund 48, Fot 47,
Balle 30 …); att runbiblioteket bara har två stenar (Åsmund). Inga modeller körda.

## Provbänken (samma för alla varianter)
Exakt som provningen: korpus 7b9061c9, de 18 ristarna med minst 8 säkra stenar, random forest 500 träd, seed 2026,
5 × 3 korsvalidering **grupperad per socken**, samma uppdelning för alla varianter. Facit: de 117 signerade stenarna.
Mått: (1) andel rätt förstaval, (2) medel per ristare (de 16 ristare som har signerade stenar), (3) log-förlust, (4)
ECE efter omkalibrering (potens vald på sockenhalva 1, mätt på halva 2, som i provningen). Sekundärt: de 380
attribuerade stenarna. Parvisa skillnader mot jämförelsemodellen med bootstrap över socknar (2 000).

## Vad som prövas, i den här ordningen (framåtval)
Varje steg jämförs med den bästa modellen hittills. Ett steg **behålls** om både (1) och (2) blir bättre (punktskattning
> 0) och log-förlusten inte blir sämre; **påvisad förbättring** om bootstrap-intervallet för (1) inte rör 0.

1. **Korsformen (ornamentik).** Ur Runor 2020: för varje kombination aspekt+form som finns på minst 10 runstenar ett
   ja/nej-drag (en sten med kors men utan typologi = okänt), plus ”korsform beskriven”. Stenar matchas på signum.
2. **Stavningsavtrycket.** För de 30 vanligaste normaliserade orden i Rundata (namn och skadade ord borträknade): vilken
   stavning stenen har (de högst fyra vanligaste stavningarna som egna nivåer, övriga ”annan”, ordet saknas = okänt).
   Plus skiljetecknens form i början och slutet av texten.
3. **Ristarens bygd och tid.** I stället för råa koordinater: för varje ristare en kärnskattning (Gauss, 15 km) av hans
   **träningsstenars** platser, och överlapp mellan stenens stildatering och hans. Sannolikheten blir
   P(ristare | sten) ∝ P_skog(ristare | drag utan koordinater) × bygd(ristare, plats)^w × tid(ristare, datering)^w,
   där w väljs på sockenhalva 1 (rutnät 0–2) och mäts på halva 2. Allt räknas inne i varje korsvalideringsdel.
4. **”Samma hand?”** – en annan sorts modell. För par av stenar med säker ristare (alla ristare med minst 2 säkra
   stenar, inte bara de 18) lär sig en skog om två stenar har samma ristare, ur hur lika de är i varje drag (samma
   dragsamling som bästa modellen efter steg 1–3) och avståndet mellan dem. En ny sten får för varje ristare medelvärdet
   av de tre högsta parsannolikheterna mot hans träningsstenar; omnormerat. Jämförs med bästa modellen på samma 117
   stenar (a) bland de 18 ristarna och (b) bland alla ristare i träningsdelen. Behålls om (a) uppfyller regeln ovan.
   Dessutom: kan den skilja ”okänd ristare” bättre? Utelämnad ristare i tur och ordning (som i provningen), andel
   flaggade vid samma andel flaggade kända stenar.
5. **Runformerna** prövas **inte** nu: runbiblioteket har två stenar. Villkor för att pröva: minst 5 skannade och
   uppmärkta stenar för minst 5 ristare.

## Vad som händer sedan
Den slutliga modellen = de behållna stegen. Den ersätter dagens i appen (r/attribution.R) med omkalibreringen inbyggd,
och provbänkens siffror blir de som appen visar. Behålls inget steg, står dagens modell kvar, omkalibrerad. Risk som
redovisas: samma 117 stenar används för alla jämförelser; skillnader på några procentenheter kan vara slump, därför
bootstrap och de attribuerade stenarna som andra mått.
