"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Fullt prövat fynd): "Runstenarna vände texten mot
vägen – hälften av ristningarna inom 45 grader från vägen, mot en fjärdedel väntat" (sv + en). Den låsta planen
analysplaner/2026-10-29-ristningens-riktning.md (H1–H4) och tilläggsplanen för robusthetsstegen
analysplaner/2026-10-31-riktning-trappan.md. Alla siffror asserteras mot utdata/riktning/riktning.json och trappan.json.
    ../../../.venv/bin/python build_rapport_riktning.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-10-31"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = "analysplanen låstes 2026-10-29; analysen kördes 2026-10-29; tilläggsplanen för känslighetsanalyserna låstes och kördes 2026-10-31"
TL_EN = "the analysis plan was locked 2026-10-29; the analysis was run 2026-10-29; the addendum plan for the sensitivity analyses was locked and run 2026-10-31"
RD = os.path.join(ROOT, "utdata", "riktning")
R = json.load(open(os.path.join(RD, "riktning.json"), encoding="utf-8"))
TR = json.load(open(os.path.join(RD, "trappan.json"), encoding="utf-8"))
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0][:16]
       for k in ("2026-10-29-ristningens-riktning", "2026-10-31-riktning-trappan")}
assert SHA["2026-10-29-ristningens-riktning"].startswith("cd73b962") and SHA["2026-10-31-riktning-trappan"].startswith("4da9710d")

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731


def pfmt(p, en=False):
    if p < 0.001:
        s = f"{p:.4f}"
    elif p < 0.1:
        s = f"{p:.3f}"
    else:
        s = f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the locked plan (H1–H4) ------------------------------------------------------------------------------------------
assert (R["n"], R["n_vag"], R["n_vag_text"], R["n_gard"]) == (219, 123, 69, 94)
A, HA, HB = R["resultat"]["alla"], R["resultat"]["A"], R["resultat"]["B"]
H1, H2, H3, H4 = A["H1"], A["H2"], A["H3"], A["H4"]
assert R["status"] == {"H1": "ingen skillnad påvisad", "H2": "håller", "H3": "ingen skillnad påvisad", "H4": "ingen skillnad påvisad"}
assert (d2(H2["medel_cos"]), d2(H2["vantat"]), pc(H2["andel_inom_45"]), H2["p"]) == ("0,37", "0,01", 50, 0.0001)
assert abs(R["holm"]["H2"] - 0.0004) < 1e-9
assert (HA["H2"]["n"], HB["H2"]["n"], d2(HA["H2"]["medel_cos"]), d2(HB["H2"]["medel_cos"])) == (71, 52, "0,45", "0,26")
assert HA["H2"]["p"] == 0.0001 and 0.018 < HB["H2"]["p"] < 0.019
assert 0.48 < H1["p"] < 0.49 and 0.30 < H3["p"] < 0.31 and 0.86 < H4["p"] < 0.87 and H4["n_bro"] == 9
DESC = R["beskrivning"]
ST = DESC["streck"]
assert (ST["V"], ST["N"], ST["Ö"], ST["S"], pc(DESC["andel_soder"])) == (37, 26, 25, 25, 32)

# ---- the addendum ladder ----------------------------------------------------------------------------------------------
assert TR["plan"] == "analysplaner/2026-10-31-riktning-trappan.md" and TR["all_hold"] is True and TR["lopo_holds"] is True
RU, LO = TR["rungs"], TR["lopo"]
assert set(RU) == {"huvud", "halva_A", "halva_B", "socken", "en_per_ristare", "utan_aterresta", "utan_flyttade_runor",
                   "dagens_flyttregel", "bara_text", "bara_registrerad"} and all(r["holds"] for r in RU.values())
assert abs(RU["huvud"]["medel_cos"] - H2["medel_cos"]) < 1e-9  # same measure as the plan's H2
assert (RU["en_per_ristare"]["n"], TR["n_carvers"], TR["n_parishes"], TR["n_reerected"], TR["n_reerected_alla_219"], TR["n_moved_runor"],
        TR["n_moved_now"]) == (93, 20, 76, 14, 29, 10, 0)
assert (RU["bara_text"]["n"], pc(RU["bara_text"]["andel_inom_45"]), RU["bara_registrerad"]["n"], pc(RU["bara_registrerad"]["andel_inom_45"])) == (69, 62, 80, 28)
assert 0.019 < RU["bara_registrerad"]["p"] < 0.020 and set(LO) == {"U", "Sö", "Ög"}
assert (LO["U"]["n"], pc(LO["U"]["andel_kvar"]), LO["Sö"]["n"], LO["Ög"]["n"]) == (62, 50, 92, 113)

SLUG = "ristningen-vand-mot-vagen"
title = "Runstenarna vände texten mot vägen – hälften av ristningarna inom 45 grader från vägen, mot en fjärdedel väntat"
title_en = "The runestones turned their text towards the road – half of the inscriptions within 45 degrees of the road, against a quarter expected"
summary = ("Förregistrerad studie. Av de runstenar som står kvar på sin plats och där vi vet var vägen gick vänder hälften "
           "ristningen mot vägen, mot en fjärdedel om riktningen vore slumpvis. Fyndet håller i båda halvorna av "
           "materialet och i alla känslighetsanalyser. Texten vändes mot den som gick förbi, inte mot solen och inte mot "
           "gården.")
summary_en = ("Pre-registered study. Of the runestones that still stand in place and where we know where the road ran, half "
              "turn the inscription towards the road, against a quarter if the direction were random. The finding holds in "
              "both halves of the material and in every sensitivity analysis. The text was turned towards those passing by, "
              "not towards the sun and not towards the farm.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    f = (lambda x: f"{100 * x:.1f}".replace(".", ",")) if sv else (lambda x: f"{100 * x:.1f}")
    rows = [":::chart Ristningen vänd inom 45 grader från vägen, procent" if sv else ":::chart Inscription turned within 45 degrees of the road, percent",
            f"+{'Alla stenar med väg' if sv else 'All stones with a road'} | {f(H2['andel_inom_45'])} | {H2['n']} {'stenar' if sv else 'stones'}",
            f"{'Väg ur registrets text' if sv else 'Road from the register text'} | {f(RU['bara_text']['andel_inom_45'])} | {RU['bara_text']['n']} {'stenar' if sv else 'stones'}",
            f"{'Registrerad färdväg inom 500 m' if sv else 'Registered route within 500 m'} | {f(RU['bara_registrerad']['andel_inom_45'])} | {RU['bara_registrerad']['n']} {'stenar' if sv else 'stones'}",
            f"{'Väntat om riktningen vore slumpvis' if sv else 'Expected if the direction were random'} | {f(0.25)} |",
            "Källa: Kulturmiljöregistret och Rundata." if sv else "Source: the Swedish register of ancient monuments and Rundata.", ":::"]
    return "\n".join(rows)


def rung_sv(k, label):
    r = RU[k]
    return f"- {label} ({r['n']} stenar): medel-cos {d2(r['medel_cos'])} mot {d2(r['vantat'])}, {pfmt(r['p'])}."


def rung_en(k, label):
    r = RU[k]
    return f"- {label} ({r['n']} stones): mean cos {r['medel_cos']:.2f} against {r['vantat']:.2f}, {pfmt(r['p'], True)}."


body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, vägar, placering, ristningens riktning, cirkulär statistik, Kulturmiljöregistret, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Var runstenarna restes har diskuterats länge, och vägarna är ett av svaren: stenar vid vägar syntes. Ingen har mätt åt vilket håll ristningen vändes. Frågan här är om texten vändes mot vägen, mot gården eller mot ett visst väderstreck.
**Material.** {R['n']} svenska vikingatida runstenar som står kvar på sin plats och där Kulturmiljöregistret anger åt vilket håll ristningen vetter. För {R['n_vag']} av dem finns en väg att mäta mot, för {R['n_gard']} en bytomt.
**Metod.** Förregistrerad studie med fyra test och Holm-korrigering. Måttet är cosinus för vinkeln mellan ristningens riktning och riktningen till vägen, jämfört med 9 999 omblandningar av riktningarna inom landskapet. Intern replikering i två halvor och tio känslighetsanalyser enligt en låst tilläggsplan.
**Resultat.** Hälften av stenarna, {pc(H2['andel_inom_45'])} procent, vänder ristningen inom 45 grader från vägen, mot en fjärdedel om riktningen vore slumpvis. Medel-cos {d2(H2['medel_cos'])} mot {d2(H2['vantat'])} väntat, {pfmt(H2['p'])}, Holm-korrigerat p = 0,0004. Det håller i båda halvorna och i alla känslighetsanalyser, också utan Uppland, socken för socken, med en sten per ristare och utan återresta stenar. Riktningarna i sig är jämnt spridda över kompassen, och ristningen vänds inte mot gården.
**Slutsats.** Texten vändes mot den som gick förbi på vägen, inte mot solen och inte mot gården. Den största svagheten är att vägen i registret ofta är dagens väg; med bara registrerade äldre färdvägar är sambandet svagare men går åt samma håll.

## 1. Inledning

Gunnar Ekholm (1950) frågade var runstenarna restes. Torun Zachrisson (1998) har satt dem i samband med gård, gräns och gravfält, Lydia Klos (2009) har hävdat att de flesta restes vid gravfält, och Shane McLeod (2014) har invänt att det överbetonar gravfälten på bekostnad av andra platser, som vägarna. Johan Bollaert (2016) jämförde stenar längs tre vikingatida vägar med andra stenar i samma trakter och fann att stenarna vid vägarna oftare har påfallande ornamentik och oftare ingår i monument med flera stenar, vilket stöder att de restes för att synas.

Det som saknas är ett mått på hur själva ristningen vändes. En sten kan stå vid en väg men vända texten åt ett annat håll. Syftet här är att pröva om ristningen vändes mot vägen, mot gården eller mot ett visst väderstreck, med de uppgifter om ristningens riktning som Kulturmiljöregistret har för en del stenar.

## 2. Förregistrering: hypotes och plan

Hypoteserna, måtten och tolkningsreglerna skrevs ned i en analysplan den 29 oktober 2026, innan någon riktning hade räknats. Planen har kontrollsumman SHA-256 `{SHA['2026-10-29-ristningens-riktning']}…` (se Data och kod). Före låsningen var bara antalet poster känt: 456 poster i registret anger en riktning, 369 gäller en enda sten med en riktning, 219 av dem står kvar på sin plats, och 88 av de 369 nämner en väg med väderstreck.

Planen prövar fyra hypoteser med Holm-korrigering: H1 att riktningarna inte är jämnt fördelade över kompassen, H2 att ristningen vänds mot vägen, H3 att den vänds mot gården och H4 att bro- och vägstenar vänds mer mot vägen än andra. En hypotes *håller* när Holm-p är under 0,05 och riktningen är densamma med p under 0,05 i båda halvorna.

Planen innehöll inte projektets fasta känslighetsanalyser, som är byggda för samband mellan två drag och inte för riktningar. Motsvarande steg för riktningar bestämdes därför i en tilläggsplan den 31 oktober 2026 (SHA-256 `{SHA['2026-10-31-riktning-trappan']}…`), innan de räknades. Två av stegen, halvorna och vägens källa, fanns redan i huvudplanen. En kontroll av återresta stenar gjordes efter huvudkörningen den 29 oktober med en annan ordlista; i tilläggsplanen låstes ordlistan innan steget räknades.

## 3. Material

- **Stenarna.** Svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata) som står kvar på sin plats och har känt läge, och vars post i Riksantikvarieämbetets Kulturmiljöregister gäller just den stenen och anger en enda riktning med orden ”vetter mot” och ett av sexton väderstreck: {R['n']} stenar. Bara runstenar.
- **Vägen.** I första hand registrets egen uppgift om stenens läge i förhållande till en väg (”5 m Ö om väg”; vägen ligger då åt motsatt håll): {R['n_vag_text']} stenar. Annars närmaste registrerade färdväg eller vägmärke inom 500 meter. Sammanlagt {R['n_vag']} stenar med väg.
- **Gården.** Närmaste registrerade bytomt eller gårdstomt inom en kilometer: {R['n_gard']} stenar.
- **Riktningarna** räknas som bäringar från stenen, med norr som 0 grader och väderstrecken i steg om 22,5 grader.
- **Halvorna** är projektets fasta indelning socken för socken.

## 4. Metod

**4.1 Måttet.** För varje sten räknas cosinus för vinkeln mellan ristningens riktning och riktningen till vägen: 1 när ristningen vetter rakt mot vägen, 0 när den vetter åt sidan och −1 när den vetter bort. Medelvärdet över stenarna jämförs med 9 999 omblandningar där ristningarnas riktningar fördelas om mellan stenarna inom samma landskap, så att landskapets allmänna riktningsmönster behålls. Testet är ensidigt. Andelen stenar inom 45 grader från vägen redovisas också; om riktningen vore slumpvis vore den en fjärdedel.

**4.2 De andra hypoteserna.** H1 prövas med Rayleighs test för jämn fördelning (Mardia & Jupp 2000). H3 prövas som H2 mot riktningen till gården. H4 jämför medel-cos mot vägen mellan bro- och vägstenar och övriga, med omblandning av etiketten inom landskapet, tvåsidigt.

**4.3 Korrigering och replikering.** Holm-korrigering (Holm 1979) över de fyra testen. Varje hypotes prövas också i var halva för sig.

**4.4 Känslighetsanalyserna** enligt tilläggsplanen: halvorna; utan ett landskap i taget (landskap med minst tio stenar med väg; signifikans krävs bara där minst två tredjedelar av stenarna är kvar); socknen som enhet, med ett värde per socken; en sten per säker ristare; utan återresta stenar; utan stenar som Riksantikvarieämbetets register Runor (2020) anger som flyttade; med dagens regel för flyttade stenar; bara vägar ur registrets text; och bara registrerade färdvägar och vägmärken. Ett steg håller när medel-cos ligger över det väntade och p är under 0,05.

**4.5 Avvikelser från planen.** Inga.

## 5. Resultat

**5.1 Mot vägen (H2).** Av de {H2['n']} stenarna med väg vänder {pc(H2['andel_inom_45'])} procent ristningen inom 45 grader från vägen. Medel-cos är {d2(H2['medel_cos'])} mot {d2(H2['vantat'])} väntat, {pfmt(H2['p'])}, det lägsta värde 9 999 omblandningar kan ge, och Holm-korrigerat p = 0,0004. Halva A: {HA['H2']['n']} stenar, medel-cos {d2(HA['H2']['medel_cos'])}, {pfmt(HA['H2']['p'])}. Halva B: {HB['H2']['n']} stenar, medel-cos {d2(HB['H2']['medel_cos'])}, {pfmt(HB['H2']['p'])}. H2 *håller* enligt planens regel. I klartext: av de stenar där vi vet var vägen gick vänder hälften texten mot vägen, inom 45 grader åt vardera hållet; om riktningen vore slumpvis skulle en fjärdedel göra det.

{chart(True)}

**5.2 Väderstrecket, gården och broarna (H1, H3, H4).** Riktningarna är jämnt spridda över kompassen: Rayleighs test {pfmt(H1['p'])}. Väster är vanligast ({ST['V']} stenar), sedan norr ({ST['N']}), öster ({ST['Ö']}) och söder ({ST['S']}); {pc(DESC['andel_soder'])} procent vetter mot söder, sydost eller sydväst. Mot gården: medel-cos {d2(H3['medel_cos'])} mot {d2(H3['vantat'])}, {pfmt(H3['p'])}. Bro- och vägstenarna ({H4['n_bro']} med väg) vänds inte mer mot vägen än andra stenar: {pfmt(H4['p'])}. Ingen av dem håller.

**5.3 Känslighetsanalyserna.** Alla håller:

{rung_sv('halva_A', 'Halva A')}
{rung_sv('halva_B', 'Halva B')}
- Utan ett landskap i taget: utan Uppland ({LO['U']['n']} stenar kvar, hälften, så bara riktningen krävs) medel-cos {d2(LO['U']['medel_cos'])}, {pfmt(LO['U']['p'])}; utan Södermanland ({LO['Sö']['n']}) {d2(LO['Sö']['medel_cos'])}, {pfmt(LO['Sö']['p'])}; utan Östergötland ({LO['Ög']['n']}) {d2(LO['Ög']['medel_cos'])}, {pfmt(LO['Ög']['p'])}.
{rung_sv('socken', f"Socknen som enhet, {TR['n_parishes']} socknar")}
{rung_sv('en_per_ristare', f"En sten per säker ristare, {TR['n_carvers']} ristare")}
{rung_sv('utan_aterresta', f"Utan återresta stenar, {TR['n_reerected']} bort")}
{rung_sv('utan_flyttade_runor', f"Utan stenar som Runor anger som flyttade, {TR['n_moved_runor']} bort")}
- Med dagens regel för flyttade stenar räknas ingen av de {H2['n']} som flyttad; resultatet är detsamma som huvudtestet.
{rung_sv('bara_text', f"Bara vägar ur registrets text, {pc(RU['bara_text']['andel_inom_45'])} procent inom 45 grader")}
{rung_sv('bara_registrerad', f"Bara registrerade färdvägar och vägmärken, {pc(RU['bara_registrerad']['andel_inom_45'])} procent inom 45 grader")}

Ordlistan för återresta stenar i tilläggsplanen träffar {TR['n_reerected_alla_219']} av alla {R['n']} stenar; kontrollen efter huvudkörningen, med en bredare ordlista, träffade 58. Båda ger samma resultat.

## 6. Diskussion

**Vad fyndet säger.** De som reste runstenarna vände texten mot vägen. Det gäller i hela materialet, i var halva, utan Uppland, socken för socken och med en sten per ristare, så det beror inte på några få platser eller verkstäder. Det gäller också utan de stenar som har rests upp på nytt, som annars kunde ha vänts mot dagens väg. Att riktningarna i övrigt är jämnt spridda över kompassen och inte följer gården visar att det var vägen, inte solen eller hemmet, som bestämde hur stenen vändes.

**Mot tidigare forskning.** Resultatet ger ett mått åt tanken att stenarna vid vägarna restes för att synas (Bollaert 2016) och åt McLeods (2014) invändning att vägarna har underskattats. Det står inte emot att många stenar restes vid gravfält (Klos 2009): en sten kan stå vid ett gravfält och vända texten mot vägen förbi det.

**Svagheter, i ordning efter vikt.**

1. **Vägen är ofta dagens väg.** Registrets text anger vägen vid inventeringen. Med bara registrerade äldre färdvägar och vägmärken är sambandet svagare ({pc(RU['bara_registrerad']['andel_inom_45'])} procent inom 45 grader, {pfmt(RU['bara_registrerad']['p'])}) men går åt samma håll. Där en sentida väg följer den gamla sträckningen mäter båda samma sak; där den inte gör det blir sambandet svagare, inte starkare.
2. **Urvalet.** Bara {R['n']} stenar har en riktning i registret, och vi vet inte vad som styrde vilka stenar som fick en sådan uppgift.
3. **Återresningar.** Ordsökningen fångar inte alla stenar som har rests upp på nytt. Resultatet är dock starkare utan de stenar den hittar, inte svagare.
4. **Upplösningen.** Riktningarna anges i sexton väderstreck, alltså i steg om 22,5 grader.

**Vad som skulle fälla fyndet.** Att sambandet försvann när vägarna mättes på de äldsta lantmäterikartorna, eller att en ny inventering av fler stenars riktning gav en jämn fördelning mot vägen.

## 7. Slutsats

Runstenarna vände sin text mot vägen: hälften av ristningarna vetter inom 45 grader från vägen, mot en fjärdedel om riktningen vore slumpvis, och sambandet tål varje känslighetsanalys. Ristarna skrev för den som gick förbi. Nästa steg är att mäta vägarna på 1600- och 1700-talens kartor.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Analysplanerna: `analysplaner/2026-10-29-ristningens-riktning.md` och `analysplaner/2026-10-31-riktning-trappan.md`, med kontrollsummorna i `.sha256`-filerna bredvid.
- Analysen: `utdata/riktning/analys.py` (resultat `riktning.json`, stenarna i `stenar.csv`); känslighetsanalyserna `utdata/riktning/trappa.py` (`trappan.json`).
- Registret: `data/raa/kmr_runstenar.json`, `data/raa/lamningar.csv` och `data/raa/lamningar_extra/`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_riktning.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.

## Referenser

- Bollaert, J. 2016. *Runstenar längs vägen. En undersökning av samband mellan runstenarnas placering och utformning*. Masteruppsats. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137 ff.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Mardia, K. V. & Jupp, P. E. 2000. *Directional Statistics*. Chichester: Wiley.
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25. doi:10.3721/037.006.2503
- Riksantikvarieämbetet. Kulturmiljöregistret, via K-samsök. Hämtat oktober 2026.
- Riksantikvarieämbetet. 2020. *Runor*. Runinskrifter i Sverige, databas.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholms universitet.

:::box Det viktigaste i korthet
- Runstenarna vände sin text mot vägen, inte mot solen och inte mot gården.
- Ristarna skrev för den som gick förbi: stenen var ett budskap till vägfarande, inte bara ett minne vid hemmet.
- Det tål varje kontroll vi har, men vägen i registret är ofta dagens väg, så nästa prov är de gamla kartorna.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, roads, placement, orientation of the inscription, circular statistics, Swedish register of ancient monuments, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Where the runestones were raised has long been discussed, and the roads are one of the answers: stones by roads were seen. Nobody has measured which way the inscription was turned. The question here is whether the text was turned towards the road, towards the farm or towards a particular point of the compass.
**Material.** {R['n']} Swedish Viking-Age runestones that still stand in place and for which the Swedish register of ancient monuments gives the direction the inscription faces. For {R['n_vag']} of them there is a road to measure against, for {R['n_gard']} a farm site.
**Method.** A pre-registered study with four tests and Holm correction. The measure is the cosine of the angle between the inscription's direction and the direction to the road, compared with 9,999 shuffles of the directions within the province. Internal replication in two halves and ten sensitivity analyses under a locked addendum plan.
**Results.** Half of the stones, {pc(H2['andel_inom_45'])} percent, turn the inscription within 45 degrees of the road, against a quarter if the direction were random. Mean cos {H2['medel_cos']:.2f} against {H2['vantat']:.2f} expected, {pfmt(H2['p'], True)}, Holm-corrected p = 0.0004. It holds in both halves and in every sensitivity analysis, also without Uppland, parish by parish, with one stone per carver and without re-erected stones. The directions themselves are spread evenly over the compass, and the inscription is not turned towards the farm.
**Conclusion.** The text was turned towards those passing by on the road, not towards the sun and not towards the farm. The main weakness is that the road in the register is often today's road; with only registered older routes the association is weaker but goes the same way.

## 1. Introduction

Gunnar Ekholm (1950) asked where the runestones were raised. Torun Zachrisson (1998) has related them to farm, boundary and grave field, Lydia Klos (2009) has argued that most were raised at grave fields, and Shane McLeod (2014) has objected that this overstates the grave fields at the expense of other places, such as the roads. Johan Bollaert (2016) compared stones along three Viking-Age roads with other stones in the same districts and found that the stones by the roads more often have striking ornament and more often belong to monuments of several stones, which supports that they were raised to be seen.

What is missing is a measure of how the inscription itself was turned. A stone may stand by a road but turn its text another way. The aim here is to test whether the inscription was turned towards the road, towards the farm or towards a particular point of the compass, with the information on the inscription's direction that the register gives for some stones.

## 2. Pre-registration: hypothesis and plan

The hypotheses, measures and rules of interpretation were written down in an analysis plan on 29 October 2026, before any direction had been computed. The plan has the SHA-256 checksum `{SHA['2026-10-29-ristningens-riktning']}…` (see Data and code). Before locking only the number of records was known: 456 records in the register give a direction, 369 concern a single stone with one direction, 219 of these stand in place, and 88 of the 369 mention a road with a compass point.

The plan tests four hypotheses with Holm correction: H1 that the directions are not evenly spread over the compass, H2 that the inscription is turned towards the road, H3 that it is turned towards the farm and H4 that bridge and road stones are turned towards the road more than others. A hypothesis *holds* when Holm p is below 0.05 and the direction is the same with p below 0.05 in both halves.

The plan did not contain the project's fixed sensitivity analyses, which are built for associations between two traits and not for directions. The corresponding steps for directions were therefore fixed in an addendum plan on 31 October 2026 (SHA-256 `{SHA['2026-10-31-riktning-trappan']}…`), before they were computed. Two of the steps, the halves and the source of the road, were already in the main plan. A check of re-erected stones was made after the main run on 29 October with a different word list; in the addendum plan the word list was locked before the step was computed.

## 3. Material

- **The stones.** Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata) that still stand in place and have a known location, and whose record in the Swedish National Heritage Board's register of ancient monuments concerns just that stone and gives one direction with the words "faces" and one of sixteen compass points: {R['n']} stones. Runestones only.
- **The road.** First the register's own statement of the stone's position relative to a road ("5 m E of road"; the road then lies in the opposite direction): {R['n_vag_text']} stones. Otherwise the nearest registered route or road marker within 500 metres. {R['n_vag']} stones with a road in all.
- **The farm.** The nearest registered village or farm site within one kilometre: {R['n_gard']} stones.
- **The directions** are computed as bearings from the stone, with north as 0 degrees and the compass points in steps of 22.5 degrees.
- **The halves** are the project's fixed division parish by parish.

## 4. Method

**4.1 The measure.** For each stone the cosine of the angle between the inscription's direction and the direction to the road is computed: 1 when the inscription faces the road straight on, 0 when it faces sideways and −1 when it faces away. The mean over the stones is compared with 9,999 shuffles in which the inscriptions' directions are redistributed among the stones within the same province, so that each province's general pattern of directions is kept. The test is one-sided. The share of stones within 45 degrees of the road is also reported; if the direction were random it would be a quarter.

**4.2 The other hypotheses.** H1 is tested with Rayleigh's test of uniformity (Mardia & Jupp 2000). H3 is tested like H2 against the direction to the farm. H4 compares the mean cos towards the road between bridge and road stones and the others, with the label shuffled within the province, two-sided.

**4.3 Correction and replication.** Holm correction (Holm 1979) over the four tests. Each hypothesis is also tested in each half on its own.

**4.4 The sensitivity analyses** under the addendum plan: the halves; without one province at a time (provinces with at least ten stones with a road; significance required only where at least two thirds of the stones remain); the parish as the unit, with one value per parish; one stone per secure carver; without re-erected stones; without stones the National Heritage Board's register Runor (2020) gives as moved; with today's rule for moved stones; only roads from the register text; and only registered routes and road markers. A step holds when the mean cos lies above the expected value and p is below 0.05.

**4.5 Deviations from the plan.** None.

## 5. Results

**5.1 Towards the road (H2).** Of the {H2['n']} stones with a road, {pc(H2['andel_inom_45'])} percent turn the inscription within 45 degrees of the road. The mean cos is {H2['medel_cos']:.2f} against {H2['vantat']:.2f} expected, {pfmt(H2['p'], True)}, the lowest value 9,999 shuffles can give, and Holm-corrected p = 0.0004. Half A: {HA['H2']['n']} stones, mean cos {HA['H2']['medel_cos']:.2f}, {pfmt(HA['H2']['p'], True)}. Half B: {HB['H2']['n']} stones, mean cos {HB['H2']['medel_cos']:.2f}, {pfmt(HB['H2']['p'], True)}. H2 *holds* by the plan's rule. In plain words: of the stones where we know where the road ran, half turn their text towards the road, within 45 degrees either way; if the direction were random, a quarter would.

{chart(False)}

**5.2 The compass, the farm and the bridges (H1, H3, H4).** The directions are spread evenly over the compass: Rayleigh's test {pfmt(H1['p'], True)}. West is the most common ({ST['V']} stones), then north ({ST['N']}), east ({ST['Ö']}) and south ({ST['S']}); {pc(DESC['andel_soder'])} percent face south, south-east or south-west. Towards the farm: mean cos {H3['medel_cos']:.2f} against {H3['vantat']:.2f}, {pfmt(H3['p'], True)}. The bridge and road stones ({H4['n_bro']} with a road) are not turned towards the road more than other stones: {pfmt(H4['p'], True)}. None of these holds.

**5.3 The sensitivity analyses.** All hold:

{rung_en('halva_A', 'Half A')}
{rung_en('halva_B', 'Half B')}
- Without one province at a time: without Uppland ({LO['U']['n']} stones left, half, so only the direction is required) mean cos {LO['U']['medel_cos']:.2f}, {pfmt(LO['U']['p'], True)}; without Södermanland ({LO['Sö']['n']}) {LO['Sö']['medel_cos']:.2f}, {pfmt(LO['Sö']['p'], True)}; without Östergötland ({LO['Ög']['n']}) {LO['Ög']['medel_cos']:.2f}, {pfmt(LO['Ög']['p'], True)}.
{rung_en('socken', f"The parish as the unit, {TR['n_parishes']} parishes")}
{rung_en('en_per_ristare', f"One stone per secure carver, {TR['n_carvers']} carvers")}
{rung_en('utan_aterresta', f"Without re-erected stones, {TR['n_reerected']} removed")}
{rung_en('utan_flyttade_runor', f"Without stones Runor gives as moved, {TR['n_moved_runor']} removed")}
- With today's rule for moved stones none of the {H2['n']} counts as moved; the result is the same as the main test.
{rung_en('bara_text', f"Only roads from the register text, {pc(RU['bara_text']['andel_inom_45'])} percent within 45 degrees")}
{rung_en('bara_registrerad', f"Only registered routes and road markers, {pc(RU['bara_registrerad']['andel_inom_45'])} percent within 45 degrees")}

The addendum plan's word list for re-erected stones hits {TR['n_reerected_alla_219']} of all {R['n']} stones; the check after the main run, with a wider word list, hit 58. Both give the same result.

## 6. Discussion

**What the finding says.** Those who raised the runestones turned the text towards the road. It holds in the whole material, in each half, without Uppland, parish by parish and with one stone per carver, so it does not depend on a few places or workshops. It also holds without the stones that have been re-erected, which could otherwise have been turned towards today's road. That the directions are otherwise spread evenly over the compass and do not follow the farm shows that it was the road, not the sun or the home, that decided how the stone was turned.

**Against earlier research.** The result gives a measure to the idea that the stones by the roads were raised to be seen (Bollaert 2016) and to McLeod's (2014) objection that the roads have been underrated. It does not contradict that many stones were raised at grave fields (Klos 2009): a stone can stand at a grave field and turn its text towards the road past it.

**Weaknesses, in order of weight.**

1. **The road is often today's road.** The register text gives the road at the time of the survey. With only registered older routes and road markers the association is weaker ({pc(RU['bara_registrerad']['andel_inom_45'])} percent within 45 degrees, {pfmt(RU['bara_registrerad']['p'], True)}) but goes the same way. Where a later road follows the old line both measure the same thing; where it does not, the association becomes weaker, not stronger.
2. **The selection.** Only {R['n']} stones have a direction in the register, and we do not know what decided which stones received such a statement.
3. **Re-erections.** The word search does not catch every stone that has been re-erected. The result is, however, stronger without the stones it finds, not weaker.
4. **The resolution.** The directions are given in sixteen compass points, that is in steps of 22.5 degrees.

**What would overturn the finding.** If the association disappeared when the roads were measured on the oldest land-survey maps, or if a new survey of more stones' directions gave an even distribution relative to the road.

## 7. Conclusion

The runestones turned their text towards the road: half of the inscriptions face within 45 degrees of the road, against a quarter if the direction were random, and the association withstands every sensitivity analysis. The carvers wrote for those who passed by. The next step is to measure the roads on the maps of the seventeenth and eighteenth centuries.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The analysis plans: `analysplaner/2026-10-29-ristningens-riktning.md` and `analysplaner/2026-10-31-riktning-trappan.md`, with their checksums in the `.sha256` files beside them.
- The analysis: `utdata/riktning/analys.py` (results `riktning.json`, the stones in `stenar.csv`); the sensitivity analyses `utdata/riktning/trappa.py` (`trappan.json`).
- The register: `data/raa/kmr_runstenar.json`, `data/raa/lamningar.csv` and `data/raa/lamningar_extra/`.
- The report is built by `utdata/blogg/build/build_rapport_riktning.py`, which reads every number from the result files and stops if anything disagrees.

## References

- Bollaert, J. 2016. *Runstenar längs vägen. En undersökning av samband mellan runstenarnas placering och utformning*. Master's thesis. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, pp. 137 ff.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Mardia, K. V. & Jupp, P. E. 2000. *Directional Statistics*. Chichester: Wiley.
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25. doi:10.3721/037.006.2503
- Swedish National Heritage Board. The register of ancient monuments (Kulturmiljöregistret), via K-samsök. Retrieved October 2026.
- Swedish National Heritage Board. 2020. *Runor*. Runic inscriptions in Sweden, database.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholm University.

:::box The essentials
- The runestones turned their text towards the road, not towards the sun and not towards the farm.
- The carvers wrote for those who passed by: the stone was a message to travellers, not only a memorial by the home.
- It withstands every check we have, but the road in the register is often today's road, so the next test is the old maps.
:::
"""

JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert "I klartext" in body and "In plain words" in body_en  # mallen version 4
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion 1, 2026-10-31. Tidslinje: ")

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_riktning.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body.split("## Data")[0].split()), "före Data och kod;", len(body_en.split()), "words")

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
                 "topic": "Rapport|riktning", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
