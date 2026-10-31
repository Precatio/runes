"""Artikeln om r för ʀ (sv + en): klustret i västra Uppland – bygdens tal eller ristarens hand? Körs efter rforR.py:
    PYTHONDONTWRITEBYTECODE=1 SITE_PUBLISH=0 .venv/bin/python utdata/blogg/build/build_rforR.py
Skriver utdata/blogg/erik-skrev-r.json."""
_PROJ = str(__import__("pathlib").Path(__file__).resolve().parents[3])  # projektmappen, var den än ligger
import json
import math
import os
import sys

import pandas as pd
from scipy import stats

ROOT = _PROJ
sys.path.insert(0, ROOT)
from src import blog_figures, blog_maps  # noqa: E402

FP = "e83202e01a5e6d27"  # recomputed 2026-10-31 (corrected moved stones); first version d6cffd1578418f74
D = os.path.join(ROOT, "data/cache/r/corpus", FP)
B = os.path.join(ROOT, "utdata/blogg/build")
R = json.load(open(os.path.join(B, "rforR.json")))
h = json.load(open(os.path.join(D, "hotspots.json")))
pat = next(x for x in h["patterns"] if x["key"] == "r_for_R")
cl = pat["clusters"][0]
inside = set(cl["stones"])
d = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
k = d[d.pm_r_for_R.notna() & (d.moved.isna() | (d.moved == 0))].copy()  # moved stones are not counted anywhere (as in the cluster)
k["inside"] = k.signum.isin(inside)
k["early"] = k["style"].isin(["RAK", "Fp", "Pr1", "Pr2"])
k["late"] = k["style"].isin(["Pr3", "Pr4", "Pr5"])


def frac(df):
    return int(df.pm_r_for_R.sum()), len(df)


def certain(name):
    return k[(k.carver == name) & (k.carvers_uncertain == 0)]


erik, balle, asmund = certain("Erik"), certain("Balle"), certain("Åsmund")
E_in, E_out = frac(erik[erik.inside]), frac(erik[~erik.inside])
B_in, B_out = frac(balle[balle.inside]), frac(balle[~balle.inside])
A_in, A_out = frac(asmund[asmund.inside]), frac(asmund[~asmund.inside])
ball = k[k.carvers_all.fillna("").str.contains("Balle")]  # Balli with the uncertain attributions too
BA_in, BA_out = frac(ball[ball.inside]), frac(ball[~ball.inside])
BAp = stats.fisher_exact([[BA_in[0], BA_in[1] - BA_in[0]], [BA_out[0], BA_out[1] - BA_out[0]]])[1]
sg = k[k.signed == 1]
S_in, S_out = frac(sg[sg.inside]), frac(sg[~sg.inside])
S_p = stats.fisher_exact([[S_in[0], S_in[1] - S_in[0]], [S_out[0], S_out[1] - S_out[0]]])[1]
EA_in, EA_out = frac(k[k.early & k.inside]), frac(k[k.early & ~k.inside])
LA_in, LA_out = frac(k[k.late & k.inside]), frac(k[k.late & ~k.inside])
L_p = stats.fisher_exact([[LA_in[0], LA_in[1] - LA_in[0]], [LA_out[0], LA_out[1] - LA_out[0]]])[1]
LU_out = frac(k[k.late & ~k.inside & (k.province == "U") & (k.carver != "Balle")])
LO_in = frac(k[k.late & k.inside & ~k.carver.isin(["Erik", "Balle"])])
Bp = stats.fisher_exact([[B_in[0], B_in[1] - B_in[0]], [B_out[0], B_out[1] - B_out[0]]])[1]
W_in, W_out = R["words_in"], R["words_out"]
_hot_vg = [s_["signum"] for s_ in pat["stones"] if s_["signum"].startswith("Vg")]  # the hot stones (Getis-Ord) in Västergötland
_vg = k[k.province == "Vg"]
VG = {"k": int(_vg[_vg.signum.isin(_hot_vg)].pm_r_for_R.sum()), "n": int(_vg.signum.isin(_hot_vg).sum()),
      "vg_rest_k": int(_vg[~_vg.signum.isin(_hot_vg)].pm_r_for_R.sum()), "vg_rest_n": int((~_vg.signum.isin(_hot_vg)).sum())}
assert E_in == (11, 11) and E_out == (1, 1), (E_in, E_out)
assert (B_in, B_out, A_in, A_out, BA_in, BA_out) == ((3, 5), (5, 19), (0, 3), (0, 10), (5, 7), (6, 20)), (B_in, B_out, A_in, A_out, BA_in, BA_out)
assert (VG["k"], VG["n"], VG["vg_rest_k"], VG["vg_rest_n"]) == (7, 9, 2, 32), VG
assert (cl["center"], round(cl["radius_km"]), cl["n"], cl["cases"]) == ("U 1172", 30, 36, 24)
N_KNOWN = len(k)
SHARE_ALL = k.pm_r_for_R.mean()
half_a, half_b = cl["halves"]["A"], cl["halves"]["B"]

# The maps (utdata/rapporter/figurer/karta_r_for_R.R, the article variant), the map tool's time view and the model's curve
FIGD = os.path.join(ROOT, "utdata/rapporter/figurer")
_fz = lambda n: blog_figures.freeze(open(os.path.join(FIGD, n), "rb").read())  # noqa: E731
fig_cluster, fig_cluster_en = _fz("artikel_r_for_R_sv.png"), _fz("artikel_r_for_R_en.png")
fig_zoom, fig_zoom_en = _fz("artikel_r_for_R_zoom_sv.png"), _fz("artikel_r_for_R_zoom_en.png")
fd = {"label": "Var stenarna med r i stället för yr-runan står", "label_en": "Where the stones with r instead of the yr-rune stand"}
tm = blog_maps.time_map(os.path.join(D, "corpus.csv"), "r_for_R", "r i stället för yr-runan", "r instead of the yr-rune")
cv = blog_maps.curves(os.path.join(D, "change.json"), ["r_for_R"], ["r i stället för yr-runan"], ["r instead of the yr-rune"])
assert tm and cv


def pc(x, n=None):
    return str(int(round((x / n if n else x) * 100)))


def dec(x, n=2, lang="sv"):
    s = f"{x:.{n}f}"
    return s.replace(".", ",") if lang == "sv" else s


def num(n, lang="sv"):
    return f"{n:,}".replace(",", " " if lang == "sv" else ",")


def chart_distance(lang):
    sv = lang == "sv"
    rows = [":::chart Andel stenar med r för ʀ, efter avstånd från Holm i Vittinge" if sv else
            ":::chart Share of stones with r for ʀ, by distance from Holm in Vittinge"]
    for b in R["bands"]:
        lab = (f"{b['from']}–{b['to']} km" if b["to"] < 2000 else f"över {b['from']} km") if sv else \
              (f"{b['from']}–{b['to']} km" if b["to"] < 2000 else f"over {b['from']} km")
        rows.append(f"{'+' if b['from'] == 0 else ''}{lab} | {pc(b['share'])} | {b['n']} {'stenar' if sv else 'stones'}")
    rows.append("Källa: Vitkis korpusanalys av Samnordisk runtextdatabas; stenar där minst ett ord som slutar på ʀ går att läsa och som står kvar på sin plats."
                if sv else "Source: Vitki's corpus analysis of the Scandinavian Runic-text Data Base; stones where at least one "
                "word ending in ʀ can be read and which stand in their original place.")
    return "\n".join(rows) + "\n:::"


def chart_carvers(lang):
    sv = lang == "sv"
    st = "stenar" if sv else "stones"
    rows = [":::chart Vem skriver r för ʀ – i bygden och utanför" if sv else ":::chart Who writes r for ʀ – in the district and outside",
            "# I bygden (inom 30 km)" if sv else "# In the district (within 30 km)",
            f"+Erik | {pc(*E_in)} | {E_in[1]} {st}",
            f"Balle | {pc(*B_in)} | {B_in[1]} {st}",
            f"Åsmund | {pc(*A_in)} | {A_in[1]} {st}",
            f"{'Övriga stenar efter 1050' if sv else 'Other stones after 1050'} | {pc(*LO_in)} | {LO_in[1]} {st}",
            "# Utanför bygden" if sv else "# Outside the district",
            f"+Erik | {pc(*E_out)} | {E_out[1]} {st}",
            f"Balle | {pc(*B_out)} | {B_out[1]} {st}",
            f"Åsmund | {pc(*A_out)} | {A_out[1]} {st}",
            f"{'Övriga stenar efter 1050 i Uppland' if sv else 'Other stones after 1050 in Uppland'} | {pc(*LU_out)} | {LU_out[1]} {st}",
            "Källa: som ovan. Bara säkra attribueringar i Rundata." if sv else "Source: as above. Only certain attributions in Rundata."]
    return "\n".join(rows) + "\n:::"


def fig(url, label, src, lang="sv"):
    return f"![{label}]({url})\n{label}. {'Källa' if lang == 'sv' else 'Source'}: {src}."


U1165 = "![Runstenen U 1165](https://upload.wikimedia.org/wikipedia/commons/4/4a/U1165_Rotbrunna_-_KMB_-_16000300033310.jpg)"
U1165_SRC = ("Bengt A. Lundberg, [CC BY 2.5](https://creativecommons.org/licenses/by/2.5), via "
             "[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:U1165_Rotbrunna_-_KMB_-_16000300033310.jpg).")
U768 = "![Runstenen U 768](https://upload.wikimedia.org/wikipedia/commons/9/93/U768_Grop-Norrby_-_KMB_-_16000300033396.jpg)"
U768_SRC = ("Bengt A. Lundberg, [CC BY 2.5](https://creativecommons.org/licenses/by/2.5), via "
            "[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:U768_Grop-Norrby_-_KMB_-_16000300033396.jpg).")
U1151 = ("![Runstenen U 1151](https://thumb.wikimedia.org/wikipedia/commons/thumb/3/32/Runsten_U1151_%28Ra%C3%A4-nr_Fr%C3%B6sthult_6-1%29_0685.jpg/"
         "1280px-Runsten_U1151_%28Ra%C3%A4-nr_Fr%C3%B6sthult_6-1%29_0685.jpg)")
U1151_SRC = ("Achird, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0), via "
             "[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Runsten_U1151_%28Ra%C3%A4-nr_Fr%C3%B6sthult_6-1%29_0685.jpg).")
BONEN = "/artiklar/2026-10-bonen-tystnade-korset-stod-kvar"
RISTAREN = "/artiklar/2026-10-ristarsignatur-breder-ut-sig"

title = "Erik skrev r – och bygden skrev efter"
summary = (f"Kring Enköping skrivs ord som æftiʀ med vanligt r i stället för den gamla ʀ-runan fem gånger så ofta som i "
           f"resten av landet. Var det bygdens uttal? Spåren leder till en ristare, Erik, som skrev r på varenda sten, och till "
           f"ristarna efter honom. Vi tror att stavningen var en skrivtradition, inte ett talspråk.")

body = f"""*Hjalmdis och Torsten reste dessa stenar efter Nokke. Erik högg.*

Så står det på en runsten vid Rotbrunna i Härnevi socken, mellan Enköping och Sala. Ristarens namn står sist, och han skriver det *airikr*. Det sista tecknet är vanligt r. Men i hans språk slutade namnet på ett särskilt ljud, ʀ, som hade en egen runa. Erik använde den aldrig. Inte i sitt eget namn, och inte på någon av de tolv stenar som säkert är tillskrivna honom, står kvar på sin plats och där ett sådant ord går att läsa. Och i hans bygd blev det vanligt att skriva så.

{U1165}
U 1165 vid Rotbrunna i Uppland, den enda sten som Erik har signerat. Namnet står sist: *airikr hiuk*, Erik högg. Foto: {U1165_SRC}

:::box Kort sagt
- Ett gammalt r-ljud, ʀ, hade en egen runa. Inom 30 kilometer från Holm i Vittinge, norr om Enköping, skrivs det med vanligt r på {pc(cl['rate_in'])} % av stenarna, mot {pc(cl['rate_out'])} % i resten av landet.
- Var det bygdens uttal? Ristaren Erik skrev r på varje sten där ordet går att läsa – också på den han ristade utanför bygden.
- Efter Erik fortsatte bygden: på senare stenar där är stavningen fyra gånger så vanlig som i resten av landet. Åsmund, som ristade över stora delar av Uppland, skrev yr-runan också på stenarna han högg i bygden. Balle, en generation efter Erik, skrev däremot r oftare i bygden än utanför.
- Vår hypotes: r för ʀ i västra Uppland var en skrivtradition som började hos Erik och levde vidare bland ristarna – inte ett tecken på att bygden talade annorlunda. Tidigare forskare har läst det som uttal, och Balle talar delvis för dem. Det kan prövas.
:::

## Ett ljud på väg att försvinna

Den yngre runraden hade två r-runor. Den ena, ᚱ, stod för vårt vanliga r. Den andra, ᛦ, stod för ett r-liknande ljud som hade utvecklats ur ett äldre z. Forskarna skriver det ʀ när de återger runorna med latinska bokstäver. Ljudet fanns framför allt i ordslut: *æftiʀ* (efter), *þæiʀ* (de), *stæinaʀ* (stenar) och i namn som *Æirikʀ*. Under vikingatiden och den tidiga medeltiden föll de två r-ljuden samman i uttalet. Hur yr-runan användes och vad den betydde i de nordiska runinskrifterna har Patrik Larsson undersökt i sin avhandling (2002). Men om stavningen i en enskild bygd följde bygdens uttal, eller ristarens vana, är en annan fråga.

Vi gick igenom de {num(N_KNOWN)} svenska runstenar där minst ett ord som slutar på ʀ går att läsa och som står kvar på sin plats, och räknade hur ofta det skrivs med vanligt r. Det gör det på {pc(SHARE_ALL)} % av stenarna. Men inte jämnt fördelat.

## En bygd som skriver r

{fig(fig_cluster, fd['label'], 'Samnordisk runtextdatabas (ODbL); kustlinjer och sjöar: Natural Earth')}

Stenar med r för ʀ står oftare nära varandra än slumpen ger, och de samlas särskilt i västra Uppland, i socknarna kring Enköping och norrut mot Vittinge: Simtuna, Vårfrukyrka, Tillinge, Nysätra, Fröslunda och Jumkil. Inom 30 kilometer från Holm i Vittinge har {cl['cases']} av {cl['n']} stenar stavningen, alltså {pc(cl['rate_in'])} %. I resten av landet är det {pc(cl['rate_out'])} %. Stavningen är omkring {dec(cl['rr'], 0)} gånger så vanlig i bygden.

{chart_distance('sv')}

Ju längre från bygden, desto ovanligare: från {pc(R['bands'][0]['share'])} % närmast till {pc(R['bands'][1]['share'])} % tre till fem mil bort och omkring en tiondel längre bort. Det ser ut som en dialektgräns. Men är det en?

## Bygdens tal eller ristarens hand?

Det finns två förklaringar, och de gör olika förutsägelser.

**Bygdens tal.** Om ʀ hade försvunnit ur uttalet i västra Uppland, skrev ristarna som folk där talade. Då borde alla ristare som arbetade i bygden skriva r oftare där än på andra håll, och samma ristare borde skriva ʀ oftare när han högg stenar för beställare i andra bygder.

**Ristarens hand.** Om stavningen var en ristares eller en verkstads vana, följer den ristaren och inte platsen. Då borde ristaren skriva r var han än ristade, och andra ristare i bygden borde inte göra det.

{U768}
U 768 vid Grop-Norrby i Vårfrukyrka, i bygden, en av Eriks stenar: *aftir nuka*, efter Nokke. Foto: {U768_SRC}

## Erik

Svaret börjar med en ristare. Tolv stenar med läsbara ʀ-ord som står kvar på sin plats är säkert tillskrivna Erik i Rundata, och på alla tolv skriver han r. Elva står i bygden. Den som står utanför, vid Hjulsta i Enköpings-Näs, har samma stavning, och så har de tre stenar som Rundata osäkert tillskriver honom. Erik skrev *aftir*, aldrig *aftiʀ*, var han än högg.

{fig(fig_zoom, 'Eriks stenar i bygden', 'Samnordisk runtextdatabas (ODbL); kustlinjer och sjöar: Natural Earth')}

{chart_carvers('sv')}

Det talar för ristarens hand. Men det förklarar inte allt, för stavningen överlevde Erik. Han hör till den tidiga stilgruppen Fp, den första hälften av 1000-talet. Av de stenar i bygden som ristades då har {EA_in[0]} av {EA_in[1]} r för ʀ. Bland de senare stenarna i bygden, från omkring 1050 och framåt, har fortfarande {pc(*LA_in)} % stavningen – mot {pc(*LA_out)} % på senare stenar i resten av landet. En så stor skillnad skulle uppstå av en slump i ungefär ett fall på {int(round(1 / L_p, -2)):,}.

## Två prövningar: Balle och Åsmund

Om stavningen speglade bygdens uttal, borde ristare som högg stenar både i och utanför bygden ha skrivit r oftare i bygden. Om den var ristarens vana, borde de ha stavat likadant överallt.

Balle är en av de mest kända ristarna i västra Uppland. Han verkade en generation efter Erik, med stenar främst i stilgrupperna Pr3 och Pr4. På de stenar som säkert är hans skriver han r för ʀ på {B_in[0]} av {B_in[1]} i bygden ({pc(*B_in)} %) och på {B_out[0]} av {B_out[1]} utanför ({pc(*B_out)} %). Räknar man också med de stenar som bara osäkert tillskrivs honom blir skillnaden större: {BA_in[0]} av {BA_in[1]} mot {BA_out[0]} av {BA_out[1]} ({pc(*BA_in)} mot {pc(*BA_out)} %). Stenarna är för få för att skillnaden ska vara säker (p {dec(Bp, 1)} och {dec(BAp, 2)}), men den går åt det håll talhypotesen förutsäger. Balle talar alltså snarare för bygdens tal än emot det.

Åsmund ger ett tydligare besked åt andra hållet. Han är en av de flitigaste ristarna i Uppland, och han skrev yr-runan på alla {A_in[1] + A_out[1]} stenar som säkert är hans och där ordet går att läsa – också på de {A_in[1]} han högg inom bygden. Hans stavning följde honom, inte bygden, precis som Eriks.

Vi håller fast vid hypotesen, med Balle som en invändning:

> r för ʀ i västra Uppland var en skrivtradition som började hos Erik och fördes vidare av ristarna i bygden – inte ett tecken på att bygden talade annorlunda än andra.

Runologerna Per Stille (1999) och Patrik Larsson (2002) har läst Eriks r annorlunda: som tecken på att ljuden hade fallit samman i hans eget tal. Där går vi emot dem. Men vi kan inte utesluta att de har rätt, för om Erik och ristarna efter honom själva talade så, ger det samma mönster – och Balles stenar pekar åt deras håll.

Prövningarna har sina gränser. Balle och Åsmund har tillsammans {B_in[1] + B_out[1] + A_in[1] + A_out[1]} säkert attribuerade stenar med läsbara ʀ-ord, och det finns ett annat tecken som borde ha synts om ljuden hade fallit samman i talet: att ristarna ibland skrev ʀ där det skulle vara r, en så kallad omvänd stavning. I bygden finns ingen sådan, men där finns bara {W_in['r_n']} ord som slutar på vanligt r, och i resten av landet är omvänd stavning sällsynt ({W_out['r_R']} av {W_out['r_n']} ord). Orden är för få för att det ska säga mycket.

:::box Så säkra är vi
Ett mönster i ett stort material kan uppstå av en slump, eller av att materialet är skevt. Därför har vi prövat det på flera sätt:

- **Inte slumpen.** Vi lät datorn fördela stavningen slumpvis över stenarna 999 gånger och jämförde. Ett lika tydligt kluster uppstod nästan aldrig (Kulldorffs scanstatistik). Efter justering för att vi letade efter kluster i alla mönster på en gång väntas högst omkring {max(1, round(cl['q_bh'] * 100))} % av lika starka kluster vara slumpfynd.
- **Två oberoende halvor.** Vi delade stenarna i två grupper, socken för socken, så att båda fick stenar från samma trakter och ungefär samma tid. Klustret syns i båda: {pc(half_a['rate_in'])} mot {pc(half_a['rate_out'])} % i den ena och {pc(half_b['rate_in'])} mot {pc(half_b['rate_out'])} % i den andra.
- **Inte bara attribueringarna.** Många stenar är tillskrivna ristare efter stilen, och forskarna kan ha låtit stavningen väga in. Därför prövade vi också med bara signerade stenar, där ristaren själv har skrivit sitt namn: {S_in[0]} av {S_in[1]} i bygden har r för ʀ, mot {S_out[0]} av {S_out[1]} utanför ({pc(*S_in)} mot {pc(*S_out)} %).
- **Ord för ord.** Vi räknar bara ord som slutar på ʀ i Rundatas normalisering och som går att läsa. Namn räknas inte i jämförelsen.
- **Flyttade stenar.** Ingen av räkningarna tar med stenar som har flyttats till kyrkor eller museer, eftersom deras plats inte säger var de ristades.
- **Samma kontroller som allt annat.** I Vitkis robusthetstrappa – ristaren och socknen som slumpeffekter, var halva för sig, utan flyttade stenar – håller klustret i alla åtta steg.
:::

## Tre stenar som kan vara Eriks

Stavningen kan också hjälpa till att skilja ristare åt. Tre stenar från Eriks tid, stilgrupp Fp, två i bygden och en strax utanför, har r för ʀ men ingen säker ristare: U 732 vid Grillby, U 755 vid Kälsta och U 1151 vid Brunnby. Rundata ger dem osäkra förslag: Balle eller Erik, Erik eller Balle, och Erik eller Äskil.

Två spår som inte bygger på varandra pekar mot Erik. Stilen: alla tre hör till Fp, Eriks tid, medan Balles stenar i regel hör till en senare stilgrupp. Och stavningen: Erik skrev r på alla sina stenar, Balle på en tredjedel av sina. Vitkis attribueringsmodell föreslår också Erik för alla tre, men den väger in stavningen, också r för ʀ, och är därför inget eget spår. Ingenting här avgör saken, men det är en prövbar hypotes för runologerna: att de tre stenarna är Eriks.

{U1151}
U 1151 vid Brunnby i Frösthult, en av de tre stenarna. Foto: {U1151_SRC}

## En andra ficka – utan ristare

Kartan visar ytterligare ett ställe där stavningen samlas: nordöstra Västergötland, kring Mariestad och Leksberg vid Vänern. Där har {VG['k']} av {VG['n']} stenar r för ʀ, mot {VG['vg_rest_k']} av {VG['vg_rest_n']} i resten av Västergötland. Alla är tidiga, i stilgrupperna RAK och Fp, och ingen har en känd ristare. Här vet vi alltså inte om det är en ristares hand eller bygdens tal. Det är nästa prov.

## Så kan hypotesen prövas vidare

1. **Eriks andra vanor.** Har Erik fler egna stavningar, och lever de också vidare i bygden efter honom? Följer flera av hans vanor med till de senare ristarna, talar det för en skola snarare än ett uttal.
2. **Ristarna i Västergötland.** Huggteknik och ornamentik på de nio stenarna kring Mariestad kan visa om de är ristade av en och samma hand. Är de det, liknar fickan Eriks bygd. Är de det inte, talar det för bygdens tal.
3. **Den omvända stavningen.** Med fler inskrifter, också medeltida, går det att se var ristarna börjar skriva ʀ där det ska vara r – det säkraste tecknet på att ljuden har fallit samman i talet.
4. **Lärare och elever.** Om stavningen fördes vidare från Erik, bör de ristare som skriver r i bygden vara de som har samarbetat med eller lärt av varandra.

## Förbehåll

- Eriks stenar är, utom en, tillskrivna honom efter stil och språk. Om stavningen har vägts in i attribueringarna är hans konsekvens delvis inbyggd. Prövningen med signerade stenar visar att klustret finns ändå, men inte att det är just Eriks.
- Bara en av Eriks stenar är signerad, och på den går de vanliga ʀ-orden inte att läsa. Hans namn, *airikr*, räknas inte i jämförelsen.
- Antalen är små: tolv stenar av Erik, {B_in[1] + B_out[1]} av Balle, {A_in[1] + A_out[1]} av Åsmund och nio i Västergötland.
- Normaliseringen i Rundata är en tolkning. Var ett ord slutade på ʀ eller r är ibland osäkert.
- Ett samband är inte en orsak. Hypotesen förklarar mönstret, men andra förklaringar är möjliga – till exempel att beställarna i bygden valde ristare som skrev som de själva talade.

## Se själv

{blog_maps.markdown(tm, 'sv')}

{blog_maps.markdown(cv, 'sv')}

Om hur sedvänjor spreds mellan ristare: [Ristaren tog sista ordet]({RISTAREN}).

{blog_maps.github_note('sv')}

## Uppdatering 31 oktober 2026

Siffrorna är omräknade på en rättad version av materialet. Flyttade stenar räknas nu inte någonstans; i den första versionen räknades de som om de stod utanför bygden, också när de står mitt i den. Klustret har därför fått ett nytt centrum, Holm i Vittinge i stället för Grop-Norrby, och en större radie, 30 i stället för 22 kilometer. Huvudresultatet står kvar. Balle-provet ger däremot inte längre samma besked: i den första versionen såg han ut att stava likadant överallt, nu skrev han r oftare i bygden. Åsmund har lagts till som prov.

## Källor och data

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter*. Runrön 17. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26, s. 1481–1496.
- Getis, A. & Ord, J. K. 1992. The analysis of spatial association by use of distance statistics. *Geographical Analysis* 24, s. 189–206.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B* 57, s. 289–300.
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna. Kartor: Vitkis korpusanalys i R, kustlinjer och sjöar från Natural Earth."""

title_en = "Erik wrote r – and the district followed"
summary_en = (f"Around Enköping, words such as æftiʀ are written with an ordinary r instead of the old ʀ-rune five times as "
              f"often as in the rest of the country. Was it the local pronunciation? The traces lead to a carver, Erik, who wrote r "
              f"on every stone, and to the carvers after him. We think the spelling was a writing tradition, not a spoken one.")

body_en = f"""*Hjalmdís and Þorsteinn raised these stones in memory of Nokki. Æirikr cut.*

So it reads on a runestone at Rotbrunna in Härnevi parish, between Enköping and Sala. The carver's name comes last, and he writes it *airikr*. The last sign is an ordinary r. But in his language the name ended in a special sound, ʀ, which had a rune of its own. Erik never used it. Not in his own name, and not on any of the twelve stones securely attributed to him that stand in their original place and where such a word can be read. And in his district it became common to write that way.

{U1165.replace('Runstenen', 'The runestone')}
U 1165 at Rotbrunna in Uppland, the only stone Erik signed. His name comes last: *airikr hiuk*, Æirikr cut. Photo: {U1165_SRC}

:::box In short
- An old r-sound, ʀ, had a rune of its own. Within 30 kilometres of Holm in Vittinge, north of Enköping, it is written with an ordinary r on {pc(cl['rate_in'])} % of the stones, against {pc(cl['rate_out'])} % in the rest of the country.
- Was it the local pronunciation? The carver Erik wrote r on every stone where the word can be read – also on the one he carved outside the district.
- After Erik the district carried on: on later stones there the spelling is four times as common as in the rest of the country. Åsmund, who carved across much of Uppland, wrote the yr-rune also on the stones he cut in the district. Balli, a generation after Erik, on the other hand wrote r more often in the district than outside it.
- Our hypothesis: r for ʀ in western Uppland was a writing tradition that began with Erik and lived on among the carvers – not a sign that the district spoke differently. Earlier scholars have read it as pronunciation, and Balli speaks partly for them. It can be tested.
:::

## A sound on its way out

The younger futhark had two r-runes. One, ᚱ, stood for our ordinary r. The other, ᛦ, stood for an r-like sound that had developed from an older z. Scholars write it ʀ when they render the runes in Latin letters. The sound occurred above all at the ends of words: *æftiʀ* (after), *þæiʀ* (they), *stæinaʀ* (stones) and in names such as *Æirikʀ*. During the Viking Age and the early Middle Ages the two r-sounds merged in pronunciation. How the yr-rune was used and what it stood for in the Scandinavian runic inscriptions has been studied by Patrik Larsson in his dissertation (2002). But whether the spelling in a single district followed the district's pronunciation, or the carver's habit, is another question.

We went through the {num(N_KNOWN, 'en')} Swedish runestones where at least one word ending in ʀ can be read and which stand in their original place, and counted how often it is written with an ordinary r. That happens on {pc(SHARE_ALL)} % of the stones. But not evenly.

## A district that writes r

{fig(fig_cluster_en, fd['label_en'], 'Scandinavian Runic-text Data Base (ODbL); coastlines and lakes: Natural Earth', 'en')}

Stones with r for ʀ stand near each other more often than chance would give, and they gather especially in western Uppland, in the parishes around Enköping and north towards Vittinge: Simtuna, Vårfrukyrka, Tillinge, Nysätra, Fröslunda and Jumkil. Within 30 kilometres of Holm in Vittinge, {cl['cases']} of {cl['n']} stones have the spelling, that is {pc(cl['rate_in'])} %. In the rest of the country it is {pc(cl['rate_out'])} %. The spelling is about {dec(cl['rr'], 0, 'en')} times as common in the district.

{chart_distance('en')}

The further from the district, the rarer: from {pc(R['bands'][0]['share'])} % closest to {pc(R['bands'][1]['share'])} % thirty to fifty kilometres away and about a tenth further off. It looks like a dialect boundary. But is it one?

## The district's speech or the carver's hand?

There are two explanations, and they make different predictions.

**The district's speech.** If ʀ had disappeared from pronunciation in western Uppland, the carvers wrote as people there spoke. Then every carver working in the district should write r more often there than elsewhere, and the same carver should write ʀ more often when he cut stones for patrons in other districts.

**The carver's hand.** If the spelling was the habit of a carver or a workshop, it follows the carver and not the place. Then the carver should write r wherever he carved, and other carvers in the district should not.

{U768.replace('Runstenen', 'The runestone')}
U 768 at Grop-Norrby in Vårfrukyrka, in the district, one of Erik's stones: *aftir nuka*, in memory of Nokki. Photo: {U768_SRC}

## Erik

The answer begins with a carver. Twelve stones with legible ʀ-words that stand in their original place are attributed to Erik with certainty in Rundata, and on all twelve he writes r. Eleven stand in the district. The one that stands outside it, at Hjulsta in Enköpings-Näs, has the same spelling, and so do the three stones Rundata attributes to him with uncertainty. Erik wrote *aftir*, never *aftiʀ*, wherever he cut.

{fig(fig_zoom_en, "Erik's stones in the district", 'Scandinavian Runic-text Data Base (ODbL); coastlines and lakes: Natural Earth', 'en')}

{chart_carvers('en')}

That speaks for the carver's hand. But it does not explain everything, for the spelling outlived Erik. He belongs to the early style group Fp, the first half of the eleventh century. Of the stones in the district carved then, {EA_in[0]} of {EA_in[1]} have r for ʀ. Among the later stones in the district, from about 1050 onwards, {pc(*LA_in)} % still have the spelling – against {pc(*LA_out)} % on later stones in the rest of the country. A difference this large would arise by chance in about one case in {int(round(1 / L_p, -2)):,}.

## Two tests: Balli and Åsmund

If the spelling reflected the district's pronunciation, carvers who cut stones both in and outside the district should have written r more often in the district. If it was the carver's habit, they should have spelled the same everywhere.

Balli is one of the best-known carvers of western Uppland. He worked a generation after Erik, with stones mainly in the style groups Pr3 and Pr4. On the stones that are securely his, he writes r for ʀ on {B_in[0]} of {B_in[1]} in the district ({pc(*B_in)} %) and on {B_out[0]} of {B_out[1]} outside it ({pc(*B_out)} %). Counting also the stones attributed to him only with uncertainty, the difference grows: {BA_in[0]} of {BA_in[1]} against {BA_out[0]} of {BA_out[1]} ({pc(*BA_in)} against {pc(*BA_out)} %). The stones are too few for the difference to be certain (p {dec(Bp, 1, 'en')} and {dec(BAp, 2, 'en')}), but it goes the way the speech hypothesis predicts. Balli thus speaks for the district's speech rather than against it.

Åsmund gives a clearer answer the other way. He is one of the most prolific carvers of Uppland, and he wrote the yr-rune on all {A_in[1] + A_out[1]} stones that are securely his and where the word can be read – also on the {A_in[1]} he cut within the district. His spelling followed him, not the district, just as Erik's did.

We hold to the hypothesis, with Balli as an objection:

> r for ʀ in western Uppland was a writing tradition that began with Erik and was carried on by the carvers of the district – not a sign that the district spoke differently from others.

The runologists Per Stille (1999) and Patrik Larsson (2002) have read Erik's r differently: as a sign that the sounds had merged in his own speech. Here we depart from them. But we cannot rule out that they are right, for if Erik and the carvers after him themselves spoke so, that gives the same pattern – and Balli's stones point their way.

The tests have their limits. Balli and Åsmund together have {B_in[1] + B_out[1] + A_in[1] + A_out[1]} securely attributed stones with legible ʀ-words, and there is another sign that should have shown if the sounds had merged in speech: that carvers sometimes wrote ʀ where there should be r, a so-called inverse spelling. In the district there is none, but there are only {W_in['r_n']} words ending in an ordinary r there, and in the rest of the country inverse spelling is rare ({W_out['r_R']} of {W_out['r_n']} words). The words are too few for that to say much.

:::box How sure we are
A pattern in a large material can arise by chance, or because the material is skewed. So we have tested it in several ways:

- **Not chance.** We let the computer spread the spelling at random over the stones 999 times and compared. An equally clear cluster hardly ever arose (Kulldorff's scan statistic). After adjusting for having looked for clusters in all patterns at once, at most about {max(1, round(cl['q_bh'] * 100))} % of equally strong clusters are expected to be chance findings.
- **Two independent halves.** We split the stones into two groups, parish by parish, so that both got stones from the same districts and about the same time. The cluster shows in both: {pc(half_a['rate_in'])} against {pc(half_a['rate_out'])} % in one and {pc(half_b['rate_in'])} against {pc(half_b['rate_out'])} % in the other.
- **Not only the attributions.** Many stones are attributed to carvers by style, and scholars may have let the spelling weigh in. So we also tested with signed stones only, where the carver wrote his own name: {S_in[0]} of {S_in[1]} in the district have r for ʀ, against {S_out[0]} of {S_out[1]} outside ({pc(*S_in)} against {pc(*S_out)} %).
- **Word by word.** We count only words that end in ʀ in Rundata's normalisation and can be read. Names are not counted in the comparison.
- **Moved stones.** None of the counts includes stones moved to churches or museums, since their location does not say where they were carved.
- **The same checks as everything else.** In Vitki's robustness ladder – the carver and the parish as random effects, each half on its own, without moved stones – the cluster holds at all eight steps.
:::

## Three stones that may be Erik's

The spelling can also help tell carvers apart. Three stones from Erik's time, style group Fp, two in the district and one just outside it, have r for ʀ but no certain carver: U 732 at Grillby, U 755 at Kälsta and U 1151 at Brunnby. Rundata gives them uncertain suggestions: Balli or Erik, Erik or Balli, and Erik or Áskell.

Two traces that do not rest on each other point to Erik. The style: all three belong to Fp, Erik's time, while Balli's stones as a rule belong to a later style group. And the spelling: Erik wrote r on all his stones, Balli on a third of his. Vitki's attribution model also suggests Erik for all three, but it weighs in the spelling, r for ʀ included, and so is not a trace of its own. Nothing here settles the matter, but it is a testable hypothesis for runologists: that the three stones are Erik's.

{U1151.replace('Runstenen', 'The runestone')}
U 1151 at Brunnby in Frösthult, one of the three stones. Photo: {U1151_SRC}

## A second pocket – without a carver

The map shows one more place where the spelling gathers: north-eastern Västergötland, around Mariestad and Leksberg by Lake Vänern. There {VG['k']} of {VG['n']} stones have r for ʀ, against {VG['vg_rest_k']} of {VG['vg_rest_n']} in the rest of Västergötland. All are early, in the style groups RAK and Fp, and none has a known carver. Here, then, we do not know whether it is one carver's hand or the district's speech. That is the next test.

## How the hypothesis can be tested further

1. **Erik's other habits.** Does Erik have more spellings of his own, and do they too live on in the district after him? If several of his habits pass to the later carvers, that speaks for a school rather than a pronunciation.
2. **The carvers in Västergötland.** Carving technique and ornament on the nine stones around Mariestad can show whether they were cut by one and the same hand. If they were, the pocket resembles Erik's district. If not, that speaks for the district's speech.
3. **The inverse spelling.** With more inscriptions, also medieval ones, one can see where carvers begin to write ʀ where there should be r – the surest sign that the sounds have merged in speech.
4. **Masters and pupils.** If the spelling was passed on from Erik, the carvers who write r in the district should be those who worked with or learnt from each other.

## Caveats

- Erik's stones, all but one, are attributed to him by style and language. If the spelling has weighed in the attributions, his consistency is partly built in. The test with signed stones shows that the cluster exists anyway, but not that it is Erik's in particular.
- Only one of Erik's stones is signed, and on it the ordinary ʀ-words cannot be read. His name, *airikr*, is not counted in the comparison.
- The numbers are small: twelve stones by Erik, {B_in[1] + B_out[1]} by Balli, {A_in[1] + A_out[1]} by Åsmund and nine in Västergötland.
- Rundata's normalisation is an interpretation. Whether a word ended in ʀ or r is sometimes uncertain.
- An association is not a cause. The hypothesis explains the pattern, but other explanations are possible – for example that the patrons in the district chose carvers who wrote as they themselves spoke.

## See for yourself

{blog_maps.markdown(tm, 'en')}

{blog_maps.markdown(cv, 'en')}

On how customs spread between carvers: [The carver had the last word]({RISTAREN}).

{blog_maps.github_note('en')}

## Update 31 October 2026

The figures are recomputed on a corrected version of the material. Moved stones are now not counted anywhere; in the first version they were counted as if they stood outside the district, even when they stand in the middle of it. The cluster has therefore got a new centre, Holm in Vittinge instead of Grop-Norrby, and a larger radius, 30 instead of 22 kilometres. The main result stands. The Balli test, however, no longer gives the same answer: in the first version he seemed to spell the same everywhere, now he wrote r more often in the district. Åsmund has been added as a test.

## Sources and data

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter*. Runrön 17. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26, pp. 1481–1496.
- Getis, A. & Ord, J. K. 1992. The analysis of spatial association by use of distance statistics. *Geographical Analysis* 24, pp. 189–206.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B* 57, pp. 289–300.
- Photos: Wikimedia Commons, with photographer and licence in the captions. Maps: Vitki's corpus analysis in R, coastlines and lakes from Natural Earth."""

# The rune itself (ᛦ, the yr-rune) instead of the transliteration letter ʀ – the site embeds a runic typeface
RUNE_FIXES = [
    ("i stället för den gamla ʀ-runan", "i stället för den gamla yr-runan ᛦ"),
    ("instead of the old ʀ-rune", "instead of the old yr-rune ᛦ"),
    ("i hans språk slutade namnet på ett särskilt ljud, ʀ, som hade en egen runa.", "i hans språk slutade namnet på ett särskilt r-ljud, som hade en egen runa: ᛦ."),
    ("in his language the name ended in a special sound, ʀ, which had a rune of its own.", "in his language the name ended in a special r-sound, which had a rune of its own: ᛦ."),
    ("- Ett gammalt r-ljud, ʀ, hade en egen runa.", "- Ett gammalt r-ljud hade en egen runa, ᛦ."),
    ("- An old r-sound, ʀ, had a rune of its own.", "- An old r-sound had a rune of its own, ᛦ."),
    ("Forskarna skriver det ʀ när de återger runorna med latinska bokstäver.", "Forskarna återger den med ett R när de skriver runorna med latinska bokstäver; här visar vi runan själv."),
    ("Scholars write it ʀ when they render the runes in Latin letters.", "Scholars render it as R when they write the runes in Latin letters; here we show the rune itself."),
    ("Om ʀ hade försvunnit ur uttalet", "Om ᛦ-ljudet hade försvunnit ur uttalet"),
    ("If ʀ had disappeared from pronunciation", "If the ᛦ-sound had disappeared from pronunciation"),
]
def runes(t: str) -> str:
    for a, b in RUNE_FIXES:
        t = t.replace(a, b)
    return t.replace("ʀ", "ᛦ")
title, summary, body, title_en, summary_en, body_en = (runes(x) for x in (title, summary, body, title_en, summary_en, body_en))

out = {"title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "numbers": {"E_in": E_in, "E_out": E_out, "B_in": B_in, "B_out": B_out, "B_p": Bp, "S_in": S_in, "S_out": S_out, "S_p": S_p,
                   "early_in": EA_in, "early_out": EA_out, "late_in": LA_in, "late_out": LA_out, "late_p": L_p,
                   "late_U_out": LU_out, "late_other_in": LO_in, "A_in": A_in, "A_out": A_out, "BA_in": BA_in, "BA_out": BA_out, "BA_p": BAp, "VG": VG}}
path = os.path.join(ROOT, "utdata/blogg/erik-skrev-r.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1, default=str)
print(path, len(body.split()), len(body_en.split()))
print(json.dumps(out["numbers"], default=str))
