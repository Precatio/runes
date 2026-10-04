"""Jämförelse mellan appens läsning av en inskrift och Rundatas – utan AI.

  * Translitteringarna jämförs tecken för tecken och ord för ord (difflib). Skiljetecken,
    textkritiska tecken och bindrunemarkeringar räknas inte; Rundatas "-" (oläslig runa) och "..."
    (lucka) tas bort ur jämförelsen men redovisas.
  * Normaliseringarna jämförs ord för ord.
  * Varje ordform i vår normalisering slås upp bland Rundatas normaliserade former (runsvenska).
    En form som inte är belagd är inte fel i sig, men bör granskas.
"""
from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher

SEPARATORS = set("·:×+'¤÷|")
MARKUP = re.compile(r"[()\[\]{}<>?/^\"«»]")
SECTION = re.compile(r"§\w+")


# Younger futhark (and common variants) in Unicode -> Rundata's Latin transliteration
RUNE_TO_LATIN = {
    "ᚠ": "f", "ᚡ": "f", "ᚢ": "u", "ᚣ": "y", "ᚤ": "y", "ᚥ": "w", "ᚦ": "þ", "ᚧ": "þ", "ᚨ": "a", "ᚩ": "o", "ᚬ": "o",
    "ᚭ": "o", "ᚮ": "o", "ᚯ": "ø", "ᚰ": "o", "ᚱ": "r", "ᚴ": "k", "ᚵ": "g", "ᚶ": "g", "ᚷ": "g", "ᚸ": "g", "ᚼ": "h",
    "ᚽ": "h", "ᚺ": "h", "ᚻ": "h", "ᚾ": "n", "ᚿ": "n", "ᛀ": "n", "ᛁ": "i", "ᛂ": "e", "ᛃ": "j", "ᛄ": "j", "ᛅ": "a",
    "ᛆ": "a", "ᛇ": "æ", "ᛈ": "p", "ᛉ": "R", "ᛊ": "s", "ᛋ": "s", "ᛌ": "s", "ᛍ": "c", "ᛎ": "z", "ᛏ": "t", "ᛐ": "t",
    "ᛑ": "d", "ᛒ": "b", "ᛓ": "b", "ᛔ": "p", "ᛕ": "p", "ᛖ": "e", "ᛗ": "m", "ᛘ": "m", "ᛙ": "m", "ᛚ": "l", "ᛛ": "l",
    "ᛜ": "ng", "ᛝ": "ng", "ᛞ": "d", "ᛟ": "o", "ᛠ": "ea", "ᛡ": "io", "ᛢ": "q", "ᛣ": "k", "ᛤ": "k", "ᛥ": "st",
    "ᛦ": "R", "ᛧ": "y", "ᛨ": "q", "ᛩ": "q", "ᛪ": "x",
    "᛫": " · ", "᛬": " : ", "᛭": " + ",
}


def runes_to_latin(text: str) -> str:
    """Runic Unicode to Latin transliteration (Rundata style); Latin text is returned unchanged."""
    if not any(ch in RUNE_TO_LATIN for ch in text or ""):
        return text or ""
    out = "".join(RUNE_TO_LATIN.get(ch, ch) for ch in text)
    return re.sub(r"\s+", " ", out).strip()


def _canon(text: str) -> str:
    """Enhetlig translitterering: ʀ som R, övrigt med gemener (R och r är olika runor)."""
    text = runes_to_latin(text or "").replace("ʀ", "R")
    return "".join(ch if ch == "R" else ch.lower() for ch in text)


def translit_words(text: str) -> tuple[list[str], int]:
    """Läsbara ord och antal oläsliga tecken/luckor."""
    text = SECTION.sub(" ", _canon(text))
    for ch in SEPARATORS:
        text = text.replace(ch, " ")
    unreadable = text.count("-") + text.count("...")
    words = []
    for tok in text.split():
        w = MARKUP.sub("", tok).replace("-", "").replace(".", "")
        if w:
            words.append(w)
    return words, unreadable


def norm_words(text: str) -> list[str]:
    text = SECTION.sub(" ", text or "")
    out = []
    for tok in text.split():
        w = MARKUP.sub("", tok).strip(".,;:!–-").lower()
        if w:
            out.append(w)
    return out


def _segments(a: list[str], b: list[str]) -> list[dict]:
    sm = SequenceMatcher(a=a, b=b, autojunk=False)
    return [{"op": op, "ours": a[i1:i2], "rundata": b[j1:j2]} for op, i1, i2, j1, j2 in sm.get_opcodes()]


def compare(ours_translit: str, rundata_translit: str, ours_norm: str = "", rundata_norm: str = "") -> dict:
    ow, o_unread = translit_words(ours_translit)
    rw, r_unread = translit_words(rundata_translit)
    oc, rc = "".join(ow), "".join(rw)
    # Only runs of at least three runes count: single letters are found anywhere in a long text
    same_chars = sum(t.size for t in SequenceMatcher(a=oc, b=rc, autojunk=False).get_matching_blocks() if t.size >= 3)
    sm = SequenceMatcher(a=ow, b=rw, autojunk=False)
    same_words = sum(t.size for t in sm.get_matching_blocks())
    out = {
        # Agreement: how much of OUR reading is found in Rundata's (a partial reading can still agree fully)
        "char_agreement": round(same_chars / len(oc), 3) if oc else 0.0,
        "word_agreement": round(same_words / len(ow), 3) if ow else 0.0,
        # Coverage: how much of Rundata's text our reading includes
        "coverage": round(same_chars / len(rc), 3) if rc else 0.0,
        "words_ours": len(ow), "words_rundata": len(rw), "same_words": same_words,
        "unreadable_rundata": r_unread, "unreadable_ours": o_unread,
        "segments": _segments(ow, rw),
    }
    if ours_norm and rundata_norm:
        on, rn = norm_words(ours_norm), norm_words(rundata_norm)
        msm = SequenceMatcher(a=on, b=rn, autojunk=False)
        same = sum(t.size for t in msm.get_matching_blocks())
        out["normalization_agreement"] = round(same / len(on), 3) if on else 0.0
        out["normalization_segments"] = _segments(on, rn)
    out["summary"] = summary_text(out)
    return out


def summary_text(c: dict) -> str:
    level = ("stämmer i stort sett med" if c["char_agreement"] >= 0.9 else
             "stämmer delvis med" if c["char_agreement"] >= 0.6 else "skiljer sig i huvudsak från")
    text = (f"Vår läsning {level} Rundatas: {round(c['char_agreement'] * 100)} % av våra runor och "
            f"{c['same_words']} av våra {c['words_ours']} ord finns i Rundatas läsning.")
    if c["coverage"] < 0.9:
        text += f" Läsningen täcker {round(c['coverage'] * 100)} % av Rundatas text (t.ex. en beskuren bild)."
    if c.get("normalization_agreement") is not None:
        text += f" {round(c['normalization_agreement'] * 100)} % av våra normaliserade ord stämmer med Rundatas."
    if c["unreadable_rundata"]:
        text += f" Rundata markerar {c['unreadable_rundata']} oläsliga tecken eller luckor, som inte ingår i jämförelsen."
    return text


class Lexicon:
    """Normaliserade ordformer (runsvenska) i Rundatas vikingatida inskrifter."""

    def __init__(self, inscriptions: list[dict]):
        self.forms: Counter = Counter()
        for rec in inscriptions:
            if rec.get("period") != "V":
                continue
            self.forms.update(norm_words(rec.get("normalization", "")))

    def check(self, normalization: str) -> dict:
        words = norm_words(normalization)
        items = [{"form": w, "attested": self.forms.get(w, 0)} for w in words]
        attested = sum(1 for i in items if i["attested"])
        return {"items": items, "attested": attested, "total": len(items),
                "share": round(attested / len(items), 3) if items else None}
