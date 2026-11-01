# Maltstenen mot besvärjelser – resultat

Låst plan `analysplaner/2026-11-01-malt-besvarjelser.md` (sha 44d8fa9f). Kört 2026-11-01 med `utdata/Malt/besvarjelser.py`;
alla tal i `besvarjelser.json`. Ingen läsning av Malt.

## Avvikelse från planen
Första körningen stannade: runor som språkmodellen aldrig sett (latinska bokstäver på medeltida amuletter) gav oändligt
många bitar. Varje runas överraskning sätts nu till högst 20 bitar. Inget annat ändrades.

## Del A – formen
Urvalet gav 1 814 vikingatida runstenar (2 741 avsnitt om 24 runor), 15 vikingatida besvärjelser (23 avsnitt) och 78
medeltida (151 avsnitt). De vikingatida besvärjelserna: Öl Fv1976;96A och 96B, Öl SAS1989;43 (Kvinneby), U ANF1937;163,
U AST1;150, U ATA351-1796-2014, U Fv1933;134, U NOR2002;26, DR 410, DR EM85;151B (Ribeskallen), DR AUD1999;288, DR DKBh63,
DR DKSJy76, E DR419 (Canterbury), RU Melnikova2001;196.

**Huvudprovet:** modellen skiljer avsnitt ur minnesstenar från avsnitt ur besvärjelser väl (AUC 0,95). Malts fem avsnitt
får sannolikheten 0,57, 0,01, 0,04, 0,54 och 0,75 för besvärjelse, i medel **0,38**. Enligt planen **liknar Malts form
minnesstenar mer än besvärjelser**. Samma utfall med medeltida besvärjelser (AUC 0,99, Malt 0,23), utan språkmodellen
(0,96; 0,09) och med bara danska runstenar (0,94; 0,27).

**Vad som avgör.** Det klart tyngsta måttet är skiljetecknen (koefficient −3,7): minnesstenarna har 0,17 skiljetecken per
runa, de vikingatida besvärjelserna nästan inga (0,009), Malt 0,125. I de övriga måtten ligger Malt nära besvärjelserna
eller bortom dem:
- bitar per runa (hur ovan texten är för en modell tränad på runstenar): Malt 3,95, besvärjelser 4,00, minnesstenar 3,02;
- återkommande trerunsföljder: Malt 0,109, besvärjelser 0,085, minnesstenar 0,041;
- samma runa tre gånger i rad: i 1 av Malts 5 avsnitt (*tuuut*), 9 % av besvärjelsernas, 0,2 % av minnesstenarnas.
Avståndet i alla sju måtten: Malt ligger närmast de vikingatida besvärjelserna (3,1), sedan Gørlev (3,5), minnesstenarna
(4,6), Hedebypinnen (4,7) och de medeltida besvärjelserna (5,4). Malts första och två sista avsnitt (sida A och slutet)
liknar besvärjelser, de två i mitten (*huaR is … karþi … fauþr*) minnesstenar.

**Tolkning av utfallet.** Det låsta provet säger minnesstenar, och det beslutet står. Men det vilar mest på att Malt har
skiljetecken som en sten, medan amuletter av metall och ben nästan aldrig har det. Skiljetecken kan lika gärna höra till
materialet och ristartraditionen som till genren. Till innehållet (ovana ordföljder, upprepning, mångdubblade runor)
ligger Malt bland besvärjelserna. Ett nytt prov där skiljetecknen hålls utanför skulle behöva en egen låst plan.

## Del B – tolkningarnas ord
Malts högsta likhet med målorden, mot 163 vikingatida runstenar av samma längd:
- *dvärg* (*dverga*, *dværg*): 0,60, 22:a percentilen (bästa par *karþi*–*dverga*);
- *Billing* (*billingr*): 0,55, 78:e percentilen (*tuuutbilikakR*);
- *Tyr*: 0,67, 35:e percentilen (*huaR*);
- *ut*: 0,67, 29:e percentilen (*utu*).
**Inget målord ligger över 95:e percentilen.** Av 50 slumpvisa kontrollord gör 1 det, så måttet skiljer. Tolkningarnas ord
finns alltså inte oftare i Malts ristning än vilket ord som helst finns i en vanlig runsten av samma längd. Den tidigare,
oplanerade iakttagelsen (*tuRraki* liknar Ribeskallens *tuirk*) håller inte här: mot Rundatas normaliserade former *dværg*
och *dverga* når *tuRraki* inte upp till Malts bästa par.

## Svagheter
- Bara 15 vikingatida besvärjelser och 23 avsnitt; de flesta är korta metallamuletter.
- Rundatas translitterering har versaler för vissa runformer i 29 vikingatida inskrifter, bland dem Ribeskallen. Rutinen
  bryter följden vid versaler, så Ribeskallen gav inga hela avsnitt och fick inget eget mått. Rutinen ändras inte här.
- I Malts text (`malt_decode`) står *tuuutbilikakR* som en grupp; Rundata skiljer *tuuut* och *bilikikR* med mellanslag
  (utgivarens ordgräns, inget skiljetecken). Det sänker Billing-likheten något.
- Del B mäter likhet med ordformer, inte med hela tolkningar; en tolkning kan bygga på böjningar och ljudlagar som måttet
  inte ser.
