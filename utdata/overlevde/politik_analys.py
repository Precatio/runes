"""Tillägget om maktens titlar och de politiska områdena (beskrivande, inte i den låsta planen): kodningen med belägg
ur politik_underlag.json (svenska och engelska Wiktionary, svenska Wikipedia) och summorna som artikeln låses mot.
    .venv/bin/python utdata/overlevde/politik_analys.py      Skriver politik.json och politik_kodning.csv."""
import csv
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))
U = json.load(open(os.path.join(OUT, "politik_underlag.json"), encoding="utf-8"))
ST = {x["lemma"]: x["stones"] for x in U["titles"]}
AR = {x["area"]: x["stones"] for x in U["areas"]}
# Titles that are a personal name on some stone: only the stones where the word is the title
ST["jarl"] = [s for s in ST["jarl"] if s != "U 498"]  # <iarlR> on U 498 is an uninterpreted name

# lever = in today's Swedish with the same core meaning; sjönk = lives with a lower meaning; historisk = only as a
# historical term; borta = no descendant in Swedish
TITLES = {
    "konungr": ("lever", "kung", "sv.wiktionary: manligt statsöverhuvud i en monarki"),
    "styrimaðr": ("lever", "styrman", "sv.wiktionary: person som styr ett fartyg"),
    "skipari": ("lever", "skeppare", "sv.wiktionary: befälhavare på ett mindre fartyg"),
    "þingstaðr": ("lever", "ting", "sv.wiktionary: juridik, beslutsmöte; tingsrätt sedan 1971 (sv.wikipedia Tingsrätt)"),
    "drengr": ("sjönk", "dräng", "sv.wiktionary: fornsv. drænger 'ung man, tjänare'; sv.wikipedia: anställd i jordbruket"),
    "jarl": ("historisk", "jarl", "sv.wikipedia Jarl: ämbetet avskaffat 1308, siste store innehavaren Birger jarl d. 1266; riksjarl = dux regni, 'rikets hertig'"),
    "stallari": ("historisk", "stallare", "sv.wikipedia Stallare: ersattes under 1200-talet av marsken"),
    "bryti": ("historisk", "bryte", "sv.wikipedia Bryte: nordisk titel under folkvandringstid och vikingatid"),
    "húskarl": ("historisk", "huskarl", "inget uppslag i sv.wiktionary; sv.wikipedia under Hird"),
    "hundari": ("historisk", "hundare", "sv.wikipedia Härad: hundare undanträngdes under unionstiden av ordet härad"),
    "dróttinn": ("historisk", "drott", "sv.wiktionary drott: taggat historia; lever i drottning; på runstenarna alltid om Gud"),
    "þegn": ("borta", "", "ingen svensk ättling (sv.wikipedia Tegn; jfr eng. thane)"),
    "landmaðr": ("borta", "", "ingen svensk ättling"),
    "hersir": ("borta", "", "ingen svensk ättling; läsningen på Sö 136 är osäker"),
    "þingalið": ("borta", "", "ingen svensk ättling: Knut den stores livgarde i England"),
    "liðs forungi": ("borta", "", "ingen svensk ättling ('följets anförare')"),
}
# The medieval words for power: origin by Wiktionary
NEW = {
    "hertig": ("lån", "sv.wiktionary: belagt sedan 1285, fornsv. hærtogher av lågtyska hertoch"),
    "greve": ("lån", "sv.wiktionary: av lågtyska grēve"),
    "marsk": ("lån", "sv.wiktionary: av lågtyska marschalk 'stallmästare'; sv.wikipedia: i Sverige först 1268"),
    "fogde": ("lån", "sv.wiktionary: av latinets vocatus (en.wiktionary: via lågtyska voget)"),
    "riddare": ("lån", "en.wiktionary: av lågtyska ridder"),
    "kansler": ("lån", "en.wiktionary: av fornfranska cancelier, medeltidslatin cancellarius"),
    "riksdag": ("lån", "en.wiktionary: översättningslån av tyskans Reichstag"),
    "biskop": ("lån", "sv.wiktionary: av grekiska episkopos (genom kyrkan)"),
    "präst": ("lån", "en.wiktionary: fornsv. præster, fornvästnordiska prestr (latinets presbyter, genom kyrkan)"),
    "frälse": ("nordiskt", "sv.wiktionary: fornsv. frælse; sv.wikipedia: Alsnö stadga 1280"),
    "härad": ("nordiskt", "sv.wiktionary: fornvästnordiska hærað"),
    "lagman": ("nordiskt", "en.wiktionary: fornvästnordiska lǫgmaðr; sv.wiktionary: titeln återupprättades 1971"),
    "socken": ("nordiskt", "sv.wiktionary: fornvästnordiska sókn"),
    "ledung": ("nordiskt", "sv.wiktionary: fornvästnordiska leiðangr"),
    "adel": ("nordiskt", "en.wiktionary: fornsv. aþal, fornvästnordiska aðal, starkt påverkat av lågtyska adel"),
}
# Areas: samma = the same name in Swedish today; historisk = the name lives only for a historical region;
# bytt = the Swedish name today is another, or the place is gone
AREAS = {
    "England": ("samma", "England"), "Danmork": ("samma", "Danmark"), "Gotland": ("samma", "Gotland"),
    "Skáney": ("samma", "Skåne"), "Frísar": ("samma", "Friesland"), "Bað": ("samma", "Bath"),
    "Eistland": ("samma", "Estland"), "Finnland": ("samma", "Finland"), "Tafeistaland": ("samma", "Tavastland"),
    "Semgallar": ("samma", "Semgallen"), "Domisnes": ("samma", "Domesnäs"),
    "Virland": ("historisk", "Wierland (Virumaa)"), "Lífland": ("historisk", "Livland"),
    "Svíþjóð": ("bytt", "Sverige"), "Garðar": ("bytt", "Ryssland (Kievriket)"), "Holmgarðr": ("bytt", "Novgorod"),
    "Grikkland / Grikkir": ("bytt", "Bysantinska riket"), "Langbarðaland": ("bytt", "Italien"),
    "Serkland": ("bytt", "kalifatet (inget nutida namn)"), "Jórsalir": ("bytt", "Jerusalem"),
    "Saxland": ("bytt", "Tyskland"), "Heiðabýr": ("bytt", "Hedeby, övergivet"),
}
assert set(TITLES) == set(ST) and set(AREAS) == set(AR)

rows = [{"slag": "titel", "namn": k, "stenar": len(ST[k]), "kod": c, "i_dag": m, "belägg": b, "signa": " ".join(ST[k])}
        for k, (c, m, b) in TITLES.items()]
rows += [{"slag": "ny titel", "namn": k, "stenar": 0, "kod": c, "i_dag": k, "belägg": b, "signa": ""} for k, (c, b) in NEW.items()]
rows += [{"slag": "område", "namn": k, "stenar": len(AR[k]), "kod": c, "i_dag": m, "belägg": "", "signa": " ".join(AR[k])}
         for k, (c, m) in AREAS.items()]
with open(os.path.join(OUT, "politik_kodning.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


def by(code_map, stones):
    out = {}
    for k, v in code_map.items():
        out.setdefault(v[0], []).append(k)
    return {c: {"words": ks, "n": len(ks), "stones": len({s for k in ks for s in stones[k]})} for c, ks in out.items()}


res = {"titles": by(TITLES, ST), "n_titles": len(TITLES),
       "title_stones": {k: len(v) for k, v in ST.items()},
       "new": {c: [k for k, v in NEW.items() if v[0] == c] for c in ("lån", "nordiskt")},
       "areas": by(AREAS, AR), "n_areas": len(AREAS), "area_stones": {k: len(v) for k, v in AR.items()},
       "area_any_stones": len({s for v in AR.values() for s in v})}
json.dump(res, open(os.path.join(OUT, "politik.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("titles", "new", "areas", "area_any_stones")}, ensure_ascii=False, indent=0))
