"""Korpus nr 2 (mars 2027, *Det vi inte ser*): texter som är klara före bygget. Samma fält som nr 1 i bygg_tidskrift.py
(METOD = mflik/mrubrik/mtext, APP = appsidans dict), så att bygget kan läsa dem direkt när det blir nummerstyrt.

Siffrorna är kontrollerade 2026-11-13 mot:
- data/textmodel_candidates.json (textmodel-19): 112 öppna luckor på runstenar, 17 med förslag ≥ 50 %, 7 ≥ 80 %;
- utdata/blindtest/resultat.json (låst protokoll, 2026-10-17): 16 av 21 rätt, alla 13 förslag ≥ 95 % höll;
"""

NUMMER = dict(nr=2, sv="Nr 2 · Mars 2027", en="No. 2 · March 2027", tema_sv="Det vi inte ser", tema_en="What we cannot see")

METOD = {
    "sv": dict(
        mflik="Metodhörnan", mrubrik="Vad är fångst–återfångst?",
        mtext="Hur många fiskar finns det i en sjö? Fånga hundra, märk dem och släpp tillbaka dem. Fånga sedan hundra till. "
              "Är tio av dem märkta, är de märkta ungefär en tiondel av alla fiskar, och sjön rymmer omkring tusen. Samma "
              "räkning går att göra med runstenar. De märkta är stenar som var kända men hade försvunnit när utgåvan skrevs; "
              "de återfångade är de som sedan dök upp igen. Hur stor del av de försvunna som har återfunnits säger något om "
              "hur många stenar som aldrig har setts av någon. Metoden vilar på antaganden: att varje sten har samma chans "
              "att hittas, och att ingen letar särskilt efter just de kända. Därför redovisar vi svaret som en "
              "storleksordning med intervall – inte som ett facit."),
    "en": dict(
        mflik="Method corner", mrubrik="What is capture–recapture?",
        mtext="How many fish are there in a lake? Catch a hundred, mark them and let them go. Then catch another hundred. "
              "If ten of them are marked, the marked fish are about a tenth of all the fish, and the lake holds about a "
              "thousand. The same sum works for runestones. The marked ones are stones that were known but had disappeared "
              "when the corpus edition was written; the recaptured ones are those that later turned up again. The share of "
              "the lost stones that has been found again tells us something about how many stones no one has ever seen. "
              "The method rests on assumptions: that every stone has the same chance of being found, and that nobody "
              "searches specially for the known ones. So we report the answer as an order of magnitude with an interval – "
              "not as a final count."),
}

APP = {
    "sv": dict(
        flik="I appen", rubrik="Luckor i texten: vad stod där stenen är skadad?",
        deck="Många runstenar har luckor där stenen är skadad eller bortslagen. Sannolikhetsmodellen läser det som finns kvar "
             "runt luckan och föreslår vilket ord som saknas – med en sannolikhet som är prövad på luckor där svaret redan är känt.",
        gor=["Modellen har lärt sig hur runstenarnas texter brukar se ut: formlerna, namnen och hur orden stavas i olika bygder. "
             "För varje lucka räknar den ut vilka ord som passar mellan det som står före och efter, och hur många runor som "
             "får plats.",
             "Sannolikheten är kalibrerad: den är prövad på luckor som Rundata redan har fyllt i, där svaret är känt. I ett "
             "blindtest enligt en låst plan, på stenar som modellen aldrig hade prövats på, fick den rätt ord i 16 av 21 "
             "luckor, och alla 13 förslag med minst 95 procents sannolikhet höll."],
        steg=["Öppna Forskningsluckor i appen och välj fliken Luckor i texten.",
              "Sortera på sannolikheten. Förslag med minst 80 procent räknas som säkra, 50–80 procent som möjliga.",
              "Öppna stenen och jämför förslaget med foto, skanning och utgåvans kommentar i panelen Vad skannern ser i luckan."],
        kan_inte="Modellen läser inte stenen – den räknar på texten runt luckan. Den känner bara ord som finns på andra "
                 "stenar, så ett ovanligt namn eller ett sällsynt släktord kan saknas bland förslagen. Av de 112 luckor på "
                 "runstenar som ingen har fyllt i ger den ett säkert förslag för 7. Förslagen är underlag att granska, inte fynd.",
        panel="Hur ofta modellen har rätt",
        rader=[("Blindtest, 21 luckor", [("Rätt ord", 76, True), ("Säkra förslag som höll", 100, False)]),
               ("De 112 öppna luckorna", [("Förslag minst 50 %", 15, True), ("Säkra, minst 80 %", 6, False)])],
        kalla="Källa: Vitkis sannolikhetsmodell (textmodel-19) på Samnordisk runtextdatabas, vikingatida svenska runstenar; "
              "blindtest enligt låst protokoll 2026-10-17.",
        fot="Vitki är fri programvara och körs på din egen dator: github.com/Precatio/runes. Metoden: METHODS.md, avsnitt 8 och 14.",
        kan_inte_rubrik="Vad den inte kan", steg_rubrik="Så gör du", gor_rubrik="Vad den gör",
        innehall=("I appen", "Luckor i texten"),
        bild="bilder/app_luckor_sv.jpg",  # SAKNAS: tas med Playwright mot den lokala appen (minnet runmatt-journal)
        bildtext="<b>Så ser det ut i appen:</b> Forskningsluckor, fliken Luckor i texten. Skärmbild: Vitki."),
    "en": dict(
        flik="In the app", rubrik="Gaps in the text: what stood where the stone is damaged?",
        deck="Many runestones have gaps where the stone is damaged or broken off. The probability model reads what is left "
             "around the gap and suggests which word is missing – with a probability tested on gaps where the answer is already known.",
        gor=["The model has learned what runestone texts usually look like: the formulas, the names and how words are spelled "
             "in different districts. For each gap it works out which words fit between what comes before and after, and "
             "how many runes there is room for.",
             "The probability is calibrated: it has been tested on gaps the runic database has already filled in, where the "
             "answer is known. In a blind test under a locked plan, on stones the model had never been tested on, it found "
             "the right word in 16 of 21 gaps, and all 13 suggestions with at least 95 per cent probability held."],
        steg=["Open Research gaps in the app and choose the tab Gaps in the text.",
              "Sort by probability. Suggestions of at least 80 per cent count as sure, 50–80 per cent as possible.",
              "Open the stone and compare the suggestion with photo, scan and the edition's commentary in the panel on what the scanner sees in the gap (Swedish only in the app)."],
        kan_inte="The model does not read the stone – it calculates from the text around the gap. It only knows words that occur "
                 "on other stones, so an unusual name or a rare kinship word may be missing from its suggestions. Of the 112 "
                 "gaps on runestones that no one has filled in, it gives a sure suggestion for 7. The suggestions are material "
                 "to examine, not findings.",
        panel="How often the model is right",
        rader=[("Blind test, 21 gaps", [("Right word", 76, True), ("Sure suggestions that held", 100, False)]),
               ("The 112 open gaps", [("Suggestion at least 50 %", 15, True), ("Sure, at least 80 %", 6, False)])],
        kalla="Source: Vitki's probability model (textmodel-19) on the Scandinavian Runic-text Database, Swedish Viking-age "
              "runestones; blind test under a locked protocol 2026-10-17.",
        fot="Vitki is free software and runs on your own computer: github.com/Precatio/runes. The method: METHODS.md, sections 8 and 14.",
        kan_inte_rubrik="What it cannot do", steg_rubrik="How to use it", gor_rubrik="What it does",
        innehall=("In the app", "Gaps in the text"),
        bild="bilder/app_luckor_en.jpg",
        bildtext="<b>What it looks like in the app:</b> Research gaps, the tab Gaps in the text. Screenshot: Vitki."),
}
