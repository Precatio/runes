# Analysplan: slutprov 2 för nya ristare – samma metod mot ett nytt facit ur litteraturen

Skriven och låst 2026-11-23, innan facit 2 har jämförts med grupperna med provmåttet nedan. Programmet:
`analysplaner/2026-11-23-nya-ristare-program.md` (sha f5ce4fe7). Slutprov 1: `…-slutprov-1.md` (sha 081bf667), höll.

## Känt före låsningen
- Läsningen av litteraturen är gjord (arbetsflöde 2026-11-23).
  - Underlaget var 2 490 ställen i Fornvännen, Futhark och åtta avhandlingar där en ristare eller "samma hand" nämns nära ett
    signum.
  - Läsningen gav 1 556 uttalanden, varav 153 om samma hand och 52 om olika händer.
  - Läsarna var 28 instanser av Anthropics språkmodell Claude (Claude Opus), och 5 kontrolläsare tog ett blint stickprov på
    250 ställen. Av dem var 220 (88 %) identiska.
  - På parnivå för "samma hand" hittade läsarna 21 av kontrollens 22 par, men tog dessutom ut många fler, främst ur långa
    listor.
- **Därför granskas** varje uttalande om samma hand, olika händer och tillskrivning av två oberoende, skeptiska granskare.
  Det gäller 303 uttalanden. Ett uttalande ingår bara om båda bekräftar det, och bara med de signum som båda stöder.
- **Sett före låsningen**, och utan provmåttet: en beskrivande räkning på den ogranskade läsningen. 72 av 228 grupper
  hade minst ett par eller en gemensam ristare i litteraturen.

## Facit 2
- **Paren:** par av stenar som en författare själv säger är gjorda av samma hand, med styrkan säker eller trolig och
  bekräftat av båda granskarna.
- **Undantagna par:**
  - par som redan finns i facit 1;
  - par där båda stenarna hör till samma grupp i facit 1.
- **Grupperna:** de undantagna paren bildar sammanhängande grupper.
- **Avgränsningen:** bara svenska stenar som finns i Rundata och bland de 2 314 stenarna i `utdata/nya_ristare/belagg.py`.

## Provet (oförändrad metod)
- **Grupperna som prövas:** τ = 0,8 och samma 228 grupper som i appen (`utdata/nya_ristare/grupper.json`;
  `data/cache/hander/sammanslagningar_M1.npy`).
- **Måttet:** som i slutprov 1. Per facit-2-grupp (par inom 30 km) räknas andelen par i samma grupp. Den jämförs med
  grannkontrollen: stenar på samma avstånd (± 25 %, minst ± 1 km, högst 30 km), utanför facitgruppen. Ensidigt
  Wilcoxon-test över grupperna.
- **T1, huvudprov (alla facit-2-grupper):** håller om p < 0,05 och medelandelen är större än kontrollens.
- **T2 (grupper utan någon sten med säker ristare i Rundata):** samma prov. Håller på samma sätt med minst 5 grupper med
  skillnad, annars är det obestämt.
- **Beskrivande:**
  - de granskade uttalandena om olika händer: hur många sådana par modellen ändå lägger i samma grupp (falska
    sammanslagningar);
  - litteraturens besked per grupp (stöds, motsagd, ny, ej omnämnd) med de granskade uttalandena.

## Beslut
- **T1 håller:** metoden räknas som prövad mot två oberoende facit, och appen behåller grupperna.
- **T1 håller inte:** det redovisas i appen och i METHODS 14l att metoden inte höll mot litteraturen, och grupperna märks
  som mindre säkra.

## Utdata
`utdata/nya_ristare/slutprov2.py` → `slutprov2.json` och resultatet i `resultat.md`. Facit 2 med källor ligger i
`data/cache/hander/` (utanför git). Bara signum och källhänvisningar läggs i git.
