"""Mönsterregistret: när varje mönster i korpusanalyserna (src/r_findings.corpus_patterns) först sågs, och när dess
status senast ändrades. Statistik (R) och Forskningsluckor märker ett mönster "Nytt" de första NEW_DAYS dagarna efter
att det dök upp, och "Ändrat" när statusen bytts (t.ex. från "mönster att pröva" till "bekräftar"). Ett nytt mönster
som inte är bekräftat i robusthetstrappan (src/robustness.py: båda halvorna och den gemensamma BH-justeringen) märks
"Nytt, obekräftat" (new = "obekräftat") i stället.

Registret ligger i data/pattern_registry.json och följer med kodförrådet, så att det går att se när ett mönster kom
till. Första gången registret skapas förs de mönster som redan finns in som kända (inte nya): märkningen gäller det som
dyker upp därefter.
"""
import json
import os
import threading
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "pattern_registry.json")
NEW_DAYS = 30
_lock = threading.Lock()


def key(p: dict) -> str:
    return f"{p.get('topic')}|{p.get('key')}"


def _load() -> dict | None:
    if not os.path.exists(PATH):
        return None
    try:
        with open(PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _save(reg: dict):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, PATH)


def update(patterns: list[dict], today: str | None = None) -> dict:
    """För in mönster som inte setts förut och statusbyten; ger registret. Ett nytt register sås med de mönster som
    finns i dag, märkta som kända sedan tidigare."""
    today = today or date.today().isoformat()
    with _lock:
        reg = _load()
        seeding = reg is None
        reg = reg or {"created": today, "patterns": {}}
        changed = seeding
        for p in patterns:
            k = key(p)
            e = reg["patterns"].get(k)
            if e is None:
                reg["patterns"][k] = {"first_seen": today, "status": p.get("status"), "seeded": seeding,
                                      "text": (p.get("text") or "")[:300]}
                changed = True
            elif e.get("status") != p.get("status"):
                e.update(status=p.get("status"), status_changed=today, previous_status=e.get("status"))
                changed = True
        if changed:
            _save(reg)
        return reg


def _age(d: str | None, today: date) -> int | None:
    try:
        return (today - datetime.strptime(d, "%Y-%m-%d").date()).days
    except (TypeError, ValueError):
        return None


def annotate(patterns: list[dict], today: str | None = None) -> list[dict]:
    """Mönstren med first_seen och märkningen new ("nytt" eller "ändrat") ur registret, som kopior."""
    reg = update(patterns, today)
    t = datetime.strptime(today, "%Y-%m-%d").date() if today else date.today()
    out = []
    for p in patterns:
        e = reg["patterns"].get(key(p)) or {}
        q = {**p, "first_seen": None if e.get("seeded") else e.get("first_seen")}
        age_new, age_changed = _age(e.get("first_seen"), t), _age(e.get("status_changed"), t)
        if not e.get("seeded") and age_new is not None and age_new <= NEW_DAYS:
            # "Nytt" only once the pattern is confirmed (both halves and the common BH, src/robustness.py); before
            # that, or where it cannot be split-half tested, "obekräftat". Without the ladder (confirmed missing) as before
            q["new"] = "nytt" if p.get("confirmed", True) is True else "obekräftat"
        elif age_changed is not None and age_changed <= NEW_DAYS:
            q["new"] = "ändrat"
            q["previous_status"] = e.get("previous_status")
            q["status_changed"] = e.get("status_changed")
        out.append(q)
    return out
