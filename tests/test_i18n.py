"""The report translation (src/i18n.py) must build the same templates as the browser (web/src/i18n/core.ts)."""
import json
import shutil
import subprocess

import pytest

from src import i18n

SAMPLES = [
    "Närmaste signerade eller attribuerade sten av Öpir 1 ligger 17 km bort.",
    "U 735 (Långarnö, Villberga sn, Trögds hd, Enköping) är attribuerad till Balle i Samnordisk runtextdatabas.",
    "p 0,019 och 1 101 stenar; 26,5 % i U.",
    "Stenen: röd granit. Säkra stenar av Balle med uppgift (75): granit (37), sandsten (3).",
    "Riksantikvarieämbetets och Uppsala universitets plattform Runor.",
    "Statistiskt signifikant: q 0,028 (logistisk regression (mgcv), Holm). Under 0,05 betyder det något.",
    "För: skiljetecken (apostrof: 13 % hos ristaren mot 5 % i U); diftongen au i 'och' (monoftong: 3 % hos ristaren mot 1 % i U).",
    "Stenen: rödgrå granit med ljusgröna inslag.",
    "Emot: stungen u (y) (ja: 42 % hos ristaren mot 19 % i U, bara 8 inskrifter).",
    "område: Närmaste sten ligger 4 km bort.\nstil: Stilgrupper på ristarens stenar: RAK (1).",
    "Stungen i (e): landskapen skiljer sig (q 0,047 för den samlade skillnaden, justerat för alla drag).",
]


def test_numbers_become_english():
    assert i18n.english_number("0,43") == "0.43" and i18n.english_number("1 101") == "1,101"
    assert i18n.english_number("1 101,5") == "1,101.5" and i18n.english_number("1050") == "1050"


def test_masking_and_lookup():
    t, tokens, kinds = i18n.mask("Närmaste sten av Öpir 1 ligger 17 km bort.")
    assert t == "Närmaste sten av {0} ligger {1} km bort." and tokens == ["Öpir 1", "17"] and kinds == ["name", "number"]
    # Language traits and their values are terms, translated on their own: one template for every combination
    t, tokens, kinds = i18n.mask("diftongen au i 'och' (auk: 28 % hos ristaren mot 62 % i U)", True)
    assert t == "{0} ({1}: {2} % hos ristaren mot {3} % i U)" and kinds[:2] == ["term", "term"]
    assert i18n.translate("Swedish only", "sv") == "Swedish only"
    assert i18n.translate("U Fv1972;272") == "U Fv1972;272"
    # Lists of stones and place strings: only fixed words, translated one by one
    assert i18n.translate("U 618 (29 km), U 23 (30 km, signerad)") == "U 618 (29 km), U 23 (30 km, signed)"
    assert i18n.translate("Sundby, Sånga sn, Färentuna hd, Ekerö") == "Sundby, Sånga parish, Färentuna hundred, Ekerö"


@pytest.mark.skipif(shutil.which("node") is None, reason="node saknas")
def test_same_templates_as_the_browser():
    script = ("import { readFileSync } from 'node:fs';"
              "const c = await import(process.argv[1] + '/web/src/i18n/core.ts');"
              "c.setNames(JSON.parse(readFileSync(process.argv[1] + '/web/src/i18n/names.json', 'utf8')));"
              "const xs = JSON.parse(process.argv[2]);"
              "c.setTerms(JSON.parse(readFileSync(process.argv[1] + '/web/src/i18n/terms.json', 'utf8')));"
              "console.log(JSON.stringify(xs.map(x => [c.mask(x).template, c.segments(x), c.mask(x, true).template])));")
    r = subprocess.run(["node", "--experimental-strip-types", "--no-warnings", "--input-type=module", "-e", script,
                        i18n.ROOT, json.dumps(SAMPLES)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    js = json.loads(r.stdout)
    for text, (template, segs, with_terms) in zip(SAMPLES, js):
        assert i18n.mask(text)[0] == template, text
        assert i18n.segments(text) == segs, text
        assert i18n.mask(text, True)[0] == with_terms, text
    # A label with a short parenthesis before the colon is split off like other labels
    assert i18n.LABEL.match("Stungen i (e): landskapen skiljer sig") is not None
