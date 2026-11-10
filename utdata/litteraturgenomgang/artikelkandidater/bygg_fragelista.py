"""Frågelistan ur hela litteraturgenomgången som Excel, färgad efter hur relevant Vitkis bidrag skulle vara för
forskningen. Läser de nio temagruppernas sammanslagna filer (sammanslagen_g1–g9.jsonl, se SAMMANSLAGNING.md), slår ihop
dubbletter mellan grupperna (DUBBLETTER nedan, handgranskade bland de avgörande och betydande), märker liknande rader
bland resten och kopplar varje fråga till en studie i PUBLICERINGSPLAN.md. Viktor 2026-11-10: "markera allt i den
uppdaterade listan med en färg beroende på [hur relevant vårt bidrag skulle vara för forskningen]"; "gör som du föreslår".
    ../../../.venv/bin/python bygg_fragelista.py"""
import glob
import json
import os
import re

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "Forskningsfrågor_Fornvännen_Futhark.xlsx")
SAMLAD = os.path.join(HERE, "fragelista.jsonl")
F = "Arial"
RUST = "B7410E"

# Samma fråga i två eller flera temagrupper: titlarnas början. Den första i varje grupp behåller titeln.
DUBBLETTER = [
    ["Hur många runstenar står egentligen där de restes", "Hur långt flyttades runstenarna"],
    ["Fornminnesregistret ser ojämnt", "Bara där någon letade"],
    ["Tomma platser på kartan", "Saknas stenarna i Dalarna och Sevede", "Är Uppland bara mest letat"],
    ["Hur gamla är runstenarna egentligen? Dateringens kedja", "Hur gamla är runstenarna egentligen? Stilgrupperna mot"],
    ["Var det bara Ingvar", "Österut eller västerut? Färdernas tyngdpunkt"],
    ["Skeppssättningar, storhögar och stenarna", "Ingvars män: var utlandsfararnas gårdar"],
    ["Är stilgrupperna tid eller trakt", "Tid, plats eller hand"],
    ["Hur stor del av de döda", "Elit eller bönder"],
    ["Stod stenarna verkligen vid gravfälten", "Stod stenen vid graven eller på den"],
    ["Lagarna som facit", "Arvet på stenen"],
    ["Gudarnas platser", "Stod stenarna där platsen redan var helig"],
    ["När slutade runstenarna", "När tystnade runstenarna", "Hur startade och slutade runristandet"],
    ["Kom stilen senare till periferin", "Kom stilen senare till skogsbygderna"],
    ["Uppland som norm: hur mycket av runologin", "Uppland som norm: hur mycket vilar", "Uppland som norm, Norrland"],
    ["När hittades stenarna", "Stenar som fortfarande hittas"],
    ["Sagorna som facit: håller Snorre", "Sagorna som facit: samtida"],
    ["Stod stenarna vid gränsen", "Stod stenarna vid råmärket"],
    ["Kom kristendomen österifrån, västerifrån", "Kom kristendomen från England eller Danmark"],
    ["Byggdes kyrkan på hednisk mark", "Byggde man kyrkor vid de gamla gravarna"],
    ["Ortnamnens åldersskikt", "Gården bakom stenen", "Går gårdsnamnen att datera"],
    ["Samma man på två stenar", "Den berömde Torkel"],
    ["Hur många runstenar är bara spöken", "Hagby-fragmenten och dubbelstenarna"],
    ["Flyttades stenarna till kyrkan", "Kyrkan som magnet och som stenbrott", "Stenarna i kyrkans murar"],
    ["Gravhällarna: Östergötlands", "Gravhällarna – kyrkans äldsta"],
]

# Studierna i PUBLICERINGSPLAN.md (omskriven 2026-11-10) och vilka frågor som hör till dem (titlarnas början)
STUDIER = [
    ("dec 2026 – B. Självkontroller", ["Var det bara Ingvar", "Österut eller västerut? Färdernas", "Stod stenarna verkligen vid gravfälten", "Vid vägen – men vilken väg"]),
    ("jan 2027 – A1. Flyttade och försvunna stenar", ["Hur många runstenar står egentligen", "Hur långt flyttades runstenarna", "Hur många runstenar odlade",
                                                     "Hur många runstenar restes egentligen", "När hittades stenarna",
                                                     "Flyttades stenarna till kyrkan", "Hur många runstenar är bara spöken"]),
    ("feb 2027 – A2. Registret och nämnaren", ["Fornminnesregistret ser ojämnt", "Bara där någon letade", "Tomma platser på kartan", "Saknas stenarna i Dalarna", "Hundaret, socknen och byn",
                                               "Var är databasen tom", "Befolkning eller minne", "Uppland som norm",
                                               "Vem skrev av stenarna", "Gravar men inga stenar", "Tre databaser, en sten",
                                               "Varför har Västmanland"]),
    ("mar 2027 – C. Dateringen", ["Hur gamla är runstenarna egentligen", "Ingvars år", "Stil, språk och cirkelresonemang", "Prickarna",
                                  "Är stilgrupperna tid eller trakt", "Kom stilen senare till periferin", "Slutar stilen vid en linje",
                                  "Finns stilgrupperna på riktigt", "När slutade runstenarna", "Kyrkan som daterar stenen"]),
    ("apr 2027 – D. Platserna mot slumpen", ["Gravar, vägar eller gränser", "Stod stenarna vid bron", "Gudarnas platser",
                                             "Stod runstenarna vid tinget", "Husby, Tuna och Hov", "Stod stenarna vid gränsen",
                                             "Stod stenarna där äldre generationer", "Byggdes kyrkan på hednisk mark",
                                             "Handelsplatser eller spannmålsbygder"]),
    ("maj 2027 – E. Korset och bönen", ["Var korset en bekännelse", "När nådde korset", "Kom kristendomen österifrån, västerifrån",
                                        "Hedniskt och kristet", "Kristnades Sverige uppifrån", "Gudarna som tystnade",
                                        "Tog kvinnorna kristendomen"]),
    ("jun 2027 – F. Människorna", ["Lagarna som facit", "Hur stor del av de döda", "Var det de rika", "Hur många av runstenarna reste kvinnor",
                                   "Fanns trälarna", "Kvinnorna som flyttade", "Hade svearna mildare lag", "Stenar över tomma gravar",
                                   "Rik sten, fattig sten", "Skeppssättningar, storhögar", "Var bodde de som for"]),
    ("jul 2027 – Gränserna", ["Götar och svear", "Kolmården", "Svear, götar och danskt", "Gamla folkland och hundare",
                              "Samma karta eller olika"]),
    ("aug 2027 – R. Ristarna", ["Kännarskap mot slumpen", "Åsmund Kåreson", "Öpir", "Vad är en ristares fingeravtryck",
                                "Spreds ristandet som ett mode", "Hur långt reste ristarna", "Samma man på två stenar"]),
    ("sep 2027 – V. Vattnet och landhöjningen", ["Vilket vatten stod stenarna vid", "Hur högt över vattnet", "Ortnamnens åldersskikt",
                                                 "Lera, ås eller kärr"]),
    ("okt 2027 – S. Stenen och silvret", ["Silvret och stenarna", "Var kom stenen ifrån", "Följer stenvågorna odlingen"]),
    ("dec 2027 – K. Kyrkorna", ["Gravhällarna: Östergötlands"]),
    ("2028 – Språkets klockor", ["Försvann R-runan", "Monoftongeringen", "Skrev de som de talade", "Hur mycket av stavningen",
                                 "Småtecknen som klockor", "Skrev kortkvistristarna", "Hur ofta ristade man fel", "Skrev ristarna vers",
                                 "Namn som bara fanns i en bygd"]),
]

LEVEL = {1: "Avgörande", 2: "Betydande", 3: "Användbart", 4: "Begränsat"}
FILL = {1: ("B7410E", "F6D9CC", "FFFFFF"), 2: ("E08A5C", "FBEDE6", "000000"), 3: ("D9C7A0", "FAF6EC", "000000"), 4: ("BDBDBD", "F2F2F2", "000000")}
STOP = set("och i på av om för en ett de den det som till med vid mot eller är var vad hur men från runstenarna stenarna stenar runstenar".split())


def load():
    rows = []
    for fn in sorted(glob.glob(os.path.join(HERE, "sammanslagen_g*.jsonl"))):
        for line in open(fn, encoding="utf-8"):
            line = line.strip()
            if line:
                d = json.loads(line)
                if "titel" in d:
                    d["grupp"] = os.path.basename(fn)[13:-6]
                    rows.append(d)
    return rows


def find(rows, start):
    hit = [r for r in rows if r["titel"].startswith(start)]
    assert len(hit) == 1, (start, [r["titel"] for r in hit])
    return hit[0]


def years(r):
    out = []
    for y in r.get("ar") or []:
        try:
            out.append(int(str(y)[:4]))
        except ValueError:
            pass
    return sorted(set(out))


def merge(rows):
    for group in DUBBLETTER:
        parts = [find(rows, s) for s in group]
        head = min(parts, key=lambda r: (r["relevans"], -len(r.get("pastaenden") or [])))
        for p in parts:
            if p is head:
                continue
            for k in ("pastaenden", "kallor", "ar", "delar"):
                head[k] = list(dict.fromkeys((head.get(k) or []) + (p.get(k) or [])))
            head["relevans"] = min(head["relevans"], p["relevans"])
            head["prio"] = min(head.get("prio") or 3, p.get("prio") or 3)
            head["befintlig"] = head.get("befintlig") or p.get("befintlig")
            head.setdefault("ihopslagen_med", []).append(p["titel"])
            if p.get("relevans_skal") and p["relevans_skal"] not in head.get("relevans_skal", ""):
                head["relevans_skal"] = head.get("relevans_skal", "") + " | " + p["relevans_skal"]
            rows.remove(p)
    for r in rows:
        ys = years(r)
        r["decennier_lista"] = sorted({y // 10 * 10 for y in ys})
        r["antal_texter"] = len({i.split("#")[0] for i in r.get("pastaenden") or []}) or r.get("antal_texter")
        r["antal_pastaenden"] = len(set(r.get("pastaenden") or []))
    return rows


def words(t):
    return {w for w in re.findall(r"[a-zåäöæøþð]{4,}", t.lower()) if w not in STOP}


def similar(rows):
    W = [words(r["titel"] + " " + r.get("fraga", "")) for r in rows]
    for i, r in enumerate(rows):
        best = []
        for j, s in enumerate(rows):
            if i != j:
                inter = len(W[i] & W[j])
                if inter >= 4:
                    best.append((inter / min(len(W[i]), len(W[j])), j))
        best.sort(reverse=True)
        r["liknar"] = [j for f, j in best[:3] if f >= 0.3]


def study(r):
    for label, starts in STUDIER:
        if any(r["titel"].startswith(s) for s in starts):
            return label
    return {1: "Ej placerad – se planen", 2: "2028", 3: "Reservlista", 4: "Reservlista (låg)"}[r["relevans"]]


def dec_text(ds):
    return ", ".join(f"{d}-tal" for d in ds)


def main():
    rows = merge(load())
    rows.sort(key=lambda r: (r["relevans"], r.get("tema", ""), -(r.get("antal_texter") or 0)))
    similar(rows)
    for r in rows:
        r["studie"] = study(r)
    with open(SAMLAD, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: v for k, v in r.items() if k != "liknar"}, ensure_ascii=False) + "\n")
    unplaced = [r["titel"] for r in rows if r["relevans"] == 1 and r["studie"].startswith("Ej")]
    assert not unplaced, unplaced

    wb = Workbook()
    om = wb.active
    om.title = "Om"
    main_ws = wb.create_sheet("Alla frågor")
    HEAD = ["Nr", "Relevans", "Nivå", "Titel", "Vad vi prövar", "Tema", "Vad det betyder för forskningen", "Varför läsare bryr sig",
            "Studie i planen", "Årtionden", "Antal årtionden", "Antal texter", "Antal påståenden", "Data", "Mätbart", "Omfång",
            "Källor (urval)", "Fanns i första listan (nr)", "Ihopslagen med", "Liknande rader (nr)", "Temagrupp"]
    WID = [5, 9, 12, 44, 60, 18, 64, 44, 26, 30, 9, 9, 10, 32, 9, 20, 46, 10, 34, 12, 8]
    main_ws.append(HEAD)
    for n, r in enumerate(rows, start=1):
        rr = n + 1
        main_ws.append([n, r["relevans"], f'=INDEX(Om!$A$12:$A$15,B{rr})', r["titel"], r.get("fraga", ""), r.get("tema", ""),
                        r.get("relevans_skal", ""), r.get("varfor", ""), r["studie"], dec_text(r["decennier_lista"]),
                        len(r["decennier_lista"]), r.get("antal_texter"), r.get("antal_pastaenden"), r.get("data", ""), r.get("matbart", ""),
                        r.get("omfang", ""), "; ".join((r.get("kallor") or [])[:14]), r.get("befintlig"),
                        "; ".join(r.get("ihopslagen_med", [])), ", ".join(str(j + 1) for j in r["liknar"]), r["grupp"]])
    last = main_ws.max_row
    thin = Side(style="thin", color="D9D2C5")
    for row in main_ws.iter_rows(min_row=1, max_row=last):
        for c in row:
            c.font = Font(name=F, size=10)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = Border(bottom=thin)
    for c in main_ws[1]:
        c.font = Font(name=F, size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=RUST)
        c.alignment = Alignment(wrap_text=True, vertical="center")
    main_ws.row_dimensions[1].height = 34
    for rr in range(2, last + 1):
        main_ws.cell(rr, 4).font = Font(name=F, size=10, bold=True)
        for col in (1, 2, 11, 12, 13, 18):
            main_ws.cell(rr, col).alignment = Alignment(horizontal="center", vertical="top")
    for c, w in enumerate(WID, start=1):
        main_ws.column_dimensions[get_column_letter(c)].width = w
    main_ws.freeze_panes = "E2"
    main_ws.auto_filter.ref = f"A1:{get_column_letter(len(HEAD))}{last}"
    rng = f"A2:{get_column_letter(len(HEAD))}{last}"
    for lv, (strong, tint, txt) in FILL.items():
        main_ws.conditional_formatting.add(f"B2:C{last}", FormulaRule(formula=[f"$B2={lv}"], fill=PatternFill("solid", fgColor=strong),
                                                                       font=Font(name=F, bold=True, color=txt)))
        main_ws.conditional_formatting.add(rng, FormulaRule(formula=[f"$B2={lv}"], fill=PatternFill("solid", fgColor=tint)))
    dv = DataValidation(type="list", formula1='"1,2,3,4"', allow_blank=False)
    main_ws.add_data_validation(dv)
    dv.add(f"B2:B{last}")

    # Sammanfattning: tema × relevans, med formler
    s = wb.create_sheet("Sammanfattning")
    s["A1"] = "Frågorna per tema och relevans"
    s["A1"].font = Font(name=F, size=13, bold=True, color=RUST)
    s.append([])
    s.append(["Tema", "Avgörande", "Betydande", "Användbart", "Begränsat", "Totalt"])
    temas = sorted({r.get("tema", "") for r in rows})
    for t in temas:
        rr = s.max_row + 1
        s.append([t] + [f"=COUNTIFS('Alla frågor'!$F$2:$F${last},$A{rr},'Alla frågor'!$B$2:$B${last},{lv})" for lv in (1, 2, 3, 4)]
                 + [f"=SUM(B{rr}:E{rr})"])
    rr = s.max_row + 1
    s.append(["Totalt"] + [f"=SUM({get_column_letter(c)}4:{get_column_letter(c)}{rr - 1})" for c in range(2, 7)])
    s.append([])
    s.append(["Studie i planen", "Avgörande", "Betydande", "Användbart", "Begränsat", "Totalt"])
    hdr2 = s.max_row
    for label in [x for x, _ in STUDIER] + ["2028", "Reservlista", "Reservlista (låg)"]:
        r2 = s.max_row + 1
        s.append([label] + [f"=COUNTIFS('Alla frågor'!$I$2:$I${last},$A{r2},'Alla frågor'!$B$2:$B${last},{lv})" for lv in (1, 2, 3, 4)]
                 + [f"=SUM(B{r2}:E{r2})"])
    for row in s.iter_rows(min_row=2, max_row=s.max_row):
        for c in row:
            c.font = Font(name=F, size=10)
    for hr in (3, hdr2):
        for c in s[hr]:
            c.font = Font(name=F, size=10, bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=RUST)
    for c in s[rr]:
        c.font = Font(name=F, size=10, bold=True)
    for col, (strong, _, txt) in zip("BCDE", [FILL[i] for i in (1, 2, 3, 4)]):
        for hr in (3, hdr2):
            s[f"{col}{hr}"].fill = PatternFill("solid", fgColor=strong)
            s[f"{col}{hr}"].font = Font(name=F, size=10, bold=True, color=txt)
    s.column_dimensions["A"].width = 44
    for col in "BCDEF":
        s.column_dimensions[col].width = 13

    # En flik per tema (kopior; huvudlistan är Alla frågor)
    short = {"Bevarande och källkritik": "Bevarande", "Datering och kronologi": "Datering", "Ekonomi och silver": "Ekonomi",
             "Gränser och regioner": "Gränser", "Kontakter och resor": "Kontakter", "Landskap och platser": "Landskap",
             "Makt och samhälle": "Makt", "Metod och nollmodeller": "Metod", "Ristare och verkstäder": "Ristare",
             "Språk och runor": "Språk", "Stenen som föremål": "Stenen", "Vägar och vatten": "Vägar och vatten",
             "Andra föremål": "Andra föremål", "Forskningshistoria": "Forskningshistoria", "Människor": "Människor", "Tro och kult": "Tro och kult"}
    TH = ["Nr", "Relevans", "Titel", "Vad vi prövar", "Vad det betyder för forskningen", "Studie i planen", "Årtionden", "Antal texter"]
    for t in temas:
        ws = wb.create_sheet(short.get(t, t)[:31])
        ws.append(TH)
        for n, r in enumerate(rows, start=1):
            if r.get("tema") == t:
                ws.append([n, LEVEL[r["relevans"]], r["titel"], r.get("fraga", ""), r.get("relevans_skal", ""), r["studie"],
                           dec_text(r["decennier_lista"]), r.get("antal_texter")])
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
            for c in row:
                c.font = Font(name=F, size=10)
                c.alignment = Alignment(wrap_text=True, vertical="top")
        for c in ws[1]:
            c.font = Font(name=F, size=10, bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=RUST)
        for rr2 in range(2, ws.max_row + 1):
            lv = {v: k for k, v in LEVEL.items()}[ws.cell(rr2, 2).value]
            strong, tint, txt = FILL[lv]
            ws.cell(rr2, 2).fill = PatternFill("solid", fgColor=strong)
            ws.cell(rr2, 2).font = Font(name=F, size=10, bold=True, color=txt)
            for col in range(3, len(TH) + 1):
                ws.cell(rr2, col).fill = PatternFill("solid", fgColor=tint)
            ws.cell(rr2, 3).font = Font(name=F, size=10, bold=True)
        for c, w in enumerate([5, 12, 44, 60, 64, 26, 30, 9], start=1):
            ws.column_dimensions[get_column_letter(c)].width = w
        ws.freeze_panes = "C2"

    # Om
    n_claims = sum(1 for _ in open(os.path.join(os.path.dirname(HERE), "pastaenden.jsonl"), encoding="utf-8"))
    info = [
        ("Forskningsfrågor ur Fornvännen och Futhark", None),
        ("Vitki, sammanställd 10 november 2026", None),
        (None, None),
        ("Underlag", f"Alla {n_claims:,} mätbara påståenden".replace(",", " ") + " ur 1 577 lästa texter i Fornvännen 1906–2023 och Futhark 1–15. "
         "Påståendena grupperades först i 16 tidsdelar (732 artikelkandidater), slogs sedan ihop per tema (9 grupper) och till sist "
         f"mellan grupperna. Resultat: {len(rows)} frågor."),
        ("Relevans", "Hur relevant Vitkis bidrag skulle vara för forskningen, inte hur ny frågan är. Bedömt utifrån vad som hänger på "
         "svaret, om det finns en levande debatt, om Vitkis data kan ge ett svar och om någon redan har avgjort frågan. Vid tvekan "
         "valdes den lägre nivån."),
        ("Färgerna", "Raden färgas efter kolumn B. Ändrar du relevansen (1–4) ändras färgen och sammanfattningen."),
        (None, None),
        ("Studie i planen", "Den låsta studie i PUBLICERINGSPLAN.md (omskriven 10 nov 2026) som frågan hör till. Alla avgörande frågor "
         "ligger i 2027. Betydande som inte har en studie ligger i 2028; användbara och begränsade är reservlistan för fria luckor."),
        ("Viktigt om källorna", "Källor och motiveringar är skrivna av läsare (AI) ur påståendena och sökindexet. Läsarkontrollen visade att "
         "76 % av påståendena var rätt återgivna, och några motiveringar nämner litteratur ur minnet. Kontrollera varje källa mot "
         "originaltexten innan något citeras eller byggs på."),
        (None, None),
        ("Nivå", "Betyder"),
        (LEVEL[1], "Vitkis svar skulle avgöra en långvarig debatt eller pröva ett antagande som många andra resultat vilar på."),
        (LEVEL[2], "Nya, starka belägg i en aktiv fråga inom ett fält; skulle citeras och kunna ändra hur frågan diskuteras."),
        (LEVEL[3], "Kompletterar, nyanserar eller bekräftar med hela korpusen; värdefullt men med begränsad räckvidd."),
        (LEVEL[4], "Främst intressant för en bred publik, eller Vitkis data räcker inte för att säga mycket."),
        (None, None),
        ("Filer", "utdata/litteraturgenomgang/artikelkandidater/ (kandidater_*.jsonl, sammanslagen_g*.jsonl, fragelista.jsonl, "
         "bygg_fragelista.py); påståendena i pastaenden.jsonl."),
    ]
    for k, v in info:
        om.append([k, v])
    om["A1"].font = Font(name=F, size=13, bold=True, color=RUST)
    for row in om.iter_rows(min_row=2, max_row=om.max_row):
        for c in row:
            c.font = Font(name=F, size=10, bold=c.column == 1)
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, lv in enumerate((1, 2, 3, 4)):
        strong, tint, txt = FILL[lv]
        om.cell(12 + i, 1).fill = PatternFill("solid", fgColor=strong)
        om.cell(12 + i, 1).font = Font(name=F, size=10, bold=True, color=txt)
        om.cell(12 + i, 2).fill = PatternFill("solid", fgColor=tint)
    assert om["A12"].value == LEVEL[1] and om["A15"].value == LEVEL[4]
    om["A2"].font = Font(name=F, size=10, italic=True)
    om.column_dimensions["A"].width = 22
    om.column_dimensions["B"].width = 110

    wb.active = 1
    wb.calculation.fullCalcOnLoad = True
    wb.save(OUT)
    from collections import Counter
    print(OUT, len(rows), "frågor", Counter(r["relevans"] for r in rows), Counter(r["studie"] for r in rows if r["relevans"] <= 2))


if __name__ == "__main__":
    main()
