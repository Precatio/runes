"""AI-bedömningen av stilgrupp (api/routers/twod.py, samma systemprompt och schema som appen) prövad mot Rundata.

Underlag: svenska vikingatida runstenar med säker stilgrupp i Rundata och en fritt licensierad bild i Wikidata
(wikidata_bilder.json, 827 stenar). Bilden hämtas i 1200 px bredd från Commons (samma tumnagel som artiklarna använder).
Urvalet är stratifierat: lika många per stilgrupp (--per-grupp), slumpat med fast frö, så att RAK och Pr4 inte dominerar.
Varje svar sparas rad för rad (resultat.jsonl) och skriptet kan köras om utan att betala för redan bedömda stenar.
    ANTHROPIC_API_KEY=… .venv/bin/python utdata/stilgrupp_ai/stilgrupp_test.py --per-grupp 15
    .venv/bin/python utdata/stilgrupp_ai/stilgrupp_test.py --utvardera        # bara sammanställningen
"""
import argparse
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
HERE = os.path.dirname(os.path.abspath(__file__))
BILDER = os.path.join(HERE, "bilder")
RES = os.path.join(HERE, "resultat.jsonl")
CODES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]  # KB bedömer inte appen; Rundatas KB-stenar utelämnas
# Appens instruktion och schema som de var när provet gjordes (stilbedömningen togs bort ur appen 2026-10-20)
from pydantic import BaseModel  # noqa: E402
from typing import Literal  # noqa: E402
from src.styles import STYLE_GROUPS  # noqa: E402


class Marker(BaseModel):
    label: str
    description: str
    polygon: list[list[int]]


class TwoDAIResult(BaseModel):
    predicted_style: Literal["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5", "Osäker"]
    confidence: int
    reasoning: str
    rune_types: str
    markers: list[Marker]


STYLE_REFERENCE = "\n".join(
    f"- {g['code']}: {g['features']}" + (f" (ca {g['from']}–{g['to']})" if g["from"] else "")
    for g in STYLE_GROUPS if g["code"] != "KB"
)

SYSTEM_INSTRUCTION = """
Du är en expert-runolog och epigrafiker som specialiserar sig på paleografi och ornamentik på svenska runstenar.
I din stilanalys (ornamentik) utgår du ifrån Anne-Sofie Gräslunds kronologiska metoder.
Din uppgift är att analysera en uppladdad 2D-bild (ett foto eller en uppmålning) av en runsten.

Du måste identifiera vilken av Anne-Sofie Gräslunds stilgrupper (RAK, Fp, Pr1, Pr2, Pr3, Pr4, Pr5) som stenen med störst sannolikhet tillhör.
Använd koderna exakt så (RAK, Fp, Pr1–Pr5). Om bilden inte visar ornamentik som går att bedöma, svara "Osäker". Referens (ungefärliga dateringar som överlappar):
""" + STYLE_REFERENCE + """
Om bilden innehåller ett rundjur med huvud är det ALDRIG Rak. Var noggrann och variera din bedömning baserat på faktiska visuella bevis i bilden. Undvik att defaulta till Rak.

Din uppskattning genererar även en procentsats (confidence). Den visas som en okalibrerad självskattning. Ange ett realistiskt värde (t.ex. 40-90%) baserat på bildens tydlighet, var inte överdrivet säker (95%) om bilden är suddig eller svårtolkad.

I fältet "reasoning" (Epigrafisk motivering) MÅSTE du vara mycket utförlig. Analysera eventuella drakhuvuden, ögonform, fotflikar och bandens dragning grundligt, eller avsaknaden av dessa.

Du måste även identifiera runtyperna som används på stenen. I fältet "rune_types" beskriv de distinkta paleografiska dragen.

När du identifierar nyckeldetaljer (t.ex. drakhuvud, svans, rakt bandavslut, specifik runa), inkludera dessa i "markers"-listan. 
Du SKA sträva efter att inkludera så många relevanta markörer som möjligt (gärna 5-10 stycken om bilden tillåter) för att bygga ett massivt och detaljerat visuellt bevis för din bedömning. Markera ögon, öron, nosflikar, fötter, svansar, ormöglor, kors och särpräglade runor separat.
För varje markör (marker), ange en 'label' (t.ex. "Drakhuvud - Mandelformat öga"), en mycket djupgående och detaljerad 'description' (t.ex. "Ett tydligt mandelformat öga med utdragen snibb som är starkt indikativt för stil Pr3, placerat strax bakom nospartiet."), och dess utbredning i 'polygon' med en lista av koordinater i formatet [[y1, x1], [y2, x2], ...] normaliserat till 0-1000. Sätt ut tillräckligt med punkter (minst 4, men gärna fler) så att polygonen noggrant följer den visuella formen du markerar istället för att bara vara en inexakt rektangel.
Exempel på polygon: [[150, 200], [150, 400], [250, 420], [300, 400], [300, 200]] för en mer oregelbunden form.

Du måste svara EXAKT enligt det angivna JSON-schemat.
"""


UA = {"User-Agent": "Vitki/1.0 (vitkirunor.se; forskning) python-requests"}


def urval(per_grupp: int, fro: int = 20261020) -> list[tuple[str, str, str]]:
    d = json.load(open(os.path.join(HERE, "wikidata_bilder.json")))
    rng = random.Random(fro)
    by = defaultdict(list)
    for sg, f in d["files"].items():
        st = d["style"][sg]
        if st in CODES:
            by[st].append((sg, st, f))
    out = []
    for st in CODES:
        rows = sorted(by[st])
        rng.shuffle(rows)
        out += rows[:per_grupp]
    return out


def hamta_bild(signum: str, fil: str) -> str | None:
    """Bilden från Commons, högst 1600 px, sparad lokalt; väntar och försöker igen vid 429 (Wikimedias takbegränsning)."""
    from io import BytesIO
    from PIL import Image
    from src import commons
    os.makedirs(BILDER, exist_ok=True)
    path = os.path.join(BILDER, commons.re.sub(r"[^\w]+", "_", signum) + ".jpg")
    if os.path.exists(path):
        return path
    info = commons.commons_info([fil]).get(fil)
    if not info or not info.get("thumb"):
        return None
    for forsok in range(4):
        r = requests.get(info["thumb"], headers=UA, timeout=90)
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After") or 15) * (forsok + 1))
            continue
        if r.status_code != 200 or len(r.content) < 2000:
            return None
        try:
            im = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            return None
        if max(im.size) > 1600:
            im.thumbnail((1600, 1600))
        im.save(path, "JPEG", quality=90)
        time.sleep(2)  # artigt mot Commons
        return path
    return None


def bedom(path: str, ctx) -> dict:
    from api import llm
    r = llm.generate(ctx, "Analysera denna runsten paleografiskt och epigrafiskt.", system=SYSTEM_INSTRUCTION,
                     images=[(open(path, "rb").read(), "image/jpeg")], schema=TwoDAIResult, tier="pro")
    return {"predicted": r.data.get("predicted_style"), "confidence": r.data.get("confidence"),
            "reasoning": (r.data.get("reasoning") or "")[:600], "tokens": r.tokens, "model": r.model}


def kor(per_grupp: int):
    from api import llm
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    assert key, "Sätt ANTHROPIC_API_KEY (din egen nyckel ur appens inställningar) i miljön eller .env"
    ctx = llm.AIContext("claude", key)
    done = {json.loads(l)["signum"] for l in open(RES) if json.loads(l).get("predicted")} if os.path.exists(RES) else set()
    rows = urval(per_grupp)
    print(f"{len(rows)} stenar i urvalet, {len(done)} redan bedömda")
    fel_i_rad = 0
    with open(RES, "a") as out:
        for i, (sg, st, fil) in enumerate(rows):
            if sg in done:
                continue
            path = hamta_bild(sg, fil)
            if not path:
                out.write(json.dumps({"signum": sg, "rundata": st, "file": fil, "error": "ingen bild"}, ensure_ascii=False) + "\n")
                continue
            try:
                res = bedom(path, ctx)
                fel_i_rad = 0
            except Exception as e:
                res = {"error": str(e)[:300]}
                fel_i_rad += 1
                text = str(e).lower()
                if fel_i_rad >= 3 or any(k in text for k in ("credit", "billing", "insufficient", "401", "402", "authentication")):
                    out.write(json.dumps({"signum": sg, "rundata": st, "file": fil, **res}, ensure_ascii=False) + "\n")
                    print("stoppar: nyckeln eller krediten verkar vara slut:", str(e)[:200])
                    break
                time.sleep(5)
            out.write(json.dumps({"signum": sg, "rundata": st, "file": fil, **res}, ensure_ascii=False) + "\n")
            out.flush()
            print(f"{i + 1}/{len(rows)} {sg}: Rundata {st} → AI {res.get('predicted')} ({res.get('confidence')} %, {res.get('tokens')} tokens)")


def utvardera():
    rows = [json.loads(l) for l in open(RES)]
    ok = [r for r in rows if r.get("predicted")]
    errs = [r for r in rows if not r.get("predicted")]
    n = len(ok)
    exact = sum(r["predicted"] == r["rundata"] for r in ok)
    unsure = sum(r["predicted"] == "Osäker" for r in ok)
    decided = [r for r in ok if r["predicted"] != "Osäker"]
    exact_d = sum(r["predicted"] == r["rundata"] for r in decided)
    # Grova klasser: RAK | Fp | Pr1–2 (Ringerike) | Pr3–5 (Urnes)
    grov = {"RAK": "RAK", "Fp": "Fp", "Pr1": "Ringerike", "Pr2": "Ringerike", "Pr3": "Urnes", "Pr4": "Urnes", "Pr5": "Urnes"}
    grov_ok = sum(grov.get(r["predicted"]) == grov[r["rundata"]] for r in decided)
    # Grannfel: en stilgrupp intill i Gräslunds serie räknas som "nära"
    order = {c: i for i, c in enumerate(CODES)}
    near = sum(abs(order[r["predicted"]] - order[r["rundata"]]) <= 1 for r in decided if r["predicted"] in order)
    conf = defaultdict(Counter)
    for r in ok:
        conf[r["rundata"]][r["predicted"]] += 1
    # Slumpnivå för exakt grupp med urvalets fördelning, och majoritetsgissning
    maj = Counter(r["rundata"] for r in ok).most_common(1)[0][1] / n if n else 0
    # Kalibrering: träff per självskattad säkerhet
    kal = defaultdict(lambda: [0, 0])
    for r in decided:
        b = "<60" if (r.get("confidence") or 0) < 60 else "60–79" if r["confidence"] < 80 else "≥80"
        kal[b][0] += r["predicted"] == r["rundata"]
        kal[b][1] += 1
    tokens = [r["tokens"] for r in ok if r.get("tokens")]
    out = {"n": n, "fel": len(errs), "exakt": exact / n if n else None, "osaker": unsure / n if n else None,
           "exakt_bland_avgjorda": exact_d / len(decided) if decided else None, "grov_bland_avgjorda": grov_ok / len(decided) if decided else None,
           "inom_en_grupp_bland_avgjorda": near / len(decided) if decided else None, "majoritetsgissning": maj,
           "slump_exakt": 1 / len(CODES), "forvaxling": {k: dict(v) for k, v in conf.items()},
           "kalibrering": {k: {"ratt": v[0], "n": v[1], "andel": v[0] / v[1]} for k, v in kal.items()},
           "tokens_medel": sum(tokens) / len(tokens) if tokens else None, "modell": ok[0]["model"] if ok else None}
    json.dump(out, open(os.path.join(HERE, "utvardering.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-grupp", type=int, default=15)
    ap.add_argument("--utvardera", action="store_true")
    a = ap.parse_args()
    if not a.utvardera:
        kor(a.per_grupp)
    utvardera()
