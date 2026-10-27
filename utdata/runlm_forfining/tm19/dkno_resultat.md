# Luckor i texten på danska och norska inskrifter: inte godkänt (2026-10-27)

Plan: analysplan_dkno.md (låst, SHA-256 e5e9f7c3…). Inventering: klass3_dkno_f0–f4.json → klass3_dkno.json,
159 luckor (85 återställda, 74 öppna; efter ifyllnad 81 och 68). Prövning: dkno_eval.py → dkno_resultat.json.

| | Återställda | Samma ord som Rundata | Kalibrerat ≥ 0,8: antal | … samma ord |
|---|---|---|---|---|
| Sverige (klass3_alla) | 673 | 75 % | 414 | 95 % |
| Danmark (DR) | 63 | 51 % | 24 | 79 % |
| Norge (N) | 18 | 17 % | 6 | 17 % |
| DR + N | 81 | 43 % | 30 | 67 % |

Krav 1 (≥ 75 % rätt bland kalibrerat ≥ 0,8, minst 10 luckor): 67 % – **inte klarat**. Krav 2 (högst 10 procentenheter
under Sverige): 43 % mot 75 % – **inte klarat**. Enligt planen förblir listan svensk.

Modellen har lärt sig språket främst av svenska inskrifter (östnordiska). På danska inskrifter träffar den hälften av
de återställda orden, på norska (västnordiska) nästan inga, och listkalibreringen, anpassad på svenska luckor, ger för
höga procent där. Att välja ut Danmark i efterhand vore en ny fråga och kräver en ny låst plan; Danmark ensamt klarar
dessutom inte krav 2 (51 % mot 75 %). En väg framåt är en modell med egna danska och västnordiska skikt och en
kalibrering per land.
