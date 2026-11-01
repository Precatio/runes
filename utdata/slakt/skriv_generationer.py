"""Skriver generationer_resultat.md ur generationer.json (alla tal ur filen).
    .venv/bin/python utdata/slakt/skriv_generationer.py"""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(OUT, "generationer.json")))
P, S, D = r["primary"], r["steps"], r["descriptive"]


def pf(p):
    return f"{p:.4f}".replace(".", ",") if p >= 0.0001 else "< 0,0001"


def row(name, s):
    return (f"| {name} | {s['n']} | {s['later']} | {s['ties']} | {s['earlier']} | {pf(s['p'])} | "
            f"{'håller' if s['holds'] else 'håller inte'} |")


by_year = {tuple(v["raised"]): v["years"] for v in r["votes"]}
lines = [
    "# Släktnätverket steg 2b: följer stilgrupperna generationerna?", "",
    f"Låst plan `{r['plan']}` (sha {r['plan_sha']}), korpus `{r['corpus']}`. Kört 2026-11-01 med "
    "`utdata/slakt/generationer.py`; alla tal i `generationer.json`.", "",
    "## Svar", "",
    f"**Ja, med en reservation.** Av {P['n']} personer som reser en sten och själva minns på en annan har minnesstenen "
    f"senare stilgrupp för {P['later']}, samma för {P['ties']} och tidigare för {P['earlier']} "
    f"(teckentest, ensidigt, p = {pf(P['p'])}). Fem av planens sex steg håller. Steg 1 (halvorna) faller: i den ena "
    f"halvan är det {S['1_halvor']['halves'][0]['later']} mot {S['1_halvor']['halves'][0]['earlier']} "
    f"(p = {pf(S['1_halvor']['halves'][0]['p'])}), i den andra {S['1_halvor']['halves'][1]['later']} mot "
    f"{S['1_halvor']['halves'][1]['earlier']} (p = {pf(S['1_halvor']['halves'][1]['p'])}). Riktningen är densamma i "
    "båda, men den ena halvan är för liten för att nå p < 0,05. Enligt planen är fyndet därför **Delvis prövat**. "
    "Forskningsrapportmallens golv (p < 0,05 och samma riktning i båda halvorna) nås inte, så fyndet blir **ingen "
    "rapport**. Det kan nämnas i artiklar som en antydan, eller prövas på nytt under en ny låst plan när fler släktsamband "
    "finns (till exempel Mueller-Vollmers släktträd).", "",
    "## Huvudprov och steg", "",
    "| Prov | Personer | Senare | Lika | Tidigare | p | |", "|---|---|---|---|---|---|---|",
    row("Huvudprovet (Williams säkra par + appens 61 länkar)", P),
    row("1a. Första halvan av släkterna", S["1_halvor"]["halves"][0]),
    row("1b. Andra halvan", S["1_halvor"]["halves"][1]),
    row("2. Bara Williams", S["2_bara_williams"]),
    row(f"3. Utan Jarlabankes släkt ({len(S['3_utan_jarlabanke']['family_stones'])} stenar)", S["3_utan_jarlabanke"]),
    row("4. Bara fasta stilgrupper", S["4_bara_fasta"]),
    row("5. Med Williams osäkra par", S["5_med_osakra"]), "",
    f"Steg 6, omblandning av stilgrupperna mellan de {S['6_omblandning']['n_stones']} stenarna inom landskapet: "
    f"observerat senare − tidigare = {S['6_omblandning']['observed']}, p = {pf(S['6_omblandning']['p'])} "
    f"({'håller' if S['6_omblandning']['holds'] else 'håller inte'}).", "",
    f"Paren: {r['n_pairs']['williams_sure']} säkra par hos Williams mellan svenska runstenar i materialet, "
    f"{r['n_pairs']['williams_all']} med de osäkra, och appens {r['n_pairs']['app_sure']} säkra länkar. Nästan alla "
    "personer kommer ur Williams par. Appens länkar lägger till en enda person, så provet säger lite om appens egna nya "
    "länkar.", "",
    "## Beskrivande (prövas inte)", "",
    f"- **Lika stilgrupp** för {P['ties']} av {P['n']} ({round(100 * D['share_ties'])} %): personen reser en sten och "
    "får en egen inom samma stilgrupp. En stilgrupp spänner över 30–40 år, så det är väntat.",
    f"- **Avståndet i år** mellan stilgruppernas mittår: median {D['years_median']:.0f} år, kvartiler "
    f"{D['years_quartiles'][0]:.0f} och {D['years_quartiles'][2]:.0f} år. Medianen ligger nära noll eftersom en tredjedel "
    "är lika; övre kvartilen är ungefär en generation.",
    "- **Landskap:** " + ", ".join(f"{k} {v}" for k, v in D["by_province"].items()) + " personer. Provet är i praktiken "
    "ett uppländskt prov.", "",
    "## De fyra som säger emot", "",
    "Här säger antingen stilgruppen eller länken (att det är samma person) emot ordningen. Listan är öppen för runologer.", ""]
for c in r["earlier_cases"]:
    y = by_year[tuple(s["signum"] for s in c["raised"])]
    fmt = lambda ss: ", ".join(f"{s['signum']} ({s['style']}{'; ' + ', '.join(s['carvers']) if s['carvers'] else ''})"
                               for s in ss)
    lines.append(f"- **{c['person']}** reser {fmt(c['raised'])}, minns på {fmt(c['remembered'])}: "
                 f"{abs(y):.0f} år tidigare i mittår.")
lines += ["",
          "Sveinns fall (Pr2 mot Fp) ligger inom stilgruppernas överlappande dateringar (Fp 1010–1050, Pr2 1020–1050) och "
          "är därför ingen egentlig motsägelse i år, bara i rangordningen. De tre andra är det.", "",
          "## Svagheter", "",
          "- Bara 30 personer, nästan alla i Uppland. Halvorna är därför små, och den ena når inte p < 0,05.",
          "- Gräslund prövade sin metod mot Jarlabankesläktens ordning enligt texterna, med ”ett delvis motsägelsefullt "
          "resultat” (Gräslund 1992 s. 193, enligt Larsson 1996 s. 144). Provet håller utan Jarlabankes släkt. Om fler "
          "släkter användes när kronologin byggdes har vi inte kunnat se.",
          "- Att samma namn i två länkade inskrifter är samma person är ett antagande. Namn går i arv inom släkterna, så "
          "farfar och sonson kan heta lika; Larsson (1996) föreslår just två Jarlabanke. Felaktiga sammanslagningar drar "
          "resultatet mot slumpen, inte mot fyndet, och kan ligga bakom de fyra som säger emot.",
          "- Rangskalan behandlar Fp och Pr1 som samtida och stegen mellan grupperna som lika stora.", "",
          "## Källa", "",
          "Larsson, M. G. 1996. Tvegifte i Täby? Några synpunkter på Jarlabanke-stenarnas datering och placering. "
          "*Fornvännen* 91:3, s. 143–151."]
open(os.path.join(OUT, "generationer_resultat.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
