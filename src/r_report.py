"""Stenrapportens avsnitt från R-analysen: metod, resultat (inbakade i attribueringen och som egna avsnitt om
stenen i korpusen och i landskapet), begränsningar, reproducerbarhet och referenser."""
from __future__ import annotations

import base64
import os

from src.academic import bullets, h, p


def _d(v, digits: int = 2) -> str:
    return "–" if v is None else f"{v:.{digits}f}".replace(".", ",")


def _pct(v) -> str:
    return "–" if v is None else f"{round(v * 100)} %"


def _png(directory: str | None, name: str | None) -> str | None:
    if not directory or not name:
        return None
    path = os.path.join(directory, name)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


R_REFERENCES = [
    "R Core Team. R: A Language and Environment for Statistical Computing. R Foundation for Statistical Computing, "
    "Wien. https://www.R-project.org/",
    "Pebesma, E. 2018. Simple Features for R: Standardized Support for Spatial Vector Data. The R Journal 10(1), s. 439–446.",
    "Kuhn, M. & Wickham, H. 2020. Tidymodels: A Collection of Packages for Modeling and Machine Learning Using "
    "Tidyverse Principles. https://www.tidymodels.org",
    "Wright, M. N. & Ziegler, A. 2017. ranger: A Fast Implementation of Random Forests for High Dimensional Data in "
    "C++ and R. Journal of Statistical Software 77(1), s. 1–17.",
    "Breiman, L. 2001. Random Forests. Machine Learning 45, s. 5–32.",
    "Gower, J. C. 1971. A General Coefficient of Similarity and Some of Its Properties. Biometrics 27, s. 857–871.",
    "Kaufman, L. & Rousseeuw, P. J. 1990. Finding Groups in Data. An Introduction to Cluster Analysis. New York.",
    "Lê, S., Josse, J. & Husson, F. 2008. FactoMineR: An R Package for Multivariate Analysis. Journal of Statistical "
    "Software 25(1), s. 1–18.",
    "Nenadić, O. & Greenacre, M. 2007. Correspondence Analysis in R, with Two- and Three-dimensional Graphics: The ca "
    "Package. Journal of Statistical Software 20(3), s. 1–13.",
    "Hijmans, R. J. terra: Spatial Data Analysis. R-paket. https://CRAN.R-project.org/package=terra",
    "van Etten, J. 2017. R Package gdistance: Distances and Routes on Geographical Grids. Journal of Statistical "
    "Software 76(13), s. 1–21.",
    "Tobler, W. 1993. Three Presentations on Geographical Analysis and Modeling. (NCGIA Technical Report 93-1.) Santa Barbara.",
    "Axelson, J. 1993. Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter. (Runrön 5.) Uppsala.",
    "Natural Earth. Free Vector and Raster Map Data at 1:10m, 1:50m, and 1:110m Scales. https://www.naturalearthdata.com",
    "Terrain Tiles (Tilezen/Mapzen). Registry of Open Data on AWS. https://registry.opendata.aws/terrain-tiles/",
]


def method_blocks(r: dict) -> list:
    return [
        h(2, "3.4 Statistik i R"),
        p("Stenen ställdes mot hela korpusen av svenska vikingatida runstenar i Samnordisk runtextdatabas med "
          "analyser i R (R Core Team). En attribueringsmodell (random forest; Breiman 2001, ranger, tidymodels) väger "
          "samman geografi, stilgrupp, språkdrag, formler, runbigram och innehåll och är tränad på stenar med säker "
          "ristare; dess träffsäkerhet mättes med upprepad korsvalidering, både slumpvis och med hela socknar och "
          "härader utelämnade (grupperad korsvalidering). Stenens läge jämfördes med kandidaternas "
          "områden (sf; tyngdpunkt, konvext hölje). Stenen placerades i en klustring av stil, språk och innehåll "
          "(Gowers avstånd, PAM; Gower 1971, Kaufman & Rousseeuw 1990) och i Upplands seriation (korrespondensanalys, "
          "ca; Nenadić & Greenacre 2007), som prövats mot Gräslunds stilkronologi. Landskapet runt stenen analyserades "
          "med en höjdmodell (Terrain Tiles; terra): läge i terrängen, modellerad strand vid vikingatiden, sikt och "
          "bästa vägar mellan grannplatserna (gdistance; Tobler 1993). Skript, data och versioner finns i "
          "reproducerbarhetspaketet."),
    ]


def attribution_blocks(r: dict, signum: str, fig, tab) -> list:
    """Inbakat i avsnittet om attribuering: modellens sannolikheter och kandidaternas områden."""
    out = []
    m = r.get("model")
    if m:
        top = m["top"][0]
        rel = next((x for x in reversed(m.get("reliability") or []) if top["p"] >= x["threshold"]), None)
        txt = (f"Attribueringsmodellen i R ger {top['carver']} högst sannolikhet ({_d(top['p'])}) bland sina ristare "
               f"({m['source']}). ")
        txt += (f"När modellen ger minst {_d(rel['threshold'], 1)} till sitt förstaval är det rätt i {_pct(rel['accuracy'])} "
                "av de korsvaliderade fallen." if rel else
                "Sannolikheten är låg; vid så låga värden är modellens förstaval osäkra.")
        if not m.get("in_range"):
            txt += f" Stenen ligger mer än {m['near_limit_km']} km från närmaste träningssten, så förslaget är svagt."
        out.append(p(txt + " Sannolikheterna gäller under antagandet att ristaren är en av modellens ristare."))
        png = _png(r.get("figure_dir"), (r.get("figures") or {}).get("model"))
        if png:
            out.append(fig(png, f"Attribueringsmodellens sannolikheter för {signum} (random forest i R). Kandidaterna från "
                                "sammanvägningen är markerade.", "r_modell"))
        cands = [c for c in m.get("candidates") or []]
        if cands:
            out.append(tab(["Kandidat", "I modellen", "Sannolikhet", "Plats"],
                           [[c["carver"], "ja" if c["in_model"] else "nej (för få säkra stenar)",
                             _d(c.get("p")), str(c["rank"]) if c.get("rank") else "–"] for c in cands],
                           f"Sammanvägningens kandidater i attribueringsmodellen för {signum}."))
    g = r.get("geography")
    if g and g.get("candidates"):
        rows = [[c["carver"], str(c.get("n", "–")), _d(c.get("centroid_km"), 1), _d(c.get("nearest_km"), 1),
                 "ja" if c.get("inside_hull") else "nej", _pct(c.get("share_farther"))]
                for c in g["candidates"] if c.get("centroid_km") is not None]
        if rows:
            out.append(tab(["Ristare", "Säkra stenar", "Till tyngdpunkt (km)", "Närmaste egna sten (km)",
                            "Inom ristarens område", "Egna stenar längre bort"], rows,
                           f"{signum} i förhållande till ristarnas kända områden (säkra stenar i Rundata)."))
        png = _png(r.get("figure_dir"), (r.get("figures") or {}).get("map"))
        if png:
            out.append(fig(png, f"{signum} och kandidaternas säkra stenar med konvexa höljen.", "r_karta"))
    return out


def corpus_blocks(r: dict, signum: str, fig, tab) -> list:
    """Eget resultatavsnitt: stenen bland korpusens grupper, formler och seriation."""
    out = [h(2, "4.9 Stenen i korpusen")]
    c = r.get("cluster") or {}
    if c.get("included"):
        prof = c.get("profile") or {}
        feats = ", ".join(f"{f['level'].split('=')[-1].lower()} ({_pct(f['share_in_cluster'])} mot {_pct(f['share_overall'])})"
                          for f in (prof.get("features") or [])[:4])
        out.append(p(f"I klustringen av stil, språkdrag och innehåll hamnar {signum} i grupp {c['cluster']} av {c['k']} "
                     f"({prof.get('n', '–')} stenar; strukturen är {c['structure']}). Gruppen utmärks av {feats}. "
                     f"Stenens silhuettbredd är {_d(c['silhouette'])}."))
        nb = c.get("neighbours") or []
        if nb:
            out.append(tab(["Sten", "Gower-avstånd", "Ristare (Rundata)", "Grupp"],
                           [[n["signum"], _d(n["distance"]), n.get("carver") or "–", str(n["cluster"])] for n in nb],
                           f"De stenar som i stil, språk och innehåll liknar {signum} mest."))
        png = _png(r.get("figure_dir"), (r.get("figures") or {}).get("mca"))
        if png:
            out.append(fig(png, f"{signum} i korrespondensanalysens två första dimensioner, med stenens grupp markerad.",
                           "r_mca"))
    elif c:
        out.append(p(c.get("note") or "Stenen ingick inte i klustringen."))
    fm = r.get("formulas") or []
    if fm:
        cands = [x["carver"] for x in (fm[0].get("candidates") or [])]
        rows = []
        for f in fm:
            row = [f["label"], f["value"], _pct(f["overall_share"])]
            for cn in cands:
                x = next((y for y in f["candidates"] if y["carver"] == cn), None)
                row.append(f"{x['k']} av {x['n']}" if x and x["n"] else "–")
            rows.append(row)
        out.append(tab(["Formel", signum, "Alla stenar"] + cands, rows,
                       "Inskriftens formler jämförda med kandidaternas säkra inskrifter (antal med samma formel)."))
    ch = r.get("chronology") or {}
    if ch.get("included"):
        out.append(p(f"I Upplands seriation (korrespondensanalys av språk och innehåll, rho {_d(ch['rho'])} mot Gräslunds "
                     f"stilkronologi) ligger stenen vid percentil {round(ch['percentile'] * 100)}, motsvarande ungefär "
                     f"{ch['estimate']} (80 % intervall {ch['lo']}–{ch['hi']}). Tidsskattningens medelfel är "
                     f"{ch['mae_loo_years']} år mot {ch['mae_naive_years']} år utan modell, så ordningen är säkrare än årtalet."))
    elif ch:
        out.append(p(ch.get("note") or ""))
    fnd = r.get("findings") or []
    if fnd:
        out.append(p("Resultat för stenen i Forskningsluckor (R):"))
        out.append(bullets([f"{f['verdict'].capitalize()}: {f['ours']}. {f['assessment']}." for f in fnd]))
    return out


def landscape_blocks(land: dict | None, signum: str, fig, tab) -> list:
    if not land or land.get("error"):
        return []
    t, s, v, rt = land["terrain"], land["shore"], land["view"], land.get("routes")
    out = [h(2, "4.10 Stenen i landskapet")]
    rows = [["Höjd över havet", f"{_d(t['elevation_m'], 1)} m"],
            ["Lutning", f"{_d(t['slope_deg'], 1)}°"],
            ["Höjd relativt omgivningen inom 300 m", f"{_d(t['tpi300_m'], 1)} m"],
            ["Andel av omgivningen inom 2 km som ligger lägre", _pct(t["lower_share_2km"])],
            ["Avstånd till vatten i dag", f"{_d(s['today_km'])} km"],
            [f"Avstånd till modellerad strand (dagens höjd − {_d(land['uplift_m'], 1)} m)", f"{_d(s['viking_age_km'])} km"],
            ["Synlig yta inom 2 km", f"{_d(v['visible_km2_2km'])} km² ({_pct(v['share_2km'])})"],
            ["Slumpvisa punkter i närheten (median)", _pct(v.get("random_share_2km_median"))],
            ["Synligare än andel av slumpvisa punkter", _pct(v.get("percentile"))]]
    if rt:
        rows += [["Avstånd till simulerade vägar mellan grannplatserna", f"{_d(rt['stone_to_route_km'])} km"],
                 ["Slumpvisa punkter på land (median)", f"{_d(rt['random_median_km'])} km"],
                 ["Andel slumpvisa punkter närmare vägarna", _pct(rt["percentile"])]]
    out.append(tab(["", ""], rows, f"{signum} i terrängen (höjdmodell ca 20 m)."))
    txt = []
    if v.get("percentile") is not None:
        txt.append(f"Stenen står synligare än {_pct(v['percentile'])} av slumpvisa platser på land inom 3 km.")
    if rt:
        txt.append(f"Den ligger {_d(rt['stone_to_route_km'])} km från de simulerade bästa vägarna mellan {rt['n_neighbours']} "
                   f"andra runstensplatser i närheten, mot {_d(rt['random_median_km'])} km för slumpvisa punkter "
                   f"({_pct(rt['percentile'])} av dem ligger närmare).")
    if txt:
        out.append(p(" ".join(txt)))
    figs = land.get("figures") or {}
    png = _png(land.get("figure_dir"), figs.get("map"))
    if png:
        out.append(fig(png, f"{signum} i landskapet: höjdmodell, dagens vatten, modellerad strand vid vikingatiden och "
                            "bästa vägar mellan andra runstensplatser.", "r_landskap"))
    png = _png(land.get("figure_dir"), figs.get("view"))
    if png:
        out.append(fig(png, f"Var {signum} syns (viewshed, stenens topp 2 m, betraktare 1,6 m).", "r_sikt"))
    return out


LIMITATIONS = [
    "Attribueringsmodellen väljer bara bland ristare med minst åtta säkra stenar, och den är tränad på Rundatas "
    "attribueringar, i Mälardalen främst Axelsons (1993), som själv vägde in stil, stavning och geografi. "
    "Korsvalideringen mäter därför överensstämmelse med de bedömningarna snarare än med en oberoende sanning.",
    "Seriationen gäller bara Uppland, där Gräslunds kronologi är framtagen; i hela korpusen följer den första "
    "dimensionen andra mönster än tid.",
    "Vattnet i de geografiska analyserna är Natural Earth i skala 1:10 miljoner; mindre vattendrag och våtmarker saknas.",
    "Strandlinjen vid vikingatiden är en grov modell (dagens höjd minus en landhöjning per landskap), och "
    "höjdmodellen visar dagens markyta. Vägarna är simulerade bästa vägar, inte belagda vikingatida vägar.",
]


def data_text(r: dict) -> str:
    return ("R-analysernas skript, korpusens CSV, resultat och sessionInfo() finns i ett reproducerbarhetspaket som kan "
            "laddas ner från appen och köras om i R utan appen (KOR_OM.R).")
