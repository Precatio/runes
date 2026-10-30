"""Handkodningen enligt analysplaner/2026-10-30-utvandrarna-och-hemmet.md, gjord 2026-10-30 efter att planen låstes
(5e0baa7), ur Rundatas normalisering och översättning. Skriver kodning.csv; analys.py räknar.
Kolumner: signum, plats_andra_sidan, slakt_bakat, slakt_bakat_nordisk, pris, namn (namn:ursprung; n = nordiskt,
g = gaeliskt, ? = osäkert; oläsliga <…>-namn utelämnas), anm."""
import csv
import os

N, G, U = "n", "g", "?"
ROWS = [
    # ---- Norge ---------------------------------------------------------------------------------------------------
    ("N 29", 0, 1, 1, 0, [("Finnr", N), ("Skopti", N), ("Váli", N)], "synir Vála"),
    ("N 59", 0, 0, 0, 0, [("Hróarr", N), ("Ôlvir", N)], ""),
    ("N 61", 0, 0, 0, 0, [("Jórunnr", N)], "Hringaríki och Ulfey är norska"),
    ("N 62", 1, 0, 0, 0, [("Engli", N), ("Þóraldr", N)], "Garðar"),
    ("N 63", 0, 1, 1, 0, [("Aun", N)], "synir Aunar"),
    ("N 64", 0, 0, 0, 0, [], ""),
    ("N 66", 0, 0, 0, 0, [("Gunnvôr", N), ("Ônundr", N)], ""),
    ("N 68", 0, 1, 1, 1, [("Gunnvôr", N), ("Þrýðríkr", N), ("Ástríðr", N)], "Þrýðríks dóttir; mær hônnurst"),
    ("N 84", 0, 1, 1, 0, [("Gási", N), ("Gunnarr", N)], "Gása synir"),
    ("N 162", 0, 1, 1, 0, [("Gnúpr", N), ("Þorleifr", N)], "sonr Þorleifs"),
    ("N 163", 0, 1, 1, 0, [("Arngeirr", N), ("Þjóðulfr", N), ("Guðmundr", N), ("Ôndóttr", N)], "Arngeirs synir"),
    ("N 180", 0, 0, 0, 0, [], ""),
    ("N 184", 1, 0, 0, 0, [("Arnsteinn", N), ("Bjórr", N), ("Knútr", N)], "England"),
    ("N 186", 0, 1, 1, 0, [("Þorlafr", N), ("Stáli", N), ("Ólafr", N), ("Erlendr", N)], "Stála sonr, Erlendsson"),
    ("N 208", 0, 0, 0, 0, [("Gunnarr", N)], ""),
    ("N 209", 0, 1, 1, 0, [("Þórir", N), ("Neriðr", N)], "Neriðs son"),
    ("N 211", 0, 0, 0, 0, [("Eyvindr", N), ("Gunnhvatr", N)], ""),
    ("N 213", 0, 1, 1, 0, [("Rannveig", N), ("Ôgmundr", N), ("Hreppir", N), ("Skógr", N)], "Hreppisson"),
    ("N 217", 0, 0, 0, 0, [], ""),
    ("N 222", 0, 0, 0, 0, [], ""),
    ("N 223", 0, 0, 0, 0, [("Gautr", N), ("Steinarr", N), ("Ulfríkr", N)], "ristaren sorgþungr – inte pris av den döde"),
    ("N 225", 0, 1, 1, 0, [("Þórir", N), ("Harðr", N), ("Ásgerðr", N), ("Gunnarr", N), ("Helgi", N)], "Harðarsonr, dóttur Gunnars"),
    ("N 228", 0, 0, 0, 0, [("Helgi", N), ("Ketill", N)], ""),
    ("N 237", 0, 0, 0, 0, [("Ónn", N), ("Ulfríkr", N)], ""),
    ("N 238", 0, 0, 0, 0, [("Ónn", N)], ""),
    ("N 239", 0, 0, 0, 0, [("Þorbjôrn", N)], "Danmark ligger i Norden"),
    ("N 244", 0, 0, 0, 1, [("Skarði", N), ("Bjalfi", N)], "harða góðan mann"),
    ("N 245", 0, 0, 0, 0, [("Þormóðr", N), ("Þróndr", N)], ""),
    ("N 251", 0, 1, 1, 0, [("Ketill", N), ("Jórunn", N), ("Úþyrmir", N)], "dóttur Úþyrmis"),
    ("N 252", 0, 0, 0, 0, [("Erlingr", N), ("Óleifr", N)], ""),
    ("N 259", 0, 0, 0, 0, [("Þormóðr", N), ("Þorgarðr", N), ("Gautr", N)], ""),
    ("N 260", 0, 0, 0, 0, [("Sveinki", N), ("Þróndr", N)], ""),
    ("N 271", 0, 0, 0, 0, [("Erlendr", N), ("Ôlvir", N)], ""),
    ("N 273", 0, 0, 0, 0, [("Þormóðr", N)], "far och son samma namn"),
    ("N 300", 0, 0, 0, 0, [], ""),
    ("N 413", 0, 1, 1, 0, [("Grímr", N), ("Bersi", N), ("Þór-", N), ("Ketill", N)], "Bersasonr, Ketilssonar"),
    ("N 417", 0, 0, 0, 0, [("Þórðr", N)], ""),
    ("N 449", 0, 0, 0, 0, [("Þórir", N), ("Hallvarðr", N), ("Ulfljótr", N)], "Nóregi är det egna landet"),
    ("N 453", 0, 0, 0, 0, [("Óttarr", N), ("Ôrn", N), ("Bjôrn", N)], ""),
    ("N 543", 0, 0, 0, 0, [("Atli", N), ("Steinn", N)], ""),
    ("N A13", 0, 0, 0, 0, [("Þórir", N), ("Ígull", N)], ""),
    ("N A23", 0, 0, 0, 0, [("Akli", N), ("Ulfr", N)], ""),
    ("N A222", 0, 0, 0, 0, [("Kolr", N), ("Þórir", N)], ""),
    # ---- väster ----------------------------------------------------------------------------------------------------
    ("Sh 3", 0, 0, 0, 0, [("Þorbjôrn", N)], ""),
    ("Sh 4", 0, 0, 0, 0, [], ""),
    ("Or 18", 0, 0, 0, 0, [("Þorfinnr", N)], ""),
    ("Sc 8", 0, 1, 1, 0, [("Þorgerðr", N), ("Steinarr", N)], "Steinars dóttur"),
    ("Sc 11", 0, 0, 0, 0, [("Ingulfr", N)], ""),
    ("Sc 14", 0, 1, 1, 0, [("Kali", N), ("Ôlvir", N), ("Fugl", N)], "Ôlvis sonr"),
    ("E 19", 0, 0, 0, 0, [("Maelmuire", G)], ""),
    ("IM AndreasVIII", 0, 1, 0, 0, [], "sonr <m-r--ns>, dóttur <uf-->: föräldrarnas namn oläsliga"),
    ("IM MM99", 0, 1, 1, 0, [("Ófeigr", N), ("Gautr", N), ("Bjôrn", N)], "sonr Bjarnar frá Kolli – Kollr ligger i väster"),
    ("IM MM101", 0, 1, 0, 0, [("Melbrigði", G), ("Aðakán", G), ("Gautr", N)], "sonr Aðakáns; Môn är det nya landet"),
    ("IM MM102", 0, 0, 0, 0, [], ""),
    ("IM MM106", 0, 1, 1, 0, [("Áleifr", N), ("Ljótulfr", N), ("Ulfr", N)], "Ljótulfs sonr"),
    ("IM MM112", 0, 1, 0, 0, [("Þorsteinn", N), ("Ófeigr", N), ("Krínán", G)], "son Krínáns"),
    ("IM MM113", 0, 0, 0, 0, [], ""),
    ("IM MM118", 0, 1, 0, 0, [("Druian", G), ("Dufgal", G), ("Aþmiul", G)], "sonr Dufgals"),
    ("IM MM123", 0, 0, 0, 0, [], ""),
    ("IM MM126", 0, 0, 0, 0, [("Grímr", N), ("Hróðmundr", N)], ""),
    ("IM MM127", 0, 0, 0, 0, [("Þor-", N)], ""),
    ("IM MM128", 0, 0, 0, 0, [("Þorvaldr", N)], "Torvalds kors (bilderna räknas inte)"),
    ("IM MM130", 0, 1, 0, 1, [("Mallymkun", G), ("Malmury", G), ("Dufgal", G), ("Aðísl", N)], "dóttur Dufgals; ordspråket"),
    ("IM MM131", 0, 0, 0, 0, [("Sandulfr", N), ("Arinbjôrg", N)], "binamn hinn Svarti – inte pris"),
    ("IM MM132", 0, 1, 1, 0, [("Þórulfr", N), ("Fríða", N)], "sonr Þórulfs; <iualfir> osäkert"),
    ("IM MM135", 0, 0, 0, 0, [("Þorleifr", N), ("Fiak", G), ("Hafr", N)], "bróðurson Hafrs är farbror, inte förälder"),
    ("IM MM136", 0, 0, 0, 0, [("Oddr", N), ("Frakki", N), ("Þorbjôrn", N)], ""),
    ("IM MM139", 0, 0, 0, 0, [("Þorbjôrn", N)], ""),
    ("IM MM140", 0, 1, 1, 0, [("Ástríðr", N), ("Oddr", N)], "dóttur Odds"),
    ("IM MM141", 0, 1, 0, 0, [("Myrgjôl", G), ("Þúríð", N)], "… sonr: faderns namn förlorat"),
    ("IM MM142", 0, 0, 0, 0, [("Heðinn", N), ("Hlífhildr", N), ("Árni", N), ("Sigurðr", N)], ""),
    ("IM MM175", 0, 1, 0, 0, [("Cuan", G), ("Mael-B…", G)], "sonr <mailb…>"),
]
# H5: parent -> child on Man, both named, origin known (planens generationspar)
GENERATION = [("IM MM99", "Bjôrn", N, "Gautr", N), ("IM MM101", "Aðakán", G, "Melbrigði", G),
              ("IM MM106", "Ljótulfr", N, "Áleifr", N), ("IM MM106", "Áleifr", N, "Ulfr", N),
              ("IM MM112", "Krínán", G, "Ófeigr", N), ("IM MM118", "Dufgal", G, "Druian", G),
              ("IM MM130", "Dufgal", G, "Malmury", G), ("IM MM135", "Þorleifr", N, "Fiak", G),
              ("IM MM136", "Frakki", N, "Oddr", N), ("IM MM140", "Oddr", N, "Ástríðr", N),
              ("IM MM142", "Heðinn", N, "Hlífhildr", N), ("IM MM175", "Mael-B…", G, "Cuan", G)]

if __name__ == "__main__":
    out = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(out, "kodning.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["signum", "plats_andra_sidan", "slakt_bakat", "slakt_bakat_nordisk", "pris", "namn", "anm"])
        for s, pl, sl, sn, pr, names, anm in ROWS:
            w.writerow([s, pl, sl, sn, pr, ";".join(f"{a}:{b}" for a, b in names), anm])
    with open(os.path.join(out, "generationer.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["signum", "förälder", "ursprung_förälder", "barn", "ursprung_barn"])
        w.writerows(GENERATION)
    print(len(ROWS), "rader")
