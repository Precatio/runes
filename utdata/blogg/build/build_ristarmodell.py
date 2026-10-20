"""Artikeln "Kan statistiken föreslå vem som ristade en sten?" om attribueringsmodellen i R (r/attribution.R, Statistik →
Vem ristade?): hur den prövas, vad den klarar, vilka ledtrådar som bär, vilka ristare den blandar ihop, hur säker den är
och varför facit inte är oberoende. Varje siffra hämtas ur körningens attribution.json och låses med asserts.
    ../../../.venv/bin/python build_ristarmodell.py [--write | --update DOC]
Skriver utdata/blogg/ristarmodell.json; --write sparar ett nytt opublicerat utkast i Firestore."""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

FP = "5ebd6df1627127fd"
RUN = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
A = json.load(open(os.path.join(RUN, "attribution.json"), encoding="utf-8"))
pr = lambda x: round(100 * x)  # noqa: E731
sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731

# ---- låsningarna -----------------------------------------------------------------------------------
assert A["n_train"] == 497 and len(A["carvers"]) == 18 and A["min_inscriptions"] == 8
assert A["folds"] == 5 and A["repeats"] == 3 and A["trees"] == 500 and pr(A["majority_baseline"]) == 19
AB = {x["features"]: x for x in A["ablation"]}
assert (pr(AB["Alla"]["accuracy"]), pr(AB["Alla"]["top3"])) == (73, 87)
assert [pr(AB[k]["accuracy"]) for k in ("Språk och innehåll", "Geografi", "Stil", "Bergart")] == [61, 44, 33, 19]
G = A["grouped_cv"]
par = next(x for x in G["Socken"]["ablation"] if x["features"] == "Alla")
har = next(x for x in G["Härad"]["ablation"] if x["features"] == "Alla")
assert (G["Socken"]["n_groups"], pr(par["accuracy"]), G["Härad"]["n_groups"], pr(har["accuracy"])) == (164, 69, 69, 59)
ratio_all = AB["Alla"]["accuracy"] / A["majority_baseline"]
ratio_har = har["accuracy"] / A["majority_baseline"]
assert 3.7 < ratio_all < 3.9 and 3.0 < ratio_har < 3.2
GI = {x["group"]: x for x in A["group_importance"]}
assert [pr(GI[k]["share"]) for k in ("Språk och innehåll", "Geografi", "Stil")] == [72, 22, 6]
IMP = [x["label"] for x in A["importance"]]
assert IMP[:2] == ["Öst–väst (km)", "Skiljetecken"]
FAM = {x["family"]: x for x in A["material"]["per_family"]}
assert (pr(FAM["granitoid"]["accuracy"]), pr(FAM["sandsten"]["accuracy"]), FAM["sandsten"]["n"]) == (74, 67, 52)
PC = {x["carver"]: x for x in A["per_carver"]}
right = lambda c: round(PC[c]["recall"] * PC[c]["n"])  # noqa: E731
assert [(right(c), PC[c]["n"]) for c in ("Balle", "Öpir 1", "Tore 1", "Vidbjörn", "Tidkume")] == [(66, 69), (88, 95), (0, 9), (0, 8), (2, 12)]
assert pr(PC["Öpir 1"]["precision"]) == 61
CF = {(x["truth"], x["pred"]): x["Freq"] for x in A["confused"]}
assert (CF[("Tidkume", "Balle")], CF[("Åsmund", "Öpir 1")], CF[("Gunnar", "Öpir 1")], CF[("Visäte", "Öpir 1")]) == (10, 10, 8, 8)
assert (PC["Åsmund"]["n"], PC["Gunnar"]["n"], PC["Visäte"]["n"]) == (49, 34, 29)
REL = {x["threshold"]: x for x in A["calibration"]["reliability"]}
assert (REL[0.5]["n"], pr(REL[0.5]["accuracy"]), pr(REL[0.5]["share_of_stones"])) == (148, 95, 30)
BIN = next(b for b in A["calibration"]["bins"] if b["bin"] == "(0.2,0.3]")
assert (pr(BIN["mean_p"]), pr(BIN["accuracy"])) == (25, 51)
assert A["uncertain"] == {"n": 113, "agree": 49} and A["n_predictions"] == 923 and A["near_km"] == 25
PRED = {p["signum"]: p for p in A["predictions"]}
U485 = PRED["U 485"]
assert U485["top"] == "Öpir 1" and pr(U485["p"]) == 91 and U485["rundata_uncertain"] == "Ofeg;Öpir 1"
open_hi = [p for p in A["predictions"] if p["agrees_rundata"] is None and p["p"] >= 0.5]
assert len(open_hi) == 61
TOP5 = ["U 1026", "U 894", "U 843", "Sö 53", "Sö 232"]
assert [p["signum"] for p in open_hi if p["signum"] in TOP5] == TOP5
assert [(PRED[s]["top"], pr(PRED[s]["p"])) for s in TOP5] == [("Öpir 1", 85), ("Öpir 1", 75), ("Fot 2", 72), ("Traen", 70), ("Amunde", 70)]

# "Kanske någon annan" (open set, r/attribution.R)
O = A["open_set"]
assert O["threshold"] == 0.35 and (pr(O["left_out"]["flagged"]), pr(O["known"]["flagged"]), pr(O["known"]["accuracy_kept"])) == (80, 41, 87)
assert (O["small_carvers"]["n"], O["small_carvers"]["carvers"], pr(O["small_carvers"]["flagged"])) == (139, 62, 71)
assert (A["n_someone_else"], A["n_predictions"]) == (608, 923) and U485["someone_else"] is False
assert not [p for p in open_hi if p["someone_else"]]

# The training stones' provinces (the closed world of the model)
import csv  # noqa: E402
from collections import Counter  # noqa: E402
PROV = Counter(r["signum"].split()[0] for r in csv.DictReader(open(os.path.join(RUN, "attribution_oof.csv"), encoding="utf-8")))
assert PROV == Counter({"U": 412, "Sö": 76, "Gs": 5, "Vs": 4}), PROV

# ---- bilderna ----------------------------------------------------------------------------------------
files = commons.wikidata_files(["U 485"])
info = commons.commons_info(list(files.values()))
img = {**info[files["U 485"]], "signum": "U 485"}
assert img["author"] == "Uwe Zimmermann" and img["licence"] == "CC BY-SA 3.0"
PHOTO = commons.markdown(img, "sv")


def fig(name: str) -> str:
    d = blog_figures.describe(name)
    return blog_figures.markdown(blog_figures.freeze(open(os.path.join(RUN, name), "rb").read()), d, "sv")


FIG_AB = fig("modell_delmodeller.png")
FIG_CF = fig("modell_forvaxling.png")

rows = "\n".join(f"| {s} | {PRED[s]['place']} | {PRED[s]['top']} | {pr(PRED[s]['p'])} % |" for s in TOP5)

title = "Kan statistiken föreslå vem som ristade en sten?"
summary = ("Vi lät 500 små beslutsträd gissa ristaren på 497 runstenar där svaret redan var känt. De hade rätt på nästan "
           "tre av fyra – och visade att ristarna avslöjar sig mer i prickarna mellan orden än i ormarnas slingor. Men "
           "facit är skrivet av forskare som letade efter samma ledtrådar.")

body = f"""*En OfæigR/ofæigR ØpiR risti.*

Så slutar inskriften på runstenen U 485 vid Marma i Lagga socken i Uppland. Antingen står det att Ofeg och Öpir ristade, eller att Öpir – den *ofæigr*, den som inte är dödsmärkt – ristade. Rundata lämnar båda läsningarna öppna och listar två ristare.

Vi ställde frågan till statistiken. Svaret kom direkt: Öpir, {pr(U485['p'])} procent. Men frågan var orättvis från början. Ofeg finns på tre runstenar, och modellen känner bara ristare med minst {A['min_inscriptions']}. Den hade aldrig kunnat svara Ofeg. Det är spelets första regel, och vi kommer tillbaka till den.

{PHOTO}

## Spelet

Reglerna är enkla. Ta de {A['n_train']} runstenar där Rundata anger en säker ristare som har minst {A['min_inscriptions']} stenar – det blir {len(A['carvers'])} ristare. Dela stenarna i fem högar. Göm en hög, låt datorn lära sig av de fyra andra, och be den gissa vem som ristade varje gömd sten. Fortsätt tills alla högar har varit gömda, och gör sedan om alltihop med nya högar, tre gånger. Statistiker kallar det korsvalidering. Det betyder bara att datorn aldrig får titta på den sten den ska gissa på.

## Femhundra amatördetektiver

Datorn är i själva verket {A['trees']} små beslutsträd, en så kallad slumpskog (random forest). Varje träd är en ganska dålig detektiv. Det får se ett slumpvis urval av stenarna, och vid varje fråga det ställer bara en handfull av ledtrådarna: Står stenen längre österut än så här? Sätter ristaren kolon mellan orden? Skrivs *æftiR* med i eller e? Men när {A['trees']} sådana detektiver röstar tar deras misstag ut varandra, och det som blir kvar är ofta rätt.

Ledtrådarna är var stenen står, ornamentikens stilgrupp, kors och kortkvistrunor, elva språkdrag, fem formler, de hundra vanligaste runparen och nio slags innehåll. Namnen är bortplockade, så att en signatur inte kan avslöja svaret.

## Poängtavlan

Datorn gissade rätt ristare på första försöket för **{pr(AB['Alla']['accuracy'])} procent** av stenarna. Fick den gissa tre gånger fanns rätt namn bland dem för {pr(AB['Alla']['top3'])} procent.

Är det bra? Jämför med latmaskens strategi: gissa alltid på Öpir, den flitigaste ristaren med {PC['Öpir 1']['n']} av de {A['n_train']} stenarna. Det ger rätt i {pr(A['majority_baseline'])} procent. Datorn är nästan fyra gånger så bra som latmasken.

## Fuskar den?

En misstänksam läsare invänder: stenar i samma socken har ofta samma ristare. Kanske känner datorn bara igen platsen, inte handen? Så vi gjorde provet svårare. Hela socknar gömdes på en gång, så att datorn aldrig hade sett en enda sten från den socknen. Då sjönk träffen till {pr(par['accuracy'])} procent. När vi gömde hela härader – {G['Härad']['n_groups']} stycken – blev den {pr(har['accuracy'])} procent. Det är fortfarande tre gånger latmaskens resultat, och då har datorn fått gissa på stenar från trakter den aldrig sett.

## Prickarna avslöjar

Vilka ledtrådar gör jobbet? Vi lät datorn spela med en sorts ledtråd i taget.

{FIG_AB}
Varje stapelgrupp är en omgång av spelet med bara en sorts ledtråd. Den streckade linjen är latmaskens {pr(A['majority_baseline'])} procent.

Med bara språk och innehåll – stavning, skiljetecken, formler och runpar – gissade den rätt på {pr(AB['Språk och innehåll']['accuracy'])} procent. Med bara stenens läge blev det {pr(AB['Geografi']['accuracy'])} procent, och med bara ornamentikens stilgrupp {pr(AB['Stil']['accuracy'])}. Med bara bergarten blev det {pr(AB['Bergart']['accuracy'])} procent, precis lika bra som att alltid gissa på Öpir. Vad stenen är gjord av hjälper alltså inte alls. Hela modellen fungerar också ungefär lika bra på granit ({pr(FAM['granitoid']['accuracy'])} procent rätt) som på de {FAM['sandsten']['n']} sandstenarna ({pr(FAM['sandsten']['accuracy'])} procent).

Räknat i grupp står språk och innehåll för {pr(GI['Språk och innehåll']['share'])} procent av det datorn lutar sig mot, var stenen står för {pr(GI['Geografi']['share'])} och stilen för {pr(GI['Stil']['share'])}. Den enskilt viktigaste ledtråden är hur långt österut stenen står. Tvåa kommer skiljetecknen: om ristaren satte punkt, kolon, kryss eller ingenting alls mellan orden. Ristarens fingeravtryck sitter, med andra ord, mer i prickarna mellan orden än i ormens slingor.

## Öpir-magneten

När datorn har fel gissar den ofta på Öpir. Tio av Åsmunds {PC['Åsmund']['n']} stenar, åtta av Gunnars {PC['Gunnar']['n']} och åtta av Visätes {PC['Visäte']['n']} hamnar hos honom. Öpir har flest stenar i spelet, så när ledtrådarna pekar åt flera håll är han det säkraste kortet. Det syns åt andra hållet också: när datorn säger Öpir har den rätt i {pr(PC['Öpir 1']['precision'])} procent av fallen. Öpir får beröm för fler stenar än han ristade.

{FIG_CF}
Raderna är ristaren enligt Rundata, kolumnerna datorns förstaval. Ju mörkare ruta, desto större andel av ristarens stenar. Den mörka diagonalen är rätt svar; Öpirs kolumn samlar många av felen.

Lättast att känna igen är Balle ({right('Balle')} av {PC['Balle']['n']} stenar rätt) och Öpir ({right('Öpir 1')} av {PC['Öpir 1']['n']}). Svårast är Tore 1 och Vidbjörn, som datorn inte kände igen på en enda sten ({right('Tore 1')} av {PC['Tore 1']['n']} och {right('Vidbjörn')} av {PC['Vidbjörn']['n']}), och Tidkume: tio av hans tolv stenar tog datorn för Balles. Om det betyder att de två skrev likadant, att de arbetade nära varandra eller bara att tolv stenar är för lite att lära sig av, kan datorn inte avgöra. Det är en fråga för någon som kan titta på stenarna.

## En blygsam maskin

Datorn säger också hur säker den är. När den säger minst 50 procent har den rätt i {pr(REL[0.5]['accuracy'])} procent av fallen, och det gäller {REL[0.5]['n']} stenar, knappt var tredje. När den säger omkring {pr(BIN['mean_p'])} procent har den rätt ungefär varannan gång. Datorn underskattar sig själv: den svarar rätt men tror att det är en chansning. Det beror på att rösterna sprids över {len(A['carvers'])} namn, så att även ett ganska säkert svar bara får en liten del av dem.

## Vem rättade provet?

Här kommer haken. Facit – vem som ristade vilken sten – är inte skrivet av stenarna själva. I Uppland och Södermanland bygger Rundatas attribueringar till stor del på Jan Axelsons förteckning över mellansvenska runristare från 1993, och Axelson vägde själv in stil, stavning och geografi. Det är samma slags ledtrådar som datorn använder. Datorn har alltså delvis gått i Axelsons skola, och de {pr(AB['Alla']['accuracy'])} procenten mäter till en del hur väl den tänker som han – inte bara hur ofta den har rätt.

## Arton namn – och alla andra

Tillbaka till spelets första regel. Datorn känner {len(A['carvers'])} ristare, och alla deras träningsstenar står i Mälardalen: {PROV['U']} i Uppland, {PROV['Sö']} i Södermanland, {PROV['Gs']} i Gästrikland och {PROV['Vs']} i Västmanland. En sten som ristades av någon annan – en ristare med färre än {A['min_inscriptions']} kända stenar, en som är helt okänd eller en från ett annat landskap – får ändå ett av de {len(A['carvers'])} namnen. Därför ger datorn bara förslag för stenar inom {A['near_km']} kilometer från en sten den tränats på. Och därför ska förslagen läsas som *om det var någon av de {len(A['carvers'])}, så troligen den här*.

Nu har datorn fått ett nytt svar att ge: *kanske någon annan*. Vi lärde den det genom att gömma en ristare i taget och se hur osäker den blev på stenar av någon den aldrig träffat. När förstavalet får mindre än {pr(O['threshold'])} procent säger den nu kanske någon annan. Det fångar {pr(O['left_out']['flagged'])} procent av de gömda ristarnas stenar, och när vi prövade på {O['small_carvers']['n']} stenar av {O['small_carvers']['carvers']} ristare med för få stenar för att vara med – ristare i samma läge som Ofeg – fångade det {pr(O['small_carvers']['flagged'])} procent. Priset är att datorn också säger kanske någon annan om {pr(O['known']['flagged'])} procent av de kända ristarnas stenar. Den blygsamma maskinen kan inte alltid skilja en främling från en sten den bara är osäker på. Men där den vågar ge ett namn har den rätt i {pr(O['known']['accuracy_kept'])} procent av fallen. Om U 485 är den inte i tvivel: Öpir, {pr(U485['p'])} procent.

## Förslag att pröva

Med de reservationerna har datorn tittat på {sv(A['n_predictions'])} stenar som saknar en säker ristare men står nära en träningssten. För {A['n_someone_else']} av dem säger den kanske någon annan. För {len(open_hi)} stenar som inte har någon ristare alls i Rundata ger den ett namn med minst 50 procent. Här är de fem säkraste:

| Sten | Plats | Datorns förslag | Sannolikhet |
|---|---|---|---|
{rows}

På de {A['uncertain']['n']} stenar där Rundata tvekar mellan flera ristare väljer datorn en av Rundatas kandidater i {A['uncertain']['agree']} fall. Varje förslag är en hypotes att pröva mot stenen själv – mot ornamentiken, huggningen och det som står – inte en ny attribuering.

Vill du se själv finns alltihop i Vitki under Statistik → *Vem ristade?*, och förslagen sten för sten under Forskningsluckor → *Våra resultat*.

:::box Det viktigaste i korthet
- Statistiken kan föreslå en ristare, och den har oftast rätt. Men den väljer bara bland de {len(A['carvers'])} den känner – numera med möjligheten att säga kanske någon annan – och facit den rättas mot är skrivet av forskare som letade efter samma slags ledtrådar.
- Handen syns mest i skrivandet. Skiljetecken, stavning och formler säger mer om ristaren än ornamentiken, och bergarten säger ingenting alls.
- Förslagen för stenar utan ristare är en lista att pröva mot stenarna själva, inte nya attribueringar.
:::

:::box Så räknade vi
- {A['n_train']} vikingatida runstenar med en säker ristare i Samnordisk runtextdatabas (Rundata 3.1), {len(A['carvers'])} ristare med minst {A['min_inscriptions']} stenar var.
- En slumpskog (random forest, R-paketet ranger) med {A['trees']} träd. Femfaldig korsvalidering upprepad tre gånger, och samma prov med hela socknar ({G['Socken']['n_groups']}) och härader ({G['Härad']['n_groups']}) utelämnade.
- Ledtrådar: koordinater och landskap, stilgrupp, kors och kortkvistrunor, elva språkdrag, fem formler, de hundra vanligaste runparen och nio innehållskategorier. Namn är borttagna ur texterna.
- Delmodellerna använder en sorts ledtråd i taget; latmasken gissar alltid på den ristare som har flest stenar.
- Kanske någon annan: förstavalet under {pr(O['threshold'])} procent. Gränsen valdes med en ristare i taget utelämnad och prövades på stenar av ristare med färre än {A['min_inscriptions']} stenar.
- Modulen r/attribution.R i Vitki (Statistik → Vem ristade?), metoddokumentationen avsnitt 1i, korpusversion {FP}.
:::

## Källor

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter.* Runrön 5. Uppsala.
- Breiman, L. 2001. Random forests. *Machine Learning* 45: 5–32.
- Samnordisk runtextdatabas, version 3.1 (ODbL).
- Foto av U 485: se bildtexten."""

out = {"slug": "kan-statistiken-foresla-vem-som-ristade", "title": title, "summary": summary, "body": body,
       "title_en": "", "summary_en": "", "body_en": "", "labels": ["Metod", "Ristare"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "ristarmodell.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "ristarmodell.json"), len(body.split()), "ord")

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
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Attribuering|model", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
