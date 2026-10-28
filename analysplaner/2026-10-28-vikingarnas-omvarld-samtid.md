# Tillägg till analysplanen Vikingarnas omvärld: samtidssagorna

Låst 2026-10-28, innan något nedan har räknats. Tillägg till `analysplaner/2026-10-28-vikingarnas-omvarld.md`, vars
mått, ortnamnslista och metoder gäller oförändrade. SHA-256 i `analysplaner/2026-10-28-vikingarnas-omvarld-samtid.sha256`.
Resultat och avvikelser i `utdata/varlden/resultat_samtid.md`.

Bakgrund: huvudplanens test 1 visade att fornaldarsagorna (om forntiden) ser mer mot öster än islänningasagorna (om de
egna förfäderna). Vår hypotes, publicerad 2026-10-28 i artikeln ”Vikingarnas värld – vilka platser nämner de?”, är att
österleden på Island hade blivit forntid. Den förutsäger att samtidssagorna – skrivna på Island på 1200-talet om
samtiden – inte ser mot öster.

Före låsningen har bara följande gjorts: texterna har hämtats och sparats i `utdata/varlden/korpus/samtidssagor/`, och
deras ordantal har räknats. Inga platser har räknats i dem.

## Material
- **Samtidssagor:** de sex delar av Sturlunga saga (Guðni Jónssons utgåva 1948, via heimskringla.no) som finns som ren
  text: Þorgils saga ok Hafliða, Hrafns saga Sveinbjarnarsonar (Sturlunga-versionen), Svínfellinga saga, Sturlu þáttr,
  Arons saga och Smákaflar ok brot, cirka 51 000 ord. Prosan räknas; versen skiljs av som i huvudplanen och redovisas
  bara beskrivande. Íslendinga saga, Þórðar saga kakala, Þorgils saga skarða, Sturlu saga, Prestssaga Guðmundar och
  Guðmundar saga dýra saknas i ren text och ingår inte.
- **Jämförelser:** fornaldarsagorna och islänningasagorna (prosa) som i huvudplanen.
- **Ortnamnslistan** `platser.csv` som den är vid låsningen, oförändrad.

## Mått
Som i huvudplanen: olika platser i öster (Ö) och väster (V) per text, östandel = ΣÖ / Σ(Ö + V), klusterbootstrap och
permutationer med 10 000 dragningar.

## Test (Holm-korrigerade tillsammans, tvåsidiga, α = 0,05)
- **Spärr:** samtidssagornas Σ(Ö + V) måste vara minst 20. Annars redovisas tillägget som ”för få träffar” och inga test
  tolkas.
- **Test 4:** samtidssagor mot fornaldarsagor, skillnaden i östandel, permutationstest över texterna.
- **Test 5:** samtidssagor mot islänningasagor, samma test.
- Tolkningsregler för varje test som i huvudplanen (”skillnaden håller”, ”ingen skillnad av betydelse” inom ±15
  procentenheter, annars ”obestämt”).

## Utslag för hypotesen (bestämt i förväg)
- **Stöds:** test 4 ”skillnaden håller” med lägre östandel i samtidssagorna, och test 5 visar inte att samtidssagorna
  ser signifikant mer mot öster än islänningasagorna.
- **Motsägs:** samtidssagornas östandel är minst lika hög som fornaldarsagornas, eller test 5 ”skillnaden håller” med
  högre östandel i samtidssagorna.
- **Obestämt:** allt annat.

## Robusthet och beskrivning (ändrar inte utslaget)
1. Utan ”Österled/Västerled (allmänt)”. 2. Träffar i stället för olika platser. 3. Utan den största texten (Arons
saga). 4. Nordatlanten som väster. Beskrivande: andelen platser i söder (Rom, Jerusalem m.fl.), som hypotesen
förväntar sig, och de vanligaste platserna. Alla träffar granskas i sitt sammanhang; falska träffar rättas och båda
resultaten redovisas som avvikelse.

## Förbehåll som redovisas
Korpusen är liten och saknar Íslendinga saga, den största samtidssagan. Arons saga är skriven senare än händelserna,
troligen på 1300-talet. Ett obestämt utfall betyder att materialet inte räcker, inte att hypotesen är fel.
