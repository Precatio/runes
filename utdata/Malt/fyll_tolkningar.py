"""Avskrift av Grønvik 1992 och Heltoft 2017 i tolkningar_ord.json, ord för ord mot Rundatas grupper.

Avskriften är gjord 2026-10-19 direkt ur originalen (kallor/litteratur/anf.txt = ANF 107, 1-34;
kallor/litteratur/heltoft2017.txt = Danske Studier 2017, 27-100), aldrig ur minnet. Sidhänvisning per
rad; obs förklarar var tolkningens orddelning avviker från Rundatas gruppindelning. Grønviks läsning
sammanfattas på ANF s. 20-21, Heltofts i sluttabellen Danske Studier s. 93-94.
"""
import os
_PROJ = str(__import__("pathlib").Path(__file__).resolve().parents[2])  # projektmappen, var den än ligger
import json

FIL = os.path.join(_PROJ, "utdata/Malt/tolkningar_ord.json")
d = json.load(open(FIL))

G = [
    ("sua", "svá", "s. 6 (§8.1)", "'så/sålunda'; orddelningen sua a i titul titul"),
    ("ai", "á í", "s. 6 (§8.1)", "två ord: 'har ... i (sig)' - svá á í titul titull"),
    ("titultitul", "titul titull", "s. 6 (§8.1); om lånordet s. 27-29 (§12)",
     "'så har inskriften en inskrift i sig' - inskriften inuti är futharken; titull av lat. titulus"),
    ("fuþorkhniastbmlR", "<runraden>", "s. 8-9 (§8.6-8.7)", "futharken som 'mächtige heilige Formel'"),
    ("huaR", "hverr", "s. 6 (§8.2)", "gammalt substantiviskt frågepronomen, jfr Rök och Eggja"),
    ("is", "es", "s. 6 (§8.2)", None),
    ("i", "í", "s. 6 (§8.2)", "adverbiellt: 'däri' (i futharken)"),
    ("alisti", "elzti", "s. 7 (§8.3)", "stödvokal i; svag form utan artikel - 'den äldste'"),
    ("osa", "ása", "s. 7 (§8.3)", "'av asarna (gudarna)'"),
    ("huaR", "hverr", "s. 7 (§8.4)", "frågan upprepas didaktiskt (§8.9, not 4 s. 11)"),
    ("is", "es", "s. 7 (§8.4)",
     "Grønvik läser därtill ett delvis skadat i (B1:23): 'hverr es í?'; Rundata har inget ord här (not 2a, s. 7)"),
    ("uifrþuR", "Véfrøðr", "s. 7-8 (§8.4-8.5)",
     "läses uifr<i>þuR, ristaren antas ha glömt i-runan; gudaheite 'vé-väktaren' = Tor"),
    ("karþi", "gerði", "s. 10 (§9.1)", "'gjorde, ställde till'"),
    ("afr", "afr", "s. 10, 12-14 (§9.1, §9.3-9.6)", "'öl/gravöl': gerði afr 'ställde till gravöl'"),
    ("aft", "at (eptir)", "s. 10 (§9.1)", "'efter'"),
    ("asini", "*æsni-", "s. 10-11 (§9.1)", "'älskade' (jfr Eikeland); stödvokal; förled i *æsni-fǫðr"),
    ("fauþr", "-fǫðr", "s. 10-11 (§9.1-9.2)", "'far'; formen bara som efterled i sammansättningar"),
    ("kul", "Kol-", "s. 10 (§9.1)", "förled i namnet Kolfinnr, satsens subjekt, placerat sist"),
    ("finR", "-finnr", "s. 10 (§9.1)", "efterled i Kolfinnr"),
    ("fal(s)", "falsk", "s. 14-15 (§9.8)", "reflexivt fela: 'det framsades/överläts'; sandhi -sk > -s"),
    ("taitirunoR", "teiti-rúnar", "s. 14 (§9.7)", "'glädjerunor' - ord som väcker glädje i laget"),
    ("u", "ok", "s. 14 (§9.7)", "Grønvik delar runorna uk 'och' där Rundata har u + (a)iuinrunoR"),
    ("(a)iuinrunoR", "œvin-rúnar", "s. 14 (§9.7)", "'evig-runor', jfr œvinrúnar ok aldrrúnar i Rigsþula 43"),
    ("sulialta", "sýli alda", "s. 16 (§10.1); s. 19-20 (§10.4)",
     "sýli konjunktiv av sýla 'bli iskall' + alda 'av människor' - den heliga rysningen"),
    ("huaR", "hverr", "s. 16 (§10.1)", "'alda hverr' = 'var man'"),
    ("?", None, "s. 16 (§10.1); s. 20-21 (§10.5)",
     "inget språkligt ord: gudasymbol ('potenserad t-runa'), samtidigt skiljetecken; jfr Kylver och brakteat DR br. 61"),
    ("utu", "utu", "s. 17-18 (§10.2)",
     "interjektion för köldrysning, jfr utututu i Rǫgnvaldr jarls lausavísa (Orkneyinga saga kap. 85)"),
    ("tuuut", "tu-u-ut", "s. 17-18 (§10.2)", "interjektionens fortsättning"),
    ("bilikikR", "belli gengr", "s. 18 (§10.3.1, §10.3.3)",
     "belli dativ 'med djärvhet' + gengr 'går' (nasalen utelämnad i skrift)"),
    ("tuR", "tor-", "s. 18 (§10.3.2)", "förled i tor-ræki (jfr torfenginn)"),
    ("ra(k)(i)", "-ræki", "s. 18 (§10.3.2)", "tor-ræki 'den som är svår att driva bort' = Tor"),
    ("(t)(u)(l)i", "at óli", "s. 18-19 (§10.3.4-10.3.5)",
     "t = at utan vokal (Rök-parallell); ól 'skadegörare (jätte)' - 'går mot jätten', Hrungnir-myten"),
]

H = [
    ("sua", "swā", "s. 93-94 (sluttabellen); jfr s. 64", "'således:' - inleder uddrivelseformeln"),
    ("ai", "æi", "s. 63-65 (§6.4); tabell s. 94", "negationen 'icke', skild från ē 'alltid'"),
    ("titultitul", "tī duldi dul", "s. 65-67 (§6.5); tabell s. 94",
     "reduktionsläsning: tī dat. av tīr 'guden' + duldi 'narrade' + dul 'bländverk' - 'bedrägeriet narrade inte guden'"),
    ("fuþorkhniastbmlR", "<runraden>", "tabell s. 94", "futharken som värnetext"),
    ("huaR", "hwar", "s. 76-83 (§8.2); tabell s. 93",
     "första raden är avsiktligt flertydiga 'drilleruner': hwar es ī / es ē / ē sē / ē sēi / ī sēi"),
    ("is", "es", "tabell s. 93", "ingår i flertydigheten (es / ē s-)"),
    ("i", "ī", "tabell s. 93", "ingår i flertydigheten (ī / ē / sē / sēi)"),
    ("alisti", "ælisti", "tabell s. 93", "'den urgamle'"),
    ("osa", "ą̄sa", "tabell s. 93", "'asen' - 'den urgamle asen'"),
    ("huaR", "hwar", "tabell s. 93", None),
    ("is", "es", "tabell s. 93",
     "andra frågan likaså flertydig: hwar es ī? / hwar ī sē?; Heltoft supplerar [i]: huaris[i]"),
    ("uifrþuR", "Vīfriðr", "s. 46 (§5.1); tabell s. 93-94", "personnamn: resaren (vīfriður)"),
    ("karþi", "gærði", "s. 46-49 (§5.2); tabell s. 93-94", "'uppförde' (kumlet) eller 'fastställde' (boten)"),
    ("afr", "afra", "s. 45-56 (§5); tabell s. 93-94",
     "adjektivet afarr 'framstående' (ack.), bevarat arkaiskt ord; hör till fǫðr"),
    ("aft", "aft", "s. 45-56 (§5); tabell s. 93-94", "'efter' resp. 'som bot för' i guld-läsningen"),
    ("asini", "Æsi Nef-", "s. 49-56 (§5.4-5.6); tabell s. 93-94",
     "delas asi + ni: Æsi = namnet, ni läses som början av binamnet Nef - fadern 'Æsir Nef'"),
    ("fauþr", "fǫðr", "s. 51-55 (§5.5); tabell s. 93-94", "arkaisk ackusativ 'fader'"),
    ("kul", "gull / kuml", "tabell s. 93-94",
     "två likvärdiga läsningar: 'guld' (bot för fadern) eller 'kuml' (monumentet); abstractet ger båda"),
    ("finR", "Finnr", "tabell s. 94", "dvärgnamn: 'dvärgen Finn gömde sig'"),
    ("fal(s)", "falṣ", "s. 67-70 (§7.1-7.2); tabell s. 94", "'gömde sig'; generaliserad medialform på -s"),
    ("taitirunoR", "tæitirūnąr", "s. 70-72 (§7.3)", "'morskabs-/drilleruner' - retas med dvärgen"),
    ("u", "ȳ", "s. 84-87 (§9.1-9.2); tabell s. 94", "'idegran (taks)' - värneträdet som drivs in"),
    ("(a)iuinrunoR", "æiwinrūnąr", "s. 70-72 (§7.3)", "'evighets-/värneruner'"),
    ("sulialta", "sōl ī ælta", "s. 72-73 (§7.4); tabell s. 94",
     "reduktionsläsning: 'driver solen in (häri)' - solen dödar dvärgen"),
    ("huaR", "hwar", "tabell s. 94", "'den som' - binds samman med raden 5:9-23"),
    ("?", "tīr tīr tīr", "tabell s. 94",
     "symbolen läst som möjlig tredubbel gudaåkallan; tīr 'gud' i singular bevarat"),
    ("utu", "ōttu", "s. 86-87 (§9.2); tabell s. 94", "'tidigt om morgonen (i ottan)'"),
    ("tuuut", "dȳ ȳ ȳt", "s. 86-87 (§9.2); tabell s. 94",
     "reduktionsläsning: dȳja 'slå' + ȳ 'idegran' + ȳta 'driva ut' - 'slå med idegran, driv ut (honom)'"),
    ("bilikikR", "Billingi ekr", "s. 59-60 (§6.1); tabell s. 94",
     "dvärgen Billing (dat.) + ekr 'driver ut' - 'driver ut dvärgen Billing'"),
    ("tuR", "dweragi (början)", "s. 60-62 (§6.2)",
     "turraki läses som ett ord: dweragi 'dvärgen' (dat.) enligt reduktionsprincipen; täcker tuR + ra(k)(i)"),
    ("ra(k)(i)", "(ingår i dweragi)", "s. 60-62 (§6.2)", None),
    ("(t)(u)(l)i", "dyli", "s. 62-63 (§6.3); tabell s. 94", "'skall utsäga en förnekelse'"),
]

def fyll(nyckel, rader, oversattning, status):
    post = d["lasningar"][nyckel]
    assert [r[0] for r in rader] == d["grupper"], f"{nyckel}: gruppordningen stämmer inte"
    post["ord"] = [{k: v for k, v in
                    (("runor", r[0]), ("ord", r[1]), ("sida", r[2]), ("obs", r[3])) if v is not None}
                   for r in rader]
    post["oversattning"] = oversattning
    post["status"] = status

fyll("G", G,
     "Så har inskriften en inskrift i sig: futharken. Vem är däri? Den äldste av asarna. Vem är däri? "
     "Véfrøðr (= Tor, vé-väktaren). Kolfinn ställde till gravöl efter sin älskade far; det framsades "
     "glädjerunor och evig-runor. Må var man bli iskall (i helig bävan)! utu tu-u-ut! Med djärvhet går "
     "den som är svår att driva bort (Tor) mot skadegöraren (jätten).",
     "avskriven ur originalet 2026-10-19 (ANF 107, s. 1-34); samlad läsning s. 20-21")
fyll("H", H,
     "Minnesformeln (två likvärdiga läsningar): Vifred uppförde kumlet / fastställde guld som bot efter "
     "sin framstående fader Æsir Nef. Dvärgen Finn gömde sig. Drillerunor (driver) idegran (in), "
     "värnerunor driver solen in (häri). Den som ... (tīr tīr tīr - gudaåkallan?) Tidigt i ottan: slå "
     "med idegran, driv ut (honom), driver ut dvärgen Billing, skall utsäga förnekelsen: således: "
     "bländverket narrade icke guden. (Runraden som värnetext.)",
     "avskriven ur originalet 2026-10-19 (Danske Studier 2017, s. 27-100); sluttabell s. 93-94")

json.dump(d, open(FIL, "w"), ensure_ascii=False, indent=1)
print("G:", sum(1 for o in d["lasningar"]["G"]["ord"] if o.get("ord")), "ord ifyllda;",
      "H:", sum(1 for o in d["lasningar"]["H"]["ord"] if o.get("ord")), "ord ifyllda")
