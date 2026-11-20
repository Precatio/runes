# Analysplan: grannstenarnas namn med brantare närhet (textmodel-24-kandidat)

Skriven och låst 2026-11-20, innan något nedan har körts. Viktor 2026-11-20: "ja" till en låst plan för hur modellen
väljer mellan namn.

## Känt före låsningen
- **Namnen är modellens svagaste del.** I maskeringsprovet med appens inställning (app_f0–f4, runstenar) blir 82 av 164
  namnluckor rätt när namnet står på minst tre andra runstenar, mot 832 av 1 067 för andra ord. 60 av 281 namnluckor
  gäller ett namn som inte står på någon annan runsten (8 rätt). Räknat 2026-11-20, beskrivande.
- **Grannstenarnas namn används redan** (`textmodel.FILL`: `near_km` 10, `lam_near` 0,1): namn på stenar inom 10 km
  blir kandidater med vikten 1 / (1 + d / 5) (d i km, `Model.names_near`), så en sten 5 km bort väger hälften så mycket
  som en på samma plats.
- **Ristarens krets** prövades 2026-10-16 utan vinst (METHODS 8.1, "Ristaren"). Den ingår inte här.
- **Familjegrupperna** (rapporten Familjegrupper vid gravfälten, v5): grannstenar i samma grupp nämner samma namn
  oftare än stenar längre bort; med grupper som enhet försvagat men åt samma håll.

## Mekanismen
Bara närhetsskalan s i vikten 1 / (1 + d / s) och vikten λ_near ändras; allt annat är appens inställning.
Kandidater (rutnät, bestämt nu): s ∈ {5 (i dag), 1, 0,25} km × λ_near ∈ {0,1 (i dag), 0,2}, alltså fem nya
kombinationer. Avståndsgränsen 10 km ändras inte. Kräver en flagga `--near_scale` i runlm_restore_test.py och en
parameter `scale` i `names_near` (förval 5,0, så att appen och tidigare körningar är oförändrade; kontrolleras först med
en körning på veck 0 som ska ge samma val som app_f0).

## Steg 1: val på veck 0
De fem kombinationerna körs på veck 0 och jämförs parvis per lucka mot app_f0 (bara runstenar). Den kombination väljs
som har flest vunna minus förlorade **namnluckor** (is_name, hela namnet rätt), bland dem som inte har fler fel bland
svar ≥ 95 % än app_f0; vid lika netto den som ligger närmast i dag (först större s, sedan mindre λ). Har ingen ett
positivt netto stoppar provet, och det redovisas som negativt.

## Steg 2: det avgörande provet, veck 1–4
Den valda kombinationen mot app_f1–f4. **Håller** när alla fyra gäller (samma som plan 321c3a6d):
1. fler vunna än förlorade namnluckor över veck 1–4;
2. alla luckor (båda slagen): vunna minus förlorade ≥ 0;
3. svar ≥ 95 % (tm19:s kalibrering): inte fler fel än i app;
4. korta luckor (1–2 runor): inte fler nya fel än nya rätt.
Håller provet körs dok5 med kombinationen (efter rättningen i plan 2026-11-20-okant-ord-och-samma-ord); den får inte ge
färre rätt ord eller fler fel bland svar ≥ 95 % än appens inställning räknad på samma sätt. Först då ändras FILL i appen
(textmodel-24). Om textmodel-23 (Petersons namn) har slagits på innan provet körs, är det app-inställningen med namnen
som är jämförelsen, och det redovisas.

## Beskrivande
Hur många namnluckor som vunnits och förlorats efter avstånd till närmaste sten med samma namn (0–1, 1–5, 5–10 km,
ingen); exempel på vunna och förlorade.

## Vad som inte får göras
Inga fler värden än rutnätet. Inget annat ändras i FILL. Ingen kombination väljs om efter att veck 1–4 har setts.

## Ordning
Efter textmodel-23 och omräkningen i plan 2026-11-20-okant-ord-och-samma-ord, ett tungt jobb i taget; omkring två dygn.

## Utdata
`utdata/runlm_forfining/tm24/` (kor.sh, jamfor.py, sammanfattning.json) och `utdata/runlm_forfining/tm24_resultat.md`.
