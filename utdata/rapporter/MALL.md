# Forskningsrapport – mallen (2026-10-31)

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

## Fasta rubriker, i denna ordning

1. **Sammanfattning** (sv i texten, en i den engelska versionen): fyndet i en mening med effekt och osäkerhet,
   materialet i en mening, vad som prövats, vad som inte visats.
2. **Fråga och hypotes som den låstes**: planens fil, datum och SHA-256; hypotesen ordagrant; förutbestämda gränser.
3. **Material**: Rundata-version/korpusens fingerprint, urvalet steg för steg med antal (vikingatida, svenska
   landskap, läsbara, flyttfiltret), vad som mäts och hur (regel + facit mot handkodning med felandel).
4. **Metod**: modellen i ord (utfall, jämförelse, justeringar, slumpeffekter), programvara, korrigering för flera
   test, halvorna, trappan.
5. **Resultat**: huvudtalet (andelar, oddskvot med 95 %-intervall, p, Holm-p, q_global), båda halvorna var för sig,
   trappan steg för steg som lista, modellkontroll, kodningsfelens inverkan.
6. **Tolkning och svagheter**: vad fyndet säger, vad det inte säger, alternativa förklaringar som prövats
   (med hänvisning till uppföljande låsta planer), vad som skulle fälla det.
7. **Reproduktion**: kommando, skript, commit/fingerprint, data, licens, hur man ser mönstret i appen.
8. **Referenser** i Futhark-stil.
9. `:::box Det viktigaste i korthet` (korthetsregeln) – tolkningen, inte sifferrepris.

## Versioner
v1 med datum i rubrikraden under titeln. En rättelse ger v2 med en ändringslogg sist i rapporten (vad, varför, när);
aldrig tyst patch. DOI via Zenodo när repot släpps (RELEASING.md): rapporten hänvisar då till den versionen.
