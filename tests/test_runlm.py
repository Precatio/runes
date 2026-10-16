"""Sannolikhetsmodellen för runtext (src/runlm.py): stavning, samma ord i olika normaliseringar och avkodning."""
import math

from src.runlm import Model, carved_groups, decode, key, pairs, sections


def _rec(signum, translit, norm):
    return {"signum": signum, "period": "V", "transliteration": translit, "normalization": norm}


RECS = [_rec(f"T {i}", "þurir : raisþi : stain : þansi : aft : faþur : sin", "Þorir ræisti stæin þannsi æft faður sinn.")
        for i in range(6)] + [
    _rec("T 10", "kunar : raisþi : stain : aft : sun : sin", "Gunnarr ræisti stæin æft sun sinn."),
    _rec("T 11", "asa : raisþi : stain : þansi : aft : sun : sin", "Asa ræisti stæin þannsi æft sun sinn."),
]


def test_same_word_in_different_normalizations():
    assert key("stæinn") == key("sten") == key("steinn")
    assert key("sin") == key("sinn") and key("þøsi") == key("þausi") and key("faður") == key("faþur")
    assert key("æftiR") == key("eptir")
    assert key("isi") != key("es") and key("lifa") != key("lefa")


def test_sections_drop_alternative_readings_and_groups_follow_the_dividers():
    assert [lab for lab, _ in sections("§P a : b §Q c : d")] == ["-"]
    assert carved_groups("þurir raisþi : stain¶þansi") == ["þurirraisþi", "stainþansi"]
    assert pairs(RECS[0])[:3] == [("þurir", "Þorir"), ("raisþi", "ræisti"), ("stain", "stæin")]


def test_spelling_learned_from_the_carvers():
    m = Model(RECS)
    spellings = m.spell.expand("stæin")
    assert max(spellings, key=spellings.get) == "stain"
    assert abs(sum(spellings.values()) - 1) < 1e-9


def test_decoding_finds_the_words_inside_an_undivided_group():
    m = Model(RECS[:-1])  # Asa's stone is not in training
    logZ, path, post, text = decode(m, ["asaraisþistainþansi", "aft", "sunsin"])
    words = [w for _, _, w, _ in path]
    assert words[1:] == ["ræisti", "stæin", "þannsi", "æft", "sun", "sinn"]
    assert all(0 <= p <= 1 + 1e-9 for _, _, _, p in path) and math.isfinite(logZ)
    # the posteriors of the words that cover each rune sum to at most one
    for i in range(len(text)):
        assert sum(p for (a, b, _), p in post.items() if a <= i < b) <= 1 + 1e-6


def test_a_divider_is_evidence_for_a_word_boundary():
    m = Model(RECS)
    with_div = decode(m, ["stain", "þansi"])[0]
    without = decode(m, ["stainþansi"])[0]
    assert m.d > 0.5 and with_div > without


def test_dating_strings_and_epochs():
    from src.runlm import epoch, years
    assert years("V 1065-1075") == (1065, 1075) and years("V s 1000-t") == (1066, 1099)
    assert years("V inte före 915/920") == (915, 965) and years("V Helnæs-Gørlev") == (750, 900)
    assert epoch({"period": "V", "dating": "V 800-t"}) == "800"
    assert epoch({"period": "V", "dating": "V", "style": "Pr4"}) == "1100"
    assert epoch({"period": "V", "dating": "V 800-900-t"}) is None  # too wide to place
    assert epoch({"period": "M", "dating": "M"}) == "M"


def test_alignment_survives_damaged_and_restored_words():
    from src.runlm import align
    got = align(["þurir", "...", "stain", "þansi", "----", "faþur"], ["Þorir", "ræisti", "stæin", "þannsi", "æft", "faður"])
    assert ("þurir", "Þorir") in got and ("stain", "stæin") in got and ("faþur", "faður") in got
    assert all(a[0] != "." and a[0] != "-" for a, _ in got)


def test_epochs_are_weighed_by_how_probable_the_text_is():
    from src.runlm import EPOCHS, decode_epochs
    early = [dict(r, dating="V 800-t", signum=f"E {i}") for i, r in enumerate(RECS[:4])]
    late = [_rec(f"L {i}", "þurir : rist : stin : þansi : eftiR : faþur : sin", "Þorir ræisti stæin þannsi æftiR faður sinn.")
            for i in range(4)]
    for r in late:
        r["dating"] = "V 1100-t"
    m = Model(early + late, contexts=True, aligned=True)
    _, path, post, text, ep_post, ll = decode_epochs(m, ["þurir", "rist", "stin", "þansi", "eftiR", "faþur", "sin"])
    assert abs(sum(ep_post.values()) - 1) < 1e-9 and set(ll) == set(EPOCHS)
    assert ep_post["1100"] > ep_post["800"]


def test_a_name_never_seen_is_composed_of_known_name_elements():
    from collections import Counter
    from src.runlm import NameModel, Spelling
    seen = Counter({"þorbiorn": 3, "þorstæinn": 3, "þorulfR": 3, "asbiorn": 3, "asstæinn": 2, "asulfR": 2,
                    "sigbiorn": 2, "sigulfR": 2, "gunnbiorn": 2, "gunnstæinn": 2, "gunnmundr": 1, "asmundr": 1})
    nm = NameModel(seen, Spelling([]))
    assert {"þor", "as"} <= set(nm.first) and {"biorn", "stæinn"} <= set(nm.second)
    got = nm.candidates("kunulfR")  # Gunnulfr is not among the names seen
    assert "gunnulfR" in got


def test_name_parts_are_spelled_as_the_carvers_spelled_them():
    from collections import Counter
    from src.runlm import NameModel, Spelling
    # women's names in -ví keep their second element (not Ragn + v + i)
    seen = Counter({"ragnvaldr": 3, "ragnhildr": 3, "þorvaldr": 2, "þorhildr": 2, "kætilvi": 3, "þyrvi": 3, "arnvi": 3,
                    "kætilbiorn": 2, "arnbiorn": 2, "þyrbiorn": 1})
    plain = NameModel(seen, Spelling([]), min_share=2)
    assert "vi" in plain.second and "ragn" in plain.first
    # the carvers wrote Ragn- with h (rahnualtr); without their spellings the name cannot be read in that form
    carved = [("ragnvaldr", "rahnualtr"), ("ragnhildr", "rahnhiltr"), ("ragnvaldr", "rahnualtr"), ("kætilvi", "kitilui")]
    learned = NameModel(seen, Spelling([]), min_share=2, carved=carved)
    assert "ragnvi" not in plain.candidates("rahnui")
    assert "ragnvi" in learned.candidates("rahnui")


def test_an_overconfident_dating_is_softened():
    import random
    from src.runlm import EPOCHS, epoch_posterior, fit_temperature
    rng = random.Random(1)
    rows = []
    for _ in range(300):  # the model always says 'sure', but is right only 60 % of the time
        true = rng.choice(EPOCHS)
        said = true if rng.random() < 0.6 else rng.choice([e for e in EPOCHS if e != true])
        rows.append({"true": true, "ll": {e: (0.0 if e == said else -12.0) for e in EPOCHS}, "prior": {e: 1 for e in EPOCHS}})
    T = fit_temperature(rows, use_prior=False)
    p = epoch_posterior(rows[0]["ll"], None, T)
    assert T > 3 and 0.45 < max(p.values()) < 0.75


def test_lost_runes_are_filled_from_the_language():
    from src.runlm import restore, restore_all
    m = Model(RECS)
    res = restore(m, ["þurir", "raisþi", "s??in", "þansi", "aft", "faþur", "sin"], (2, 1, 3))
    assert res[0][0] == "ta" and abs(sum(p for _, p in res) - 1) < 1e-9
    combos, gaps, words = restore_all(m, ["þurir", "raisþi", "s??in", "þansi", "aft", "faþur", "s?n"])
    assert len(gaps) == 2 and combos[0][0] == ("ta", "i")
    assert max(words[0], key=words[0].get) == "stæin" and abs(sum(words[1].values()) - 1) < 1e-9
    # what is visible of the lost runes limits the fillings: here only i/e and n/h are possible
    res = restore(m, ["þurir", "raisþi", "s??in", "þansi", "aft", "faþur", "sin"], (2, 1, 3), allowed=["ie", "hn"])
    assert {f[0] for f, _ in res} <= set("ie") and {f[1] for f, _ in res} <= set("hn")
    # nothing visible of the first rune: it is unconstrained
    res = restore(m, ["þurir", "raisþi", "s??in", "þansi", "aft", "faþur", "sin"], (2, 1, 3), allowed=[None, "a"])
    assert res[0][0] == "ta" and all(f[1] == "a" for f, _ in res)


def test_two_runs_filled_as_one_keep_a_word_each():
    from src.runlm import merge_runs, restore_all
    m = Model(RECS)
    # aft and faþur in one undivided group, one rune lost in each: the runs are filled as one gap
    work, spans, cons, _ = merge_runs(["þurir", "raisþi", "stain", "þansi", "af?fa?ur", "sin"], [(4, 2, 3), (4, 5, 6)])
    assert spans == [(4, 2, 6)]
    pos = {}
    combos, gaps, words = restore_all(m, work, only=spans, allowed=cons, positions=pos)
    assert combos[0][0] == ("tfaþ",)
    # the gap's word is the one where it starts; each position has the word that stands there
    assert max(words[0], key=words[0].get) == "æft"
    assert [max(d, key=d.get) for d in pos[0]] == ["æft", "faður", "faður", "faður"]


def test_soft_traces_overrule_a_misread_trace_but_never_a_preserved_rune():
    from src.runlm import merge_runs, restore_all
    m = Model(RECS)
    work, spans, cons, _ = merge_runs(["þurir", "raisþi", "stain", "þansi", "af?fa?ur", "sin"], [(4, 2, 3), (4, 5, 6)])
    # the first lost rune misread as n; the preserved f and a inside the gap are certain
    wrong = {spans[0]: ["n", "f", "a", None]}
    hard_only = restore_all(m, work, only=spans, allowed=wrong)[0]
    soft = restore_all(m, work, only=spans, allowed=wrong, trace_eps=0.05, hard={spans[0]: [1, 2]})[0]
    assert hard_only[0][0][0][0] == "n"   # a hard trace rules out the right rune
    assert soft[0][0] == ("tfaþ",)         # a soft one lets the language overrule it
    assert all(f[1:3] == "fa" for f in [c[0][0] for c in soft])  # the preserved runes never change


def test_the_reading_weighs_a_soft_trace_as_the_gap_does():
    from src.runlm import restore_all
    m = Model(RECS)
    work = ["kunar", "raisþi", "stain", "aft", "s?n", "sin"]
    assert restore_all(m, work)[0][0][0] == ("u",)  # without traces the language says sun
    det = {}
    combos = restore_all(m, work, allowed={(4, 1, 2): ["i"]}, trace_eps=0.01, details=det)[0]
    # a trace of i, strong enough to win in the gap, also wins the reading of the whole text
    assert det[0][0][0] == "i" and combos[0][0] == ("i",)
    assert abs(combos[0][1] - det[0][0][1]) < 0.01


def _parallel(signum, translit, norm, en):
    return {"signum": signum, "period": "V", "transliteration": translit, "normalization": norm, "translation_en": en}


PAR = [
    _parallel("P 1", "þurir : raisþi : stain : þansi : aft : faþur : sin", '"Þorir ræisti stæin þannsi æft faður sinn.',
              "Þórir raised this stone in memory of his father."),
    _parallel("P 2", "kunar : raisþi : stain : aft : sun : sin", '"Gunnarr ræisti stæin æft sun sinn.',
              "Gunnarr raised the stone in memory of his son."),
    _parallel("P 3", "asa : raisþi : stain : þansi : aft : sun : sin", '"Asa ræisti stæin þannsi æft sun sinn.',
              "Ása raised this stone in memory of her son."),
    _parallel("P 4", "ulfr : raisþi : stain : aft : bruþur : sin", '"UlfR ræisti stæin æft broður sinn.',
              "Ulfr raised the stone in memory of his brother."),
    _parallel("P 5", "þurir : raisþi : stain : aft : bruþur : sin", '"Þorir ræisti stæin æft broður sinn.',
              "Þórir raised the stone in memory of his brother."),
    _parallel("P 6", "kunar : raisþi : stain : aft : faþur : sin", '"Gunnarr ræisti stæin æft faður sinn.',
              "Gunnarr raised the stone in memory of his father."),
]


def test_the_glossary_learns_meanings_from_texts_and_their_translations():
    from src.rungloss import Glossary
    g = Glossary(PAR)
    assert g.gloss("faður")[0][0] == "father" and g.gloss("sun")[0][0] == "son" and g.gloss("broður")[0][0] == "brother"
    # words that always stand together (ræisti, stæin, æft, sinn here) cannot be told apart; in Rundata they vary
    assert "asa" in g.names and g.translate(["asa", "sun"], "sv") == "Ása son"


DA_ROWS = ["Thore rejste denne sten efter sin fader.", "Gunnar rejste stenen efter sin søn.",
           "Åse rejste denne sten efter sin søn.", "Ulv rejste stenen efter sin broder.",
           "Thore rejste stenen efter sin bror.", "Gunnar rejste stenen efter sin far."]


def test_danish_translations_are_matched_learned_and_put_in_swedish(tmp_path):
    from src.rungloss import Glossary, _danish, _sv_name, load_danish, ows_map, swedish
    recs = [dict(r, references=f"DK nr.: T {i + 1}, http://runer.ku.dk", normalization_ows=r["normalization"])
            for i, r in enumerate(PAR)]
    table = tmp_path / "indskrifter.txt"
    sep = " " * 8
    table.write_text("\ufeff" + "\n".join(f"T {i + 1}{sep}runer{sep}{da}{sep}English" for i, da in enumerate(DA_ROWS))
                     + f"\nT 99{sep}...{sep}Utolket.{sep}...\n", encoding="utf-8")
    da_tr = load_danish(recs, str(table))
    assert da_tr["P 1"] == DA_ROWS[0] and len(da_tr) == 6  # matched by 'DK nr.'; T 99 is neither in Rundata nor read
    da = Glossary([dict(r, translation_da=da_tr[r["signum"]]) for r in recs], field="translation_da", words=_danish,
                  src="normalization_ows")
    # bror/broder and far/fader are counted as one word
    assert da.gloss("faður")[0][0] == "fader" and da.gloss("broður")[0][0] == "broder" and da.gloss("sun")[0][0] == "søn"
    assert ows_map(recs)["stæin"] == "stæin"
    assert _sv_name("Thorbjørn") == "Torbjörn" and _sv_name("Svend") == "Sven" and _sv_name("Ødbjørn") == "Ödbjörn"
    # Old Norse puts the possessive after the noun; Swedish before it, with a comma after a name
    en = Glossary(PAR)
    en.t["sinn"] = {"his": 1.0}  # in these six texts sinn always stands with ræisti, so its meaning is not learned
    assert swedish(["asa", "sun", "sinn"], en) == "Ása, sin son"
    assert swedish(["faður", "sinn"], en) == "sin fader"


def test_same_word_allows_another_case_form_or_normalization():
    from src.runlm import same_word
    assert same_word("vigbiorn", "Vig[b]iarn") and same_word("guðmundr", "Guðmu[nda]R") and same_word("stæinn", "stæi[n]")
    assert not same_word("þæiR", "[G]æi[RR]") and not same_word("tiugu", "[k]u[n]u") and not same_word("<unk>", "ok")


def test_names_from_nearby_stones():
    m = Model([dict(r, lat=59.0, lon=18.0) for r in PAR])
    near, spell = m.names_near(59.01, 18.01, km=5)
    far, _ = m.names_near(62.0, 15.0, km=5)
    assert "þorir" in near and "þurir" in spell and not far
