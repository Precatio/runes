"""Artikeln "Fyra stenar för två barn – släkterna som går att följa över runstenarna" (sv + en): släktnätverkets länkar
(data/links.json, avståndsbanden sedan 2026-11-01) och släkterna (utdata/slakt/steg2a.json), prövade mot Williams 1990.
Varje citat kontrolleras mot Rundatas normalisering och varje tal mot filerna. Sparas som opublicerat utkast.
    ../../../.venv/bin/python build_slakter.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402

J = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))  # noqa: E731
D, F, W = J("data", "links.json"), J("utdata", "slakt", "steg2a.json"), J("utdata", "slakt", "williams1990_bilaga.json")
INS = {x["signum"]: x for x in J("data", "rundata.json")["inscriptions"]}
SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
sure = [x for x in D["links"] if x["q"] < 0.1 and not x["contradictions"] and x["a"].split(" ")[0] in SE and x["b"].split(" ")[0] in SE]
NB, OB = D["null_mean_by_band"], D["obs_by_band"]
WG = {}
for gi, g in enumerate(W["groups"]):
    for m in g["members"]:
        if m["rundata"]:
            WG.setdefault(m["rundata"], set()).add(gi)
WP = {"Ög", "Sö", "Sm", "Vg", "U", "Vs", "Hs"}
w2 = [x for x in sure if x["a"].split(" ")[0] in WP and x["b"].split(" ")[0] in WP]
w2h = sum(1 for x in w2 if WG.get(x["a"], set()) & WG.get(x["b"], set()))
assert (len(sure), w2h, len(w2), F["n_families"], F["stones_in_families"]) == (61, 54, 59, 42, 95)
assert (round(NB["A"]), OB["A"], round(NB["C"]), OB["C"]) == (3, 42, 329, 323)
assert F["by_province"]["U"] == 32 and F["by_size"] == {"2": 35, "3": 3, "4": 4}
pairs = {tuple(sorted((x["a"], x["b"]))) for x in sure}
assert "Gisl(?)" in INS["U 1047"]["normalization"] and "Igull" in INS["U 1027"]["normalization"]
assert (INS["U 261"]["parish"], INS["U 212"]["parish"], INS["U 127"]["parish"]) == ("Fresta sn", "Vallentuna sn", "Danderyds sn")
for p in [("U 312", "U 313"), ("G 111", "G 112"), ("Hs 14", "Hs 15"), ("U 941", "U 986"), ("U 1027", "U 1047"), ("U 147", "U 287"),
          ("U 164", "U 165")]:
    assert tuple(sorted(p)) in pairs, p
FAM = [set(f["stones"]) for f in F["families"]]
assert any({"U 100", "U 160", "U 161", "U 225"} == fs for fs in FAM)              # Ulvs söner: fyra stenar i samma släkt
assert any({"U 164", "U 165", "U 212", "U 261"} == fs for fs in FAM)              # Jarlabanke: fyra stenar, U 127 utanför
assert any({"U 312", "U 313", "U 314", "U 315"} == fs for fs in FAM)              # Harg


def q(sig, frag):
    """A verbatim piece of Rundata's normalisation (quotes and brackets kept as Rundata has them, double quotes dropped)."""
    t = (INS[sig].get("normalization") or "").replace('"', "")
    assert frag in t, (sig, frag)
    return f"*{frag}*"


def fig(name, cap):
    assert "Vitki" in cap[-200:]
    with open(os.path.join(ROOT, "utdata", "blogg", "artikelfigurer", name), "rb") as fh:
        return f"![{cap.split('.')[0]}]({blog_figures.freeze(fh.read())})\n{cap}"


SLUG = "slakterna-pa-runstenarna"
DOTTRAR = "/artiklar/dottrarna-som-runstenarna-glomde"
title = "Fyra stenar för två barn – släkterna som går att följa över runstenarna"
title_en = "Four stones for two children – the families that can be followed across the runestones"
summary = ("Samma människor står ofta på flera runstenar. Vi har länkat dem med en modell som prövar namnen mot slumpen på samma "
           f"avstånd: {F['n_families']} släkter över {F['stones_in_families']} stenar, och nio av tio länkar står redan i "
           "runologernas förteckning. Tre gör det inte, och en av dem är troligen fel.")
summary_en = ("The same people often stand on several runestones. We have linked them with a model that tests the names against "
              f"chance at the same distance: {F['n_families']} families across {F['stones_in_families']} stones, and nine in ten "
              "links already stand in the runologists' list. Three do not, and one of them is probably wrong.")
MAP_SV = fig("slakter_karta_sv.png", f"De {F['n_families']} släkterna. Strecken förenar stenar som nämner samma personer oftare än slumpen ger på samma avstånd; {F['by_province']['U']} av släkterna finns i Uppland. Karta: Vitki, ur Samnordisk runtextdatabas; kustlinjer och sjöar: Natural Earth.")
MAP_EN = fig("slakter_karta_en.png", f"The {F['n_families']} families. The lines join stones that name the same people more often than chance gives at the same distance; {F['by_province']['U']} of the families are in Uppland. Map: Vitki, from the Scandinavian Runic-text Database; coastlines and lakes: Natural Earth.")
HARG_SV = fig("harg_sv.png", "Vem som står på vilken av de fyra stenarna vid Harg. Holmdis och Gunnar står på tre av dem, Jofurfast minns på tre och Tord på en. Illustration: Vitki, efter Samnordisk runtextdatabas.")
HARG_EN = fig("harg_en.png", "Who stands on which of the four stones at Harg. Holmdís and Gunnarr stand on three of them, Jôfurfast is remembered on three and Þórðr on one. Illustration: Vitki, after the Scandinavian Runic-text Database.")

body = f"""Den som har släktforskat vet hur det känns när samma namn dyker upp på två ställen: en farfar i en husförhörslängd, samma namn på samma gård i en bouppteckning. Det är så man vet att det är samma människa. Runstenarna går att läsa på samma sätt. Bara namnen är äldre.

Vid gården Harg i Skånela socken i Uppland står fyra runstenar. På den ena står {q('U 313', 'Gunnarr let haggva stæin æftiR Iufurfast, stiupu sina, ok Holmdis æftiR')} – "Gunnar lät hugga stenen efter Jofurfast, sin styvdotter, och Holmdis efter sin dotter." På den andra står modern ensam: {q('U 314', 'Holmdis let gæra mærki at Iufurfast, dottur sina.')} – "Holmdis lät göra minnesmärket efter Jofurfast, sin dotter." På den tredje låter Gunnar göra ett minnesmärke {q('U 312', 'fyr sial IufurfastaR')}, "för Jofurfasts själ". Och på den fjärde står de båda igen, nu efter ett annat barn: {q('U 315', 'Gunnarr, sunn Farulfs, letu ok Holmdis gærðu mærki æftiR Þorð, sun sinn.')} – "Gunnar, Farulvs son, och Holmdis lät göra minnesmärket efter Tord, sin son."

Fyra stenar för två barn. Jofurfast var Holmdis dotter, som Gunnar kallar sin styvdotter, och Tord var deras gemensamma son. Ingen av stenarna berättar det ensam. Det är först när vi lägger dem bredvid varandra som en familj framträder, med en mor som sörjde två barn och en styvfar som reste stenar för båda. Vi har skrivit om döttrarna vid Harg tidigare, i [Döttrarna som runstenarna glömde]({DOTTRAR}).

{HARG_SV}

## Samma namn är inte samma människa

Att knyta ihop stenar för hand är runologernas gamla arbete. Henrik Williams sammanställde 1990 de samband som forskningen hade pekat ut, landskap för landskap: 144 grupper med 382 inskrifter. Lena Peterson markerar i sitt runnamnslexikon (2007) när två belägg avser samma person. Men ingen av förteckningarna anger hur säker en länk är, och ingen går att räkna om när en läsning ändras.

Det svåra är att samma namn inte betyder samma människa. Det fanns många Sven, Björn och Torsten. Två stenar som båda nämner Gunnar säger ingenting. Två stenar som båda nämner Gunnar och Holmdis säger mycket mer, särskilt om de står nära varandra.

Därför prövar vi varje namnpar mot slumpen. Vi blandar namnen mellan stenarna i landskapet två tusen gånger och räknar hur ofta slumpen ger ett lika starkt par. Det avgörande visade sig vara avståndet. Inom två kilometer ger slumpen i genomsnitt {round(NB['A'])} sådana namnpar, men i verkligheten finns {OB['A']}. Över en mil ger slumpen {round(NB['C'])}, och i verkligheten finns {OB['C']}: där är nästan alla namnpar slump. Släkterna höll sig nära sina gårdar. När vi prövar de nära paren för sig syns de, i stället för att drunkna bland de avlägsna.

Så kommer vi fram till {len(sure)} länkar mellan svenska runstenar, och de knyter ihop {F['stones_in_families']} stenar i {F['n_families']} släkter. Av länkarna i de landskap Williams gick igenom står {w2h} av {len(w2)} redan hos honom. Det betyder att modellen och runologerna oftast pekar på samma släkter, fast modellen bara har sett texterna och avstånden.

{MAP_SV}

:::box Så säkra är vi
- **Varje länk anger sin osäkerhet.** Vi räknar en länk som säker när högst var tionde lika stark länk på samma avstånd väntas vara slump.
- **Runologernas förteckning bekräftar nio av tio.** {w2h} av {len(w2)} länkar står i Williams förteckning från 1990, som är gjord för hand och oberoende av vår modell.
- **Räknesättet valdes efter att vi sett förteckningen.** Därför gjorde vi ett blint prov: de fem länkar som Williams saknar blandades med kända länkar och namnpar som modellen inte länkar, utan signum. Alla fem bedömdes som samma släkt, men provet var inte avgörande, eftersom bedömaren bara kände igen tre av fem kända länkar ur texterna.
- **Nätverket är tunt.** Bara 4 procent av runstenarna ingår, och par med bara vanliga namn prövas inte alls.
:::

## Släkter vi kan följa

**Ardre på Gotland.** På två stenar i Ardre kyrka står samme man. På den ena: {q('G 111', 'Do ung fran oformagum.')} – "Hon dog ung, ifrån omyndiga barn." Det är hans hustru Hróðþjóð. På den andra låter han göra en sten {q('G 112', 'æftiR dottur sina ok HroðþiuðaR')}, "efter sin och Hróðþjóðs dotter". Mannens namn går inte att läsa säkert, Sibbe eller Simpe, men han står på båda.

**Malsta och Sunnå i Hälsingland.** Hróðmundr reste två stenar efter sin far, och på den ena räknar han upp faderns släkt: {q('Hs 14', 'En Brisi vas Lina sunn. En Lini vas UnaR sunn.')} – "Och Brise var Lines son. Och Line var Unns son." Så fortsätter det bakåt i sex led, och han berättar varifrån stenen kom: {q('Hs 14', 'ViR sottum stæin þenna norðr i Balas[tæ]in.')} – "Vi hämtade denna sten norrut i Balasten."

**Ulvs söner i Täby och Vallentuna.** Om fadern står det {q('U 160', 'Hann byggi i Skulhambri.')} – "Han bodde i Skålhamra." Sönerna byggde en tingsplats och skröt: {q('U 225', 'þan Ulfs syniR æftiR gær[ðu]')}, att inga minnesmärken skulle bli större "än dem som Ulvs söner gjorde efter" honom. Fyra stenar hänger ihop i den släkten.

**Jarlabanke.** Fyra av Jarlabankes stenar, i Täby, Vallentuna och Fresta, hänger ihop, de där han säger att han {q('U 164', 'æinn atti allan Tæby')}, "ensam ägde hela Täby". En femte, U 127 i Danderyd, står mer än en mil bort. Där ger slumpen för många namnpar för att länken ska bli säker, fast den är äkta.

## Tre länkar som ingen har gjort – och en som troligen är fel

Tre av länkarna står varken i Rundata, hos Williams eller i Petersons lexikon. Vi har inte gått igenom all senare litteratur, så de är förslag att pröva, inte fynd.

**U 941 och U 986, fem kilometer isär.** På U 986 står {q('U 986', 'Ali/Alli ok Sigvaldi ok Ingifast letu retta stæin þenna')} – "Ale och Sigvalde och Ingefast lät resa denna sten", efter Ingefasts make och Ales far. Den skadade stenen U 941 i Uppsala börjar med samma tre namn och nämner också {q('U 941', '[boa]nda I[ngi]fastaR')}, "Ingefasts make". Samma mor och samma två söner, som troligen reste två stenar efter samme man.

**U 1027 och U 1047, en mil isär.** Ígull och Gísl står på båda: på den skadade U 1027 tillsammans med en tredje man, kanske Eyndr, och på U 1047 med Eygeirr och Ketilbjôrn, efter sin far Eybjôrn. Gísl är osäkert läst på U 1047, så länken vilar mest på det ovanliga namnet Ígull.

**U 147 och U 287 – troligen fel.** Här delar stenarna Ingefast och Ingvar. På U 287 är Ingefast son till Kjallak: {q('U 287', 'let ræisa stæin æftiR sun sinn Ingifast')}. Men U 147 hör till Jarlabankes släkt, och på en tredje sten, U 135, står att den Ingefast var son till Östen: {q('U 135', 'Ingifastr ok Øystæinn ok Svæinn letu ræisa stæina þessa at Øystæin, faður sinn')}. Två bröder Ingefast och Ingvar, men med olika fäder. Modellen ser bara två stenar i taget och kan inte se fadersnamnet på den tredje. Därför behöver länkarna en runolog som läser vidare.

## Vad vi inte ser

Nätverket är tunt. Bara 4 procent av de svenska runstenarna ingår, och de flesta släkter består av två stenar. Par som bara delar Sven, Björn eller Ulv prövas inte, så många verkliga släkter med vanliga namn syns inte. Reglerna som läser personerna ur texterna missar ungefär vart fjärde släktband. Och modellen ser bara det som står i Rundatas läsning: ett namn som inte går att läsa länkar ingenting.

Det modellen ger är inte en ny förteckning som ersätter runologernas. Det är en förteckning som går att räkna om, med en angiven osäkerhet för varje länk, och som pekar ut var det lönar sig att läsa vidare. U 941 och U 986 kan vem som helst lägga bredvid varandra i kväll.

:::box Det viktigaste i korthet
- Samma människor står ofta på flera runstenar, och när stenarna läggs bredvid varandra framträder familjer: en mor vid Harg som sörjde två barn, en änkling i Ardre som förlorade hustru och dotter.
- Släkterna höll sig nära sina gårdar. Därför går de att skilja från slumpen när namnen prövas på samma avstånd.
- Nio av tio av våra länkar har runologerna redan gjort för hand. Tre är nya förslag, och en av dem är troligen fel, vilket visar att en modell inte ersätter den som läser.
:::

## Källor

- Peterson, L. 2007. *Nordiskt runnamnslexikon*. 5 uppl. Uppsala: Institutet för språk och folkminnen.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Williams, H. 1990. *Åsrunan. Användning och ljudvärde i runsvenska steninskrifter*. Runrön 3. Uppsala: Institutionen för nordiska språk. Bilaga: Inskrifter med genealogiskt samband, s. 185–187.
- Metoden, länkarna och det blinda provet: Vitkis metodbeskrivning, avsnitt 1r, och planerna `analysplaner/2026-11-01-slaktnatverket-steg1.md` och `-steg1b.md` på [GitHub](https://github.com/Precatio/runes).
"""

body_en = f"""Anyone who has done family history knows the feeling when the same name turns up in two places: a grandfather in a parish register, the same name on the same farm in an estate inventory. That is how you know it is the same person. The runestones can be read the same way. Only the names are older.

At the farm of Harg in Skånela parish in Uppland stand four runestones. On one of them it says {q('U 313', 'Gunnarr let haggva stæin æftiR Iufurfast, stiupu sina, ok Holmdis æftiR')} – "Gunnarr had the stone cut in memory of Jôfurfast, his stepdaughter, and Holmdís in memory of her daughter." On the second the mother stands alone: {q('U 314', 'Holmdis let gæra mærki at Iufurfast, dottur sina.')} – "Holmdís had the landmark made in memory of Jôfurfast, her daughter." On the third Gunnarr has a landmark made {q('U 312', 'fyr sial IufurfastaR')}, "for Jôfurfast's soul". And on the fourth both stand again, now for another child: {q('U 315', 'Gunnarr, sunn Farulfs, letu ok Holmdis gærðu mærki æftiR Þorð, sun sinn.')} – "Gunnarr, Farulfr's son, and Holmdís had the landmark made in memory of Þórðr, their son."

Four stones for two children. Jôfurfast was Holmdís's daughter, whom Gunnarr calls his stepdaughter, and Þórðr was their shared son. None of the stones tells it alone. Only when we lay them side by side does a family appear, with a mother who mourned two children and a stepfather who raised stones for both. We have written about the daughters at Harg before, in Swedish, in [Döttrarna som runstenarna glömde]({DOTTRAR}).

{HARG_EN}

## The same name is not the same person

Tying stones together by hand is the runologists' old work. In 1990 Henrik Williams compiled the ties that research had pointed out, province by province: 144 groups with 382 inscriptions. In her lexicon of runic names (2007) Lena Peterson marks when two attestations refer to the same person. But neither list says how sure a link is, and neither can be recounted when a reading changes.

The difficulty is that the same name does not mean the same person. There were many Sveinn, Bjôrn and Þorsteinn. Two stones that both name Gunnarr say nothing. Two stones that both name Gunnarr and Holmdís say far more, especially if they stand close together.

So we test every pair of names against chance. We shuffle the names between the stones of the province two thousand times and count how often chance gives an equally strong pair. Distance turned out to decide it. Within two kilometres chance gives on average {round(NB['A'])} such name pairs, but in reality there are {OB['A']}. Beyond ten kilometres chance gives {round(NB['C'])}, and in reality there are {OB['C']}: there nearly every name pair is chance. The families stayed close to their farms. When we test the near pairs on their own, they show, instead of drowning among the distant ones.

That gives us {len(sure)} links between Swedish runestones, and they tie together {F['stones_in_families']} stones in {F['n_families']} families. Of the links in the provinces Williams went through, {w2h} of {len(w2)} already stand in his list. The model and the runologists mostly point to the same families, though the model has seen only the texts and the distances.

{MAP_EN}

:::box How sure we are
- **Every link states its uncertainty.** We count a link as sure when at most one in ten equally strong links at the same distance is expected to be chance.
- **The runologists' list confirms nine in ten.** {w2h} of {len(w2)} links stand in Williams's list of 1990, made by hand and independent of our model.
- **The way of counting was chosen after we saw the list.** So we ran a blind test: the five links Williams lacks were mixed with known links and with name pairs the model does not link, without signa. All five were judged the same family, but the test was not decisive, since the judge recognised only three of five known links from the texts.
- **The network is thin.** Only 4 per cent of the runestones are in it, and pairs with only common names are not tested at all.
:::

## Families we can follow

**Ardre on Gotland.** On two stones in Ardre church stands the same man. On one: {q('G 111', 'Do ung fran oformagum.')} – "She died young, leaving under-age children." That is his wife Hróðþjóð. On the other he has a stone made {q('G 112', 'æftiR dottur sina ok HroðþiuðaR')}, "in memory of his and Hróðþjóð's daughter". The man's name cannot be read for certain, Sibbi or Simpi, but he stands on both.

**Malsta and Sunnå in Hälsingland.** Hróðmundr raised two stones for his father, and on one he lists his father's line: {q('Hs 14', 'En Brisi vas Lina sunn. En Lini vas UnaR sunn.')} – "And Brísi was Lini's son. And Lini was Unn's son." It goes back six generations, and he tells where the stone came from: {q('Hs 14', 'ViR sottum stæin þenna norðr i Balas[tæ]in.')} – "We fetched this stone in the north at Balasteinn."

**Ulfr's sons in Täby and Vallentuna.** Of the father it says {q('U 160', 'Hann byggi i Skulhambri.')} – "He lived in Skolhamarr." The sons made an assembly place and boasted {q('U 225', 'þan Ulfs syniR æftiR gær[ðu]')}, that no landmarks would be greater "than those Ulfr's sons made in memory" of him. Four stones hang together in that family.

**Jarlabanke.** Four of Jarlabanke's stones, in Täby, Vallentuna and Fresta, hang together, those where he says that he {q('U 164', 'æinn atti allan Tæby')}, "alone owned all of Täby". A fifth, U 127 in Danderyd, stands more than ten kilometres away. There chance gives too many name pairs for the link to be sure, though it is real.

## Three links nobody has made – and one that is probably wrong

Three of the links stand neither in Rundata, in Williams nor in Peterson's lexicon. We have not gone through all later literature, so they are proposals to test, not findings.

**U 941 and U 986, five kilometres apart.** On U 986 it says {q('U 986', 'Ali/Alli ok Sigvaldi ok Ingifast letu retta stæin þenna')} – "Áli and Sigvaldi and Ingifast had this stone erected", in memory of Ingifast's husband and Áli's father. The damaged stone U 941 in Uppsala begins with the same three names and also names {q('U 941', '[boa]nda I[ngi]fastaR')}, "Ingifast's husband". The same mother and the same two sons, who probably raised two stones for the same man.

**U 1027 and U 1047, ten kilometres apart.** Ígull and Gísl stand on both: on the damaged U 1027 together with a third man, perhaps Eyndr, and on U 1047 with Eygeirr and Ketilbjôrn, in memory of their father Eybjôrn. Gísl is an uncertain reading on U 1047, so the link rests mostly on the uncommon name Ígull.

**U 147 and U 287 – probably wrong.** Here the stones share Ingifastr and Ingvarr. On U 287 Ingifastr is the son of Kjallakr: {q('U 287', 'let ræisa stæin æftiR sun sinn Ingifast')}. But U 147 belongs to Jarlabanke's family, and on a third stone, U 135, that Ingifastr is the son of Eysteinn: {q('U 135', 'Ingifastr ok Øystæinn ok Svæinn letu ræisa stæina þessa at Øystæin, faður sinn')}. Two brothers Ingifastr and Ingvarr, but with different fathers. The model sees only two stones at a time and cannot see the father's name on the third. That is why the links need a runologist who reads on.

## What we do not see

The network is thin. Only 4 per cent of the Swedish runestones are in it, and most families consist of two stones. Pairs that share only Sveinn, Bjôrn or Ulfr are not tested, so many real families with common names do not show. The rules that read the persons from the texts miss about one kin tie in four. And the model sees only what stands in Rundata's reading: a name that cannot be read links nothing.

What the model gives is not a new list that replaces the runologists'. It is a list that can be recounted, with a stated uncertainty for each link, and that points to where it pays to read on. Anyone can lay U 941 and U 986 side by side tonight.

:::box The essentials in brief
- The same people often stand on several runestones, and when the stones are laid side by side families appear: a mother at Harg who mourned two children, a widower at Ardre who lost wife and daughter.
- The families stayed close to their farms. That is why they can be told apart from chance when the names are tested at the same distance.
- Nine in ten of our links the runologists had already made by hand. Three are new proposals, and one of them is probably wrong, which shows that a model does not replace the reader.
:::

## Sources

- Peterson, L. 2007. *Nordiskt runnamnslexikon*. 5th ed. Uppsala: Institutet för språk och folkminnen.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Williams, H. 1990. *Åsrunan. Användning och ljudvärde i runsvenska steninskrifter*. Runrön 3. Uppsala: Department of Scandinavian Languages. Appendix: Inscriptions with genealogical ties, pp. 185–187.
- The method, the links and the blind test: Vitki's method description, section 1r, and the plans `analysplaner/2026-11-01-slaktnatverket-steg1.md` and `-steg1b.md` on [GitHub](https://github.com/Precatio/runes).
"""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b and "jag " not in b.lower()
assert "Det viktigaste i korthet" in body and "The essentials in brief" in body_en
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Forskning", "Kvinnor och barn", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "blogg", "slakter.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body_en.split()), "words")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p_ for p_ in blog._all() if p_.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "slakter", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
