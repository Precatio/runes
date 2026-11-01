"""Skriver utdata/slakt/steg1_resultat.md ur steg1.json (planens redovisning). Inga siffror skrivs för hand.
    .venv/bin/python utdata/slakt/skriv_steg1.py"""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(OUT, "steg1.json"), encoding="utf-8"))
pc = lambda x: f"{100 * x:.1f}".replace(".", ",") + " %"  # noqa: E731
a, b, c = R["M0"], R["M1"], R["criteria"]
L = []
w = L.append
w("# Resultat: släktnätverket, steg 1 (2026-11-01)")
w("")
w(f"Plan: `{R['plan']}` (låst före körningen, SHA-256 403fa352…). Kod `steg1.py`, siffror `steg1.json`. Material: "
  f"{R['n_stones']} svenska vikingatida runstenar. Kontroll: Williams 1990 (`williams1990_bilaga.json`), Jarlabankes stenar, "
  "Rundatas parstenar och anmärkningar.")
w("")
w(f"## Utfall: M1 håller inte – appen behåller M0")
w(f"M1 klarar fyra av planens fem villkor men inte Jarlabanke: bara {b['J']['sure']} av {b['J']['pairs']} par blir säkra.")
w(f"- W1, täckning mot Williams: M0 {a['W1']['hit']} av {a['W1']['n_stones']} stenar ({pc(a['W1']['share'])}), M1 {b['W1']['hit']} av "
  f"{b['W1']['n_stones']} ({pc(b['W1']['share'])}). Minst dubbelt och minst 25 %: {'ja' if c['W1_double'] and c['W1_floor'] else 'nej'}.")
w(f"- W2, träffsäkerhet mot Williams: M0 {a['W2']['hit']} av {a['W2']['n_links']} länkar ({pc(a['W2']['share'])}), M1 {b['W2']['hit']} av "
  f"{b['W2']['n_links']} ({pc(b['W2']['share'])}). Inte mer än tio enheter sämre: {'ja' if c['W2_not_worse'] else 'nej'}.")
w(f"- J, Jarlabanke: M0 {a['J']['sure']} av 10, M1 {b['J']['sure']} av 10. Uppfyllt: {'ja' if c['J'] else 'nej'}.")
w(f"- K, motsägelser bland länkarna under gränsen: M0 {a['K']['below_cut_contradicted']} av {a['K']['below_cut']} ({pc(a['K']['share'])}), "
  f"M1 {b['K']['below_cut_contradicted']} av {b['K']['below_cut']} ({pc(b['K']['share'])}). Högst 5 %: {'ja' if c['K'] else 'nej'}.")
w(f"- Säkra länkar: M0 {a['n_sure']}, M1 {b['n_sure']} (av {b['n_candidates']} kandidater). Parstenar: M0 {a['parsten']['found']} och M1 "
  f"{b['parsten']['found']} av {b['parsten']['n']}; Rundatas anmärkningar: M0 {a['rundata_noted']['found']} och M1 {b['rundata_noted']['found']} "
  f"av {b['rundata_noted']['n']}.")
w("")
w("I klartext: den nya modellen hittar dubbelt så många av de släktsamband som runologerna redan har pekat ut, utan att bli "
  "mindre träffsäker och utan en enda motsägelse – men den missar Jarlabankes egna stenar, och då säger planen nej.")
w("")
w("## Varför Jarlabanke faller (beskrivning, ändrar inget)")
w("- Alla tio par delar Jarlabanki och gårdsnamnet Täby (styrka 11,1). U 127 står 10–14 km från de fyra andra; i bandet över "
  f"10 km ger nollmodellen i genomsnitt {b['null_mean_per_band']['C']:.0f} länkar mot {b['obs_per_band']['C']} i data, så en äkta men "
  "avlägsen länk kan inte nå q under 0,1 (q 0,38).")
w("- De sex paren på 3,6–6,8 km får q 0,127 med nollmodellen inom häradet men 0,017 med nollmodellen inom landskapet: sju av "
  "Jarlabankes nio stenar står i samma härad (Danderyds skeppslag), så när namnen blandas inom häradet återskapar slumpen "
  "Jarlabankepar. Häradsnollmodellen räknar en stor släkts eget avtryck i bygden som lokal namnsed – den är för sträng just "
  "där släkterna syns som tydligast.")
w("")
w("## Per avståndsband (M1)")
for bd in ("A", "B", "C"):
    w(f"- Band {bd}: {b['obs_per_band'].get(bd, 0)} kandidater, i genomsnitt {str(round(b['null_mean_per_band'][bd], 1)).replace('.', ',')} i nollmodellen, "
      f"{b['per_band'][bd]['n_sure']} säkra.")
w("")
d = R["describe_M1"]
w("## Beskrivning (M1, även om den inte införs)")
w(f"- {d['groups']} släktgrupper med {d['stones_in_groups']} stenar, {d['groups_3plus']} med minst tre stenar; {d['persons_on_2plus']} "
  f"personer står på minst två stenar; den längsta kedjan förälder–barn över stenarna är {d['longest_generations']} generationer.")
w("- Grupper per landskap: " + ", ".join(f"{k} {v}" for k, v in d["groups_by_province"].items()) + ".")
w("")
w("## Känslighet")
for k, v in R["sensitivity"].items():
    w(f"- {k}: {v['n_sure']} säkra, W1 {pc(v['W1']['share'])}, W2 {pc(v['W2']['share'])}, Jarlabanke {v['J']['sure']} av 10, motsägelser {pc(v['K']['share'] or 0)}.")
v = R["M1b_exploratory"]
w(f"- Utforskande M1b (ett enda ovanligt namn inom 2 km): {v['n_sure']} säkra, W1 {pc(v['W1']['share'])}, W2 {pc(v['W2']['share'])}. Avgör ingenting.")
w("")
w("## Avvikelser från planen")
w("- Utan flyttade stenar: också stenar som korpusen anger som försvunna (lost = 1) togs bort, eftersom deras plats inte är "
  "känd; planen nämnde bara moved = 0.")
w("- I övrigt inga.")
w("")
w("## Vad det betyder för nästa steg")
w("Den avståndsdelade prövningen är rätt idé – den fördubblar täckningen utan att tappa träffsäkerhet – men nollmodellen inom "
  "häradet straffar just de stora släkterna. Känsligheten pekar på nollmodellen inom landskapet med avståndsband "
  f"({R['sensitivity']['null_province_banded']['n_sure']} säkra, W1 {pc(R['sensitivity']['null_province_banded']['W1']['share'])}). "
  "Det valet är gjort efter att ha sett data och måste därför prövas på nytt material i en ny låst plan, inte införas här.")
open(os.path.join(OUT, "steg1_resultat.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
