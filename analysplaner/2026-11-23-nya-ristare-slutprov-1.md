# Analysplan: slutprov 1 för nya ristare – grupper ur den inlärda parmodellen mot facits provdel

Skriven och låst 2026-11-23, innan provdelen har öppnats. Programmet följer `analysplaner/2026-11-23-nya-ristare-program.md`
(sha f5ce4fe7). Det här är första användningen av provdelen.

## Metoden (fastställd på utvecklingsdelen, ändras inte)
- **Beläggen:** `utdata/nya_ristare/belagg.py`, med följande parmått (stenpar inom 30 km):
  - överskottslikheten i textdragen (samlad, ortografisk och för språkdragen);
  - stilgrupp;
  - korsets form enligt Runor 2020;
  - SRI:s ornament- och runformsord;
  - kortkvist;
  - bergart;
  - de kategoriska språkdragen, lika eller olika (skiljetecken, stavningen av *eftir* och *þenna*, *ai*, *auk* med flera);
  - gemensamma namn;
  - avståndet.
- **Parmodellen M1:** `utdata/nya_ristare/parmodell.py`.
  - Gradient boosting tränad på par av säkra stenar i Rundata, med ristarna delade i fem vikter.
  - Inga par inom en facitgrupp och inga par som rör provdelens stenar ingår i träningen.
  - Sannolikheterna finns i `data/cache/hander/parsannolikhet_M1.npy`.
- **Grupperna:** `utdata/nya_ristare/gruppering.py`, genomsnittlig länkning på M1:s sannolikheter med diametern ≤ 30 km,
  avskuren vid **τ = 0,8**. Gränsen valdes på utvecklingsdelen: den högsta precisionen på namngivna par (0,77) som samtidigt
  ger en tydlig täckning av utvecklingsdelens facitpar (34 % mot 3 % för grannarna).
- **Utfallet på utvecklingsdelen** (ingen slutsats av det):

  | Grupper | Antal | I samma grupp | Grannarna | p |
  |---|---|---|---|---|
  | Alla | 43 | 0,37 | 0,06 | 0,0002 |
  | Onämnda | 16 | 0,33 | 0,09 | 0,01 |

## Provet (provdelen P, en gång)
- **Måttet:** `utdata/nya_ristare/slutprov.py P`. Per facitgrupp i provdelen (par inom 30 km) räknas andelen par i samma
  grupp. Den jämförs med grannkontrollen:
  - stenar på samma avstånd från a (± 25 %, minst ± 1 km, högst 30 km);
  - utanför facitgruppen;
  - andelen av dem i a:s grupp;
  - medel över paren.
- **S1 (huvudprov, alla grupper):** ensidigt Wilcoxon-test över grupperna. **Håller** om p < 0,05 och medelandelen i samma
  grupp är större än kontrollens.
- **S2 (bara grupper med onämnda händer):** samma prov. Håller på samma sätt om det finns minst 5 grupper med skillnad,
  annars är det obestämt.
- **Loggning:** utfallet skrivs i `utdata/nya_ristare/provdelen_logg.md`.

## Beslut (bestämt nu)
- **S1 håller:** metoden räknas som prövad.
  - Grupperna med minst tre stenar, vid τ = 0,8 och på hela korpusen, får visas i appen som **förslag: stenar som kan ha
    samma hand**, med precisionen redovisad.
  - Grupper utan någon sten med säker ristare märks **möjlig onämnd hand**.
  - Inget publiceras som en ny ristare förrän litteraturen har kontrollerats grupp för grupp.
- **S1 håller inte:** grupperna visas inte. Metoden redovisas, och nästa steg blir nya belägg (3D, ornamentik), inte en
  ny gräns.

## Vad som inte skrivs
- Facit är runologernas bedömningar, inte säkra fakta.
- Rundatas tillskrivningar bygger delvis på samma slags drag (Axelson 1993), så träningen är delvis cirkulär. Provdelens
  onämnda grupper (S2) är det renaste provet.
