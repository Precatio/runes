"""Vitkis ifyllningar: ett eget lager ovanpå Rundata för förlorade runor som Vitki har fyllt i.

Rundata ändras aldrig. En ifyllning sparas i data/vitki_ifyllningar.json (vår egen data, CC BY 4.0, följer med i git)
med luckans läge, de bevarade runorna, ifyllningen och ordet, metoden (sannolikhetsmodellen, spår ur skanningen eller
utgivarens läsning), modellversion och sannolikhet, belägg (SRI-sida, skanning, Runor 2020) och en status med historik:
förslag, bekräftad eller avvisad, med vem, datum och kommentar för varje steg.

Analyserna använder Rundata som förval. Där det är meningsfullt kan de bekräftade ifyllningarna slås på (apply_words),
och resultatet säger det. Sannolikhetsmodellen (src/runlm.py, src/textmodel.py och proven i scripts/) läser aldrig den
här filen: modellen skulle annars tränas eller prövas på sina egna svar. Records som bär en ifyllning är märkta
(FILLED_MARK), och runlm.Model vägrar ta emot dem (tests/test_vitki_fills.py)."""
from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(ROOT, "data", "vitki_ifyllningar.json")
LICENSE = "CC BY 4.0"
FILLED_MARK = "_vitki_filled"  # set on a copy of a record that carries Vitki's fillings; runlm.Model refuses these

STATUSES = ("förslag", "bekräftad", "avvisad")
METHODS = ("sannolikhetsmodellen", "spår ur skanningen", "utgivarens läsning")
EVIDENCE_KINDS = ("sri", "skanning", "runor2020", "annat")
EVIDENCE_LABEL = {"sri": "SRI", "skanning": "skanning", "runor2020": "Runor 2020", "annat": "annat"}
SHOWN = ("förslag", "bekräftad")  # avvisade ifyllningar visas inte på stensidan, men finns kvar i filen

_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _empty() -> dict:
    return {"_om": "Vitkis ifyllningar av förlorade runor (src/vitki_fills.py), ett eget lager ovanpå Rundata som "
                   "aldrig ändras. Sannolikhetsmodellen tränas och prövas aldrig på dem.",
            "licens": LICENSE, "fills": []}


def load(path: str | None = None) -> dict:
    p = path or FILE
    if not os.path.exists(p):
        return _empty()
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("fills", [])
    return data


def _save(data: dict, path: str | None = None):
    p = path or FILE
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=os.path.dirname(p), suffix=".tmp", delete=False) as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(fh.name, p)


def _who(user: dict) -> str:
    return user.get("email") or user.get("name") or user.get("uid") or "okänd"


def _evidence(xs) -> list[dict]:
    out = []
    for x in xs or []:
        kind, ref = (x.get("kind") or "").strip(), (x.get("ref") or "").strip()
        if kind not in EVIDENCE_KINDS:
            raise ValueError(f"Okänt slag av belägg: {kind!r} (ett av {', '.join(EVIDENCE_KINDS)}).")
        if not ref:
            raise ValueError("Ett belägg behöver en hänvisning (sida, fil eller länk).")
        out.append({"kind": kind, "ref": ref[:500]})
    return out


def check(entry: dict) -> None:
    """Raises ValueError when a filling cannot be stored: wrong status or method, a missing comment, or runes that do
    not fit the gap (as many as the lost runes assumed, the preserved runes inside the gap kept)."""
    if entry.get("status") not in STATUSES:
        raise ValueError(f"Status måste vara en av: {', '.join(STATUSES)}.")
    if entry.get("method") not in METHODS:
        raise ValueError(f"Metoden måste vara en av: {', '.join(METHODS)}.")
    if not (entry.get("comment") or "").strip():
        raise ValueError("En kommentar krävs.")
    gap, fill = entry.get("gap") or {}, entry.get("fill") or ""
    if not fill or not re.fullmatch(r"[a-zþðæøåöäąR]+", fill):
        raise ValueError("Ifyllningen måste vara runor i Rundatas translitterering.")
    if len(fill) != gap.get("width", len(fill)):
        raise ValueError("Ifyllningen har inte lika många runor som luckan.")
    for i, ch in enumerate(gap.get("preserved_inside") or []):
        if ch and fill[i] != ch:
            raise ValueError("Ifyllningen ändrar en bevarad runa inne i luckan.")


def add(entry: dict, user: dict, path: str | None = None) -> dict:
    """Stores a new filling (status förslag or bekräftad) and returns it with id and history."""
    if entry.get("status") == "avvisad":
        raise ValueError("En ny ifyllning sparas som förslag eller bekräftad.")
    rec = {
        "id": uuid.uuid4().hex[:12], "signum": entry["signum"], "gap": entry["gap"], "fill": entry["fill"],
        "word": entry.get("word"), "name": bool(entry.get("name")), "method": entry["method"],
        "model_version": entry.get("model_version"), "p": entry.get("p"), "p_model": entry.get("p_model"),
        "evidence": _evidence(entry.get("evidence")), "status": entry["status"], "comment": (entry.get("comment") or "").strip(),
        "by": _who(user), "date": _now(), "created": _now(), "license": LICENSE,
    }
    check(rec)
    rec["history"] = [{"status": rec["status"], "by": rec["by"], "date": rec["date"], "comment": rec["comment"]}]
    with _lock:
        data = load(path)
        same = [x for x in data["fills"] if x["signum"] == rec["signum"] and x["gap"].get("key") == rec["gap"].get("key")
                and x["fill"] == rec["fill"] and x["status"] != "avvisad"]
        if same:
            raise ValueError("Samma ifyllning finns redan för luckan; ändra dess status i stället.")
        if rec["status"] == "bekräftad" and any(x["signum"] == rec["signum"] and x["gap"].get("key") == rec["gap"].get("key")
                                                 and x["status"] == "bekräftad" for x in data["fills"]):
            raise ValueError("Luckan har redan en bekräftad ifyllning; avvisa den först.")
        data["fills"].append(rec)
        _save(data, path)
    return rec


def set_status(fill_id: str, status: str, user: dict, comment: str, evidence=None, path: str | None = None) -> dict:
    """Moves a filling to another status (förslag → bekräftad, either → avvisad, avvisad → förslag), with who, when
    and why; added evidence is kept."""
    if status not in STATUSES:
        raise ValueError(f"Status måste vara en av: {', '.join(STATUSES)}.")
    if not (comment or "").strip():
        raise ValueError("En kommentar krävs.")
    with _lock:
        data = load(path)
        rec = next((x for x in data["fills"] if x["id"] == fill_id), None)
        if rec is None:
            raise KeyError(fill_id)
        if status == rec["status"]:
            raise ValueError(f"Ifyllningen har redan status {status}.")
        if status == "bekräftad" and any(x["id"] != fill_id and x["signum"] == rec["signum"]
                                         and x["gap"].get("key") == rec["gap"].get("key") and x["status"] == "bekräftad"
                                         for x in data["fills"]):
            raise ValueError("Luckan har redan en bekräftad ifyllning; avvisa den först.")
        rec["evidence"] = rec.get("evidence", []) + _evidence(evidence)
        rec.update(status=status, by=_who(user), date=_now(), comment=comment.strip())
        rec.setdefault("history", []).append({"status": status, "by": rec["by"], "date": rec["date"], "comment": rec["comment"]})
        _save(data, path)
    return rec


def for_stone(signum: str, statuses=SHOWN, path: str | None = None) -> list[dict]:
    return [x for x in load(path)["fills"] if x["signum"] == signum and x["status"] in statuses]


def label(x: dict) -> str:
    """'ifyllt av Vitki, 92 %, bekräftat 2026-11-20' – how a filling is described wherever it is shown."""
    pct = f", {min(99, round(100 * x['p']))} %" if x.get("p") is not None else ""
    state = {"bekräftad": "bekräftat", "förslag": "förslag", "avvisad": "avvisat"}[x["status"]]
    return f"ifyllt av Vitki ({x['method']}){pct}, {state} {x['date'][:10]}"


def provenance(signum: str, statuses=SHOWN, path: str | None = None) -> str:
    """One cell for a corpus table: every shown filling of the stone with status and provenance, '' when none."""
    out = []
    for x in for_stone(signum, statuses, path):
        g = x["gap"]
        carved = g.get("carved") or ""
        a, e = g.get("start", 0), g.get("end", 0)
        where = f"{carved[:a]}[{x['fill']}]{carved[e:]}" if carved else x["fill"]
        ver = f", {x['model_version']}" if x.get("model_version") else ""
        out.append(f"{x['status']}: {where} = {x.get('word') or '?'} ({label(x)}{ver})")
    return "; ".join(out)


def apply_words(signum: str, statuses=("bekräftad",), path: str | None = None) -> list[tuple[str, bool]]:
    """The words of the stone's confirmed fillings as (word, is_name), for an analysis that counts words and has the
    choice 'med Vitkis bekräftade ifyllningar' switched on."""
    return [(x["word"], bool(x.get("name"))) for x in for_stone(signum, statuses, path) if x.get("word")]


def mark(rec: dict) -> dict:
    """A copy of a Rundata record marked as carrying Vitki's fillings (for analyses only; never for the model)."""
    return {**rec, FILLED_MARK: True}


def provenance_map(statuses=SHOWN, path: str | None = None) -> dict[str, str]:
    """{signum: provenance cell} for every stone with a shown filling – the file read once, for a whole table."""
    sig = {x["signum"] for x in load(path)["fills"] if x["status"] in statuses}
    return {s: provenance(s, statuses, path) for s in sorted(sig)}
