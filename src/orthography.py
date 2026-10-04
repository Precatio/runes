"""Ortografisk stilometri på Rundata-translittereringar.

Särdrag per inskrift:
  * tecken-n-gram (2–3) i läsbara ord (TF-IDF),
  * skiljeteckenprofil (·, :, ×, +, ', ¤, ÷) och täthet,
  * bindrunor (^) per ord,
  * stavningsvarianter av vanliga ord, där translittereringen kan paras ord för ord
    med den normaliserade texten (t.ex. æftiR -> "iftiR"/"aftiR"/"eftiR").

Likhet mäts med cosinus. Ristarrangordning görs med närmaste centroid och utvärderas
med lämna-en-ute-korsvalidering, så att träffsäkerheten alltid kan redovisas.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache

import numpy as np
from scipy import sparse

SEPARATORS = {"·": "punkt", ":": "kolon", "×": "kryss", "+": "plus", "'": "apostrof", "¤": "semikolon", "÷": "övrigt"}
MARKUP_RE = re.compile(r"[()\[\]{}<>|?/]")
DAMAGED_RE = re.compile(r"-|\.\.\.")
# Egennamn tas bort ur särdragen: ristarens signatur ("bali risti") skulle annars
# avslöja svaret, och beställarnamn speglar familj/plats snarare än ortografi.
KEEP_NAMES = {"guð", "guðs", "kristr", "krist", "maria"}
MIN_WORDS = 5
MIN_CARVER_INSCRIPTIONS = 5


def _tokens(translit: str):
    """Ord och skiljetecken ur en translittererad text."""
    words, seps = [], []
    for tok in translit.split():
        if tok.startswith("§") or tok in ("¶", "¶¶"):
            continue
        if all(ch in SEPARATORS for ch in tok):
            seps.extend(tok)
            continue
        words.append(tok)
    return words, seps


def _clean_word(tok: str) -> str | None:
    """Läsbart ord utan textkritiska tecken, eller None om ordet är skadat."""
    if DAMAGED_RE.search(tok):
        return None
    w = MARKUP_RE.sub("", tok).replace("^", "")
    return w or None


def _norm_tokens(text: str):
    """[(ord, är_egennamn)] ur normaliserad text."""
    out = []
    for tok in text.split():
        if tok.startswith("§"):
            continue
        tok = tok.strip('.,;:!?')
        is_name = tok.startswith('"')
        tok = tok.lstrip('"').lower()
        if tok:
            out.append((tok, is_name and tok.split("/")[0] not in KEEP_NAMES))
    return out


def name_forms(inscriptions: list[dict]) -> set[str]:
    """Translittererade former som någonstans i Rundata normaliseras som egennamn."""
    forms = set()
    for rec in inscriptions:
        words, _ = _tokens(rec.get("transliteration", ""))
        norm = _norm_tokens(rec.get("normalization", ""))
        if norm and len(norm) == len(words):
            for raw, (_, is_name) in zip(words, norm):
                w = _clean_word(raw)
                if w and is_name:
                    forms.add(w)
    return forms


def features(rec: dict, names: frozenset | set = frozenset()) -> dict:
    words, seps = _tokens(rec.get("transliteration", ""))
    norm = _norm_tokens(rec.get("normalization", ""))
    aligned = bool(norm) and len(norm) == len(words)
    clean = []
    for k, raw in enumerate(words):
        w = _clean_word(raw)
        if not w:
            continue
        if (aligned and norm[k][1]) or (not aligned and w in names):
            continue
        clean.append(w)
    feats: Counter = Counter()
    for w in clean:
        padded = f"#{w}#"
        for n in (2, 3):
            for i in range(len(padded) - n + 1):
                feats[f"ng:{padded[i:i + n]}"] += 1
    if words:
        for s in seps:
            feats[f"sep:{SEPARATORS[s]}"] += 1
        feats["sep:täthet"] = len(seps) / len(words)
        feats["bind:andel"] = sum(t.count("^") for t in words) / len(words)
    variants = {}
    if aligned:
        for raw, (n, is_name) in zip(words, norm):
            w = _clean_word(raw)
            if w and not is_name and "[" not in n and "(?)" not in n:
                variants[n] = w
    return {"counts": feats, "variants": variants, "n_words": len(clean), "n_tokens": len(words)}


class OrthographyModel:
    def __init__(self, inscriptions: list[dict]):
        # Vikingatida inskrifter med tillräckligt mycket läsbar text
        self.records = []
        self.feats = []
        names = name_forms(inscriptions)
        for rec in inscriptions:
            if rec.get("period") != "V":
                continue
            f = features(rec, names)
            if f["n_words"] < MIN_WORDS:
                continue
            self.records.append(rec)
            self.feats.append(f)
        self.index = {r["signum"]: i for i, r in enumerate(self.records)}
        self._build_matrix()

    def _build_matrix(self):
        vocab: dict[str, int] = {}
        df: Counter = Counter()
        for f in self.feats:
            for k in f["counts"]:
                df[k] += 1
        # Ta bort mycket sällsynta n-gram (brus) men behåll alla icke-n-gram-särdrag
        keep = [k for k, c in df.items() if c >= 3 or not k.startswith("ng:")]
        vocab = {k: i for i, k in enumerate(sorted(keep))}
        n_docs = len(self.feats)
        idf = np.zeros(len(vocab))
        for k, i in vocab.items():
            idf[i] = math.log((1 + n_docs) / (1 + df[k])) + 1
        rows, cols, vals = [], [], []
        for r, f in enumerate(self.feats):
            for k, v in f["counts"].items():
                i = vocab.get(k)
                if i is None:
                    continue
                weight = (1 + math.log(v)) if k.startswith("ng:") and v > 0 else v
                rows.append(r)
                cols.append(i)
                vals.append(weight * idf[i])
        X = sparse.csr_matrix((vals, (rows, cols)), shape=(n_docs, len(vocab)))
        norms = np.sqrt(X.multiply(X).sum(axis=1)).A1
        norms[norms == 0] = 1
        self.X = sparse.diags(1 / norms) @ X
        self.vocab = vocab

    # ---- likhet -------------------------------------------------------------

    def similar(self, signum: str, limit: int = 10):
        i = self.index.get(signum)
        if i is None:
            return None
        sims = (self.X @ self.X[i].T).toarray().ravel()
        sims[i] = -1
        order = np.argsort(-sims)[:limit]
        q_var = self.feats[i]["variants"]
        out = []
        for j in order:
            rec = self.records[j]
            shared = {k: v for k, v in self.feats[j]["variants"].items() if q_var.get(k) == v}
            out.append({
                "signum": rec["signum"], "place": rec["place"], "similarity": float(sims[j]),
                "carvers": [c for c in rec["carvers"] if c["kind"] in ("S", "A")],
                "style": rec["style"], "shared_spellings": shared,
            })
        return out

    # ---- ristarattribuering --------------------------------------------------

    def _labelled(self):
        """Inskrifter med en (1) säker signerad/attribuerad ristare."""
        labels, self._kinds = {}, {}
        for i, rec in enumerate(self.records):
            cs = [c for c in rec["carvers"] if c["kind"] in ("S", "A") and not c["uncertain"]]
            if len(cs) == 1:
                labels[i] = cs[0]["name"]
                self._kinds[i] = cs[0]["kind"]
        counts = Counter(labels.values())
        return {i: g for i, g in labels.items() if counts[g] >= MIN_CARVER_INSCRIPTIONS}

    def _centroids(self, labels: dict[int, str], exclude: int | None = None):
        groups: dict[str, list[int]] = {}
        for i, g in labels.items():
            if i != exclude:
                groups.setdefault(g, []).append(i)
        names = sorted(groups)
        C = np.vstack([np.asarray(self.X[groups[g]].mean(axis=0)).ravel() for g in names])
        C /= np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-12)
        return names, C, {g: len(groups[g]) for g in names}

    def rank_carvers(self, signum: str, limit: int = 10):
        i = self.index.get(signum)
        if i is None:
            return None
        labels = self._labelled()
        names, C, sizes = self._centroids(labels, exclude=i)
        x = self.X[i].toarray().ravel()
        sims = C @ x
        order = np.argsort(-sims)[:limit]
        return {
            "ranking": [{"carver": names[k], "similarity": float(sims[k]), "n_inscriptions": sizes[names[k]]}
                        for k in order],
            "n_words": self.feats[i]["n_words"],
            "known_attribution": [c for c in self.records[i]["carvers"] if c["kind"] in ("S", "A")],
        }

    @lru_cache(maxsize=1)
    def evaluate(self):
        """Lämna-en-ute: hur ofta hamnar rätt ristare först / bland de tre första?"""
        labels = self._labelled()
        if not labels:
            return None
        idx = list(labels)
        top1 = top3 = 0
        signed_n = signed_top1 = 0
        groups: dict[str, list[int]] = {}
        for i, g in labels.items():
            groups.setdefault(g, []).append(i)
        names = sorted(groups)
        sums = {g: np.asarray(self.X[groups[g]].sum(axis=0)).ravel() for g in names}
        for i in idx:
            g_true = labels[i]
            x = self.X[i].toarray().ravel()
            sims = []
            for g in names:
                s = sums[g] - (x if g == g_true else 0)
                n = len(groups[g]) - (1 if g == g_true else 0)
                if n == 0:
                    continue
                c = s / n
                sims.append((float(c @ x / max(np.linalg.norm(c), 1e-12)), g))
            sims.sort(reverse=True)
            order = [g for _, g in sims]
            top1 += order[0] == g_true
            top3 += g_true in order[:3]
            if self._kinds[i] == "S":
                signed_n += 1
                signed_top1 += order[0] == g_true
        n = len(idx)
        return {
            # Attribuerade (A) inskrifter kan ha attribuerats just på grund av ortografin,
            # så siffran för enbart signerade inskrifter är det mer rättvisande måttet.
            "signed_only": {"n": signed_n, "top1_accuracy": signed_top1 / signed_n if signed_n else None},
            "n_inscriptions": n,
            "n_carvers": len(names),
            "top1_accuracy": top1 / n,
            "top3_accuracy": top3 / n,
            "chance_top1": 1 / len(names),
            "min_inscriptions_per_carver": MIN_CARVER_INSCRIPTIONS,
            "method": "Lämna-en-ute, närmaste centroid, cosinuslikhet på TF-IDF av tecken-n-gram, "
                      "skiljetecken och bindrunor (vikingatida inskrifter med minst 5 läsbara ord, "
                      "egennamn borttagna så att signaturer inte avslöjar ristaren)",
        }

    def profile(self, signum: str):
        i = self.index.get(signum)
        if i is None:
            return None
        f = self.feats[i]
        c = f["counts"]
        seps = {name: int(c.get(f"sep:{name}", 0)) for name in SEPARATORS.values()}
        return {
            "n_words": f["n_words"],
            "separators": seps,
            "separator_density": float(c.get("sep:täthet", 0.0)),
            "bindrune_rate": float(c.get("bind:andel", 0.0)),
            "spellings": f["variants"],
        }
