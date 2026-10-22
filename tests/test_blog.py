"""Artiklarna (api/routers/blog.py): utkastet ur mönstren, publiceringstiden och de nya mönstren om strand och lämningar."""
import datetime as dt
import json
import os
import re

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
    assert not out["draft"]["slug"].startswith("2026-") and out["draft"]["slug"]  # the address no longer carries a month
    assert "3 mönster" in out["draft"]["summary"]
    assert any("tidigare mönster att pröva" in s for s in out["sources"])


APP_LINK = re.compile(r"\]\(/(?!artiklar|api/blog/figures)")  # the public website has no app to link to


def test_draft_mentions_the_map_shift_without_linking_into_the_app():
    shift = {"key": "o_runa", "label": "o-runan för o", "early": 0.08, "late": 0.51, "n_early": 218, "n_late": 136}
    out = blog.build_draft("2026-11", [_pattern("b", "mönster att pröva")], {}, shift)
    body = out["draft"]["body"]
    assert "mönsterkartan gäller o-runan för o" in body and "8 %" in body
    assert not APP_LINK.search(body) and "](https://github.com/Precatio/runes)" in body


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
    assert commons.signa_in("Ög Fv1958;252 och DR NOR1998;21") == ["Ög Fv1958;252", "DR NOR1998;21"]


def test_several_photos_per_stone_photos_before_drawings(tmp_path, monkeypatch):
    from src import commons
    monkeypatch.setattr(commons, "CACHE", str(tmp_path))
    monkeypatch.setattr(commons, "wikidata_items", lambda signa: {
        "U 29": {"file": "U 29, Hillersjö (drawing).jpg", "category": "U 29"}, "U 2": {"file": None, "category": None}})
    monkeypatch.setattr(commons, "category_files", lambda cat: ["U29 Hillersjö.jpg", "U29 rights.jpg", "U 29, Hillersjö (drawing).jpg"])
    monkeypatch.setattr(commons, "commons_search", lambda signum: [])  # U 2 has no category: Commons is searched instead
    info = lambda **k: {"thumb": f"https://upload.wikimedia.org/wikipedia/commons/a/ab/{k['f']}", "page": "p", "licence_url": None,  # noqa: E731
                        "author": k.get("a", "Berig"), "licence": k.get("l", "CC BY 2.5"), "description": k.get("d", "")}
    monkeypatch.setattr(commons, "commons_info", lambda files: {
        "U 29, Hillersjö (drawing).jpg": info(f="d.jpg", a="Johan Hadorph", l="Public domain"),
        "U29 Hillersjö.jpg": info(f="p.jpg", a="No machine-readable author provided. Cattie assumed (based on copyright claims)."),
        "U29 rights.jpg": info(f="r.jpg", l="All rights reserved")})
    st = commons.stone_photos(["U 29", "U 2"])
    assert [s["signum"] for s in st] == ["U 29"]  # U 2 has no picture at all
    ph = st[0]["photos"]
    assert [p["file"] for p in ph] == ["U29 Hillersjö.jpg", "U 29, Hillersjö (drawing).jpg"]  # the photo first, not the unfree one
    assert ph[0]["author"] == "Cattie" and not ph[0]["old"] and not ph[0]["main"]
    assert ph[1]["old"] and ph[1]["main"]  # Wikidata's own picture, but an older drawing
    assert ph[0]["preview"] == "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/p.jpg/330px-p.jpg"
    assert commons.stone_photos(["U 29"])[0]["photos"][0]["file"] == "U29 Hillersjö.jpg"  # from the cache
    old = {"signum": "Sö 101", "page": "p", "author": "Swedish National Heritage Board", "licence": "No restrictions"}
    assert "inga kända upphovsrättsliga begränsningar" in commons.caption(old) and "no known copyright" in commons.caption(old, "en")


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
                 "](https://github.com/Precatio/runes)", "## Källor och data", "Gräslund, A.-S. 2006", "Holm, S. 1979",
                 "10 av 10 omräkningar"):
        assert part in body, part
    en = bt.draft(_p("Geografi", "hotspot_r_for_R_U 768"), res, "en", map_keys=frozenset({"r_for_R"}))["body"]
    assert ":::box In short" in en and "Kulldorff, M. 1997" in en and "## A first test" in en
    assert not APP_LINK.search(body) and not APP_LINK.search(en)


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
    assert md.startswith("![r för ʀ") and "Källa: Vitkis korpusanalys i R (hotspots.R)" in md
    res = {"hotspots": {"figures": {"hotspot_r_for_R": "hotspot_r_for_R.png"}}, "text": {"figures": {"a": "text_formler.png"}}}
    assert [x["name"] for x in bf.available(res, {"r_for_R": "r för ʀ"})] == ["hotspot_r_for_R.png", "text_formler.png"]


def test_scheduled_articles_go_live_when_their_time_comes():
    utc = dt.timezone.utc
    now = dt.datetime(2026, 10, 13, 12, 0, tzinfo=utc)
    assert blog._ts("2026-10-20T07:00:00Z") == dt.datetime(2026, 10, 20, 7, 0, tzinfo=utc)
    assert blog._ts("2026-10-20T09:00:00+02:00") == dt.datetime(2026, 10, 20, 7, 0, tzinfo=utc)
    assert blog._ts("2026-10-20T07:00:00") == dt.datetime(2026, 10, 20, 7, 0, tzinfo=utc)  # without a zone: UTC
    assert blog._ts("i morgon") is None and blog._ts("") is None and blog._ts(None) is None
    assert blog.is_live({"published": True, "publishedAt": "2026-10-13T11:59:00Z"}, now)
    assert not blog.is_live({"published": True, "publishedAt": "2026-10-13T12:01:00Z"}, now)  # scheduled
    assert blog.is_live({"published": True}, now)  # older articles without a time
    assert not blog.is_live({"published": False, "publishedAt": "2026-10-01T00:00:00Z"}, now)


def test_the_publication_time():
    utc = dt.timezone.utc
    now = dt.datetime(2026, 10, 13, 12, 0, tzinfo=utc)
    later, earlier = now + dt.timedelta(days=7), now - dt.timedelta(days=30)
    assert blog.publication_time(later, None, now) == later  # scheduled
    assert blog.publication_time(later, earlier, now) == later  # rescheduled
    assert blog.publication_time(None, None, now) == now  # published at once
    assert blog.publication_time(None, earlier, now) == earlier  # an edit keeps its date
    assert blog.publication_time(None, later, now) == now  # a scheduled article published at once


def test_indexnow_only_with_a_key_and_a_public_site(monkeypatch):
    monkeypatch.delenv("INDEXNOW_KEY", raising=False)
    assert blog.indexnow("x") is False
    monkeypatch.setenv("INDEXNOW_KEY", "abc123")
    monkeypatch.setenv("SITE_URL", "http://localhost:3000")
    assert blog.indexnow("x") is False


def test_statistics_are_explained_in_plain_words():
    from src import blog_topics as bt
    bh = "Kulldorffs scanstatistik, Benjamini–Hochberg över mönstren"
    assert bt.plain_significance({"value": 0.013, "test": bh}, "sv") == \
        "Bland alla mönster som är minst så här tydliga väntas högst omkring 1,3 procent vara slumpfynd."
    assert bt.plain_significance({"value": 0.0003, "test": "Holm"}, "sv").endswith("i mindre än ett fall av tusen.")
    assert bt.plain_significance({"value": 0.033, "test": "p"}, "en") == "A pattern this clear would arise by pure chance in about one case in 30."
    assert bt.plain_significance(None, "sv") == ""
    res = _res()
    res["hotspots"]["patterns"][0]["moran"] = {"i": 0.205}
    p = _p("Geografi", "hotspot_r_for_R_U 768", note="Klustret söktes med 999 simuleringar. Ett kluster är en plats att titta på.",
           significance={"label": "q 0,013", "value": 0.013, "test": bh})
    b = bt.draft(p, res, "sv", label="r för ʀ", provinces={"U": "Uppland"})["body"]
    assert "väntas högst omkring 1,3 procent vara slumpfynd (q 0,013)." in b
    assert "Morans I, är 0,20, där 0 betyder ingen samling alls" in b
    cav = b[b.index("## Förbehåll"):b.index("## Se själv")]
    assert "simuleringar" not in cav and "Ett kluster är en plats att titta på." in cav


def _chart_png(width=1800, height=900) -> bytes:
    import io

    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((100, 100, 700, 800), fill=(183, 65, 14, 255))
    d.text((800, 400), "Runstenar per landskap", fill=(15, 23, 42, 255))
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def test_the_website_gets_only_live_articles_and_their_figures(tmp_path, monkeypatch):
    from src import blog_figures, site_export
    monkeypatch.setattr(site_export, "CONTENT", str(tmp_path / "content" / "articles.json"))
    monkeypatch.setattr(site_export, "FIGURES", str(tmp_path / "figurer"))
    monkeypatch.setattr(site_export, "SEARCH", str(tmp_path / "artiklar-sok.json"))
    monkeypatch.setattr(blog_figures, "DIR", str(tmp_path / "frozen"))
    url = blog_figures.freeze(_chart_png())
    name = url.rsplit("/", 1)[1]
    (tmp_path / "figurer").mkdir()
    (tmp_path / "figurer" / "0123456789abcdef.png").write_bytes(b"old")  # no article uses it any more
    (tmp_path / "figurer" / "0123456789abcdef.webp").write_bytes(b"old")
    posts = [
        {"id": "a", "slug": "live", "title": "A", "published": True, "publishedAt": "2026-10-12T10:00:00+00:00",
         "body": f"![Figur]({url})\nText.", "by": "uid", "snapshot": {"x": 1}},
        {"id": "b", "slug": "later", "title": "B", "published": True, "publishedAt": "2099-01-01T00:00:00+00:00"},
        {"id": "c", "slug": "draft", "title": "C", "published": False},
    ]
    out = site_export.export(posts, "2026-10-13T12:00:00+00:00")
    data = json.loads((tmp_path / "content" / "articles.json").read_text())
    assert [p["slug"] for p in data["posts"]] == ["live"]  # a scheduled article stays out of the public repository
    assert "by" not in data["posts"][0] and "snapshot" not in data["posts"][0]
    assert out == {"articles": 1, "figures": 1, "missing_figures": []}
    # The website gets the figure as WebP under a name of its own, and the exported text points at it
    webp = blog_figures.site_name(name)
    assert sorted(os.listdir(tmp_path / "figurer")) == [webp]
    assert data["posts"][0]["body"] == f"![Figur](/figurer/{webp})\nText."
    assert posts[0]["body"] == f"![Figur]({url})\nText."  # the article itself (Firestore, the local app) is unchanged
    index = json.loads((tmp_path / "artiklar-sok.json").read_text())
    assert [p["slug"] for p in index["posts"]] == ["live"]


def test_the_article_of_the_month_goes_to_the_website(tmp_path, monkeypatch):
    from src import site_export
    monkeypatch.setattr(site_export, "CONTENT", str(tmp_path / "content" / "articles.json"))
    monkeypatch.setattr(site_export, "FIGURES", str(tmp_path / "figurer"))
    posts = [{"id": "a", "slug": "nyare", "title": "A", "published": True, "publishedAt": "2026-10-14T10:00:00+00:00"},
             {"id": "b", "slug": "manadens", "title": "B", "published": True, "publishedAt": "2026-10-13T10:00:00+00:00",
              "featured": True}]
    site_export.export(posts, "2026-10-14T12:00:00+00:00")
    data = json.loads((tmp_path / "content" / "articles.json").read_text())
    # Newest first in the file; the site puts the article of the month first (web/src/lib/featured.ts)
    assert [(p["slug"], p.get("featured")) for p in data["posts"]] == [("nyare", None), ("manadens", True)]
    from api.routers.blog import PUBLIC, PostRequest
    assert "featured" in PUBLIC and PostRequest(slug="x", title="T", body="b").featured is False


def test_the_article_of_the_month_is_set_from_the_list(monkeypatch):
    from api.routers import blog
    from src import site_export
    docs = {"a": {"id": "a", "published": True, "featured": True}, "b": {"id": "b", "published": True}, "c": {"id": "c"}}
    writes = []

    class Doc:
        def __init__(self, i): self.i = i
        def set(self, data, merge=False): writes.append((self.i, data)); docs[self.i].update(data)

    class Col:
        def document(self, i): return Doc(i)

    monkeypatch.setattr(blog, "_all", lambda: [dict(d) for d in docs.values()])
    monkeypatch.setattr(blog, "_forget", lambda: None)
    monkeypatch.setattr(blog, "firestore", lambda: type("F", (), {"collection": lambda self, name: Col()})())
    monkeypatch.setattr(site_export, "publish_soon", lambda: writes.append(("site", None)))
    assert blog.set_featured(blog.FeaturedRequest(id="b"), {}) == {"featured": "b"}
    # Only the two that change are written, and only the flag; then the website is published
    assert writes == [("a", {"featured": False}), ("b", {"featured": True}), ("site", None)]
    writes.clear()
    blog.set_featured(blog.FeaturedRequest(id=None), {})
    assert writes == [("b", {"featured": False}), ("site", None)] and not any(d.get("featured") for d in docs.values())
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        blog.set_featured(blog.FeaturedRequest(id="x"), {})


def test_the_website_push_waits_for_a_busy_git_index(monkeypatch):
    import subprocess
    from src import site_export
    calls = []

    def git(*args):
        calls.append(args[0])
        busy = args[0] == "add" and calls.count("add") == 1  # the first add meets another git command's index.lock
        code = 1 if busy else (1 if args[0] == "diff" else 0)  # diff --quiet: 1 means there is something to commit
        return subprocess.CompletedProcess(args, code, "", "index.lock" if busy else "")
    monkeypatch.setattr(site_export, "_git", git)
    monkeypatch.setattr(site_export.time, "sleep", lambda s: None)
    out = site_export.push()
    # (rev-list: how many other commits the push takes along, see site_export._push)
    assert out["pushed"] and [c for c in calls if c != "rev-list"] == ["add", "add", "diff", "commit", "push"]


def test_the_latest_website_publish_is_recorded_for_admin(tmp_path, monkeypatch):
    import subprocess
    from src import site_export
    monkeypatch.setattr(site_export, "STATUS", str(tmp_path / "site_publish.json"))
    monkeypatch.setattr(site_export, "_git", lambda *a: subprocess.CompletedProcess(a, 0, " M web/content/articles.json\n", ""))
    out = site_export.record({"pushed": False, "note": "Kunde inte committa artiklarna: index.lock"})
    st = site_export.status()
    assert st["note"] == out["note"] and st["at"] == out["at"] and st["unpushed"] is True


def test_photos_are_found_on_commons_when_wikidata_does_not_answer(tmp_path, monkeypatch):
    from src import commons
    monkeypatch.setattr(commons, "CACHE", str(tmp_path))

    def down(signa):
        raise TimeoutError("The read operation timed out")
    monkeypatch.setattr(commons, "wikidata_items", down)
    monkeypatch.setattr(commons, "commons_search", lambda s: ["U861 Norsta - KMB - 1.jpg", "Kylix Louvre U861.jpg"])
    monkeypatch.setattr(commons, "commons_info", lambda files: {f: {
        "thumb": "https://upload.wikimedia.org/wikipedia/commons/a/ab/x.jpg", "page": "p", "author": "B", "licence": "CC BY 2.5",
        "description": "runsten" if "KMB" in f else "a Greek cup"} for f in files})
    st = commons.stone_photos(["U 861"])
    assert [p["file"] for p in st[0]["photos"]] == ["U861 Norsta - KMB - 1.jpg"]  # only pictures of runestones
    assert not list(tmp_path.iterdir())  # not cached, so the next try asks Wikidata again


def test_figures_go_to_the_website_as_webp_charts_lossless_scans_lossy(tmp_path):
    from PIL import Image

    from src import blog_figures
    chart = tmp_path / "chart.png"
    chart.write_bytes(_chart_png(2400, 1000))
    noise = Image.frombytes("RGB", (1200, 800), os.urandom(1200 * 800 * 3))  # a scan render: shades everywhere
    scan = tmp_path / "scan.png"
    noise.save(scan)
    a = blog_figures.to_site(str(chart), str(tmp_path / "chart.webp"))
    b = blog_figures.to_site(str(scan), str(tmp_path / "scan.webp"))
    assert a == {"photo": False, "size": (blog_figures.SITE_WIDTH, 667)} and b == {"photo": True, "size": (1200, 800)}
    with Image.open(tmp_path / "chart.webp") as im:
        assert im.format == "WEBP" and im.mode == "RGB"  # the opaque alpha channel is dropped
        assert im.getpixel((300, 300)) == (183, 65, 14)  # lossless: the chart's colours exactly
    assert blog_figures.site_name("0123456789abcdef.png").endswith(".webp")
    assert blog_figures.site_name("0123456789abcdef.png") != blog_figures.site_name("fedcba9876543210.png")


def test_commons_photos_get_the_width_the_website_needs():
    from src import commons
    sizes = {"Big.jpg": {"width": 4000, "size": 2_000_000}, "Small.jpg": {"width": 600, "size": 90_000},
             "Light wide.jpg": {"width": 1200, "size": 60_000}}
    base = "https://upload.wikimedia.org/wikipedia/commons"
    assert commons.site_photo(f"{base}/a/ab/Big.jpg", sizes) == f"{base}/thumb/a/ab/Big.jpg/960px-Big.jpg"
    assert commons.site_photo(f"{base}/a/ab/Small.jpg", sizes) == f"{base}/a/ab/Small.jpg"  # narrow originals stay
    assert commons.site_photo(f"{base}/a/ab/Light_wide.jpg", sizes) == f"{base}/a/ab/Light_wide.jpg"  # and light ones
    assert commons.site_photo(f"{base}/a/ab/Unknown.jpg", sizes) == f"{base}/a/ab/Unknown.jpg"  # Commons did not answer
    assert commons.site_photo(f"{base}/thumb/a/ab/X_%28U_1%29.jpg/1280px-X_%28U_1%29.jpg", {}) == \
        f"{base}/thumb/a/ab/X_%28U_1%29.jpg/960px-X_%28U_1%29.jpg"
    assert commons.site_photo(f"{base}/thumb/a/ab/X.jpg/500px-X.jpg", {}) == f"{base}/thumb/a/ab/X.jpg/500px-X.jpg"
    thumbs = "https://thumb.wikimedia.org/wikipedia/commons"  # Commons' newer host for thumbnails
    assert commons.site_photo(f"{thumbs}/thumb/a/ab/X.JPG/1280px-X.JPG", {}) == f"{thumbs}/thumb/a/ab/X.JPG/960px-X.JPG"
    assert commons.original_name(f"{base}/9/90/U_329%2C_Sn%C3%A5ttsta.JPG") == "U_329,_Snåttsta.JPG"


def test_commons_sizes_are_cached_and_an_unreachable_commons_changes_nothing(tmp_path, monkeypatch):
    import urllib.request

    from src import commons
    monkeypatch.setattr(commons, "SIZES", str(tmp_path / "sizes.json"))

    class Answer:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, *a):
            return json.dumps({"query": {"normalized": [{"from": "File:Big_one.jpg", "to": "File:Big one.jpg"}],
                                         "pages": {"1": {"title": "File:Big one.jpg",
                                                         "imageinfo": [{"width": 3000, "height": 2000, "size": 900000}]}}}}).encode()
    seen = []

    def answer(req, timeout):
        seen.append((req.get_header("User-agent"), timeout))
        return Answer()
    monkeypatch.setattr(urllib.request, "urlopen", answer)
    assert commons.original_sizes(["Big_one.jpg"])["Big_one.jpg"]["width"] == 3000
    assert seen and seen[0][0].startswith("Vitki/") and seen[0][1] == 10

    def down(req, timeout):
        raise TimeoutError("Commons does not answer")
    monkeypatch.setattr(urllib.request, "urlopen", down)
    assert commons.original_sizes(["Big_one.jpg"])["Big_one.jpg"]["width"] == 3000  # from the cache
    assert commons.original_sizes(["Other.jpg"]) == {}


def test_the_exported_articles_get_lighter_commons_photos(tmp_path, monkeypatch):
    from src import site_export
    base = "https://upload.wikimedia.org/wikipedia/commons"
    monkeypatch.setattr(site_export, "_photo_sizes", lambda urls: {"Big.jpg": {"width": 3000, "size": 2_000_000}})
    body = f"Text.\n\n![Runstenen U 1]({base}/a/ab/Big.jpg)\nU 1. Foto: B, CC BY 2.5, via [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Big.jpg)."
    posts = [{"id": "a", "slug": "live", "title": "A", "published": True, "publishedAt": "2026-10-12T10:00:00+00:00",
              "body": body, "body_en": f"![The runestone U 1]({base}/thumb/c/cd/Y.jpg/1280px-Y.jpg)\nCaption."}]
    site_export.export(posts, "2026-10-13T12:00:00+00:00")
    got = json.loads(open(site_export.CONTENT, encoding="utf-8").read())["posts"][0]
    assert f"({base}/thumb/a/ab/Big.jpg/960px-Big.jpg)\nU 1. Foto: B" in got["body"]
    assert "[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Big.jpg)" in got["body"]  # the credit stays
    assert got["body_en"].startswith(f"![The runestone U 1]({base}/thumb/c/cd/Y.jpg/960px-Y.jpg)")


def test_an_export_that_looks_wrong_is_not_written_or_pushed(monkeypatch):
    from src import site_export
    live = {"published": True, "publishedAt": "2026-10-12T10:00:00+00:00"}
    posts = [{"id": s, "slug": s, "title": s.upper(), **live} for s in "abcd"]
    site_export.export(posts, "2026-10-13T12:00:00+00:00")
    before = open(site_export.CONTENT, encoding="utf-8").read()
    out = site_export.export([], "2026-10-14T12:00:00+00:00")  # an empty read: wrong database, credentials …
    assert "inga publicerade artiklar" in out["blocked"] and open(site_export.CONTENT, encoding="utf-8").read() == before
    out = site_export.export(posts[:1], "2026-10-14T12:00:00+00:00")  # three articles gone at once
    assert "3 artiklar skulle försvinna" in out["blocked"]
    gone = [{**posts[0], "body": "![Figur](/api/blog/figures/0123456789abcdef.png)\nFigur."}, *posts[1:]]
    out = site_export.export(gone, "2026-10-14T12:00:00+00:00")
    assert out["missing_figures"] == ["0123456789abcdef.png"] and "Figurer saknas" in out["blocked"]
    assert open(site_export.CONTENT, encoding="utf-8").read() == before
    # Removing two is an ordinary edit; a deliberate larger removal goes out with force
    assert "blocked" not in site_export.export(posts[:2], "2026-10-14T12:00:00+00:00")
    assert "blocked" not in site_export.export([], "2026-10-14T12:00:00+00:00", force=True)
    assert json.loads(open(site_export.CONTENT, encoding="utf-8").read())["posts"] == []
    # publish_now does not push a blocked export, and Admin is told why
    site_export.export(posts, "2026-10-14T12:00:00+00:00")
    from api.routers import blog as b
    monkeypatch.setattr(b, "_all", lambda: [])
    monkeypatch.setattr(site_export, "push", lambda: (_ for _ in ()).throw(AssertionError("pushed")))
    rec = site_export.publish_now()
    assert rec["pushed"] is False and rec["note"].startswith("Webbplatsen publicerades inte: Exporten gav inga")


def test_a_pending_publication_survives_a_restart(monkeypatch):
    from src import site_export
    monkeypatch.setattr(site_export, "enabled", lambda: True)
    timers = []
    monkeypatch.setattr(site_export, "_later", lambda key, s, fn: timers.append(key))
    monkeypatch.setattr(site_export, "schedule", lambda posts: None)
    site_export.publish_soon()
    assert os.path.exists(site_export.PENDING) and timers == ["soon"]
    timers.clear()
    site_export.catch_up([])  # the server restarted before the half minute was up
    assert timers == ["soon"]
    from api.routers import blog as b
    monkeypatch.setattr(b, "_all", lambda: [])
    monkeypatch.setattr(site_export, "export", lambda posts, now, force=False: {"articles": 0})
    monkeypatch.setattr(site_export, "push", lambda: {"pushed": False, "note": "Committat men inte pushat: offline"})
    site_export.publish_now()
    assert os.path.exists(site_export.PENDING)  # not on GitHub yet: the next start tries again
    monkeypatch.setattr(site_export, "push", lambda: {"pushed": True, "note": "Pushat"})
    site_export.publish_now()
    assert not os.path.exists(site_export.PENDING) and site_export.status()["pending"] is False
    timers.clear()
    site_export.catch_up([])
    assert timers == []


def test_page_views_are_capped_per_article_and_day_and_small_shifts_do_not_republish():
    from src import site_export
    flood = [{"kind": "view", "path": "/artiklar/a", "day": "2026-10-21"}] * 5000
    rows = flood + [{"kind": "view", "path": "/en/artiklar/a", "day": "2026-10-22"}] * 3 + \
        [{"kind": "view", "path": "/artiklar/b", "day": "2026-10-21"}] * 7
    assert site_export.capped_views(rows) == {"a": site_export.VIEWS_PER_DAY + 3, "b": 7}
    old = [{"slug": "a", "views": 10, "publishedAt": "2026-10-01"}, {"slug": "b", "views": 10, "publishedAt": "2026-10-02"}]
    tie = [{**old[0], "views": 11}, old[1]]  # one view breaks the tie: the order changes, but not by much
    assert site_export.views_order(tie) != site_export.views_order(old) and not site_export.views_moved(old, tie)
    real = [{**old[0], "views": 16}, old[1]]
    assert site_export.views_moved(old, real)
    assert not site_export.views_moved(old, [{**old[0], "views": 9}, {**old[1], "views": 30}])  # b first already


def test_an_article_is_backed_up_before_it_is_overwritten_or_deleted(monkeypatch):
    from src import site_export
    stored = {"x": {"slug": "x", "title": "Före", "body": "Gammal text", "published": False,
                    "updatedAt": dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)}}

    class Snap:
        def __init__(self, i): self.i = i
        def to_dict(self): return dict(stored[self.i]) if self.i in stored else None

    class Doc:
        def __init__(self, i): self.id = i
        def get(self): return Snap(self.id)
        def delete(self): stored.pop(self.id, None)

    class Col:
        def document(self, i): return Doc(i)

    monkeypatch.setattr(blog, "firestore", lambda: type("F", (), {"collection": lambda self, name: Col()})())
    monkeypatch.setattr(blog, "_all", lambda: [])
    monkeypatch.setattr(site_export, "schedule", lambda posts: None)
    blog.delete_post("x", {})
    files = os.listdir(os.path.join(blog.BACKUP, "x"))
    assert len(files) == 1 and files[0].endswith("Z.json") and "x" not in stored
    saved = json.loads(open(os.path.join(blog.BACKUP, "x", files[0]), encoding="utf-8").read())
    assert saved["title"] == "Före" and saved["body"] == "Gammal text" and saved["updatedAt"].startswith("2026-10-01")
    # A backup that cannot be written never stops the save or the deletion
    monkeypatch.setattr(blog, "BACKUP", "/dev/null/not-a-folder")
    blog._backup("y", {"title": "T"})
