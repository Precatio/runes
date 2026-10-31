"""Etiketterna på artiklarna (vitkirunor.se/artiklar): en TYP per artikel och ett eller flera ÄMNEN.

Typen säger vad slags text det är, ämnet vad den handlar om. Listan är fast, så att artikelsidan kan visa samma
filter varje gång och engelskan följer med; samma lista står i web/src/lib/labels.ts (tests/test_blog_labels.py
jämför dem). En etikett som inte står här avvisas när artikeln sparas (api/routers/blog.py).
"""
from __future__ import annotations

TYPES = [
    ("Forskning", "Research"),            # nytt mönster eller ny mätning, med statistiken förklarad
    ("Metod", "Method"),                  # hur en metod fungerar och hur den prövats
    ("Så gör du", "How to"),              # steg för steg i Vitki, med skärmbilder
    ("Pågående arbete", "Work in progress"),
    ("Personligt", "Personal"),
    ("Rapport", "Report"),                # forskningsrapport i fast form (utdata/rapporter/MALL.md): bekräftade fynd, citerbara
]
SUBJECTS = [
    ("Ristare", "Carvers"),
    ("Språk och stavning", "Language and spelling"),
    ("Formler och syfte", "Formulas and purpose"),
    ("Tro och magi", "Belief and magic"),
    ("Kvinnor och barn", "Women and children"),
    ("Norden", "The Nordic countries"),
    ("Datering och stil", "Dating and style"),
    ("Geografi", "Geography"),
    ("Kryptologi", "Cryptology"),
    ("Tolkning", "Interpretation"),
    ("Sannolikhetsmodellen", "The probability model"),
    ("Huggspår och 3D", "Grooves and 3D"),
    ("Eddan", "The Edda"),
]
TYPE_NAMES = [sv for sv, _ in TYPES]
SUBJECT_NAMES = [sv for sv, _ in SUBJECTS]
ENGLISH = {sv: en for sv, en in TYPES + SUBJECTS}
MAX_LABELS = 5


def check(labels: list[str]) -> str | None:
    """Felmeddelande om etiketterna inte följer listan (okänd, fler än en typ, för många), annars None."""
    unknown = [x for x in labels if x not in ENGLISH]
    if unknown:
        return "Okänd etikett: " + ", ".join(unknown)
    if sum(x in TYPE_NAMES for x in labels) > 1:
        return "Bara en typ per artikel (" + ", ".join(TYPE_NAMES) + ")."
    if len(labels) > MAX_LABELS:
        return f"Högst {MAX_LABELS} etiketter."
    if len(set(labels)) != len(labels):
        return "Samma etikett två gånger."
    return None


def ordered(labels: list[str]) -> list[str]:
    """Typen först, sedan ämnena i listans ordning."""
    order = {name: i for i, name in enumerate(TYPE_NAMES + SUBJECT_NAMES)}
    return sorted(labels, key=lambda x: order.get(x, 99))
