"""Lägger rutan "Det viktigaste i korthet" sist i varje publicerad artikel (Viktors önskan 2026-10-18: en
sammanfattning i klartext för läsare som inte hänger med i alla siffror). Publicerade artiklar ändras bara så
här – direkt i Firestore med den levande texten som grund, aldrig genom att bygga om – så att admin-ändringar
bevaras. Rutan läggs före "## Se själv"/"## Källor" (sv) respektive "## See for yourself"/"## Sources" (en),
annars sist; artiklar som redan har rutan hoppas över, och den personliga artikeln (korpen) får ingen. En FORE-kopia sparas per artikel.
    ../../../.venv/bin/python lagg_till_korthet.py --write
"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

B = lambda *rader: ":::box Det viktigaste i korthet\n" + "\n".join("- " + r for r in rader) + "\n:::"
E = lambda *rows: ":::box The essentials in brief\n" + "\n".join("- " + r for r in rows) + "\n:::"

KORTHET = {
 "reste-sjalv-eller-lat-resa": (B(
   "Orden på runstenarna höll sig hemma: Västergötland *reste* sina stenar med det enkla verbet, Uppland *lät resa* – en antydan om beställare och utförare – och Södermanland satte sina märken *at*, inte *æftiR*, de döda.",
   "Skillnaderna står kvar också när vi räknar bort tid, textlängd och enskilda ristare, och de håller i båda halvorna av materialet. Det är lokala traditioner, inte slump.",
   "Formelboken var inte heller evig: under 1000-talet byter stenarna språkdräkt, och i själva orden syns hur beställandet och ristaryrket växer fram – *letu* och *risti* tar plats när *gærði* dör ut.",
   "Varför orden skiljer sig – dialekt i talet, verkstädernas vanor eller beställarnas smak – kan siffrorna inte avgöra. Men gränserna de ritar är verkliga, och stavningen ritar samma gränser i en helt oberoende mätning."),
  E("The words on the runestones stayed home: Västergötland *raised* its stones with the simple verb, Uppland *had them raised* – a hint of commissioner and craftsman – and Södermanland set its marks *at*, not *æftiR*, the dead.",
    "The differences remain when we account for time, text length and individual carvers, and they hold in both halves of the material. These are local traditions, not chance.",
    "Nor was the book of formulas eternal: across the eleventh century the stones change their wording, and in the words themselves one can watch commissioning and the carver's trade emerge – *letu* and *risti* take over as *gærði* dies out.",
    "Why the words differ – dialect, workshop habit or the commissioners' taste – the numbers cannot settle. But the boundaries they draw are real, and the spelling draws the same boundaries in a fully independent measurement.")),
 "runorna-som-fattas": (B(
   "Vi bygger en modell som läser runstenarnas texter och föreslår ord för förlorade runor – utan att någonsin ha sett tolkningen av den sten den läser.",
   "Den viktigaste siffran är inte hur ofta modellen har rätt, utan att den vet när den är osäker: när den säger minst 95 procent stämmer ordet nästan alltid, och det har prövats i ett i förväg registrerat blindtest.",
   "På de svåraste luckorna – där runorna verkligen gått förlorade men svaret är känt från äldre avbildningar – väljer den rätt ord i ungefär sju fall av tio. Det räcker för att vara en verklig hjälp vid skadade stenar, men inte för att ersätta runologens omdöme – och det är så siffrorna ska läsas.",
   "Spår i 3D-skanningarna lyfter läsningen ytterligare, och allt visas öppet i appen: förslag, procent och alternativ. Modellen är ett verktyg som redovisar sin egen osäkerhet, inte ett orakel."),
  E("We are building a model that reads the runestone texts and proposes words for lost runes – without ever having seen the interpretation of the stone it reads.",
    "The most important figure is not how often the model is right, but that it knows when it is unsure: when it claims at least 95 per cent, the word is almost always right, tested in a pre-registered blind test.",
    "On the hardest gaps – where the runes are truly lost but the answer is known from older drawings – it picks the right word in about seven cases out of ten. That is enough to be a real help with damaged stones, but not to replace the runologist's judgement – and that is how the figures should be read.",
    "Traces in the 3D scans lift the reading further, and everything is shown openly in the app: proposals, percentages and alternatives. The model is a tool that declares its own uncertainty, not an oracle.")),
 "stilgruppernas-morkertal": (B(
   "En tredjedel av Sveriges runstenar kan inte stildateras – och de är inte ett slumpmässigt urval. Mörkertalet har ett mönster.",
   "Hela, välbevarade stenar utan stilgrupp signeras lika sällan som stenarna i den enklaste stilen, RAK. Det tyder på att den odaterade massan domineras av just de enkla stenarna – inte av skadade exemplar av alla sorter.",
   "Slutsatser som bara bygger på stildaterade stenar lutar sig därmed mot de påkostade och välbevarade, och kan överskatta hur vanligt det ornamentala var.",
   "Den billigaste boten är dokumentation: många stenar saknar stilgrupp för att ingen har bedömt dem, inte för att ornamentiken är borta."),
  E("A third of Sweden's runestones cannot be style-dated – and they are not a random sample. The dark figure has a pattern.",
    "Whole, well-preserved stones without a style group are signed as rarely as the stones in the plainest style, RAK. This suggests the undated mass is dominated by the plain stones – not by damaged specimens of every kind.",
    "Conclusions built only on style-dated stones therefore lean on the ornate and well-preserved, and may overstate how common the ornamental was.",
    "The cheapest remedy is documentation: many stones lack a style group because no one has assessed them, not because the ornament is gone.")),
 "hur-spraklik-ar-en-runfoljd": (B(
   "Många runföljder har aldrig kunnat läsas. Vi mäter hur språklika de är: en modell tränad på läsbara inskrifter får säga hur väl varje oläst följd beter sig som runsvenska.",
   "Metoden är prövad åt båda hållen – den känner igen riktigt språk, och den avslöjar chiffer och teckenrader som inte är språk.",
   "De flesta olästa följder beter sig som språk: orden finns där, vi har bara inte knäckt dem än. Några få är i stället systematisk lek med runor, som þistill-mistill-raderna.",
   "Resultatet är en prioriteringslista för forskningen: vilka olästa stenar som lönar mödan, och vilka som sannolikt aldrig var meningar."),
  E("Many rune sequences have never been read. We measure how language-like they are: a model trained on legible inscriptions judges how well each unread sequence behaves as runic Swedish.",
    "The method is tested in both directions – it recognises real language, and it exposes ciphers and rows of signs that are not language.",
    "Most unread sequences behave like language: the words are there, we just have not cracked them yet. A few are instead systematic play with runes, like the þistill-mistill rows.",
    "The result is a priority list for research: which unread stones are worth the effort, and which probably never were sentences.")),
 "undantaget-vid-randers": (B(
   "Danska runstenar ber nästan aldrig för den dödes själ – utom i en trakt kring Randers på Jylland, där flera stenar gör det.",
   "En enda trakt räcker inte för statistisk säkerhet, och det säger vi rakt ut: det här är en fallstudie, inte ett bevisat mönster.",
   "Men undantaget pekar på något att pröva: en lokal kristen miljö som tog till bönen tidigare än resten av Danmark.",
   "Så arbetar vi: även det som inte når signifikans kan bli en skarp hypotes för den som har mer material."),
  E("Danish runestones almost never pray for the soul of the dead – except in one district around Randers in Jutland, where several stones do.",
    "A single district is not enough for statistical certainty, and we say so plainly: this is a case study, not a proven pattern.",
    "But the exception points to something testable: a local Christian milieu that took up the prayer earlier than the rest of Denmark.",
    "This is how we work: even what falls short of significance can become a sharp hypothesis for someone with more material.")),
 "den-som-bryter-denna-sten": (B(
   "Somliga runstenar hotar: den som bryter stenen ska bli en räte, en utstött. Vi följde skyddsformlerna över tusen år.",
   "Hoten och förbannelserna vaktar framför allt själva monumenten – stenen, bron, minnesmärket – och de är vanligare söderut, medan norr hellre ber för själen.",
   "Mönstret söder–norr är antydande, inte bevisat; det säger vi tydligt.",
   "Det magiska språket försvann inte med kristendomen – det bytte form, från förbannelse till bön."),
  E("Some runestones threaten: whoever breaks this stone shall become an outcast. We followed the protection formulas across a thousand years.",
    "The threats and curses guard above all the monuments themselves – the stone, the bridge, the memorial – and they are more common in the south, while the north prefers to pray for the soul.",
    "The south–north pattern is suggestive, not proven; we say so clearly.",
    "The magical language did not vanish with Christianity – it changed form, from curse to prayer.")),
 "dottrarna-som-runstenarna-glomde": (B(
   "Runstenarna restes till minne av män: döttrar, systrar och mödrar är nästan osynliga bland de ihågkomna.",
   "Men mönstret har sprickor som håller för statistisk prövning: i Västergötland reser fäder stenar efter döttrar oftare än någon annanstans, och i Svealand är mödrarna ovanligt synliga.",
   "Sprickorna följer landskapen, inte slumpen – de håller i båda halvorna av materialet.",
   "Vår tolkning att pröva: där arvsrätten gav kvinnan en plats, fick hon också en sten."),
  E("The runestones were raised in memory of men: daughters, sisters and mothers are nearly invisible among the remembered.",
    "But the pattern has cracks that withstand statistical testing: in Västergötland fathers raise stones after daughters more often than anywhere else, and in Svealand the mothers are unusually visible.",
    "The cracks follow the provinces, not chance – they hold in both halves of the material.",
    "Our interpretation to test: where inheritance law gave the woman a place, she also got a stone.")),
 "hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna": (B(
   "Kvinnor är med och reser var fjärde runsten där resaren går att läsa – men bara tre procent av stenarna är resta efter en kvinna. Kvinnan syns som resare, inte som ihågkommen.",
   "Den gamla tanken att kvinnorna var kristendomens förtrupp får inget stöd: deras stenar har varken fler kors eller fler böner än andra stenar från samma tid och trakt.",
   "När en kvinna reser ensam är det nästan alltid efter make eller son – hon står i mannens ställe, som änka eller mor.",
   "Vår hypotes att pröva: det var arvet och släktens ordning, inte den nya tron, som gav kvinnorna en plats på stenarna."),
  E("Women take part in raising every fourth runestone where the raiser can be read – but only three per cent of the stones are raised in memory of a woman. The woman appears as raiser, not as remembered.",
    "The old idea that women were Christianity's vanguard finds no support: their stones carry neither more crosses nor more prayers than other stones of the same time and district.",
    "When a woman raises a stone alone, it is almost always after a husband or a son – she stands in the man's place, as widow or mother.",
    "Our hypothesis to test: it was inheritance and the order of the family, not the new faith, that gave women a place on the stones.")),
 "erik-skrev-r-och-bygden-skrev-efter": (B(
   "Kring Enköping skrivs det gamla r-ljudet ᛦ med vanligt r på sex stenar av tio – fem gånger så ofta som i resten av landet.",
   "Spåret leder till ristaren Erik, som skrev r på varenda sten där ordet går att läsa – också långt hemifrån. Uttalet i bygden kan alltså inte vara hela förklaringen.",
   "Efter Erik fortsatte bygdens ristare att skriva så, medan ristare utifrån höll fast vid sina egna vanor var de än högg.",
   "Vår hypotes att pröva: stavningen var en skrivtradition som ärvdes mellan ristare, inte ett talspråk – en påminnelse om att runstenarnas språk är skrivarnas, inte direkt bygdens."),
  E("Around Enköping the old r-sound ᛦ is written with a plain r on six stones in ten – five times as often as in the rest of the country.",
    "The trail leads to the carver Erik, who wrote r on every stone where the word can be read – far from home too. The local pronunciation cannot be the whole explanation.",
    "After Erik the district's carvers kept writing that way, while carvers from outside kept their own habits wherever they cut.",
    "Our hypothesis to test: the spelling was a writing tradition inherited between carvers, not speech – a reminder that the runestones' language is the writers', not directly the district's.")),
 "tor-svarade-korset-och-tystnade": (B(
   "Av 2 321 svenska runstenar nämner bara sex Tor eller bär hans hammare – mot över tusen med kors eller bön.",
   "De sex är inte rester från en äldre, hednisk tid i avlägsna trakter: de ristades medan korset bredde ut sig, mitt bland kristna stenar, och flera härmar korsets plats och bönens plats i texten.",
   "Varken de förlorade stenarna eller de som murades in i kyrkorna tyder på att det har funnits många fler.",
   "Vår hypotes att pröva: den gamla tron skrev inte sina gudar på sten – Tor kom till runstenarna först som ett svar på korset."),
  E("Of 2,321 Swedish runestones, only six name Thor or carry his hammer – against more than a thousand with a cross or a prayer.",
    "The six are not remnants of an older, pagan age in remote districts: they were carved while the cross was spreading, amid Christian stones, and several mimic the cross's place and the prayer's place in the text.",
    "Neither the lost stones nor those built into the churches suggest there were ever many more.",
    "Our hypothesis to test: the old faith did not write its gods in stone – Thor came to the runestones only as an answer to the cross.")),
 "2026-10-ristarsignatur-breder-ut-sig": (B(
   "På de tidigaste runstenarna nämns ristaren nästan aldrig; på de sista står hans namn på mer än var tredje sten, nästan alltid allra sist – efter Gud.",
   "Det sista ordet i texterna byter ägare under 1000-talet: omkring 1035 var det oftast en bön, femtio år senare oftast ristarens namn.",
   "Signaturen trängde inte undan bönen, och den följde inte efterfrågan – den följde ristarna: somliga signerade var tredje sten, andra nästan aldrig.",
   "Vår hypotes att pröva: signaturen spreds som en sed från mästare till lärjunge – ett tidigt exempel på hur hantverkare blev upphovsmän."),
  E("On the earliest runestones the carver is almost never named; on the last ones his name stands on more than every third stone, almost always last – after God.",
    "The final word of the texts changes owner during the eleventh century: around 1035 it was usually a prayer, fifty years later usually the carver's name.",
    "The signature did not displace the prayer, and it did not follow demand – it followed the carvers: some signed every third stone, others almost never.",
    "Our hypothesis to test: the signature spread as a custom from master to apprentice – an early example of craftsmen becoming authors.")),
 "2026-10-bonen-tystnade-korset-stod-kvar": (B(
   "Omkring 1035 bad mer än var tredje daterad runsten Gud om hjälp för den dödes själ. Femtio år senare gjorde nästan ingen det.",
   "Det var inte tron som försvann: korset står kvar på en stor del av de sena stenarna. Det var just bönen som tystnade.",
   "Samtidigt tog ristarens namn bönens plats sist i texterna.",
   "Vår hypotes att pröva: bönen försvann från stenarna när förbönen för de döda blev kyrkans sak – minnet stannade på stenen, omsorgen om själen flyttade in i kyrkan."),
  E("Around 1035 more than every third dated runestone asked God to help the soul of the dead. Fifty years later almost none did.",
    "It was not the faith that vanished: the cross remains on a large share of the late stones. It was precisely the prayer that fell silent.",
    "At the same time the carver's name took the prayer's place at the end of the texts.",
    "Our hypothesis to test: the prayer left the stones when intercession for the dead became the church's business – the memory stayed on the stone, the care of the soul moved into the church.")),
 "vastgotarna-skrev-som-danskarna": (B(
   "Västergötlands runstenar skriver som de danska: samma ordval i minnesmärket, samma titlar, samma stavningsvanor – fast de står i det svenska riket.",
   "Mönstret håller i båda halvorna av materialet, och vid riksgränsen händer något talande: där tystnar stenarna nästan helt, ett bälte med få resta stenar.",
   "Seden att resa stenar tycks alltså ha vandrat med människor och förbindelser, inte med riken – kulturgränsen gick inte där den politiska gick.",
   "Sedan artikeln skrevs har en oberoende mätning – vilka ord som alls står på stenarna – ritat samma gräns."),
  E("The runestones of Västergötland write like the Danish ones: the same wording in the memorial, the same titles, the same spelling habits – though they stand in the Swedish realm.",
    "The pattern holds in both halves of the material, and at the realm border something telling happens: the stones fall nearly silent, a belt with few raised stones.",
    "The custom of raising stones seems to have travelled with people and connections, not with realms – the cultural boundary did not run where the political one did.",
    "Since the article was written, an independent measurement – which words stand on the stones at all – has drawn the same boundary.")),
}

SV_FORE = ("\n## Se själv", "\n## Källor")
EN_FORE = ("\n## See for yourself", "\n## Sources")


def insert(body: str, box: str, anchors) -> str:
    for a in anchors:
        i = body.find(a)
        if i >= 0:
            return body[:i] + "\n" + box + "\n" + body[i:]
    return body.rstrip() + "\n\n" + box + "\n"


if __name__ == "__main__":
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    write = "--write" in sys.argv
    for p in blog._all():
        slug = p.get("slug")
        if not p.get("published") or slug not in KORTHET:
            continue
        if "viktigaste i korthet" in (p.get("body") or "").lower():
            print(f"{slug}: har redan rutan, hoppar över")
            continue
        sv, en = KORTHET[slug]
        body = insert(p["body"], sv, SV_FORE)
        body_en = insert(p.get("body_en") or "", en, EN_FORE) if p.get("body_en") else p.get("body_en")
        if write:
            json.dump({k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in p.items()},
                      open(os.path.join(ROOT, f"utdata/blogg/{slug}.FORE-KORTHET.json"), "w"),
                      ensure_ascii=False, indent=1, default=str)
            col.document(p["id"]).set({"body": body, "body_en": body_en, "updatedAt": now}, merge=True)
        print(f"{slug}: ruta tillagd{'' if write else ' (torrkörning)'}")
    saknas = [s for s in KORTHET if s not in {p.get('slug') for p in blog._all() if p.get('published')}]
    if saknas:
        print("VARNING – slug utan publicerad artikel:", saknas)
    if write:
        blog._forget()
