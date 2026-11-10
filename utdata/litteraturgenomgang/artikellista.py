"""Artikellistan ur litteraturgenomgången (Fornvännen 1906–2023, Futhark 1–15) som Excel: de viktigaste artiklarna Vitki
kan skriva, med frågan, underlaget i tidskrifterna, antal texter som tar upp frågan (blindflackar.json), data, status
och föreslagen månad (PUBLICERINGSPLAN.md). Viktor 2026-11-10: "en lista på alla viktigaste artiklar vi kan skriva
baserat på våra fynd från Fornvännen och Futhark, som excel".
    python3 artikellista.py"""
import json
import os

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Artikelidéer_Fornvännen_Futhark.xlsx")
BF = json.load(open(os.path.join(HERE, "blindflackar.json"), encoding="utf-8"))
N_TEXTER = BF["texter"]
COUNT = {k["kategori"]: k["texter"] for k in BF["kategorier"]}


def bf(start):
    """Antal texter för den blinda fläck vars namn börjar så."""
    hits = [k for k in COUNT if k.startswith(start)]
    assert len(hits) == 1, (start, hits)
    return hits[0], COUNT[hits[0]]


# (prio, titel, fråga, underlag, fläck, spår, typ, vinkel, data, status, månad)
A = [
    # Klara eller nästan klara
    (1, "Varför står runstenarna vid lerans kant?", "Står stenarna vid kanten av den odlade leran – också när bortfall, åsvägar, våtmark och vattennivå räknas bort?",
     "Söderberg; Lovén (åsvägarna); Myrdal 1982; Malmer 1988; Ekholm 1950; Arrhenius 1950", "Bevarande och bortfall", "4 / plan B", "Artikel", "Landskap",
     "Har", "Klar – kontrollerna håller; väntar på Viktors publicering", "nov 2026"),
    (1, "Var det bara Ingvar?", "Hur mycket av runstenarnas blick mot öster bär ett enda tåg? Ändras riktningen över 1000-talet?",
     "Sindbæk 2003; Westin 1941; Thulin 1985 (Ingvar som fast punkt)", "Sena källor", "Självkontroll / plan B", "Artikel", "Människor och resor",
     "Har", "Körd – försvagat (58 % utan Ingvar); tillägg publicerat i Vikingarnas värld", "dec 2026"),
    (1, "Vände de texten mot vägen – eller mot dagens väg?", "Vetter inskriften mot vägen också när bara gamla vägar räknas, mätt mot vägens linje på 1800-talets kartor?",
     "Skoglund & Lagerås 2002; 1941 års restaureringar; 1944_111", "Vägarnas ålder", "3 / plan D", "Artikel", "Landskap",
     "Har KMR-linjer; Häradsekonomiska kartan hämtas", "Pågår – faller mot gamla vägar som punkter; väglinjetestet planeras", "jan 2027"),
    (2, "Stod stenarna verkligen vid gravfälten?", "Håller 82 mot 55 % med bara kontrollerade gravfält, yngre järnålderns former och län i stället för landskap?",
     "Häggström 2002; Ambrosiani 1968; Holmqvist 1957", "Gravfältens ålder", "Självkontroll / plan B", "Artikel", "Människor och släkt",
     "Har", "Körd – står sig (OR 2,3–2,6)", "dec 2026"),
    (1, "Vitki prövar sina egna resultat I", "Rapport: alla självkontroller, också de som försvagade våra fynd",
     "Hela genomgången, avsnitt 4 i SYNTES.md", "Placeringar prövas inte", "Plan B", "Rapport", "Metod",
     "Har", "Pågår – tre av fyra kontroller körda (Ingvar, vägen, gravfälten)", "15 dec 2026"),
    (1, "Varför har Norge bara 66 runstenar – och Sverige 2 300?", "Vad förklarar skillnaden: jord, makt, silver eller bevarande?",
     "Palm 1992; Sawyer 2000", "Skattfynd, mynt", "6", "Artikel", "Landskap och makt",
     "Har; mynt (D5) stärker", "Utkast finns", "dec 2026"),
    # Plan A: bevarande
    (1, "Stenarna som plogen och grustaget tog", "Försvann fler stenar på plöjd lera eller på åsar och sand? Skiljer det mellan landskapen?",
     "Söderberg; Alvastra; Åby 1985; Hovgårdsberg 1935; Alsike 1947", "Bevarande och bortfall", "2 / plan A", "Artikel", "Landskap",
     "Har", "Planerad", "12 jan 2027"),
    (1, "Hur många runstenar har vi förlorat?", "Fångst–återfångst över Bautil, Liljegren, SRI och Runor 2020: hur många stenar fanns en gång?",
     "Bautil; Liljegren; SRI-banden; fynd som Alsike 1947", "Bevarande och bortfall", "2 / plan A", "Artikel", "Metod med stort tal",
     "Har; inventeringsår (D4)", "Planerad", "jan 2027"),
    (1, "Hundra års runforskning – metod, läsarkontroll och påståendedatabas", "Rapport 0: hur genomgången gjordes, hur säkra läsningarna är, databasen öppen",
     "1 577 texter, 4 555 mätbara påståenden", "Placeringar prövas inte", "14", "Rapport", "Metod",
     "Har", "Planerad", "19 jan 2027"),
    (2, "Stenarna i kyrkans murar", "Vilka stenar murades in, var och när – och vad betyder det för vad vi tror oss veta?",
     "1600-talets antikvarier; restaureringar 1941; Riksantikvariens årsberättelser", "Flyttade, inmurade", "2", "Artikel", "Forskningshistoria",
     "Har (Runor 2020, flyttfiltret)", "Idé", "fri lucka 2027"),
    # Plan C: datering
    (1, "Hur gamla är runstenarna – egentligen?", "Hur många oberoende fasta punkter har varje stilgrupp? Står dateringen på egna ben?",
     "Thulin 1985 (Ingvar som fastaste punkt); Wase 1995 (dendro mot konsthistoria); Gräslund", "Dateringen är cirkulär", "1 / plan C", "Artikel", "Metod",
     "Har; ankarstenar sammanställs", "Planerad", "9 feb 2027"),
    (2, "Hur mycket bär stilgrupperna?", "Rapport: stilgrupp mot profilstil, Ingvar ±10 år, monoftongering som oberoende klocka",
     "Thulin 1985; Gräslund; Runor 2020:s profilstil", "Dateringen är cirkulär", "1 / plan C", "Rapport", "Metod",
     "Har", "Planerad", "23 feb 2027"),
    (2, "Prickarna, åsrunan och tiden", "Daterar prickade runor och åsrunan stenarna – eller utgivaren?",
     "SRI-utgivarna; Lagman 1990", "Utgivare, antikvarier", "12", "Artikel", "Språk",
     "Har", "Utkast finns – utgivarkontroll först", "23 feb 2027"),
    (3, "Kom stilen senare till periferin?", "Når en ny stilgrupp periferin och de mindre gårdarna senare än Mälardalen?",
     "Lindqvist 1928; Hjärne; Åberg 1922", "Regional eftersläpning", "17", "Artikel", "Landskap",
     "Har", "Idé", "fri lucka 2027"),
    # Plan D: placering
    (1, "Stod runstenarna vid tinget?", "Står stenarna närmare tingsplatser och domarringar än slumpen ger inom bygden?",
     "Nordén 1938 (Arkel); Wildte 1926", "Tingsplatserna", "Nytt spår 1 / plan D", "Artikel", "Makt",
     "ISOF-namn (D3) + KMR", "Planerad", "16 mar 2027"),
    (2, "Husby, Tuna och Hov – maktens platser?", "Ligger stenarna närmare centralortsnamnen än slumpen ger?",
     "Lindqvist 1917, 1918 (bara kultnamn prövade)", "Centralortsnamnen", "15 / plan D", "Artikel", "Makt",
     "ISOF-namn (D3)", "Planerad", "mar 2027"),
    (2, "Högarna och stenarna", "Ersatte stenarna gravhögarna, eller hamnade de på samma platser?",
     "Ambrosiani 1968; Holmqvist 1957", "Gravfältens ålder", "Nytt spår 3 / plan D", "Artikel", "Människor och släkt",
     "Har (KMR)", "Planerad", "15 jun 2027"),
    (2, "Stod stenarna vid bron och vadet?", "Är brostenarna och stenarna vid vadställen närmare vatten och väg än slumpen ger?",
     "Brostenarna i SRI; Lovén", "Placeringar prövas inte", "3 / plan D", "Artikel", "Landskap",
     "Har; höjdmodell (D2) för vad", "Idé", "dec 2027"),
    (2, "Hur gammal var marken under runstenen?", "Hur länge hade marken legat torr när stenen restes – och vad säger det om bygdens ålder?",
     "Tunberg 1920; Lindroth 1914–15 (namnlagren)", "Strandlinje, landhöjning", "5", "Artikel", "Landskap",
     "Har SGU-strandlinje; höjdmodell (D2)", "Idé", "fri lucka 2027"),
    (2, "Stenarna vid vattnet – vilket vatten?", "Håller 64 % inom 500 m från vattnet med strandlinjen ±1–3 m och äldre fornlämningar som jämförelse?",
     "Stenberger 1942; Calissendorff 1991; Lindqvist 1928; Edberg", "Strandlinje, landhöjning", "Självkontroll / plan B", "Artikel", "Landskap",
     "Höjdmodell (D2)", "Planerad (självkontroll)", "dec 2027"),
    # Plan E: kors och bön
    (1, "Var korset en bekännelse?", "Står korset på stenar utan kristen text? Följer korstypen öst eller väst och släkten?",
     "Gräslund; Lindqvist 1926", "Korset läses som tro", "8 / plan E", "Artikel", "Tro",
     "Har (Runor 2020:s korstypologi)", "Planerad", "13 apr 2027"),
    (2, "Kom kristendomen från Danmark?", "Dyker kors och böner upp tidigare närmare Jelling och Hedeby, inom stilgrupp?",
     "Lindqvist 1926", "Korset läses som tro", "22 / plan E", "Artikel", "Tro",
     "Har", "Idé", "apr 2027"),
    (2, "Flyttade bönen till gravhällarna?", "Tystnade bönerna när runstenarna slutade resas – eller flyttade de till gravhällarna? (redovisas separat)",
     "Runor 2020: 260 gravhällar", "Gravhällar, medeltida runor", "13 / plan E", "Artikel", "Tro",
     "Har", "Idé", "fri lucka 2027"),
    (2, "Tegnar i söder, böner i norr", "Skiljer sig budskapen mellan rikena?",
     "Gräslund 2001 (referensen kontrolleras)", "Korset läses som tro", "Plan E", "Artikel", "Tro",
     "Har", "Utkast finns", "27 apr 2027"),
    # Plan F: människorna
    (1, "Hushållet som stenarna glömde", "Hur många personer och relationer nämns per sten? Var finns tjänstefolket och de ofria?",
     "Ringstedt 1989 (7–10 personer per hushåll)", "De ofria, tjänstefolket", "Nytt spår 4 / plan F", "Artikel", "Människor",
     "Har", "Planerad", "11 maj 2027"),
    (1, "Kvinnorna som flyttade?", "Är kvinnonamnen mindre typiska för bygden än männens – ett spår av att kvinnor gifte sig bort?",
     "Kvinnor och barn i 436 texter; Gräslund", "Kvinnor och barn", "Nytt spår 5 / plan F", "Artikel", "Människor",
     "Har", "Planerad", "25 maj 2027"),
    (2, "Félagi, drengr, gildi – vännerna utanför familjen", "Vilka utanför släkten reste stenar, och var?",
     "Kvinnor och ofria; Sawyer 2000", "De ofria, tjänstefolket", "Plan F", "Artikel", "Människor",
     "Har", "Idé", "fri lucka 2027"),
    (2, "Flickan som blev mö", "Underskattas döttrarna när møy/mǽr översätts som ”flicka”?",
     "Läsningarna av møy/mǽr", "Kvinnor och barn", "10", "Artikel", "Människor",
     "Har", "Idé (följer Döttrarna som runstenarna glömde)", "fri lucka 2027"),
    # Gränser
    (1, "När blev götarna svear?", "Syns sammanslagningen av riket som en gradient i stenarna 1000–1150?",
     "Nerman 1963; Källström 2025", "Socken-, härads- och landskapsgränser", "Nytt spår 6", "Artikel", "Gränser",
     "Har (histmaps, folklanden)", "Planerad", "13 jul 2027"),
    (2, "Kolmården – gränsen i skogen", "Skiljer Kolmården Mälardalen från Sydsverige i stil, språk och formler?",
     "Nerman 1963; Larsson 2002 (Yrrunan)", "Socken-, härads- och landskapsgränser", "Nytt spår 6", "Artikel", "Gränser",
     "Har", "Idé", "jul 2027"),
    (2, "Sammanfaller gränserna? (Kossinnatestet)", "Går gränserna för stil, språk, formler, namn och kors på samma ställen – eller är det olika kartor?",
     "Larsson 2002; Källström 2025", "Socken-, härads- och landskapsgränser", "Nytt spår 7", "Artikel", "Metod",
     "Har", "Idé", "jul 2027"),
    (2, "Roden – var kusten ny mark för österfararna?", "Var kustbygden yngre och utgångspunkt för österfärderna?",
     "Tunberg 1920", "Strandlinje, landhöjning", "20", "Artikel", "Människor och resor",
     "Har", "Idé", "fri lucka 2027"),
    # Silver och ekonomi
    (1, "Silvret och stenarna", "Skattfynd mot runstenar per socken: Gotland mot Uppland, dirhamflödets slut, skatter efter dem som dog borta",
     "Sawyer 2000; Hårdh", "Skattfynd, mynt", "6", "Artikel", "Ekonomi",
     "Saknas: skattfynd (D5)", "Väntar på data", "17 aug 2027"),
    (1, "Vad kostade en runsten?", "Landskapslagarnas öre, huggvolymen i 3D och ett monumentindex",
     "Malmer 1988 (dos–respons)", "Stenarna läses som befolkning", "Nytt spår 8", "Artikel", "Ekonomi",
     "3D har; lagarnas priser (D11)", "Planerad", "14 sep 2027"),
    (2, "Varför sten?", "Vilka bergarter valdes, och bär materialet budskapet?",
     "Bergart och proveniens i 370 texter", "Stenens bergart", "Plan F/ sep", "Artikel", "Stenen",
     "Berggrund (D1)", "Utkast finns", "28 sep 2027"),
    (2, "Var kom stenen ifrån?", "Lokal sten eller transporterad? Bergart mot berggrunden under platsen",
     "Bergart och proveniens", "Stenens bergart", "Sep", "Artikel", "Stenen",
     "Berggrund (D1)", "Väntar på data", "sep 2027"),
    # Kyrkor
    (2, "Kyrkorna som daterar stenarna", "Inmurade stenar får en senaste möjliga datering ur kyrkans byggår eller dendro",
     "Wase 1995; Frödin 1932", "Kyrkornas ålder", "1", "Artikel", "Datering",
     "Saknas: kyrkornas byggår (D6)", "Väntar på data", "12 okt 2027"),
    (3, "Träkyrkorna vi inte ser", "Ändras resultaten om kyrkans plats när de första träkyrkorna inte syns?",
     "Frödin 1932; 2016_097", "Kyrkornas ålder", "8", "Artikel", "Tro",
     "D6", "Idé", "2028"),
    # Vägar och vatten
    (2, "Vintervägen", "Gick vägarna över isen och myren – och syns det i var stenarna står?",
     "Vintervägar i 135 texter", "Vägarnas ålder", "Nytt spår 9", "Artikel", "Landskap",
     "Höjdmodell och vattendrag (D2)", "Väntar på data", "7 dec 2027"),
    # Ristare
    (1, "Kännarskap mot slumpen – hur säker är en ristartillskrivning?", "Hur ofta förekommer ett ristardrag av en slump? Attributioner med basfrekvens",
     "Ristartillskrivning i 272 texter; Källström 2007", "Ristartillskrivning", "9", "Artikel", "Ristarna",
     "Har", "Pågår (attributionsspåret)", "fri lucka 2027"),
    (2, "Dubbelstenar – stod de ihop?", "Stod stenar med samma resare och döde verkligen tillsammans?",
     "Lindqvist 1926", "Flyttade, inmurade", "19", "Artikel", "Människor och släkt",
     "Har (Runor 2020:s ursprungsplats)", "Idé", "fri lucka 2027"),
    (3, "Verkstäderna bakom stenarna", "Uppträder en ny stilgrupp först hos en namngiven ristare? Samma verkstäder för kors och torshammare?",
     "Sigtuna 1928; Lindqvist 1922", "Ristartillskrivning", "18", "Artikel", "Ristarna",
     "Har", "Idé", "2028"),
    # Forskningshistoria och metod
    (1, "Hundra år av antaganden – vad höll?", "Flaggskeppet: vad hundra års påståenden visar när de prövas mot hela korpusen",
     "Hela genomgången: 1 577 texter", "Placeringar prövas inte", "14", "Artikel", "Metod",
     "Har", "Planerad", "9 nov 2027"),
    (1, "Vad svensk runforskning har missat", "Huvudrapporten med studierna A–F, också det som inte höll",
     "Hela genomgången", "Placeringar prövas inte", "14", "Rapport", "Metod",
     "Har", "Planerad", "23 nov 2027"),
    (2, "Forskarnas favoritstenar", "Vilka stenar skriver forskarna om – och är det ”typiska” bara det mest beskrivna? (2 043 stenar i 920 artiklar)",
     "Litteraturhänvisningar i Runor 2020; Vitkis tidskriftsindex", "Forskarnas uppmärksamhet", "Nytt spår 10", "Artikel", "Forskningshistoria",
     "Har (nytt index 10 nov)", "Idé – data klar", "fri lucka 2027"),
    (2, "Uppland som norm", "Hur mycket av runologins regler bygger bara på Uppland?",
     "Uppland som norm i 91 texter", "Uppland och Mälardalen som norm", "12", "Artikel", "Metod",
     "Har", "Idé", "fri lucka 2027"),
    (2, "Läser utgivaren stenen?", "Avgör SRI-bandet och utgivaren hur en sten läses och vem som får den?",
     "SRI-utgivarna", "Utgivare, antikvarier", "12", "Artikel", "Forskningshistoria",
     "Har", "Idé", "fri lucka 2027"),
    (2, "Sagorna som facit", "Hur ofta används sagor, lagar och Adam av Bremen som facit för stenarna – och håller det?",
     "Sena källor i 202 texter", "Sena källor", "–", "Artikel", "Metod",
     "Har", "Idé", "fri lucka 2027"),
    (2, "Kan man läsa namn i slumpen?", "Nollmodeller för runologin: hur ofta blir korta runföljder namn, talmystik eller nonsens av en slump?",
     "Talmystik (16, 24, 40 runor); nonsensinskrifter", "Ristartillskrivning", "11", "Artikel", "Metod",
     "Har", "Idé", "fri lucka 2027"),
    (3, "Norrland och periferin", "Vad vet vi om runstenarna utanför Mälardalen och Götaland, och vad saknas?",
     "Norrland och samer i 181 texter", "Norrland, samer", "–", "Artikel", "Landskap",
     "Har", "Idé", "2028"),
    (3, "Runstenarna som ortnamnsbelägg", "Stenarna är 200–300 år äldre än diplomen: vad säger de om namnlagren?",
     "Lindroth 1914–15", "Centralortsnamnen", "21", "Artikel", "Språk",
     "Har", "Idé", "2028"),
    (3, "Naturvetenskapen som saknas", "Vad skulle isotoper, aDNA, pollen och fosfat kunna avgöra?",
     "Naturvetenskapliga metoder i 240 texter", "Naturvetenskapliga metoder", "–", "Artikel", "Metod",
     "Isotoper och aDNA (D9), pollen (D7)", "Idé", "2028"),
    (3, "Färgen på stenarna", "Vad vet vi om färg och ommålning – och vad kan mätas?",
     "Färg och ommålning i 67 texter", "Färg och ommålning", "–", "Artikel", "Stenen",
     "Saknas", "Idé", "2028"),
]

HEAD = ["Nr", "Prioritet", "Föreslagen titel", "Vad artikeln prövar", "Underlag i Fornvännen och Futhark",
        "Blind fläck i litteraturen", "Antal texter som tar upp den", "Andel av de lästa texterna", "Spår / plan", "Typ",
        "Vinkel", "Data", "Status", "Föreslagen tid"]
WID = [5, 9, 40, 56, 44, 34, 13, 12, 18, 9, 18, 30, 42, 15]
F = "Arial"
thin = Side(style="thin", color="D9D2C5")
RUST = "B7410E"

wb = Workbook()
ws = wb.active
ws.title = "Artiklar"
ws.append(HEAD)
for i, (prio, titel, fraga, underlag, flack, spar, typ, vinkel, data, status, manad) in enumerate(A, start=1):
    namn, n = bf(flack)
    r = i + 1
    ws.append([i, prio, titel, fraga, underlag, namn, n, f"=G{r}/Om!$B$4", spar, typ, vinkel, data, status, manad])
last = ws.max_row
for c, w in enumerate(WID, start=1):
    ws.column_dimensions[get_column_letter(c)].width = w
for row in ws.iter_rows(min_row=1, max_row=last):
    for cell in row:
        cell.font = Font(name=F, size=10)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.border = Border(bottom=thin)
for cell in ws[1]:
    cell.font = Font(name=F, size=10, bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=RUST)
    cell.alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[1].height = 32
for r in range(2, last + 1):
    ws.cell(r, 3).font = Font(name=F, size=10, bold=True)
    ws.cell(r, 2).alignment = Alignment(horizontal="center", vertical="top")
    ws.cell(r, 1).alignment = Alignment(horizontal="center", vertical="top")
    ws.cell(r, 7).number_format = "#,##0"
    ws.cell(r, 8).number_format = "0%"
ws.freeze_panes = "D2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(HEAD))}{last}"
for val, color in ((1, "F6D9CC"), (2, "FBEDE6"), (3, "FFFFFF")):
    ws.conditional_formatting.add(f"B2:B{last}", CellIsRule(operator="equal", formula=[str(val)], fill=PatternFill("solid", fgColor=color)))
dv = DataValidation(type="list", formula1='"1,2,3"', allow_blank=False)
ws.add_data_validation(dv)
dv.add(f"B2:B{last}")

# Sammanfattning med formler
s = wb.create_sheet("Sammanfattning")
s["A1"] = "Sammanfattning av artikellistan"
s["A1"].font = Font(name=F, size=13, bold=True, color=RUST)
s.append([])
s.append(["Prioritet", "Antal", "Varav artiklar", "Varav rapporter"])
for p in (1, 2, 3):
    r = s.max_row + 1
    s.append([p, f'=COUNTIF(Artiklar!$B$2:$B${last},A{r})', f'=COUNTIFS(Artiklar!$B$2:$B${last},A{r},Artiklar!$J$2:$J${last},"Artikel")',
              f'=COUNTIFS(Artiklar!$B$2:$B${last},A{r},Artiklar!$J$2:$J${last},"Rapport")'])
r = s.max_row + 1
s.append(["Totalt", f"=SUM(B4:B{r - 1})", f"=SUM(C4:C{r - 1})", f"=SUM(D4:D{r - 1})"])
s.append([])
s.append(["Status (börjar med)", "Antal"])
hdr2 = s.max_row
for st in ("Klar", "Körd", "Pågår", "Utkast finns", "Planerad", "Väntar på data", "Idé"):
    r = s.max_row + 1
    s.append([st, f'=COUNTIF(Artiklar!$M$2:$M${last},A{r}&"*")'])
s.append([])
s.append(["Vinkel", "Antal"])
hdr3 = s.max_row
for v in sorted({a[7] for a in A}):
    r = s.max_row + 1
    s.append([v, f'=COUNTIF(Artiklar!$K$2:$K${last},A{r})'])
for row in s.iter_rows(min_row=2, max_row=s.max_row):
    for cell in row:
        cell.font = Font(name=F, size=10)
for hr in (3, hdr2, hdr3):
    for cell in s[hr]:
        if cell.value:
            cell.font = Font(name=F, size=10, bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor=RUST)
tot = 7
for cell in s[tot]:
    cell.font = Font(name=F, size=10, bold=True)
s.column_dimensions["A"].width = 26
for col in "BCD":
    s.column_dimensions[col].width = 16

# Blinda fläckar
b = wb.create_sheet("Blinda fläckar")
b.append(["#", "Blind fläck", "Texter", "Andel", "Första år", "Sista år", "Tidigaste texter"])
for i, k in enumerate(sorted(BF["kategorier"], key=lambda k: -k["texter"]), start=1):
    r = b.max_row + 1
    b.append([i, k["kategori"], k["texter"], f"=C{r}/Om!$B$4", k["forsta"], k["sista"], "; ".join(k.get("tidigast", [])[:3])])
for row in b.iter_rows(min_row=1, max_row=b.max_row):
    for cell in row:
        cell.font = Font(name=F, size=10)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
for cell in b[1]:
    cell.font = Font(name=F, size=10, bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=RUST)
for r in range(2, b.max_row + 1):
    b.cell(r, 4).number_format = "0%"
for c, w in zip("ABCDEFG", (5, 60, 9, 9, 10, 10, 60)):
    b.column_dimensions[c].width = w
b.freeze_panes = "C2"

# Om listan
o = wb.create_sheet("Om")
rows = [
    ("Artikelidéer ur Fornvännen och Futhark", None),
    ("Vitki, sammanställd 10 november 2026", None),
    (None, None),
    ("Lästa texter i genomgången", N_TEXTER),
    ("Tidskrifter", "Fornvännen 1906–2023 och Futhark 1–15 (båda fria, CC BY 4.0)"),
    ("Källfiler", "utdata/litteraturgenomgang/SYNTES.md, IDEER_HUVUDSPAR.md, blindflackar.json; PUBLICERINGSPLAN.md"),
    (None, None),
    ("Prioritet", "1 = data finns eller nästan, starkt underlag i litteraturen och en tydlig fråga för läsaren; 2 = god idé, men kräver mer data eller passar senare; 3 = idé för 2028 eller saknar data"),
    ("Antal texter", "Hur många av de lästa texterna som tar upp den blinda fläck artikeln bygger på (räknat i blindflackar.json). Det mäter hur ofta frågan återkommer, inte hur stark artikeln blir."),
    ("Underlag", "Författare och år som läsarna lyfte fram. Läsarkontrollen visade att 76 % av påståendena var rätt återgivna, så varje källa kontrolleras mot originaltexten innan artikeln skrivs."),
    ("Status och tid", "Ur PUBLICERINGSPLAN.md. ”Fri lucka” betyder att artikeln kan läggas in när en planerad studie inte håller eller data dröjer."),
    ("Data", "D-koderna hänvisar till dataplanen i PUBLICERINGSPLAN.md (D1 berggrund, D2 höjdmodell, D3 ortnamn, D5 skattfynd, D6 kyrkornas byggår, D11 lagarnas priser)."),
    ("Regler", "Varje studie låses med en analysplan innan något räknas. Artiklar bara om fynd som håller; nollresultat blir rapporter. Runstenar i Sverige är standard."),
    ("Redigera", "Ändra prioritet (kolumn B, 1–3), status (M) och tid (N) direkt i fliken Artiklar. Sammanfattningen räknas om av sig själv."),
]
for k, v in rows:
    o.append([k, v])
o["A1"].font = Font(name=F, size=13, bold=True, color=RUST)
for row in o.iter_rows(min_row=2, max_row=o.max_row):
    for cell in row:
        cell.font = Font(name=F, size=10, bold=cell.column == 1)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
o["A2"].font = Font(name=F, size=10, italic=True)
o.column_dimensions["A"].width = 26
o.column_dimensions["B"].width = 100
wb.move_sheet("Om", offset=-3)
wb.active = 1
wb.calculation.fullCalcOnLoad = True  # Excel och Numbers räknar formlerna när filen öppnas
wb.save(OUT)
print(OUT, len(A), "rader")
