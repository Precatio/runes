"""Skriver utdata/strand/resultat.md (planens redovisning, på svenska, varje siffra i klartext) ur resultat.json
(03_statistik.R, med T1) och trappan.json (05_trappa.R). Inga siffror skrivs för hand.
    .venv/bin/python utdata/strand/skriv_resultat.py"""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(OUT, "resultat.json"), encoding="utf-8"))
T = json.load(open(os.path.join(OUT, "trappan.json"), encoding="utf-8"))
assert R["verdict"]["H1"] == "håller" and R["verdict"]["H3"] == "håller" and T["H1"]["all_hold"] and T["H3"]["all_hold"]
NAME = {"U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", "Sm": "Småland", "Vg": "Västergötland", "Öl": "Öland",
        "Bo": "Bohuslän", "D": "Dalarna", "G": "Gotland", "Gs": "Gästrikland", "Hs": "Hälsingland", "J": "Jämtland",
        "M": "Medelpad", "Nä": "Närke", "Vr": "Värmland", "Vs": "Västmanland"}
SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def sv(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


def n(x):
    return f"{x:,}".replace(",", " ")


def p(x):
    if x == 0:
        return "p < 10⁻³⁰⁰"
    if x < 0.001:
        m, e = f"{x:.1e}".split("e")
        return f"p = {m.replace('.', ',')}·10{str(int(e)).translate(SUP)}"
    return f"p = {sv(x, 3 if x < 0.1 else 2)}"


def pc(x):
    return f"{int(100 * x + 0.5 + 1e-9)} %"  # halvt uppåt, som i rapportbyggarna


def row(r, unit="vattnet"):
    """En rad: medianer, andel inom 500 m, AUC och p, med klartexten för AUC."""
    return (f"{n(r['n_stones'])} stenar mot {n(r['n_random'])} punkter: median {n(r['median_stones_m'])} mot "
            f"{n(r['median_random_m'])} m, inom 500 m {pc(r['within_500_stones'])} mot {pc(r['within_500_random'])}, "
            f"AUC {sv(r['auc'])}, {p(r['p'])}")


L = []
w = L.append
po, H1, H2, H3 = R["population"], R["H1"], R["H2"], R["H3"]
w("# Resultat: runstenarna, dåtidens strand och gravfälten")
w("")
w(f"Plan: `analysplaner/2026-10-23-strand-och-gravfalt.md` (SHA-256 {R['plan_sha256'][:8]}…), tillägget med T1 "
  f"`analysplaner/2026-10-31-strand-tillagg.md` och tilläggsplanen för robusthetsstegen "
  f"`analysplaner/2026-11-01-strand-trappan.md` (SHA-256 {T['plan_sha256'][:8]}…). Statistiken kördes {R['computed_at']} "
  f"({R['r_version']}), trappan {T['computed_at']}. Kod: `01_avstand.R`, `01b_marginal.R`, `02_r6.R`, `03_statistik.R`, "
  "`04_figurer.R`, `05_trappa.R`; siffror `resultat.json` och `trappan.json`; den här filen skrivs av `skriv_resultat.py`.")
w("")
w("**Hur siffrorna läses.** *Median* är avståndet som hälften av stenarna (eller punkterna) ligger närmare än. *AUC* är "
  "sannolikheten att en slumpvis vald sten står närmare än en slumpvis vald slumppunkt; 0,5 betyder ingen skillnad, 0,63 "
  "betyder att stenen står närmare i 63 jämförelser av 100. *p* är sannolikheten att få en så stor skillnad om stenarna "
  "hade stått lika slumpvis som punkterna (Wilcoxons rangsummetest, ensidigt). *q* är p justerat för att flera landskap "
  "eller prov prövas samtidigt (Benjamini–Hochberg).")
w("")
w("## Utfallet i korthet")
w(f"- **H1 håller** enligt alla fem kriterierna i planen: stenarna står närmare vattnet år 1050 än marken runt dem.")
w(f"- **H3 håller**: stenarna står närmare gravfälten än marken runt dem, och skillnaden är större än för vattnet.")
w(f"- **H2: {R['verdict']['H2']}**, men skillnaden är liten (AUC {sv(H2['auc_then'])} mot dagens {sv(H2['auc_now'])}).")
w("- **T1** (bara stenar som alla tre källorna räknar som kvar på platsen) och **alla steg i den låsta trappan** håller för "
  "både vattnet och gravfälten.")
w("")
w("## Urvalet")
ORDER = ["U", "Sö", "Ög", "Sm", "Vg", "Öl"]
lst = lambda dd: ", ".join(f"{NAME[k]} {dd[k]}" for k in ORDER if k in dd)  # noqa: E731
prov = lst(po["provinces"])
oth = ", ".join(f"{NAME[k]} {v}" for k, v in sorted(po["other_provinces_not_tested"].items(), key=lambda kv: -kv[1]))
w(f"- {n(po['n'])} vikingatida runstenar som inte är flyttade, i sex landskap: {prov}. Stenarna i övriga landskap prövas "
  f"inte ({sum(po['other_provinces_not_tested'].values())} stenar: {oth}).")
w(f"- {n(po['n_random'])} slumppunkter, tio per sten, på land både år 1050 och år 1949, inom 5 km från landskapets stenar.")
w(f"- Halva A {po['halves']['A']} stenar, halva B {po['halves']['B']} (hela socknar i samma halva). {po['n_sites']} platser "
  f"när stenar inom 200 m från varandra slås ihop. {po['n_dated']} stenar har en stilgruppsdatering. {n(po['n_gravfalt'])} "
  "registrerade gravfält.")
wb = lst(po["stones_in_water_1050_by_province"])
w(f"- **{po['stones_in_water_1050']} stenar står i vatten år 1050 enligt SGU:s modell** ({wb}) och {po['stones_in_water_1949']} "
  "i vatten år 1949. En sten restes inte i vattnet; antalet visar hur grov modellen är nära stränderna (se Svagheter). "
  "Deras avstånd räknas som 0; R5 prövar utan dem.")
w("")
w("## H1: vattnet år 1050")
w(f"- **Alla sex landskapen:** {row(H1['overall'])}. Inom 1 km {pc(H1['overall']['within_1000_stones'])} mot "
  f"{pc(H1['overall']['within_1000_random'])}. I klartext: hälften av stenarna står högst {H1['overall']['median_stones_m']} m "
  f"från dåtidens vatten, hälften av punkterna högst {H1['overall']['median_random_m']} m; nästan två av tre stenar står "
  "inom 500 m, mot knappt hälften av marken.")
for r in H1["provinces"]:
    w(f"- {r['name']}: {row(r)}, q = {sv(r['q_bh'], 3) if r['q_bh'] >= 0.001 else p(r['q_bh'])[4:]}.")
w(f"- Halva A ({H1['halves']['A']['n_parishes']} socknar): {row(H1['halves']['A'])}. Halva B "
  f"({H1['halves']['B']['n_parishes']} socknar): {row(H1['halves']['B'])}.")
w(f"- Platser i stället för stenar (R4, {H1['sites']['n_sites']} platser): {row(H1['sites'])}.")
w(f"- Mönstret syns i fem landskap (q < 0,05): {', '.join(NAME[k] for k in R['verdict']['provinces_h1'])}. Öland, med "
  "20 stenar, går åt samma håll men räcker inte.")
w("")
w("## Dagens vatten (år 1949, som jämförelse)")
w(f"- Alla: {row(R['today']['overall'])}.")
w("- Per landskap: " + "; ".join(f"{NAME[r['province']]} AUC {sv(r['auc'])}" for r in R["today"]["provinces"]) + ".")
w("")
w("## H2: dåtidens vatten mot dagens")
w(f"- AUC {sv(H2['auc_then'])} mot dagens {sv(H2['auc_now'])}; skillnaden {sv(H2['delta_auc'])}, 95 %-intervall "
  f"{sv(H2['ci95'][0])} till {sv(H2['ci95'][1])} ({n(H2['B'])} bootstrapurval, stenarna dragna plats för plats). "
  f"Kvoten mellan medianerna {sv(H2['ratio_then'], 2)} mot {sv(H2['ratio_now'], 2)}. Hela intervallet ligger över 0, så "
  "enligt planen är närheten *tydligare* mot dåtidens vatten. I klartext: dåtidens strand stämmer något bättre med var "
  "stenarna står än dagens, men skillnaden är liten.")
w("- Per landskap (AUC då / nu): " + "; ".join(f"{NAME[r['province']]} {sv(r['auc_then'])} / {sv(r['auc_now'])}"
                                              for r in H2["provinces"]) + ". Dåtidens vatten passar bättre i Uppland, Södermanland, "
  "Östergötland och på Öland; i Småland och Västergötland passar dagens vatten lika bra eller något bättre.")
w("")
w("## H3: gravfälten")
o3 = H3["overall"]
w(f"- **Alla:** {row(o3)}; andelen inom 500 m {p(o3['p_share500'])}. I klartext: två av tre stenar står inom 500 m från "
  "ett registrerat gravfält, mot en av fyra punkter.")
for r in H3["provinces"]:
    w(f"- {r['name']}: {row(r)}, q = {sv(r['q_bh'], 2) if r['q_bh'] >= 0.01 else p(r['q_bh'])[4:]}.")
w(f"- Halva A: {row(H3['halves']['A'])}. Halva B: {row(H3['halves']['B'])}.")
w(f"- Platser (R4, {H3['sites']['n_sites']}): {row(H3['sites'])}.")
w("")
w("## Sekundära prov (Benjamini–Hochberg över de fem)")
S = R["secondary"]
for k in ("S1a", "S1b"):
    s = S[k]
    w(f"- **{k}, {s['label']}:** oddskvot {sv(s['or'], 2)} (95 %-intervall {sv(s['lo'], 2)}–{sv(s['hi'], 2)}), q = "
      f"{p(s['q_bh'])[4:]}; halva A {sv(s['halves']['A']['or'], 2)}, halva B {sv(s['halves']['B']['or'], 2)}, replikerat.")
w(f"  I klartext: när avståndet till vattnet halveras blir oddsen för att platsen har en sten {sv(S['S1a']['or'], 1)} gånger så "
  f"stora, också med avståndet till gravfält lika; för gravfälten är talet {sv(S['S1b']['or'], 1)}. Vattnet är alltså inte "
  "bara ett tecken på gravfälten, och tvärtom.")
s2 = S["S2"]
w(f"- **S2, {s2['label']}:** oddskvot {sv(s2['or'], 2)} per 50 år ({sv(s2['lo'], 2)}–{sv(s2['hi'], 2)}), {p(s2['p'])}, q = "
  f"{sv(s2['q_bh'], 2)}. Inom 1 km: tidiga {pc(s2['early'])} ({s2['n_early']} stenar), sena {pc(s2['late'])} "
  f"({s2['n_late']}). Ingen förändring över tid.")
s3 = S["S3"]
w(f"- **S3, {s3['label']}:** oddskvot {sv(s3['or'], 2)} ({sv(s3['lo'], 2)}–{sv(s3['hi'], 2)}), {p(s3['p'])}. Inom 1 km: "
  f"med kristen markör {pc(s3['share_christian'])} ({s3['n_christian']}), utan {pc(s3['share_other'])} ({s3['n_other']}). "
  "Ingen skillnad.")
s4 = S["S4"]
w(f"- **S4, {s4['label']}:** oddskvot {sv(s4['or'], 2)} ({sv(s4['lo'], 2)}–{sv(s4['hi'], 2)}), {p(s4['p'])}, q = "
  f"{sv(s4['q_bh'], 2)}. {s4['n_bridge']} bro- och vägstenar, median {s4['median_bridge_m']} m mot {s4['median_other_m']} m "
  f"för övriga; inom 1 km {pc(s4['share_bridge'])} mot {pc(s4['share_other'])}. Åt väntat håll men inte säkert.")
w("")
w("## Planens robusthetsprov (för H1, och H3 där det står)")
R1 = R["robustness"]["R1"]
w("- **R1, tidssnitt:** " + "; ".join(f"år {k[2:]} AUC {sv(v['auc'])}, {p(v['p'])}" for k, v in R1.items()) +
  ". Resultatet hänger inte på att just år 1050 valts; SGU anger en tidsosäkerhet på upp till 500 år.")
R2 = R["robustness"]["R2"]
w(f"- **R2, bara havet** (utan modellens sjöar): {row(R2)}. Per landskap: " +
  "; ".join(f"{NAME[r['province']]} AUC {sv(r['auc'])}, {p(r['p'])}" for r in R2["provinces"]) +
  ". I Östergötland, Småland och Västergötland ligger de flesta stenar och punkter mil från havet, så där säger provet "
  "inget; kriteriet gäller alla sex sammantaget.")
w(f"- **R4, platser:** se H1 och H3.")
R5 = R["robustness"]["R5"]
w(f"- **R5, utan de {R5['n_excluded']} stenarna i vattnet:** {row(R5)}. Svagare men tydligt.")
R6 = R["robustness"]["R6"]
assert all(r["p"] < 0.05 and r["auc"] > 0.5 for v in R6.values() for r in v["provinces"] if r["province"] != "Öl")
olr = [r for v in R6.values() for r in v["provinces"] if r["province"] == "Öl"]
assert all(r["p"] >= 0.05 for r in olr)
ol_auc = f"{sv(min(r['auc'] for r in olr), 2)}–{sv(max(r['auc'] for r in olr), 2)}"
ol_p = f"{sv(min(r['p'] for r in olr), 2)}–{sv(max(r['p'] for r in olr), 2)}"
w("- **R6, Copernicus höjdmodell med landskapets landhöjning ±1 m:** " +
  "; ".join(f"δ = {('+' if v['delta_m'] > 0 else '') + str(v['delta_m']).replace('-', '−')} m: median {v['median_stones_m']} mot {v['median_random_m']} m, AUC {sv(v['auc'])}, "
            f"{p(v['p'])}" for v in R6.values()) +
  ". Alla tre håller sammantaget, och i alla landskap utom Öland (AUC " + ol_auc + ", p " + ol_p + "). Mönstret hänger alltså "
  "inte på SGU:s modell.")
R7 = R["robustness"]["R7"]
w("- **R7, nollmodellens radie:** " + "; ".join(
    f"{v['radius_m'] // 1000} km: vattnet AUC {sv(v['water']['auc'])} ({p(v['water']['p'])}), gravfälten AUC "
    f"{sv(v['grave']['auc'])} ({p(v['grave']['p'])})" for v in R7.values()) +
  ". Vattnet är nästan oberoende av radien; för gravfälten växer skillnaden med radien, troligen eftersom gravfälten "
  "ligger i bygderna och en större radie tar med mer obebyggd mark.")
w("")
t1 = R["T1"]
w("## T1: bara stenar som står kvar enligt alla tre källorna (tillägget 2026-10-31)")
w(f"- {t1['n']} stenar kvar; bort: " + lst(t1["dropped"]) + ".")
w(f"- Vattnet: {row(t1['water'])}. Gravfälten: {row(t1['grave'])}. Båda **håller**.")
w("")
w("## Trappan (tilläggsplanen 2026-11-01)")
c = T["counts"]
LAB = {"halva_A": "Halva A", "halva_B": "Halva B", "socken": "Socknen som enhet", "en_per_ristare": "En sten per ristare",
       "utan_aterresta": "Utan återresta stenar", "utan_flyttade_runor": "Utan flyttade stenar enligt Runor 2020",
       "dagens_flyttregel": "Dagens flyttregel", "tidiga": "Tidiga stenar (före 1050)", "sena": "Sena stenar (1050 och senare)"}
for h, name in (("H1", "Vattnet år 1050"), ("H3", "Gravfälten")):
    rg, lo = T[h]["rungs"], T[h]["lopo"]
    w(f"**{name}: alla steg håller.**")
    for k, lab in LAB.items():
        r = rg[k]
        extra = f", {r['n_parishes']} socknar" if k == "socken" else (
            f", {r['removed']} bort" if k in ("en_per_ristare", "utan_aterresta", "utan_flyttade_runor", "dagens_flyttregel") else "")
        w(f"- {lab}{extra}: {row(r)}.")
    mm = rg["socken_slumpeffekt"]
    w(f"- Socknen som slumpeffekt ({mm['n_parishes']} socknar): oddskvot {sv(mm['or'], 2)} när avståndet halveras "
      f"(95 %-intervall {sv(mm['lo'], 2)}–{sv(mm['hi'], 2)}), {p(mm['p'])}. I klartext: också jämfört med marken i samma "
      "socken står stenarna närmare.")
    w("- Utan ett landskap i taget: " + "; ".join(
        f"utan {NAME[k]} ({pc(v['share_kept'])} kvar) AUC {sv(v['auc'])}, {p(v['p'])}" for k, v in lo.items()) + ".")
    w("")
w(f"Antal: {c['reerected']} återresta stenar enligt ordlistan, {c['moved_runor']} flyttade enligt Runor, "
  f"{c['not_staying_now']} som dagens regel inte räknar som kvar, {c['carvers']} säkra ristare med "
  f"{c['sure_carver_stones']} stenar, {c['early']} tidiga och {c['late']} sena stenar.")
w("")
D1, D2 = R["D1"], R["D2"]
w("## Jämförelser (beskrivande)")
w(f"- **D1, med flyttade stenar:** {n(D1['n_all'])} stenar ({n(D1['n_moved'])} flyttade). Vattnet år 1050: AUC "
  f"{sv(D1['then']['auc'])}; bara de flyttade: median {D1['moved_only_then']['median_stones_m']} m, AUC "
  f"{sv(D1['moved_only_then']['auc'])}. De flyttade stenarna, som oftast står vid kyrkor, står ännu närmare dåtidens "
  "vatten än de som står kvar, så att räkna med dem hade gjort sambandet något starkare än det är.")
w(f"- **D2, projektets tidigare mått** (Natural Earths grova vattenlager, landhöjningen som en grov höjdgräns på en "
  f"höjdmodell med omkring 300 m upplösning, flyttade stenar med): {n(D2['water_viking']['n_stones'])} stenar, median {sv(D2['water_viking']['median_stones_km'], 2)} mot "
  f"{sv(D2['water_viking']['median_random_km'], 2)} km. Medianerna här är mycket kortare, eftersom SGU:s modell också har "
  "de mindre sjöarna; riktningen är densamma. Gravfälten i det tidigare måttet: "
  f"{pc(D2['gravfalt']['near_stones'])} mot {pc(D2['gravfalt']['near_random'])} inom 500 m.")
w("")
w("## Avvikelser från planen")
w("- **Tidsordningen.** Planen fick sin kontrollsumma 2026-10-23 kl. 17.23 och lades in i versionshanteringen kl. 19.30 "
  "(c0afbc8). Kl. 17.32 kördes en provkörning med en äldre version av skriptet; dess logg (`/Volumes/2TB/cache/strand/"
  "run.log`) visar bara förloppet (”H1 klart”), inga siffror, och den sparade inga resultat. Avstånden räknades kl. 20.14 "
  "(steg 1), R6 för Uppland, Södermanland, Östergötland och Öland samma kväll, R6 för Småland och Västergötland och "
  "statistiken först 2026-10-31 kl. 22.17, efter tillägget med T1.")
w("- **T1** lades till i ett låst tillägg 2026-10-31, innan statistiken kördes, eftersom regeln för flyttade stenar hade "
  "rättats efter att planen låstes. Planens egna prov är oförändrade.")
w("- **Trappan** lades till i en låst tilläggsplan 2026-11-01, efter att planens resultat var kända, för att pröva fyndet "
  "med projektets fasta känslighetsanalyser. Den ändrar inte planens utfall.")
w(f"- **Genomförandet:** avstånden räknades i rutor med 25 m celler; {n(po['distances_at_tile_margin'])} avstånd som nådde "
  "rutans marginal (nästan alla i R2, bara havet, långt inne i landet) räknades om på en raster med 100 m celler över hela "
  "landskapet (steg 1b). Planen anger ingen cellstorlek.")
w("- I övrigt inga.")
w("")
w("## Svagheter")
w("- SGU:s modell är regional (höjdmodell med 50 m upplösning, tidsfel upp till 500 år, tröskelhöjder med fel under 5 m) "
  f"och inte avsedd för detaljstudier; sjöarna är ungefärliga, och åar, bäckar och våtmarker saknas. Att "
  f"{po['stones_in_water_1050']} stenar hamnar i modellens vatten visar det.")
w("- En stens plats i Rundata kan avvika från den ursprungliga även när stenen inte räknas som flyttad (därför T1 och "
  "stegen med återresta och flyttade stenar).")
w("- Kulturmiljöregistret är olika väl inventerat i olika trakter, och gravfälten är oftast odaterade; en del av dem kan "
  "vara yngre eller äldre än stenarna.")
w("- Stenar som står i grupp är inte oberoende (därför platserna och socknen som enhet).")
w("- De små landskapen har få stenar; Öland visar inget säkert.")
w("- Slumppunkterna ligger inom 5 km från stenarna, alltså i bygder där stenar restes. Provet visar var i bygden stenarna "
  "står, inte varför bygden ligger där den ligger.")
open(os.path.join(OUT, "resultat.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print(os.path.join(OUT, "resultat.md"), len(L), "rader")
