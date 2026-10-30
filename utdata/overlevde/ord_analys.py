"""Del B: kodningen av överlevnad (ord_kodning.csv, med Wiktionarys definition som belägg) och test W1.
    .venv/bin/python utdata/overlevde/ord_analys.py      Skriver ord_kodning.csv och ord.json."""
import csv
import json
import os
import re

from scipy.stats import fisher_exact

OUT = os.path.dirname(os.path.abspath(__file__))
U = json.load(open(os.path.join(OUT, "ord_underlag.json"), encoding="utf-8"))
MIN_STONES = 3
# Excluded before coding: the normalization cannot tell the word apart (decided after the counts, before survival)
EXCLUDED = {"goði": "Rundatas normalisering skiljer inte goða (gode) från góða (god)",
            "vé": "ve/vi i normaliseringen är tvetydiga"}
# lever = descendant with the core meaning in today's Swedish; ändrad = descendant exists but means something lower
# or else, or only historically/archaically; borta = no descendant in general use
CODE = {
    "konungr": ("lever", "kung", "manligt statsöverhuvud i en monarki"),
    "þegn": ("borta", "", "ingen svensk ättling (jfr eng. thane)"),
    "drengr": ("ändrad", "dräng", "från hedersord för duglig ung man till 'manlig medhjälpare i jordbruket'; även nedsättande"),
    "húskarl": ("borta", "huskarl", "bara som historisk term, inget uppslag i Wiktionary"),
    "styrimaðr": ("lever", "styrman", "person som styr ett fartyg"),
    "lið": ("borta", "", "'lid' (följe, här) är försvunnet; 'led' är ett annat ord"),
    "dróttinn": ("borta", "drott", "taggat historia: 'hövding, furste' – men avledningen drottning lever"),
    "félagi": ("borta", "", "ingen svensk ättling (jfr eng. fellow)"),
    "sveinn (följesman)": ("borta", "sven", "taggat historia/ålderdomligt"),
    "þing": ("lever", "ting", "juridik: sammankomst för gemensamma angelägenheter, beslutsmöte (tingsrätt)"),
    "arfr": ("lever", "arv", "något som ärvs"),
    "Guð": ("lever", "Gud", "den ende guden"),
    "Kristr": ("lever", "Krist", "Jesus Krist (inget eget uppslag i Wiktionary; jfr Kristus)"),
    "sál": ("lever", "själ", "människans inre odödliga väsen"),
    "and (ônd)": ("lever", "ande", "immateriell substans; övernaturligt väsen"),
    "heilagr": ("lever", "helig", "av religiös betydelse, vördad"),
    "Þórr": ("ändrad", "Tor", "lever som gud i mytologin och som namn, inte i kult"),
    "faðir": ("lever", "fader/far", "manlig förälder"), "móðir": ("lever", "moder/mor", "kvinnlig förälder"),
    "bróðir": ("lever", "broder/bror", "manligt syskon"), "systir": ("lever", "syster", "kvinnligt syskon"),
    "sonr": ("lever", "son", "manlig avkomma"), "dóttir": ("lever", "dotter", "kvinnlig avkomma"),
    "kona": ("ändrad", "kona", "taggat ålderdomligt"),
    "bóndi (make)": ("ändrad", "bonde", "betyder i dag lantbrukare, inte make"),
    "fóstri": ("ändrad", "foster-", "lever bara i sammansättningar (fosterbarn, fosterfar)"),
    "mágr": ("lever", "måg", "ens barns make"), "frændi": ("lever", "frände", "(manlig) släkting"),
    "steinn": ("lever", "sten", ""), "brú": ("lever", "bro", ""), "vegr": ("lever", "väg", ""),
    "land": ("lever", "land", ""), "skip": ("lever", "skepp", ""),
    "kuml": ("ändrad", "kummel", "minnesmärke → stenhög som sjömärke"), "bý": ("lever", "by", ""),
    "haugr": ("lever", "hög", ""), "eyja": ("lever", "ö", ""), "dauðr": ("lever", "död", ""),
    "deyja": ("lever", "dö", ""), "fara": ("lever", "fara", "resa; något ålderdomligt men i bruk"),
    "ráða": ("lever", "råda", ""), "rísta": ("lever", "rista", ""), "hôggva": ("lever", "hugga", ""),
    "góðr": ("lever", "god", ""),
}
rows = []
for w in U["words"]:
    lem, n = w["lemma"], U["counts"][w["lemma"]]
    if n < MIN_STONES or lem in EXCLUDED:
        continue
    code, modern, basis = CODE[lem]
    rows.append({"domain": w["domain"], "lemma": lem, "stones": n, "code": code, "modern": modern, "basis": basis})
with open(os.path.join(OUT, "ord_kodning.csv"), "w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
    wr.writeheader()
    wr.writerows(rows)

power = [r for r in rows if r["domain"] in ("makt", "lag", "kult")]
other = [r for r in rows if r["domain"] in ("släkt", "vardag")]
t = [[sum(r["code"] == "lever" for r in power), sum(r["code"] != "lever" for r in power)],
     [sum(r["code"] == "lever" for r in other), sum(r["code"] != "lever" for r in other)]]
odds, p = fisher_exact(t, alternative="less")
by = {d: {c: [r["lemma"] for r in rows if r["domain"] == d and r["code"] == c] for c in ("lever", "ändrad", "borta")}
      for d in ("makt", "lag", "kult", "släkt", "vardag")}
tm = [[len(by["makt"]["lever"]), len(by["makt"]["ändrad"]) + len(by["makt"]["borta"])], t[1]]
om, pm = fisher_exact(tm, alternative="less")
out = {"n_words": len(rows), "excluded": EXCLUDED, "W1": {"table": t, "share_power": t[0][0] / sum(t[0]),
       "share_other": t[1][0] / sum(t[1]), "or": odds, "p": p},
       "description_rank_only": {"table": tm, "share": tm[0][0] / sum(tm[0]), "or": om, "p": pm},
       "by_domain": by}
json.dump(out, open(os.path.join(OUT, "ord.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
print(json.dumps(out, ensure_ascii=False, indent=1, default=float))
