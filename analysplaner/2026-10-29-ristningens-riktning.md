# Analysplan: Ristningens riktning – vart vände runstenarna sin text?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-ristningens-riktning.sha256`.
Kod `utdata/riktning/analys.py`, resultat `utdata/riktning/resultat.md`.

## Bakgrund
Kulturmiljöregistrets beskrivningar anger för en del runstenar åt vilket väderstreck ristningen vetter (”Ristningen
vetter mot SÖ”). Frågan: vände man texten mot vägen, mot gården – eller mot solen? Sett före låsningen: 456 KMR-poster
anger riktning; 369 gäller en enda sten med en riktning, 219 av dem står på sin plats enligt vår korpus; 88 av de 369
nämner en väg med väderstreck i texten. Inga riktningar har räknats.

## Material
Svenska vikingatida runstenar på sin plats (`moved = 0`, `lost = 0`, korpus 3f58e9339191761e) vars KMR-post
(data/raa/kmr_runstenar.json) gäller just den stenen och anger en enda riktning med ”vetter mot X” (16 väderstreck,
N = 0°, NNÖ = 22,5° …).
- **Vägen:** i första hand KMR-textens ”X m <väderstreck> om väg” (vägen ligger åt motsatt håll); annars närmaste
  registrerade färdväg eller vägmärke i KMR (data/raa/lamningar.csv typ färdväg, lamningar_extra/vägmärke) inom 500 m.
- **Gården:** närmaste bytomt/gårdstomt i KMR (lamningar_extra) inom 1 km.
- Riktningen till väg och gård räknas som bäring från stenen (SWEREF 99 TM).

## Test (Holm över H1–H4, α = 0,05)
- **H1 Riktningarna är inte jämnt fördelade:** Rayleighs test.
- **H2 Mot vägen:** statistik = medelvärdet av cos(ristningens riktning − bäringen till vägen) bland stenar med väg.
  Nollmodell: riktningarna blandas om mellan stenarna inom landskapet (9 999 gånger), så att landskapets allmänna
  riktningsmönster behålls. Ensidigt (mer mot vägen).
- **H3 Mot gården:** samma med bäringen till närmaste bytomt; ensidigt.
- **H4 Bro- och vägstenar mer mot vägen:** skillnaden i medel-cos mot vägen mellan stenar med `cat_bro_vag` och
  övriga; omblandning av etiketten inom landskapet; tvåsidigt.
**Håller:** Holm-p < 0,05 och p < 0,05 åt samma håll i båda halvorna (socken för socken som i change.R).
**Antydan:** Holm-p < 0,05 utan halvorna, eller okorrigerat p < 0,05.

## Robusthet (redovisas)
Bara vägar ur KMR-texten; bara registrerade färdvägar/vägmärken; gården inom 500 m; bara Uppland och Södermanland.

## Beskrivning (prövas inte)
Riktningsfördelningen (16 streck) totalt och per landskap; medelriktningen; andelen som vetter mot S, SÖ eller SV.

## Förbehåll
Många stenar har rests upp på nytt, och en del kan ha vänts vid återresningen. Vägarna i KMR-texten är ofta dagens
vägar, som inte alltid följer de vikingatida. Bytomterna är kända från 1600–1700-talens kartor. 219 stenar är ett
litet underlag; små effekter syns inte.
