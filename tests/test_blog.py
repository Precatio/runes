"""Månadens fynd (api/routers/blog.py): utkastet ur mönstren, och de nya mönstren om strand och lämningar."""
from api.routers import blog
from src import r_findings as rf


def _pattern(key, status, replicated=None, topic="Förändring"):
    return {"key": key, "topic": topic, "status": status, "replicated": replicated,
            "text": f"Draget {key} blir vanligare över tid (q 0,01). Mer text.", "hypothesis": "En hypotes.",
            "test": "Ett sätt att pröva den."}


def test_draft_takes_what_is_new_or_changed():
    pats = [_pattern("a", "bekräftar", True), _pattern("b", "mönster att pröva", True), _pattern("c", "indikation"),
            _pattern("d", "bekräftar", True)]
    before = {"Förändring|a": "bekräftar", "Förändring|c": "mönster att pröva"}  # a unchanged, c changed, b and d new
    out = blog.build_draft("2026-11", pats, before, None)
    body = out["draft"]["body"]
    assert "Draget a" not in body
    assert body.index("Draget b") < body.index("Draget d") < body.index("Draget c")  # new patterns to test first
    assert out["draft"]["slug"].startswith("2026-11-") and out["draft"]["month"] == "2026-11"
    assert "3 mönster" in out["draft"]["summary"]
    assert any("tidigare mönster att pröva" in s for s in out["sources"])


def test_draft_mentions_the_map_shift_with_a_link():
    shift = {"key": "o_runa", "label": "o-runan för o", "early": 0.08, "late": 0.51, "n_early": 218, "n_late": 136}
    out = blog.build_draft("2026-11", [_pattern("b", "mönster att pröva")], {}, shift)
    assert "(/karta?pattern=o_runa&split=1)" in out["draft"]["body"] and "8 %" in out["draft"]["body"]


def test_slug_rules():
    assert blog.SLUG.match("2026-10-monoftong-i-nagot-ai-ord")
    assert not blog.SLUG.match("Med Versaler") and not blog.SLUG.match("-borjar-med-streck")
    assert blog._slug("Ög 136: Rökstenen och Þórr") == "og-136-rokstenen-och-orr"


def test_viking_shore_pattern():
    today = {"median_stones_km": 4.16, "median_random_km": 5.6}
    v = {"n_stones": 2254, "median_stones_km": 3.6, "median_random_km": 5.25, "p": 1e-28,
         "provinces": [{"province": "U", "n": 1177, "p": 1e-30, "median_stones_km": 3.36, "median_random_km": 6.37},
                       {"province": "Sm", "n": 121, "p": 0.15, "median_stones_km": 5.5, "median_random_km": 5.7}]}
    (pt,) = rf._viking_shore(v, today, [{"province": "U", "median_stones_km": 4.26, "median_random_km": 6.69}])
    assert pt["status"] == "mönster att pröva" and "tydligare" in pt["text"] and "1 av 2 landskap (U)" in pt["text"]
    assert "I U (1177 stenar): 64 % med dagens vatten, 53 % omkring år 1000." in pt["text"]
    assert rf._viking_shore({}, today) == []


def test_remains_patterns():
    r = {"available": True, "near_km": 0.5, "note": "Lämningarna …",
         "distances": [{"key": "gravfalt", "near_stones": 0.59, "near_random": 0.21, "median_stones_km": 0.38,
                        "median_random_km": 1.09, "q_bh": 1e-200},
                       {"key": "hog", "near_stones": 0.32, "near_random": 0.08, "median_stones_km": 0.8,
                        "median_random_km": 1.9, "q_bh": 1e-100},
                       {"key": "vag", "near_stones": 0.16, "near_random": 0.07, "median_stones_km": 1.4,
                        "median_random_km": 2.0, "q_bh": 1e-50}],
         "tests": {"time_gravfalt": {"or": 0.88, "q_bh": 0.37, "periods": {"early": 0.56, "late": 0.62}},
                   "christian_gravfalt": {"or": 1.2, "q_bh": 0.37},
                   "bridge_vag": {"or": 2.1, "lo": 1.4, "hi": 3.1, "q_bh": 0.0014, "halves": {"replicated": True}}},
         "gravfalt_provinces": [{"province": "U", "p": 1e-90, "near_stones": 0.69, "near_random": 0.26}]}
    pats = {p["key"]: p for p in rf._remains(r)}
    g, b = pats["remains_graves"], pats["remains_bridges"]
    assert g["status"] == "bekräftar" and "59 %" in g["text"] and "lika stor för stenar med kristna markörer" in g["text"]
    assert b["status"] == "mönster att pröva" and b["replicated"] is True and "oddskvot 2,10" in b["text"]
    assert rf._remains({"available": False}) == []


def test_cult_patterns():
    t = lambda o, rep, q=0.01, **kw: {"or": o, "lo": o * 0.6, "hi": o * 1.7, "p": q, "q_bh": q, "n": 1563,
                                      "halves": {"replicated": rep}, "share_near": 0.28, "share_far": 0.15, "n_near": 74, **kw}
    c = {"available": True, "near_km": 2,
         "tests": {"prayer_a": t(2.23, True, n_places=20, loo={"min_or": 1.89, "max_or": 2.55}),
                   "prayer_central": t(1.27, False, q=0.27), "prayer_a_central": t(2.29, True),
                   "christian_a": t(1.74, False, q=0.05)},
         "radius": [{"km": 1, "n_near": 25, "or": 1.68, "p": 0.28}, {"km": 3, "n_near": 161, "or": 1.37, "p": 0.14}],
         "pagan": [{"signum": "Sö 140", "km_a": 1.2, "km_b": 3.0}, {"signum": "U 1161", "km_a": 6.0, "km_b": 4.0}],
         "churches": {"n_churches": 444, "near_church_other": 0.025, "near_km": 1,
                      "rows": [{"tier": "A", "n": 67, "near_church": 0.09, "or": 3.8, "p": 0.007}]}}
    pats = {p["key"]: p for p in rf._cult(c)}
    pr, ch = pats["cult_prayer"], pats["cult_churches"]
    assert pr["status"] == "mönster att pröva" and pr["replicated"] is True
    assert "28 % mot 15 %" in pr["text"] and "inte vanligare (oddskvot 1,27)" in pr["text"]
    assert "hänger alltså delvis på radien" in pr["note"] and "i 1 fall: Sö 140." in pr["note"]
    assert ch["status"] == "indikation" and "oddskvot 3,80" in ch["text"]
    assert rf._cult({"available": False}) == []


def test_draft_has_the_boxes():
    out = blog.build_draft("2026-11", [_pattern("b", "mönster att pröva", True)], {}, None)
    body = out["draft"]["body"]
    assert ":::box Kort sagt\n- Draget b blir vanligare över tid.\n:::" in body and ":::box Så säkra är vi" in body
    assert ":::box In short" in out["draft"]["body_en"]


def test_pictures_go_after_the_paragraph_that_names_the_stone():
    text = "Intro.\n\n:::box Kort sagt\nNämner U 431.\n\n- punkt\n:::\n\nHär står U 431 och U 4310.\n\nSlut."
    out = blog.insert_picture(text, "U 431", "![Runstenen U 431](https://upload.wikimedia.org/x.jpg)\nU 431. Foto: X.")
    parts = out.split("\n\n")
    assert parts[parts.index("Här står U 431 och U 4310.") + 1].startswith("![Runstenen U 431]")
    assert blog.insert_picture("Inget här.", "U 431", "![b](u)").endswith("\n\n![b](u)")
    img = {"signum": "U 431", "markdown": "![sv](u)", "markdown_en": "![en](u)"}
    d = blog.with_pictures({"body": "Se U 431.", "body_en": "See U 431."}, [img])
    assert d["body"] == "Se U 431.\n\n![sv](u)" and d["body_en"] == "See U 431.\n\n![en](u)"


def test_commons_pictures_carry_photographer_and_licence(tmp_path, monkeypatch):
    from src import commons
    monkeypatch.setattr(commons, "CACHE", str(tmp_path))
    monkeypatch.setattr(commons, "wikidata_files", lambda signa: {"U 431": "U 431, Åshusby.JPG", "U 1": "U 1.jpg"})
    monkeypatch.setattr(commons, "commons_info", lambda files: {
        "U 431, Åshusby.JPG": {"thumb": "https://upload.wikimedia.org/a/U_431.JPG", "page": "https://commons.wikimedia.org/wiki/File:U_431%28a%29.JPG",
                               "author": "Berig", "licence": "CC BY 3.0", "licence_url": "https://creativecommons.org/licenses/by/3.0"},
        "U 1.jpg": {"thumb": "https://upload.wikimedia.org/b.jpg", "page": "p", "author": "X", "licence": "All rights reserved"}})
    imgs = commons.stone_images(["U 431", "U 1", "U 2"])
    assert [i["signum"] for i in imgs] == ["U 431"]  # U 1 is not freely licensed, U 2 has no picture
    assert imgs[0]["markdown"].startswith("![Runstenen U 431](https://upload.wikimedia.org/a/U_431.JPG)\nU 431. Foto: Berig, ")
    assert "[CC BY 3.0](https://creativecommons.org/licenses/by/3.0)" in imgs[0]["markdown"] and "Photo: Berig" in imgs[0]["markdown_en"]
    assert commons.signa_in("Se U 344 och Sö 101, men inte U344; Ög 136 och U 649B.") == ["U 344", "Sö 101", "Ög 136", "U 649B"]
    assert commons._url("https://x.org/File:A_(b).jpg?utm_source=c&w=1") == "https://x.org/File:A_%28b%29.jpg?w=1"


def test_prayer_is_found_in_its_spellings():
    from src.language_profile import _value
    for text in ("guð hiælpi sal hans", "guð hialpin sialu hans", "kristr hialp and!", "... hialpi sialu hans", "guðs moðir"):
        assert _value("bon", {}, text, []) == "ja", text
    assert _value("bon", {}, "guðlaug let ræisa stæin", []) == "nej"
    assert _value("sjal", {}, "guð hiælpi sal hans", []) == "ja"
    assert _value("sjal", {}, "hann gærði bro fyrir and hans", []) == "nej"


def test_prayer_and_the_age_of_the_churches():
    term = lambda o, p, rep=None: {"or": o, "lo": o * 0.85, "hi": o * 1.17, "p": p, **({"halves": {"replicated": rep}} if rep is not None else {})}
    c = {"available": True, "near_km": 2, "tests": {"prayer_a": {"or": None}},
         "churches": {"n_churches": 444, "near_church_other": 0.025, "near_km": 1, "rows": [],
                      "age": {"early_year": 1200, "n_early": 267, "n_late": 177, "near_km": 2, "tests": [
                          {"feature": "bon", "label": "Kristen bön", "n": 780, "early": term(1.23, 0.008, False),
                           "late": term(1.0, 0.98), "early_time": term(1.31, 0.014), "ratio": 1.23, "p_diff": 0.04,
                           "share_early": 0.25, "n_early": 130, "share_late": 0.19, "n_late": 80, "share_none": 0.15, "n_none": 570},
                          {"feature": "kors", "label": "Kors", "n": 1144, "early": term(1.02, 0.75), "late": term(1.05, 0.38)}]}}}
    (p,) = [x for x in rf._cult(c) if x["key"] == "prayer_early_churches"]
    assert p["status"] == "indikation" and "1,23 (1,05–1,44)" in p["text"] and "Håller inte i båda halvorna" in p["text"]
    assert "Korset följer varken de tidiga" in p["note"]


def _res():
    return {"change": {"features": [
                {"key": "bon", "label": "Kristen bön", "time": {"draws": {"n": 10, "share_sig": 1}, "by_style": [
                    {"style": "RAK", "year": 998, "n": 169, "share": 0.15}, {"style": "Pr2", "year": 1035, "n": 87, "share": 0.37},
                    {"style": "Pr4", "year": 1085, "n": 198, "share": 0.10}]}},
                {"key": "preposition", "label": "Prepositionen at", "provinces": {"rows": [
                    {"province": "U", "n_mid": 192, "share1050": 0.26}, {"province": "Sö", "n_mid": 97, "share1050": 0.58},
                    {"province": "Sm", "n_mid": 4, "share1050": 0.9}]}}]},
            "hotspots": {"nsim": 999, "patterns": [{"key": "r_for_R", "clusters": [
                {"center": "U 768", "radius_km": 22, "n": 52, "rate_in": 0.615, "rate_out": 0.125, "rr": 4.9, "provinces": {"U": 50, "Vs": 2}}]}]}}


def _p(topic, key, status="mönster att pröva", replicated=True, **kw):
    return {"topic": topic, "key": key, "status": status, "replicated": replicated, "text": f"{key} är ett mönster. Mer.",
            "hypothesis": "Vi föreslår något.", "test": "Pröva så här.", "note": "Ett förbehåll.",
            "significance": {"label": "q 0,01"}, **kw}


def test_topics_are_patterns_that_hold():
    from src import blog_topics as bt
    pats = [_p("Förändring", "bon", "bekräftar"), _p("Förändring", "stungen_e", "bekräftar"), _p("Förändring", "stungna", "bekräftar"),
            _p("Geografi", "hotspot_r_for_R_U 768"), _p("Regional skillnad", "preposition"),
            _p("Geografi", "water", "bekräftar", None), _p("Attribuering", "model", "bekräftar"),
            _p("Okända ristare", "anonymous", replicated=None), _p("Förändring", "x", "indikation"),
            _p("Geografi", "y", replicated=False)]
    keys = [c["key"] for c in bt.candidates(pats, _res(), used={"Förändring|bon"})]
    assert keys[:3] == ["Geografi|hotspot_r_for_R_U 768", "Regional skillnad|preposition", "Okända ristare|anonymous"]
    assert "Förändring|stungen_e" not in keys          # covered by stungna
    assert "Geografi|water" not in keys and "Attribuering|model" not in keys and "Geografi|y" not in keys
    assert keys[-1] == "Förändring|bon"                # already written, last


def test_topic_charts_and_draft():
    from src import blog_topics as bt
    res = _res()
    c = bt.chart(_p("Förändring", "bon", "bekräftar"), res)
    assert c.startswith(":::chart Andel runstenar med mönstret (Kristen bön), efter stilgrupp") and "+Pr2, omkring 1035 | 37 | 87 stenar" in c
    c = bt.chart(_p("Regional skillnad", "preposition"), res, provinces={"Sö": "Södermanland", "U": "Uppland"})
    assert "+Södermanland | 58 | 97 stenar" in c and "Uppland | 26" in c and "Sm" not in c  # under 10 mid-period stones
    c = bt.chart(_p("Geografi", "hotspot_r_for_R_U 768"), res, label="r för ʀ")
    assert "+Inom klustret (U 768, 22 km) | 62 | 52 stenar" in c and "Övriga stenar | 12" in c
    assert bt.chart(_p("Geografi", "areas"), res) == ""
    d = bt.draft(_p("Förändring", "bon", "bekräftar"), res, "sv", map_keys=frozenset({"bon"}))
    body = d["body"]
    for part in (":::box Kort sagt", ":::chart", ":::box Så säkra är vi", "## Vår hypotes", "## En första prövning",
                 "## Så kan hypotesen prövas vidare", "1. **Det direkta provet.**", "## Förbehåll", "## Se själv",
                 "](/karta?pattern=bon&mode=tid)", "## Källor och data", "Gräslund, A.-S. 2006", "Holm, S. 1979",
                 "10 av 10 omräkningar"):
        assert part in body, part
    en = bt.draft(_p("Geografi", "hotspot_r_for_R_U 768"), res, "en", map_keys=frozenset({"r_for_R"}))["body"]
    assert ":::box In short" in en and "mode=kluster" in en and "Kulldorff, M. 1997" in en and "## A first test" in en


def test_topic_draft_has_the_published_form():
    from src import blog_topics as bt
    res = _res()
    ex = {"signum": "U 792", "place": "Ulunda", "province": "Uppland", "style": "Pr2", "years": (1020, 1050), "carver": "Balle",
          "normalization": "Karr let ræisa stæin þenna", "translation_en": "Karr had this stone raised",
          "picture": "![Runstenen U 792](https://upload.wikimedia.org/a.jpg)\nU 792 vid Ulunda i Uppland. Foto: Berig, CC BY 2.5.",
          "picture_en": "![The runestone U 792](https://upload.wikimedia.org/a.jpg)\nU 792 at Ulunda in Uppland. Photo: Berig, CC BY 2.5."}
    fig = "![r för ʀ – var mönstret samlas](/api/blog/figures/0123456789abcdef.png)\nr för ʀ – var mönstret samlas. Källa: …"
    mix = {"n": 32, "with_carver": 26, "carvers": 8, "top": "Erik", "top_n": 13}
    p = _p("Geografi", "hotspot_r_for_R_U 768", text="r för ʀ klustrar: inom 22 km har 62 % mönstret, mot 12 %. Mer.")
    d = bt.draft(p, res, "sv", label="r för ʀ", provinces={"U": "Uppland"}, map_keys=frozenset({"r_for_R"}),
                 example=ex, figure=fig, mix=mix)
    b = d["body"]
    assert d["title"] == "r för ʀ – ett kluster i Uppland"
    assert b.index("*Karr let ræisa stæin þenna*") < b.index("Så står det – i Rundatas normalisering – på runstenen U 792")
    assert "ristad någon gång mellan 1020 och 1050 att döma av ornamentiken och tillskriven ristaren Balle" in b
    assert b.index("![Runstenen U 792]") < b.index(":::box Kort sagt") < b.index("## Ett kluster i Uppland") < b.index(fig)
    assert b.index(fig) < b.index(":::box Så säkra är vi") < b.index("## Vår hypotes") < b.index("## En första prövning")
    assert "26 en säker ristare i Rundata, fördelade på 8 ristare; den vanligaste, Erik, står för 13" in b
    assert "\n> Mönstret började hos en ristare och spreds till andra i samma bygd." in b
    assert "- Vår hypotes: vi föreslår något. Den kan prövas." in b  # lower case after the colon


def test_sharpened_and_main_clause():
    from src import blog_topics as bt
    assert bt.sharpened("Vi föreslår att signaturerna blev vanliga när runristning blev ett yrke. Mer.") == \
        "Signaturerna blev vanliga när runristning blev ett yrke"
    assert bt.main_clause("o-runan för o-ljud (broþur för bruþur) blir vanligare över tid, med plats: 4 % och 43 %. Mer.") == \
        "o-runan för o-ljud blir vanligare över tid, med plats"
    assert bt.main_clause("Prepositionen at (i stället för æftiR): landskapen skiljer sig (q < 0,001), mer.") == \
        "Prepositionen at: landskapen skiljer sig"


def test_examples_follow_the_pattern_values():
    from src import blog_examples as be
    rec = {"signum": "U 1", "carvers": [{"name": "Öpir", "kind": "S", "uncertain": False}], "cross_form": "kors"}
    assert be.has_pattern(rec, "cross", {"yes": "1"}, frozenset())
    from unittest import mock
    with mock.patch("src.language_profile.traits", return_value={"o_runa": "båda"}):
        assert be.has_pattern(rec, "o_runa", {"yes": "o-runa, båda"}, frozenset())
        assert not be.has_pattern(rec, "o_runa", {"yes": "o-runa"}, frozenset())
    assert be.certain_carver(rec) == "Öpir"


def test_frozen_figures_are_kept_by_content(tmp_path, monkeypatch):
    from src import blog_figures as bf
    monkeypatch.setattr(bf, "DIR", str(tmp_path))
    url = bf.freeze(b"\x89PNG fake")
    assert url.startswith("/api/blog/figures/") and url.endswith(".png") and bf.freeze(b"\x89PNG fake") == url
    assert bf.path_of(url.rsplit("/", 1)[1]) and bf.path_of("../etc.png") is None
    d = bf.describe("hotspot_r_for_R.png", {"r_for_R": "r för ʀ"})
    assert d["group"] == "map" and d["label"].startswith("r för ʀ – var mönstret samlas") and d["script"] == "hotspots.R"
    assert bf.describe("okänd.png") is None
    md = bf.markdown(url, d)
    assert md.startswith(f"![r för ʀ") and "Källa: Vitkis korpusanalys i R (hotspots.R)" in md
    res = {"hotspots": {"figures": {"hotspot_r_for_R": "hotspot_r_for_R.png"}}, "text": {"figures": {"a": "text_formler.png"}}}
    assert [x["name"] for x in bf.available(res, {"r_for_R": "r för ʀ"})] == ["hotspot_r_for_R.png", "text_formler.png"]


def test_indexnow_only_with_a_key_and_a_public_site(monkeypatch):
    monkeypatch.delenv("INDEXNOW_KEY", raising=False)
    assert blog.indexnow("x") is False
    monkeypatch.setenv("INDEXNOW_KEY", "abc123")
    monkeypatch.setenv("SITE_URL", "http://localhost:3000")
    assert blog.indexnow("x") is False
