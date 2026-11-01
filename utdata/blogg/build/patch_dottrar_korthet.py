"""Rättelse av korthetsrutan i den publicerade artikeln "Döttrarna som runstenarna glömde" (PXwp9L2e1gJtfPg77sNw).
Rutan (inlagd 2026-10-18 av lagg_till_korthet.py) talade om fäder i Västergötland och mödrar i Svealand – barnfynd som
artikeln inte använder – och sade att mönstren håller i båda halvorna, fast texten säger att dottermönstren inte gör
det. Den nya rutan följer texten. Byter bara rutan (sv + en), behåller publiceringsdatum, publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_dottrar_korthet.py"""
import datetime as dt
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

OLD_SV = """:::box Det viktigaste i korthet
- Runstenarna restes till minne av män: döttrar, systrar och mödrar är nästan osynliga bland de ihågkomna.
- Men mönstret har sprickor som håller för statistisk prövning: i Västergötland reser fäder stenar efter döttrar oftare än någon annanstans, och i Svealand är mödrarna ovanligt synliga.
- Sprickorna följer landskapen, inte slumpen – de håller i båda halvorna av materialet.
- Vår tolkning att pröva: där arvsrätten gav kvinnan en plats, fick hon också en sten.
:::"""
NEW_SV = """:::box Det viktigaste i korthet
- Döttrarna är nästan osynliga bland de ihågkomna, fast de dog lika lätt som sönerna. Tystnaden säger mer om vad en runsten var till för än om hur mycket man sörjde.
- När en dotter får en sten är det sent i runstenstiden, och i Uppland blir den ovanligt ofta en bro.
- Vår tolkning att pröva: dottern kom på stenen när arvet gick genom henne, och när hon dog blev hennes del en bro för hennes själ.
- Det är en hypotes, inte ett fynd: stenarna är för få för att mönstret ska hålla i båda halvorna av materialet.
:::"""
OLD_EN = """:::box The essentials in brief
- The runestones were raised in memory of men: daughters, sisters and mothers are nearly invisible among the remembered.
- But the pattern has cracks that withstand statistical testing: in Västergötland fathers raise stones after daughters more often than anywhere else, and in Svealand the mothers are unusually visible.
- The cracks follow the provinces, not chance – they hold in both halves of the material.
- Our interpretation to test: where inheritance law gave the woman a place, she also got a stone.
:::"""
NEW_EN = """:::box The essentials in brief
- Daughters are nearly invisible among the remembered, though they died as easily as sons. The silence says more about what a runestone was for than about how much people grieved.
- When a daughter gets a stone, it is late in the runestone era, and in Uppland it becomes a bridge unusually often.
- Our interpretation to test: the daughter came onto the stone when the inheritance passed through her, and when she died her share became a bridge for her soul.
- It is a hypothesis, not a finding: the stones are too few for the pattern to hold in both halves of the material.
:::"""

ref = blog.firestore().collection(blog.COLLECTION).document("PXwp9L2e1gJtfPg77sNw")
old = ref.get().to_dict()
assert old and old["slug"] == "dottrarna-som-runstenarna-glomde" and old.get("published")
assert old["body"].count(OLD_SV) == 1 and old["body_en"].count(OLD_EN) == 1
# the new box only says what the text says
for b in (old["body"], old["body_en"]):
    assert "1050" in b
assert "de dog lika lätt" in old["body"] and "för få för att mönstret ska hålla i båda halvorna" in old["body"]
assert "bro för hennes själ" in old["body"]
blog._backup(ref.id, old)
ref.set({"body": old["body"].replace(OLD_SV, NEW_SV), "body_en": old["body_en"].replace(OLD_EN, NEW_EN),
         "updatedAt": dt.datetime.now(dt.timezone.utc)}, merge=True)
blog._forget()
print("korthetsrutan rättad; publiceringsdatum oförändrat:", old.get("publishedAt"))
print(site_export.publish_now())
