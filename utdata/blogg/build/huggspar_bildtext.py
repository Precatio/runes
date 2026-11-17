"""Bildtexten till huggspårsanalysens granskningsbild (src/auto_grooves._overlay_png), så att läsaren ser vad som är
Vitkis del av bilden och vad som är skanningen. Viktor 2026-11-17: "ha med lite kommentarer om vad analysen har gjort så
man förstår vår del i det man ser".

Vad bilden visar (läst ur _overlay_png, inte antaget):
- bakgrunden: skanningens yta med ett beräknat strykljus från övre vänstra hörnet;
- ljusblått: runslingorna, där runorna står och där analysen mäter – ritade för hand eller hittade av analysen
  (parameters.bands_source);
- rostorange: smala fördjupningar som analysen har tolkat som ristade spår;
- gråblått: fördjupningar för breda för att vara ett huggspår – visas, mäts inte;
- stora prickar: godkända tvärsnitt, färgade efter V-vinkeln (viridis, 30–130°: mörkt = spetsigt, gult = trubbigt);
- små grå prickar: tvärsnitt som kastades.
"""
ANGLE_LO, ANGLE_HI = 30, 130  # src/auto_grooves.ANGLE_COLOR_RANGE


def check_scale():
    """The colour scale the text describes must be the one the analysis draws."""
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    from src import auto_grooves
    assert tuple(auto_grooves.ANGLE_COLOR_RANGE) == (ANGLE_LO, ANGLE_HI), auto_grooves.ANGLE_COLOR_RANGE


def fmt(n: int, lang: str) -> str:
    return f"{n:,}".replace(",", " " if lang == "sv" else ",")


def text(lang: str, what: str, result: dict, credit: str, extra: str = "") -> str:
    """what: 'huggspårsanalysen av Gs 13 i Gästrikland, en sten som Åsmund signerade' (en: 'the groove analysis of …');
    result: the analysis' saved result (counts, parameters.bands_source); credit: the scan's credit, last."""
    check_scale()
    counts, src = result["counts"], result["parameters"].get("bands_source")
    # None: an older run (before groove-6) that drew no bands in the image and measured only what it took for runes
    assert src in ("ritade", "automatiska", None), src
    n, k = fmt(counts["candidates"], lang), fmt(counts["accepted"], lang)
    if lang == "sv":
        found = ("Analysen har själv letat upp de ristade spåren (orange). Runslingorna (ljusblått), där runorna står, ritades "
                 "in för hand i Vitki" if src == "ritade" else
                 "Analysen har själv letat upp de ristade spåren (orange) och runslingorna (ljusblått), där runorna står"
                 if src else "Analysen har själv letat upp de ristade spåren (orange) och mätt bara i dem den tog för runor")
        where = "i slingorna " if src else ""
    else:
        found = ("The analysis found the carved grooves (orange) on its own. The rune bands (light blue), where the runes "
                 "stand, were drawn by hand in Vitki" if src == "ritade" else
                 "The analysis found the carved grooves (orange) and the rune bands (light blue), where the runes stand, on "
                 "its own" if src else
                 "The analysis found the carved grooves (orange) on its own and measured only those it took for runes")
        where = "in the bands " if src else ""
    if lang == "sv":
        return (f"Bild: Vitki, {what}. Allt utom själva skanningen är Vitkis analys: ytan visas i ett beräknat strykljus "
                f"från vänster ovan, så att varje fördjupning syns. {found}. Tvärs över spåren {where}lade analysen {n} tvärsnitt och "
                f"mätte djup, bredd och vinkel i vart och ett. De {k} som klarade alla krav är de stora prickarna, färgade "
                f"efter spårets V-vinkel – mörkt för spetsigt, gult för trubbigt. De små grå prickarna är tvärsnitt som "
                f"kastades, till exempel för att de låg utanför runorna eller var för grunda. Gråblått: fördjupningar för "
                f"breda för att vara huggspår; de visas men mäts inte. {extra}{credit}")
    return (f"Image: Vitki, {what}. Everything except the scan itself is Vitki's analysis: the surface is shown in a computed "
            f"raking light from the upper left, so that every hollow stands out. {found}. Across the grooves {where}the analysis "
            f"laid {n} cross-sections and measured depth, width and angle in each. The {k} that passed every test are "
            f"the large dots, coloured by the groove's V-angle – dark for sharp, yellow for blunt. The small grey dots are "
            f"cross-sections that were discarded, for instance because they lay outside the runes or were too "
            f"shallow. Grey-blue: hollows too wide to be carved grooves; they are shown but not measured. {extra}{credit}")
