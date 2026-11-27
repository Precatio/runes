"""Böjningslagret i sannolikhetsmodellen (src/runlm.py, textmodel-24-kandidat, analysplaner/2026-11-27-bojningsmodellen-tm24.md):
av som standard, nya former ur ändelseväxlingar i träningens egna former, och inga former från provstenar."""
import math

from src.runlm import CharKN, Model, decode, ending_alternations, inflection_gap, key, p_ending

from tests.test_runlm import RECS, _rec

# stæinaR and stæinuR carved alike (twice each): the model counts them as one word, so aR ~ uR is an ending alternation
ALT = [_rec(f"A {i}", "þurir : raisþi : stainaR : aft : faþur : sin", "Þorir ræisti stæinaR æft faður sinn.") for i in range(2)] + \
      [_rec(f"B {i}", "þurir : raisþi : stainaR : aft : faþur : sin", "Þorir ræisti stæinuR æft faður sinn.") for i in range(2)]
VIF = [_rec(f"V {i}", "uifrþaR : raisþi : stain : aft : sun : sin", "VifriðaR ræisti stæin æft sun sinn.") for i in range(2)]
TOY = RECS + ALT + VIF


def test_off_by_default_and_identical():
    a, b = Model(TOY, tolerance=0.02), Model(TOY, tolerance=0.02, lam_infl=0.0, infl_min=0.02, infl_mu=0.5)
    assert a.lam_infl == b.lam_infl == 0.0 and not a.infl_src and not b.infl_src and not b.infl_stats
    assert dict(a.index) == dict(b.index) and a.rule_z == b.rule_z
    for w, prev in (("stæin", "ræisti"), ("sinn", "sun"), ("vifriðaR", "<s>")):
        assert a.p_word(w, prev) == b.p_word(w, prev)
        assert a.lemma(w) == b.lemma(w) == b.lemma_base(w)
    groups = ["uifrþuR", "raisþi", "stain", "aft", "sun", "sin"]
    la, pa, posta, _ = decode(a, groups)
    lb, pb, postb, _ = decode(b, groups)
    assert la == lb and pa == pb and posta == postb


def test_an_alternation_learned_from_one_word_makes_a_new_form_of_another():
    m = Model(TOY, tolerance=0.02, lam_infl=0.05, infl_min=0.05)
    assert m.lemma("stæinaR") == m.lemma("stæinuR")
    assert m.infl_alt["aR"]["uR"] == 1 and p_ending(m.infl_alt, "aR", "uR") >= 0.05
    assert "vifriðaR" in m.uni and "vifriðuR" not in m.uni
    assert m.infl_src["vifriðuR"] == {"vifriðaR": 1.0} and m.infl_base["vifriðuR"] == "vifriðaR"
    # its own word (not <unk>), spelled as a runic normalization, and P(w′ | prev) = λ · P(w | prev) · share
    assert m.lemma("vifriðuR") == key("vifriðuR") != m.lemma("vifriðaR")
    assert math.isclose(m.p_word("vifriðuR", "<s>"), 0.05 * m.p_word("vifriðaR", "<s>"))
    # the carved uifrþuR (Malt's spelling, the i not written) is reached through the tolerance layer's vowel rule
    c = m.candidates("uifrþuR", m.ctx(()))
    assert c.get("vifriðuR", 0.0) > 0.0
    _, path, _, _ = decode(m, ["uifrþuR", "raisþi", "stain", "aft", "sun", "sin"])
    assert path[0][2] == "vifriðuR"
    # without the layer the form has no identity
    _, path0, _, _ = decode(Model(TOY, tolerance=0.02), ["uifrþuR", "raisþi", "stain", "aft", "sun", "sin"])
    assert path0[0][2] != "vifriðuR"
    # pooled with its source form only when asked
    assert Model(TOY, tolerance=0.02, lam_infl=0.05, infl_pool=True).lemma("vifriðuR") == m.lemma("vifriðaR")


def test_the_lexicon_mass_is_shared_with_the_layer():
    off, on = Model(TOY), Model(TOY, lam_infl=0.05)
    # every known word gives up the share λ_böj, as the Edda and literature weights take theirs
    assert math.isclose(on.p_word("stæin", "ræisti") / off.p_word("stæin", "ræisti"),
                        (1 - off.lam_edda - off.lam_unk - 0.05) / (1 - off.lam_edda - off.lam_unk), rel_tol=1e-9)
    # the shares of each source form sum to one over its new forms
    tot = {}
    for src in on.infl_src.values():
        for b, q in src.items():
            tot[b] = tot.get(b, 0.0) + q
    assert tot and all(math.isclose(v, 1.0) for v in tot.values())


def test_no_form_or_alternation_from_a_held_out_stone():
    # the stones that show stæinuR held out: no alternation aR ~ uR, no new form vifriðuR
    m = Model(TOY, tolerance=0.02, lam_infl=0.05, exclude=[r["signum"] for r in ALT[2:]])
    assert "stæinuR" not in m.uni and "uR" not in m.infl_alt.get("aR", {}) and "vifriðuR" not in m.infl_src
    # the Vifriðr stones held out: the source form is not known, so nothing is made from it
    m = Model(TOY, tolerance=0.02, lam_infl=0.05, exclude=[r["signum"] for r in VIF])
    assert "vifriðaR" not in m.uni and not any("vifrið" in w for w in m.infl_src)
    assert all(b in m.uni for src in m.infl_src.values() for b in src)


def test_inflection_gaps_and_the_letter_model():
    forms = {"stæinaR", "stæinuR", "vifriðaR", "sun"}
    alt, stems = ending_alternations(forms, lambda w: key(w)[:4])
    assert set(alt) == {"aR", "uR"} and ("stæin", "aR") in stems["stæinaR"]
    keys = {key(w) for w in forms}
    assert inflection_gap("vifriðuR", forms, keys, sorted(alt))       # its stem is known
    assert inflection_gap("sunn", forms, keys, sorted(alt))           # another normalization of a known form
    assert not inflection_gap("sun", forms, keys, sorted(alt))        # a training form
    assert not inflection_gap("kumbl", forms, keys, sorted(alt))      # a word the training lacks altogether
    ch = CharKN(["stæinaR", "stæinuR", "sun", "sunu", "faður"])
    assert ch.logp("stæinaR") > ch.logp("xqzzR") and math.isfinite(ch.logp("vifriðuR"))
