# Luckor i texten på danska och norska inskrifter (plan låst 2026-10-27, före körning)

**Vad.** Samma luckinventering som för de svenska inskrifterna (scripts/runlm_gaps.py med tm19-inställningarna i
klass3_f*.json: max_gaps 2000, lam_name 0.05, lam_class 0.2, char_fills 15, context_cands, n_cands 100, tolerance 0.02,
by_word, near 0.1, near_km 10, own_d, name_cands 40), men på de vikingatida inskrifterna med signum DR (Danmark, med
Skåne, Halland, Blekinge och Sydslesvig) och N (Norge) – inga andra länder. Femfaldigt över stenarna; modellen tränas
på alla vikingatida inskrifter utom den femtedel som fylls i. Den svenska inventeringen ändras inte.
Ut: klass3_dkno_f0–f4.json och klass3_dkno.json.

**Prövning.** De luckor Rundata har återställt i DR och N är facit. Sannolikheten kalibreras med samma listkalibrering
som för de svenska luckorna (scripts/textmodel_candidates.py).

**De danska och norska kandidaterna visas i appen bara om båda gäller:**
1. Bland återställda DR/N-luckor med kalibrerad sannolikhet ≥ 0,8 kommer modellen fram till Rundatas ord i minst 75 %
   (och minst 10 sådana luckor finns).
2. Andelen återställda DR/N-luckor där modellen kommer fram till Rundatas ord är högst 10 procentenheter lägre än för de
   svenska återställda luckorna i klass3_alla.json.

Annars redovisas utfallet som negativt och listan förblir svensk.
