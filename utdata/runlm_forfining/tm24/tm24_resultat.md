# textmodel-24: böjningslagret – negativt (2026-11-28)

Plan `analysplaner/2026-11-27-bojningsmodellen-tm24.md` (sha 1656a0bf). Koden finns i `src/runlm.py` och är av som
standard (ecea135). Valet på veck 0 gjordes med `tm24_kor_val.sh` och `tm24_jamfor.py --val`, och utfallet står i
`val_val.json`.

## Utfall
- **Alla tolv kombinationer** (λ 0,003/0,01/0,03 × tröskel 0,02/0,05 × μ 0/0,5) gav på veck 0, mot `app_f0`, samma
  resultat:
  - 7 böjningsluckor, 0 vunna och 0 förlorade;
  - alla luckor 0 vunna och 0 förlorade;
  - 0 nya säkra fel.
- **Lagret ändrade inte ett enda val.**
- **Enligt planen stoppas arbetet.** Veck 1–4 körs inte, och lagret förblir av.

## Varför
- **Former som modellen räknar som samma ord är nästan aldrig olika böjningsformer.** De är olika normaliseringar av samma
  form: ð/þ, R/r, dubbelkonsonanter och accenter.
  - Tabellen över ändelseväxlingar (286 växlingar, de flesta sedda en gång) innehåller få verkliga böjningsbyten.
  - **-aR ↔ -uR lärs inte.** Malts *uifrþuR* skapas därför inte.
- **Agentens uppskattning före körningen:** av 85 ord som inte finns i träningen men vars stam finns där, skapade lagret rätt
  form för 2.
- **Huvudmåttet är dessutom litet.** Bara 7 av provluckorna på veck 0 är böjningsluckor. Även en perfekt böjningsmodell kan
  därför vinna högst några luckor per veck. Det mesta av modellens fel ligger någon annanstans.

## Avvikelser från specifikationen
Planen ändrades inte; detaljerna står i commit ecea135 och agentens rapport.
- Utjämningen görs över alla ändelser, inte bara de observerade.
- En ny form har egen nyckel. Med `infl_pool=True` delar den lemma med sitt ursprungsord.
- En ny form blockerar inte ett sammansatt namn med samma bokstäver.

## Lärdom
Böjning går inte att lära ur modellens egna lemmagrupper. Om böjning ska prövas igen måste mönstren komma utifrån, ur
fornnordisk grammatik (a-, i- och u-stammarnas ändelser, runsvenskt -aR/-iR/-uR). Men det lilla antalet böjningsluckor
visar att vinsten i maskeringsprovet ändå blir liten. Där finns värde främst för ovanliga texter som Malt.
