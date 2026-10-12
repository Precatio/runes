"""Språkdrag: fonetisk stil och språkbruk i en inskrift, och ristarens profil.

Dragen läses ur Rundata genom att translitterationen paras ord för ord med normaliseringen (samma
metod som stavningsvarianterna i den ortografiska modellen). Ett drag räknas bara där inskriften har
ordet; annars är det "ej bestämbart". Ristarens profil är fördelningen över dennes säkra inskrifter, och
en sten "stämmer" i ett drag när dess värde är det vanligaste hos ristaren eller förekommer i minst
hälften av ristarens inskrifter med ordet.

Ljudhistoriska drag (fonetisk stil) visar hur ristaren återgav uttalet; språkbruk visar formler och
ordval. Båda påverkas av dialekt, tid och beställare, inte bara av ristaren.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from src.orthography import _clean_word, _tokens, features

# trait -> (group, label, definition)
TRAITS: dict[str, tuple[str, str, str]] = {
    "ai_sten": ("ljud", "Diftongen ai i 'sten'",
                "Ordet stæinn skrivet med ai/ia (diftongen bevarad i skrift) eller med i/e (monoftongerad, "
                "östnordisk utveckling)."),
    "au_och": ("ljud", "Diftongen au i 'och'",
               "Konjunktionen ok skriven auk (diftong) eller uk/ok/ak (monoftong)."),
    "nasal": ("ljud", "Nasal före konsonant",
              "Om n/m skrivs ut före homorgan konsonant, t.ex. bonta/bunta mot buta (bónda), kumbl mot kubl."),
    "h_bortfall": ("ljud", "h-bortfall",
                   "Om h skrivs i början av ord som hans och hjalpi (hans mot ans, hialbi mot ialbi)."),
    "stungna": ("ljud", "Stungna runor",
                "Om inskriften använder stungna runor (e, g, d, y), som skiljer ljud som den vanliga yngre "
                "futharken inte skiljer på; vanligare under 1000-talets senare del."),
    "efter": ("bruk", "Stavning av 'efter'",
              "Hur æftiR skrivs: första vokalen (a, e, i, u, y) och slutet (-iR, -ir, -R)."),
    "denna": ("bruk", "Stavning av 'denna'",
              "Hur demonstrativet þenna skrivs (þina, þino, þana, þena)."),
    "bon": ("bruk", "Kristen bön",
            "Om inskriften har en bön, t.ex. Guð hjalpi and hans (Gud hjälpe hans själ), Kristr hjalpi, Guð "
            "biargi eller Guðs móðir."),
    "sjal": ("bruk", "Själsbön",
             "Om bönen nämner själen (and, sál/sálu). Avsiktsfrasen på brostenar (fyrir and hans, 'för hans själ') "
             "räknas inte som bön."),
    "signatur": ("bruk", "Ristarsignatur",
                 "Om inskriften har en ristarformel (risti, hjó, markaði, rúnaR)."),
    "runor": ("bruk", "Skrivningen av 'runor'",
              "Hur rúnaR skrivs (runaR, runa, runar)."),
    # Added 2026-10-11
    "ai_alla": ("ljud", "Diftongen ai i alla ord",
                "Som 'sten', men i alla ord med æi i normaliseringen (ræisa, stæinn, þæiR, bæði): ai/ia/ei skrivet "
                "(diftong), bara i/e (monoftong) eller båda i samma inskrift."),
    "r_for_R": ("ljud", "ʀ skrivet med r",
                "Om ord som slutar på ʀ (æftiR, þæiR, syniR, hafiR) skrivs med ʀ-runan eller med r-runan. ʀ och r "
                "föll med tiden samman i uttalet."),
    "o_runa": ("ljud", "o-runan för o-ljud",
               "Om o-ljudet i broður, bóndi, móður, sun och kona skrivs med o-runan (ᚬ, translittererad o) eller med "
               "u-runan. o-runan stod ursprungligen för nasalt a och fick efter hand värdet o."),
    "stungen_e": ("ljud", "Stungen i (e)", "Om inskriften har stungen i-runa (e), som skiljer e från i."),
    "stungen_y": ("ljud", "Stungen u (y)", "Om inskriften har stungen u-runa (y), som skiljer y från u."),
    "stungen_g": ("ljud", "Stungen k (g)", "Om inskriften har stungen k-runa (g), som skiljer g från k."),
    "preposition": ("bruk", "æftiR eller at",
                    "Om minnesformeln använder prepositionen æftiR eller at (före namnet), eller båda."),
    "skiljetecken": ("skrift", "Skiljetecken",
                     "Det vanligaste skiljetecknet mellan orden: punkt (·), kolon (:), kryss (×), apostrof (') eller "
                     "plus (+), eller blandat när det vanligaste står för mindre än tre fjärdedelar; minst tre tecken."),
    "bindrunor": ("skrift", "Bindrunor", "Om inskriften har bindrunor (två runor på samma huvudstav)."),
}

DOTTED = set("egdy")


SEPARATOR_NAMES = {"·": "punkt", ":": "kolon", "×": "kryss", "'": "apostrof", "+": "plus"}
# brøðr (plural of broður) has the vowel ø, not o, and is left out
O_WORDS = {"broður", "boanda", "bonda", "moður", "sun", "sunu", "kona", "kunu"}


def _pair_value(trait: str, pairs: list[tuple[str, str]]) -> str | None:
    """Drag ur ordparen (normaliserad form med versaler, translittererad form)."""
    if trait == "ai_alla":
        hits = [bool(re.search(r"ai|ia|ei|ae", w)) for n, w in pairs if "æi" in n.lower()]
        if not hits:
            return None
        return "diftong" if all(hits) else "monoftong" if not any(hits) else "båda"
    if trait == "r_for_R":
        ends = [w[-1] for n, w in pairs if n.endswith("R") and w[-1:] in ("R", "r")]
        if not ends:
            return None
        return "ʀ-runa" if all(e == "R" for e in ends) else "r för ʀ" if all(e == "r" for e in ends) else "båda"
    if trait == "o_runa":
        hits = ["o" in w for n, w in pairs if n.lower() in O_WORDS]
        if not hits:
            return None
        return "o-runa" if all(hits) else "u-runa" if not any(hits) else "båda"
    return None


# The soul in the prayers' normalisation (and/ǫnd "spirit", sál/salu/sialu/sal/sel "soul")
_SOUL = r"\b(and|ǫnd|ônd|salu|sálu|sál|sal|sial|sialu|sel)\b"


def _value(trait: str, variants: dict, norm: str, translit_words: list[str]) -> str | None:
    if trait == "ai_sten":
        w = variants.get("stæin") or variants.get("stæina")
        if not w:
            return None
        return "ai bevarad" if ("ai" in w or "ia" in w or "æi" in w) else "monoftong"
    if trait == "au_och":
        w = variants.get("ok")
        if not w:
            return None
        return "auk" if w.startswith("au") else "monoftong"
    if trait == "nasal":
        w = variants.get("bonda") or variants.get("kumbl")
        if not w:
            return None
        if "bonda" in variants:
            return "skriven" if "n" in w else "utelämnad"
        return "skriven" if "m" in w and "b" in w else "utelämnad"
    if trait == "h_bortfall":
        w = variants.get("hialpi") or variants.get("hans")
        if not w:
            return None
        return "h skrivet" if w.startswith("h") else "h saknas"
    if trait == "stungna":
        letters = set("".join(translit_words))
        return "ja" if letters & DOTTED else "nej"
    if trait in ("stungen_e", "stungen_y", "stungen_g"):
        return "ja" if trait[-1] in set("".join(translit_words)) else "nej"
    if trait == "preposition":
        toks = [t.strip(".,;:!?") for t in norm.split()]
        ae = any(t.lower().startswith(("æft", "aft")) for t in toks)
        at = any(t.lower() == "at" and i + 1 < len(toks) and toks[i + 1].startswith('"') for i, t in enumerate(toks))
        if not (ae or at):
            return None
        return "båda" if ae and at else "æftiR" if ae else "at"
    if trait == "efter":
        w = variants.get("æftir")
        if not w:
            return None
        end = "-R" if not re.search(r"i[Rr]$", w) and w.endswith("R") else ("-ir" if w.endswith("ir") else "-iR" if w.endswith("iR") else "annat")
        return f"{w[0]}-…{end}"
    if trait == "denna":
        return variants.get("þenna")
    if trait == "runor":
        return variants.get("runar")
    # Brackets and (?) mark uncertain readings in the normalisation; they should not hide a word
    n = re.sub(r"[\[\]]|\(\?\)", "", norm.lower())
    if trait == "bon":
        # Guð/Kristr/Drottinn hialpi … (also hiælpi, hialpin, the imperative hialp), Guð biargi …, Guð lætti …, Guðs moðiR,
        # or hialpi with a soul word where the god's name is lost ("… hialpi sialu hans")
        god = re.search(r"\b(guð|kristr|krist|drottinn?)\b", n)
        help_ = re.search(r"\b(hialpi|hjalpi|hiælpi|hialpin|hialp|hialpa|biargi|lætti|letti)\b", n)
        return "ja" if (god and help_) or "guðs moðir" in n or (help_ and re.search(_SOUL, n)) else "nej"
    if trait == "sjal":
        # A prayer for the soul, not the intention phrase on bridge stones (gærði bro fyrir and hans, "for his soul")
        rest = re.sub(r"\bfyrir\s+" + _SOUL[2:], "", n)
        return "ja" if re.search(_SOUL, rest) else "nej"
    if trait == "signatur":
        return "ja" if re.search(r"\b(risti|ristu|hiogg|hiuggu|markaði|faði|fáði)\b", n) else "nej"
    return None


_cache: dict[tuple[str, int], dict[str, str]] = {}


def traits(rec: dict, names=frozenset()) -> dict[str, str]:
    # Rundata records do not change while the server runs; cache per inscription (and name set)
    key = (rec.get("signum", ""), id(names))
    if key[0] and key in _cache:
        return _cache[key]
    out = _traits(rec, names)
    if key[0]:
        _cache[key] = out
    return out


def _case_pairs(rec: dict) -> list[tuple[str, str]]:
    """Ord för ord: normaliserad form (med versaler, så att ʀ syns) och translittererad form. Bara när texterna
    har lika många ord, och utan egennamn och osäkra läsningar, som stavningsvarianterna i orthography.features."""
    words, _ = _tokens(rec.get("transliteration", ""))
    norm = [t.strip(".,;:!?") for t in (rec.get("normalization") or "").split() if not t.startswith("§")]
    if not norm or len(norm) != len(words):
        return []
    out = []
    for raw, n in zip(words, norm):
        w = _clean_word(raw)
        if w and not n.startswith('"') and "[" not in n and "(?)" not in n:
            out.append((n, w))
    return out


# Dotted runes and the sounds they mark: a word whose normalised form has the sound can have the dotted rune
DOT_SOUNDS = {"y": "yøœ", "e": "eæ", "g": "g", "d": "dð"}


def dotted_counts(rec: dict) -> dict[str, int]:
    """Stungna runor räknade tecken för tecken (som draget: utan fragmentariska ord): hur många av de runor som kunde
    ha varit stungna (i/e, u/y, k/g, t/d) som är stungna – ett andelsmått som inte gynnar långa inskrifter. Per runa
    dessutom ord för ord: hur många ord som enligt normaliseringen har ljudet (y/ø, e/æ utom i diftongen æi, g, d/ð)
    och hur många av dem som skrivs med den stungna runan; för y också hur många som skrivs med u eller i i stället
    (r/change.R)."""
    words = [re.sub(r"[()\[\]{}<>|?/^]", "", t) for t in (rec.get("transliteration") or "").split()]
    letters = "".join(w for w in words if w and "-" not in w)
    dotted = sum(letters.count(c) for c in "eygd")
    out = {"dot_n": dotted, "dot_cand": dotted + sum(letters.count(c) for c in "iukt")}
    pairs = [(n.lower().replace("æi", ""), w) for n, w in _case_pairs(rec)]
    for rune, sounds in DOT_SOUNDS.items():
        exp = [w for n, w in pairs if any(ch in n for ch in sounds)]
        out[f"dot_{rune}_exp"] = len(exp)
        out[f"dot_{rune}_obs"] = sum(rune in w for w in exp)
    # æftiʀ separately: the commonest place for dotted i, and a word some provinces replace with at
    eft = [w for n, w in pairs if n.startswith("æftir")]
    out["dot_e_eftir_exp"] = len(eft)
    out["dot_e_eftir_obs"] = sum("e" in w for w in eft)
    exp_y = [w for n, w in pairs if any(ch in n for ch in DOT_SOUNDS["y"])]
    out["dot_y_u"] = sum("y" not in w and "u" in w for w in exp_y)
    out["dot_y_i"] = sum("y" not in w and "u" not in w and "i" in w for w in exp_y)
    return out


def prayer_form(rec: dict) -> dict[str, int]:
    """Själsbönens ordval och om inskriftens slut är bevarat (bönen står oftast sist, där stenar ofta är skadade):
    and/ônd eller sál, och om Guðs móðir nämns (r/change.R)."""
    n = (rec.get("normalization") or "").lower()
    t = (rec.get("transliteration") or "").strip()
    return {"end_intact": int(bool(t) and not re.search(r"(\.\.\.|-)\W*$", t)),
            "prayer_and": int(bool(re.search(r"\band\b|\bônd\b|\bǫnd\b", n))),
            "prayer_sal": int(bool(re.search(r"\bsal(u|ar)?\b|\bsál", n))),
            "prayer_gudsmodir": int(bool(re.search(r"guðs (moðir|møður|moður)", n)))}


def r_counts(rec: dict) -> dict[str, int]:
    """ʀ och r i ordslut, ord för ord: ord som slutar på ʀ i normaliseringen och skrivs med r-runan (r för ʀ), för
    æftiʀ och för övriga ord var för sig, och ord som slutar på r men skrivs med ʀ-runan (omvänd, hyperkorrekt
    stavning) – ett bättre mått på sammanfallet än r för ʀ ensamt (r/change.R)."""
    out = dict.fromkeys(("R_n", "R_r", "R_eftir_n", "R_eftir_r", "r_n", "r_R"), 0)
    for n, w in _case_pairs(rec):
        if w[-1:] not in ("R", "r"):
            continue
        if n.endswith("R"):
            out["R_n"] += 1; out["R_r"] += w.endswith("r")
            if n.lower().startswith("æftir"):
                out["R_eftir_n"] += 1; out["R_eftir_r"] += w.endswith("r")
        elif n.endswith("r"):
            out["r_n"] += 1; out["r_R"] += w.endswith("R")
    return out


def ai_counts(rec: dict) -> dict[str, int]:
    """Ord med æi i normaliseringen, räknade ord för ord: hur många som är skrivna med monoftong (i/e i stället för
    ai/ia/ei), för alla sådana ord och för stæinn för sig – underlaget för att pröva monoftongeringen per ord och per
    lexem i stället för bara om stenen har minst en monoftong (r/change.R)."""
    words = [(n.lower(), w) for n, w in _case_pairs(rec) if "æi" in n.lower()]
    mono = [not re.search(r"ai|ia|ei|ae", w) for _, w in words]
    sten = [m for (n, _), m in zip(words, mono) if n.startswith("stæin")]
    # How the monophthong is written: with dotted i (e, as in sten) or plain i (stin) – so that a move from stin to sten
    # is not mistaken for a move from stin to stain
    mono_words = [w for (n, w), m in zip(words, mono) if m]
    return {"ai_n": len(words), "ai_mono": sum(mono), "ai_sten_n": len(sten), "ai_sten_mono": sum(sten),
            "ai_mono_e": sum("e" in w for w in mono_words), "ai_mono_i": sum("e" not in w for w in mono_words)}


O_SOUND = O_WORDS  # words with etymological /o/ (brōður, bóndi, móður, sonr, kona)
NASAL_A = {"and", "ǫnd", "ônd"}  # ą, the ós-rune's old value


def och_counts(rec: dict) -> dict[str, int]:
    """Konjunktionen ok, förekomst för förekomst: skriven auk, uk, ok eller ak (eller annat). Draget au_och räknar allt
    utan au som monoftong, alltså också ok med åsrunan; här syns skrivningarna var för sig (r/change.R)."""
    forms = [w for n, w in _case_pairs(rec) if n.lower() == "ok"]
    out = {"och_n": len(forms), "och_auk": 0, "och_uk": 0, "och_ok": 0, "och_ak": 0}
    for w in forms:
        k = "och_auk" if w.startswith("au") else "och_uk" if w.startswith("u") else "och_ok" if w.startswith("o") else \
            "och_ak" if w.startswith("a") else None
        if k:
            out[k] += 1
    return out


def o_counts(rec: dict) -> dict[str, int]:
    """Åsrunan ord för ord: ord med etymologiskt /o/ skrivna med o, och ord med ursprungligt ą (and/ônd) skrivna med
    o – om runan överges för ą samtidigt som den tas i bruk för /o/ har värdet förskjutits (r/change.R)."""
    pairs = [(n.lower(), w) for n, w in _case_pairs(rec)]
    o = [w for n, w in pairs if n in O_SOUND]
    a = [w for n, w in pairs if n in NASAL_A]
    return {"o_n": len(o), "o_o": sum("o" in w for w in o), "aa_n": len(a), "aa_o": sum("o" in w for w in a)}


def _traits(rec: dict, names) -> dict[str, str]:
    f = features(rec, names)
    raw = (rec.get("transliteration") or "").split()
    words = [re.sub(r"[()\[\]{}<>|?/^]", "", t) for t in raw]
    norm = rec.get("normalization") or ""
    pairs = _case_pairs(rec)
    out = {}
    for t in TRAITS:
        if t in ("ai_alla", "r_for_R", "o_runa"):
            v = _pair_value(t, pairs)
        elif t == "skiljetecken":
            _, seps = _tokens(rec.get("transliteration", ""))
            known = [x for x in seps if x in SEPARATOR_NAMES]
            common = Counter(known).most_common(2)
            if len(known) < 3 or not common:
                v = None
            elif common[0][1] / len(known) < 0.75 and len(common) > 1 and common[1][1] >= 2:
                v = "blandat"  # e.g. U 92: ' in the first part, · from kira onwards
            else:
                v = SEPARATOR_NAMES[common[0][0]]
        elif t == "bindrunor":
            v = "ja" if any("^" in x for x in raw) else "nej"
        else:
            v = _value(t, f["variants"], norm, [w for w in words if w and "-" not in w])
        if v is not None:
            out[t] = v
    # Short texts say nothing about formulas
    if f["n_words"] < 5:
        for t in ("bon", "sjal", "signatur", "stungna", "stungen_e", "stungen_y", "stungen_g", "bindrunor"):
            out.pop(t, None)
    return out


def carver_profile(carver: str, inscriptions: list[dict], certain_carvers, names=frozenset(),
                   exclude: str | None = None) -> dict:
    dist: dict[str, Counter] = {t: Counter() for t in TRAITS}
    n = 0
    for r in inscriptions:
        if r["signum"] == exclude or carver not in certain_carvers(r):
            continue
        n += 1
        for t, v in traits(r, names).items():
            dist[t][v] += 1
    return {"carver": carver, "n_inscriptions": n,
            "traits": {t: dict(c.most_common()) for t, c in dist.items() if c}}


FEW_INSCRIPTIONS = 10  # a carver's share of a trait resting on fewer inscriptions than this is flagged as uncertain

# Traits that repeat another trait: left out of the combined likelihood ratio so the same evidence is not counted twice
REDUNDANT = {"stungna": ("stungen_e", "stungen_y", "stungen_g"), "ai_sten": ("ai_alla",), "sjal": ("bon",)}


def _log_lr_table(profile: dict, baseline: dict[str, Counter], min_n: int) -> dict[str, dict[str, float]]:
    """log(P(värde | ristaren) / P(värde | övriga stenar i landskapet)) per drag och värde, med additiv utjämning
    (0,5 per värde) så att ett värde som saknas hos ena sidan inte ger en oändlig kvot."""
    table = {}
    for t, dist in profile["traits"].items():
        base = baseline.get(t) or Counter()
        nc, nr = sum(dist.values()), sum(base.values())
        if nc < min_n or nr < min_n:
            continue
        values = set(dist) | set(base)
        k = max(2, len(values))
        table[t] = {v: math.log(((dist.get(v, 0) + 0.5) / (nc + 0.5 * k)) / ((base.get(v, 0) + 0.5) / (nr + 0.5 * k)))
                    for v in values}
    return table


def _score(stone: dict[str, str], table: dict[str, dict[str, float]]) -> tuple[float, int]:
    used = [t for t in stone if t in table and stone[t] in table[t]
            and not any(o in stone and o in table for o in REDUNDANT.get(t, ()))]
    return sum(table[t][stone[t]] for t in used), len(used)


def compare(stone: dict[str, str], profile: dict, min_n: int = 3, baseline: dict[str, Counter] | None = None,
            others: list[dict[str, str]] | None = None, region: str | None = None) -> dict:
    """Stenens språkdrag mot ristarens profil. Med baseline (dragen på övriga stenar i landskapet, utan ristarens
    och stenens egna) vägs varje drag efter hur utmärkande det är för ristaren, och med others (de övriga stenarnas
    drag) prövas hur ofta en slumpvis sten i landskapet passar ristarens profil minst lika bra (empiriskt p-värde)."""
    table = _log_lr_table(profile, baseline, min_n) if baseline else {}
    rows = []
    for t, v in stone.items():
        dist = profile["traits"].get(t) or {}
        total = sum(dist.values())
        if total < min_n:
            continue
        share = dist.get(v, 0) / total
        top = max(dist, key=dist.get)
        group, label, definition = TRAITS[t]
        row = {"trait": t, "group": group, "label": label, "definition": definition, "stone": v,
               "carver_common": top, "share": round(share, 3), "n": total,
               "agrees": v == top or share >= 0.5}
        if t in table and v in table[t]:
            base = baseline[t]
            row["region_share"] = round(base.get(v, 0) / sum(base.values()), 3)
            row["lr"] = round(math.exp(table[t][v]), 2)
        rows.append(row)
    # A trait that repeats another (stungna runor beside stungen i/u/k, ai i 'sten' beside ai i alla ord, själsbön
    # beside bön) is shown but not counted, so that the same evidence is not counted twice
    present = {r["trait"] for r in rows}
    for r in rows:
        r["repeats"] = any(o in present for o in REDUNDANT.get(r["trait"], ()))
    counted = [r for r in rows if not r["repeats"]]
    k = sum(r["agrees"] for r in counted)
    who = profile["carver"]
    text = (f"{k} av {len(counted)} jämförbara språkdrag stämmer med inskrifterna av {who}"
            if counted else f"Inga jämförbara språkdrag (för få gemensamma ord med inskrifterna av {who})")
    out = {"rows": rows, "agree": k, "comparable": len(counted)}
    if rows and table:
        # With the province as baseline a trait speaks for the carver when the stone's form is clearly more common with
        # the carver than on other stones there (ratio at least 1.5), against when clearly rarer, and is neutral otherwise
        where = f"i {region}" if region else "i landskapet"
        rated = [r for r in counted if r.get("lr") is not None]
        pro = sorted([r for r in rated if r["lr"] >= 1.5], key=lambda r: -r["lr"])
        con = sorted([r for r in rated if r["lr"] <= 1 / 1.5], key=lambda r: r["lr"])
        few = [r for r in rated if r["n"] < FEW_INSCRIPTIONS]

        def listing(rs):
            return "; ".join(f"{_lc(r['label'])} ({r['stone']}: {round(r['share'] * 100)} % hos ristaren mot "
                             f"{round(r['region_share'] * 100)} % {where}"
                             + (f", bara {r['n']} inskrifter" if r["n"] < FEW_INSCRIPTIONS else "") + ")" for r in rs)
        text = (f"Av {len(rated)} jämförbara språkdrag talar {len(pro)} för {who} (stenens form är tydligt vanligare hos "
                f"ristaren än på andra stenar {where}), {len(con)} emot (tydligt ovanligare hos ristaren) och "
                f"{len(rated) - len(pro) - len(con)} skiljer inte")
        if pro:
            text += ". För: " + listing(pro)
        if con:
            text += ". Emot: " + listing(con)
        if few:
            text += (f". Drag med färre än {FEW_INSCRIPTIONS} jämförbara inskrifter hos ristaren är osäkra ("
                     + "; ".join(f"{_lc(r['label'])}: {r['n']}" for r in few) + ")")
        out.update(n_for=len(pro), n_against=len(con), n_neutral=len(rated) - len(pro) - len(con),
                   few=[r["trait"] for r in few])
        score, n_used = _score(stone, table)
        out.update(lr_total=round(math.exp(score), 2), n_used=n_used)
        if others:
            null = [sc for sc, n in (_score(o, table) for o in others) if n >= max(2, n_used // 2)]
            if null:
                p = (1 + sum(1 for sc in null if sc >= score)) / (1 + len(null))
                out.update(p_region=round(p, 4), n_region=len(null))
    if counted and not table:
        off = [r for r in counted if not r["agrees"]]
        if off:
            text += f". Avviker ({len(off)}): " + "; ".join(
                f"{_lc(r['label'])} ({r['stone']}; hos ristaren oftast {r['carver_common']})" for r in off)
    if out.get("lr_total") is not None:
        lr = out["lr_total"]
        text += (f". Sammantaget är stenens språkdrag {_times(lr)} så vanliga hos {who} som på andra stenar "
                 f"{'i ' + region if region else 'i landskapet'}")
        if out.get("p_region") is not None:
            p = out["p_region"]
            text += (f"; {round(p * 100)} % av {out['n_region']} andra stenar där passar ristarens profil minst lika bra "
                     f"(p {_pfmt(p)})")
    out["text"] = text + "."
    return out


def _lc(label: str) -> str:
    """Liten första bokstav, men transliterationens versaler (æftiR) behålls."""
    return label[:1].lower() + label[1:]


def _times(lr: float) -> str:
    if lr >= 1:
        return f"{lr:.1f} gånger".replace(".", ",")
    return f"bara {lr:.2f} gånger".replace(".", ",")


def _pfmt(p: float) -> str:
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")
