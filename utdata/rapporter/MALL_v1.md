# Forskningsrapport – mallen (2026-10-31)

**LÅST 2026-10-31** (Viktor: ”jag är nöjd med rapporten nu, lås den formen”). Förebilden är rapporten om kvinnorna
bland resarna (`utdata/blogg/build/build_rapport_kvinnor.py`). Formen ändras bara genom en ny version av mallen med
datum och skäl; kontrollsumman står i `MALL.md.sha256`. Rapporter som byggts på en äldre version av mallen behåller den.

En rapport per fynd. Bara fynd som är **bekräftade** i Statistik (håller i båda halvorna av korpusen, delade socken
för socken, och q_global < 0,05 i den gemensamma Benjamini–Hochberg-justeringen över alla visade mönster) och som
har gått **hela robusthetstrappan** (METHODS.md 1v). Rapporten är registrerad till formen: planen låstes före
resultaten, och rapporten redovisar planen som den löd.

Artikeltyp: etiketten **Rapport** (en typ per artikel) + ämnen. Byggare i `utdata/blogg/build/build_rapport_*.py`
med alla siffror asserterade mot filerna i `data/cache/r/corpus/<fingerprint>/` (robustness.json, modulens json)
och planen i `analysplaner/`. Två språk ur samma byggare: den **engelska versionen är den kanoniska för citering** (DOI, ”citera som”, det
internationella fältet och Google Scholar läser engelska), den svenska är läsversionen för sajten och materialets
egna termer. Båda sidorna är märkta ScholarlyArticle i den strukturerade datan.
Titeln är påståendet med siffrorna i, inte ämnet. Längd 1 500–3 000 ord. Inga tabeller (BlogBody), listor i stället.

## Skriv för en läsare som aldrig sett Vitki

Rapporten ska gå att läsa av en runolog eller statistiker som inte känner appen. I löptexten (allt före Data och kod):
inga interna namn – inte modulnamn (människomodulen, budskapsmodulen), inte robusthetstrappan, q_global, korpusjobb,
fingeravtryck, facit, flikar i appen eller filvägar. Beskriv i stället vad saken är: ”en förregistrerad studie av vilka
som reste stenarna”, ”en fast serie känslighetsanalyser”, ”justerat för alla N samband projektet redovisar
(Benjamini–Hochberg), q”, ”handkodat kontrollurval”, ”Rundata, fryst för analysen den …”. Definiera varje begrepp
första gången (slumpeffekt, halvorna, marginaleffekt) och räkna upp landskapen bakom en landsdel. Filvägar, versionsnyckel
och appens flikar står bara under Data och kod. Byggaren ska kontrollera detta (sök efter jargong före Data och kod).

## Fasta rubriker, i denna ordning (IMRaD i registrerad form)

Ingen numrering av rapporterna i titeln; typen Rapport och versionsraden räcker.

0. **Huvud** (kursiv rad först i texten): författare och tillhörighet, version och datum, licens (CC BY 4.0),
   citeringsrad till den engelska versionen, nyckelord, konkurrerande intressen, finansiering.
1. **Sammanfattning**, strukturerad: bakgrund och syfte, material, metod, resultat (effekt och osäkerhet i siffror),
   slutsats. Säg vad som inte visats.
2. **1. Inledning**: tidigare forskning med referenser, vad som saknas i den, studiens syfte.
3. **2. Förregistrering**: planens fil, datum och SHA-256; hypotesen ordagrant; förutbestämda gränser och
   tolkningsregler; vad som var sett före låsningen; vilka analyser som är konfirmatoriska, vilka som är uppföljning
   (egen låst plan) och vilka som är explorativa.
4. **3. Material**: korpusens fingerprint, urvalet steg för steg med antal (vikingatida, svenska landskap, läsbara,
   flyttfiltret), vad som mäts och hur (regel + facit mot handkodning med felandel), jämförelsen, justeringarna.
5. **4. Metod**: 4.1 modellen, 4.2 korrigering och replikering (halvorna), 4.3 robusthetstrappan, 4.4 avvikelser
   från planen (alltid med, också när det är ”inga”).
6. **5. Resultat**: 5.1 konfirmatoriskt huvudtest med halvorna och ett diagram, 5.2 planens robusthetsprov,
   5.3 trappan steg för steg som lista med modellkontroll, kodningsfel och q_global, 5.4 uppföljning (märkt).
7. **6. Diskussion**: vad fyndet säger, mot tidigare forskning, svagheter i ordning efter vikt, vad som skulle
   fälla fyndet.
8. **7. Slutsats**, kort.
9. **Data och kod**: skript, fingerprint, kommando, licens, var mönstret syns i appen, länk till populär artikel.
10. **Referenser** i Futhark-stil (efternamn, initial, år, titel, serie, sidor).
11. `:::box Det viktigaste i korthet` (sajtens korthetsregel) – tolkningen, inte sifferrepris.

## Versioner
Två versioner hålls isär: **rapportversionen** (1, 2 … efter rättelser) och **Vitkis version** (programmet, ur
web/package.json, i dag 3.0.0), plus commit för kodläget så länge ingen release med DOI finns. Skriv aldrig bara
”version 1”.
v1 med datum i rubrikraden under titeln. En rättelse ger v2 med en ändringslogg sist i rapporten (vad, varför, när);
aldrig tyst patch. DOI via Zenodo när repot släpps (RELEASING.md): rapporten hänvisar då till den versionen.
