"""Stilgrupper för vikingatida runstenar enligt Anne-Sofie Gräslund.

Dateringarna är ungefärliga och återges som de brukar sammanfattas; de överlappar och
ska inte läsas som skarpa gränser. Källa: Gräslund, A.-S. 1998, "Ornamentiken som
dateringsgrund för Upplands runstenar", i: Innskrifter og datering / Dating inscriptions,
Trondheim, s. 73–91 (samt Gräslund 2006).
"""

SOURCE = ("Gräslund, A.-S. 1998. Ornamentiken som dateringsgrund för Upplands runstenar. "
          "I: Innskrifter og datering / Dating inscriptions. Trondheim, s. 73–91.")

STYLE_GROUPS = [
    {"code": "RAK", "from": 980, "to": 1015, "name": "Rakt avslutade rundjursändar",
     "features": "Runslingan saknar djurhuvud; ändarna är raka eller avslutas utan djurhuvud."},
    {"code": "Fp", "from": 1010, "to": 1050, "name": "Fågelperspektiv",
     "features": "Runslingan avslutas med ett djurhuvud sett ovanifrån (i fågelperspektiv)."},
    {"code": "KB", "from": None, "to": None, "name": "Kors med band",
     "features": "Kors med inramande band; används i Rundata som egen grupp utan fast datering."},
    {"code": "Pr1", "from": 1010, "to": 1050, "name": "Profil 1 (Ringerikestil)",
     "features": "Djurhuvud i profil; enkel, ofta kraftig djurkropp och sparsam ornamentik."},
    {"code": "Pr2", "from": 1020, "to": 1050, "name": "Profil 2 (Ringerikestil)",
     "features": "Djurhuvud i profil, mer utvecklad slinga; fortfarande Ringerikedrag."},
    {"code": "Pr3", "from": 1050, "to": 1080, "name": "Profil 3 (Urnesstil)",
     "features": "Urnesstil: smäckrare djur, mandelformat öga, slingor som korsar varandra."},
    {"code": "Pr4", "from": 1070, "to": 1100, "name": "Profil 4 (Urnesstil)",
     "features": "Fullt utvecklad Urnesstil med elegant, rytmiskt sammanflätade djur."},
    {"code": "Pr5", "from": 1100, "to": 1130, "name": "Profil 5 (Urnesstil)",
     "features": "Sen Urnesstil; mycket tunna, långsträckta djur och täta slingor."},
]

BY_CODE = {s["code"]: s for s in STYLE_GROUPS}


def dating_text(code: str | None) -> str:
    s = BY_CODE.get((code or "").rstrip("?"))
    if not s:
        return "Ingen stilgrupp angiven."
    if s["from"]:
        return f"{s['code']} ({s['name']}): ca {s['from']}–{s['to']} enligt Gräslunds stilkronologi."
    return f"{s['code']} ({s['name']}): ingen fast datering."
