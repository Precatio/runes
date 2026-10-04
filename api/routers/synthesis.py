"""Syntes och rapport.

Kandidaterna för ristarattribuering räknas fram deterministiskt ur tre oberoende källor:
  1. Rundata (signerad/attribuerad ristare enligt litteraturen),
  2. ortografisk stilometri över Rundatas korpus,
  3. huggteknik jämförd med den delade mätkorpusen (skickas med från klienten).
AI:n skriver bara löptext utifrån dessa belägg och får inte hitta på sannolikheter.
"""
import json
import os
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from api.config import APP_VERSION, GEMINI_PRO_MODEL, METHOD_VERSION
from api.errors import ai_error, logger
from api.rundata import context_text, store
from api.routers.orthography import model as orthography_model
from api.routers.threed import tool_heuristic
from src.stats import METRIC_LABELS, summarize
from src.styles import SOURCE as STYLE_SOURCE, dating_text

router = APIRouter()


class SliceData(BaseModel):
    angle: Optional[float] = None
    asymmetry: Optional[float] = None
    depth: Optional[float] = None
    width: Optional[float] = None
    djup_bredd_kvot: Optional[float] = None
    bottenradie: Optional[float] = None
    ytrahet: Optional[float] = None
    tool: Optional[str] = None


class SynthesisRequest(BaseModel):
    signum: str
    stoneType: str = "Okänd"
    weathering: str = "Okänt"
    slices: List[SliceData] = Field(default_factory=list)
    style_analysis: Optional[str] = None
    attributed_carver: Optional[str] = None
    location: Optional[str] = None
    ornamentation: Optional[str] = None
    period: Optional[str] = None
    feature_type: Optional[str] = None
    # Resultat från /api/stats/attribute mot den delade korpusen (valfritt)
    groove_attribution: Optional[dict] = None


class Evidence(BaseModel):
    source: str
    description: str


class AttributionCandidate(BaseModel):
    name: str
    strength: str  # "stark" | "måttlig" | "svag"
    evidence: List[Evidence]
    reasoning: str = ""


class SynthesisResponse(BaseModel):
    candidates: List[AttributionCandidate]
    geology_analysis: str
    theory_analysis: str
    dating_analysis: str
    summary: str
    evidence: dict
    sources: List[str]
    ai_used: bool


class ReportRequest(BaseModel):
    signum: str
    stoneType: str = "Okänd"
    weathering: str = "Okänt"
    attributed_carver: Optional[str] = None
    location: Optional[str] = None
    ornamentation: Optional[str] = None
    period: Optional[str] = None
    slices: List[SliceData] = Field(default_factory=list)
    geology_analysis: str = ""
    theory_analysis: str = ""
    dating_analysis: str = ""
    summary: str = ""
    candidates: List[AttributionCandidate] = Field(default_factory=list)
    evidence: Optional[dict] = None
    sources: List[str] = Field(default_factory=list)
    provenance: Optional[dict] = None


class ReportResponse(BaseModel):
    html_report: str


SLICE_FIELDS = {
    "angle": "apex_vinkel_deg", "asymmetry": "asymmetri_deg", "depth": "spårdjup_mm", "width": "spårbredd_mm",
    "djup_bredd_kvot": "djup_bredd_kvot", "bottenradie": "bottenradie_mm", "ytrahet": "ytråhet_mm",
}


def groove_summary(slices: List[SliceData]) -> dict:
    return {metric: summarize([getattr(s, field) for s in slices]) for field, metric in SLICE_FIELDS.items()}


def _fmt(stat: dict, digits: int) -> str:
    if not stat or stat["n"] == 0:
        return "–"
    out = f"{stat['mean']:.{digits}f}"
    if stat["n"] > 1:
        out += f" ± {stat['sd']:.{digits}f} (SD, n={stat['n']})"
    return out


def collect_evidence(req: SynthesisRequest) -> dict:
    rec = store().get(req.signum)
    evidence: dict = {"signum": rec["signum"] if rec else req.signum, "rundata": None,
                      "orthography": None, "groove": None, "measurements": None, "tool_heuristic": None}
    if rec:
        evidence["rundata"] = {
            "carvers": rec["carvers"], "carver_raw": rec["carver_raw"], "style": rec["style"],
            "style_uncertain": rec["style_uncertain"], "dating": rec["dating"], "material": rec["material"],
            "place": rec["place"], "parish": rec["parish"], "context": context_text(rec),
            "style_dating": dating_text(rec["style"]),
        }
        model = orthography_model()
        if rec["signum"] in model.index:
            ranking = model.rank_carvers(rec["signum"], 5)
            evidence["orthography"] = {"ranking": ranking["ranking"], "n_words": ranking["n_words"],
                                       "evaluation": model.evaluate()}
    if req.slices:
        summary = groove_summary(req.slices)
        evidence["measurements"] = summary
        angle = summary["apex_vinkel_deg"]["mean"]
        if angle is not None:
            evidence["tool_heuristic"] = tool_heuristic(angle, req.stoneType, req.weathering)
    ga = req.groove_attribution or {}
    if ga.get("ranking"):
        evidence["groove"] = {"ranking": ga["ranking"][:5], "evaluation": ga.get("evaluation"),
                              "reference_size": ga.get("reference_size")}
    return evidence


def build_candidates(evidence: dict) -> List[AttributionCandidate]:
    cands: dict[str, dict] = {}

    def add(name, source, description, weight):
        c = cands.setdefault(name, {"name": name, "evidence": [], "score": 0})
        c["evidence"].append({"source": source, "description": description})
        c["score"] += weight

    rd = evidence.get("rundata") or {}
    for c in rd.get("carvers", []):
        if c["kind"] == "S":
            add(c["name"], "Rundata",
                "Inskriften är signerad av ristaren" + (" (osäker läsning)" if c["uncertain"] else "") + ".",
                2 if c["uncertain"] else 4)
        elif c["kind"] == "A":
            add(c["name"], "Rundata",
                "Attribuerad till ristaren i litteraturen" + (" (osäker)" if c["uncertain"] else "") + ".",
                1 if c["uncertain"] else 2)
        elif c["kind"] in ("P", "L"):
            add(c["name"], "Rundata", "Parsten till eller liknar ristarens signerade inskrifter.", 1)

    orth = evidence.get("orthography") or {}
    for rank, r in enumerate(orth.get("ranking", [])[:3], start=1):
        add(r["carver"], "Ortografi",
            f"Plats {rank} i ortografisk jämförelse (cosinuslikhet {r['similarity']:.2f}, "
            f"jämfört med {r['n_inscriptions']} inskrifter av ristaren).", 2 if rank == 1 else 1)

    groove = evidence.get("groove") or {}
    for rank, r in enumerate(groove.get("ranking", [])[:3], start=1):
        add(r["group"], "Huggteknik",
            f"Plats {rank} i jämförelse med uppmätta stenar (Mahalanobisavstånd {r['distance']:.2f}, "
            f"n={r['n']} stenar).", 2 if rank == 1 else 1)

    out = []
    for c in cands.values():
        sources = {e["source"] for e in c["evidence"]}
        if c["score"] >= 4 or len(sources) >= 3:
            strength = "stark"
        elif c["score"] >= 3 or (c["score"] >= 2 and len(sources) >= 2):
            strength = "måttlig"
        else:
            strength = "svag"
        out.append((c["score"], len(sources),
                    AttributionCandidate(name=c["name"], strength=strength, evidence=c["evidence"])))
    out.sort(key=lambda t: (-t[0], -t[1], t[2].name))
    return [t[2] for t in out[:6]]


def evidence_text(evidence: dict, req: SynthesisRequest) -> str:
    lines = []
    rd = evidence.get("rundata")
    lines.append("--- RUNDATA (Samnordisk runtextdatabas) ---")
    lines.append(rd["context"] if rd else "Signumet finns inte i Rundata.")
    if rd:
        lines.append(f"Stildatering: {rd['style_dating']}")

    lines.append("\n--- UPPMÄTTA HUGGSPÅR ---")
    m = evidence.get("measurements")
    if m:
        digits = {"djup_bredd_kvot": 2, "ytråhet_mm": 3, "bottenradie_mm": 2}
        for k, stat in m.items():
            lines.append(f"{METRIC_LABELS[k]}: {_fmt(stat, digits.get(k, 1))}")
        th = evidence.get("tool_heuristic")
        if th:
            lines.append(f"Verktygsheuristik: {th['label']} (tröskel {th['threshold_deg']:.0f}°; {th['note']})")
    else:
        lines.append("Inga 3D-mätningar.")

    lines.append("\n--- ORTOGRAFISK JÄMFÖRELSE ---")
    o = evidence.get("orthography")
    if o:
        ev = o["evaluation"] or {}
        lines.append(f"Metodens träffsäkerhet (korsvaliderad): rätt ristare först i {ev.get('top1_accuracy', 0):.0%} "
                     f"av fallen bland {ev.get('n_carvers')} ristare (slump {ev.get('chance_top1', 0):.0%}).")
        for r in o["ranking"]:
            lines.append(f"- {r['carver']}: likhet {r['similarity']:.2f}")
    else:
        lines.append("Ej tillgänglig för denna inskrift.")

    lines.append("\n--- HUGGTEKNIK MOT MÄTKORPUS ---")
    g = evidence.get("groove")
    if g:
        ev = g.get("evaluation") or {}
        if ev:
            lines.append(f"Korsvaliderad träffsäkerhet: {ev.get('top1_accuracy', 0):.0%} "
                         f"(slump {ev.get('chance_top1', 0):.0%}).")
        for r in g["ranking"]:
            lines.append(f"- {r['group']}: avstånd {r['distance']:.2f} (n={r['n']})")
    else:
        lines.append("Ingen jämförelse mot mätkorpusen (för lite referensdata eller ej begärd).")

    lines.append("\n--- ANVÄNDARENS UPPGIFTER ---")
    lines.append(f"Stenart: {req.stoneType}; vittring: {req.weathering}; plats: {req.location or 'okänd'}")
    if req.style_analysis:
        lines.append(f"2D-stilanalys: {req.style_analysis}")
    return "\n".join(lines)


def fallback_reasoning(c: AttributionCandidate) -> str:
    return " ".join(e.description for e in c.evidence)


def run_ai(api_key: str, evidence_block: str, candidates: List[AttributionCandidate], signum: str) -> dict:
    client = genai.Client(api_key=api_key)
    names = [c.name for c in candidates]
    prompt = f"""
Du är en noggrann runolog. Skriv på svenska, sakligt och med tydlig osäkerhet.
Du får ENDAST använda uppgifterna nedan. Hitta inte på fakta, källor, sannolikheter eller procentsatser.
Saknas uppgift ska du säga att den saknas. Hänvisa till Rundata när du använder uppgifter därifrån.
Verktygsheuristiken och vittringsjusteringen är tumregler, inte kalibrerade mått – säg det om du nämner dem.

UNDERLAG FÖR {signum}:
{evidence_block}

KANDIDATER (framräknade av programmet): {", ".join(names) or "inga"}

Svara med JSON:
{{
  "geology_analysis": "1–3 meningar om stenart/material och vittring utifrån underlaget.",
  "theory_analysis": "2–4 meningar: stämmer mätningarna och den ortografiska jämförelsen med Rundatas attribuering?",
  "dating_analysis": "2–3 meningar utifrån Rundatas datering och stilgrupp.",
  "summary": "Kort sammanfattning med tydlig osäkerhet.",
  "reasoning": {{"<kandidatnamn>": "1–2 meningar som förklarar beläggen för just denna kandidat"}}
}}
"""
    resp = client.models.generate_content(
        model=GEMINI_PRO_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json"),
    )
    return json.loads(resp.text)


@router.post("/analyze", response_model=SynthesisResponse)
async def analyze_synthesis(
    request: SynthesisRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key"),
):
    evidence = collect_evidence(request)
    candidates = build_candidates(evidence)
    block = evidence_text(evidence, request)

    rd = evidence.get("rundata")
    sources = [store().meta["attribution"]] if rd else []
    if rd and rd.get("style"):
        sources.append(STYLE_SOURCE)

    parsed, ai_used = {}, False
    api_key = x_gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            parsed = run_ai(api_key, block, candidates, evidence["signum"])
            ai_used = True
        except Exception as e:
            # Syntesen fungerar utan AI; beläggen är redan framräknade
            logger.warning("AI-text för syntesen misslyckades: %r", e)

    reasoning = parsed.get("reasoning") or {}
    for c in candidates:
        c.reasoning = reasoning.get(c.name) or fallback_reasoning(c)

    no_ai = "AI-tolkning ej tillgänglig – se beläggen nedan."
    material = f"Material enligt Rundata: {rd['material']}." if rd and rd["material"] else no_ai
    dating = f"Rundata: {rd['dating'] or 'ingen datering'}. {rd['style_dating']}" if rd else no_ai
    return SynthesisResponse(
        candidates=candidates,
        geology_analysis=parsed.get("geology_analysis") or material,
        theory_analysis=parsed.get("theory_analysis") or no_ai,
        dating_analysis=parsed.get("dating_analysis") or dating,
        summary=parsed.get("summary") or no_ai,
        evidence=evidence,
        sources=sources,
        ai_used=ai_used,
    )


def _measurement_table(slices: List[SliceData]) -> str:
    summary = groove_summary(slices)
    rows = []
    for k, stat in summary.items():
        if stat["n"] == 0:
            continue
        ci = f"{stat['ci95'][0]:.2f}–{stat['ci95'][1]:.2f}" if stat["ci95"] else "–"
        rows.append(f"<tr><td>{METRIC_LABELS[k]}</td><td>{stat['mean']:.2f}</td><td>{stat['sd']:.2f}</td>"
                    f"<td>{ci}</td><td>{stat['n']}</td></tr>")
    if not rows:
        return "<p>Inga 3D-mätningar.</p>"
    return ("<table><thead><tr><th>Mått</th><th>Medel</th><th>SD</th><th>95 % KI</th><th>n</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>")


def _candidates_html(candidates: List[AttributionCandidate]) -> str:
    if not candidates:
        return "<p>Inga kandidater kunde beräknas ur underlaget.</p>"
    items = []
    for c in candidates:
        ev = "".join(f"<li><strong>{e.source}:</strong> {e.description}</li>" for e in c.evidence)
        items.append(f"<li><strong>{c.name}</strong> – belägg: {c.strength}<ul>{ev}</ul></li>")
    return f"<ul>{''.join(items)}</ul>"


def _method_html(provenance: Optional[dict]) -> str:
    p = provenance or {}
    mesh = p.get("mesh") or {}
    lines = [
        f"Programvara: Runforskning {p.get('version', APP_VERSION)}, mätmetod {p.get('method_version', METHOD_VERSION)}.",
        "V-vinkeln är öppningsvinkeln mellan spårväggarnas regressionslinjer i varje tvärsnitt.",
        "Verktygsklassningen (pik-/bredmejsel) är en heuristisk tumregel med tröskel 85°, "
        "justerad för vittring och bergart enligt antaganden som inte är kalibrerade mot referensmaterial.",
    ]
    if mesh.get("sha256"):
        lines.append(f"Analyserad fil: {mesh.get('filename')} (SHA-256 {mesh['sha256'][:16]}…, {mesh.get('faces')} ytor).")
    if p.get("timestamp"):
        lines.append(f"Analystidpunkt: {p['timestamp']}.")
    return "".join(f"<p>{line}</p>" for line in lines)


@router.post("/report", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key"),
):
    key_to_use = x_gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not key_to_use:
        raise HTTPException(status_code=401, detail="No Gemini API Key provided")

    base = SynthesisRequest(signum=request.signum, stoneType=request.stoneType, weathering=request.weathering,
                            slices=request.slices, location=request.location,
                            ornamentation=request.ornamentation, period=request.period)
    evidence = request.evidence or collect_evidence(base)
    block = evidence_text(evidence, base)
    cand_lines = "\n".join(f"- {c.name} ({c.strength}): {c.reasoning}" for c in request.candidates) or "inga"

    prompt = f"""
Skriv löptext för en vetenskaplig rapport på svenska om runinskriften {request.signum}.
Använd ENDAST underlaget nedan. Hitta inte på uppgifter, citat, litteraturhänvisningar eller sannolikheter.
Markera osäkerhet tydligt. Hänvisa till Rundata där uppgifterna kommer därifrån.

UNDERLAG:
{block}

KANDIDATER OCH BELÄGG:
{cand_lines}

TIDIGARE SAMMANFATTNING: {request.summary}

Svara med giltig HTML (endast <h2>, <p>, <strong>, <em>, <ul>, <li>) i dessa avsnitt:
<h2>Inskriften</h2> (text, översättning och kontext enligt Rundata)
<h2>Huggteknik</h2> (tolka mätningarna och deras spridning; nämn att verktygsklassningen är en tumregel)
<h2>Ortografi</h2> (vad den ortografiska jämförelsen visar och dess redovisade träffsäkerhet)
<h2>Attribuering</h2> (väg samman beläggen, utan procentsatser)
<h2>Datering</h2>
<h2>Slutsats</h2>
"""
    try:
        client = genai.Client(api_key=key_to_use)
        resp = client.models.generate_content(model=GEMINI_PRO_MODEL, contents=prompt,
                                              config=types.GenerateContentConfig(temperature=0.3))
        body = resp.text.strip().replace("```html", "").replace("```", "")
    except Exception as e:
        raise ai_error(e, "Rapportgenereringen misslyckades.")

    sources = request.sources or ([store().meta["attribution"]] if evidence.get("rundata") else [])
    html = (
        f"<h1>Rapport: {request.signum}</h1>"
        f"{body}"
        "<h2>Mätvärden</h2>"
        f"{_measurement_table(request.slices)}"
        "<h2>Attribueringskandidater (framräknade belägg)</h2>"
        f"{_candidates_html(request.candidates)}"
        "<h2>Metod och reproducerbarhet</h2>"
        f"{_method_html(request.provenance)}"
        "<h2>Källor</h2>"
        f"<ul>{''.join(f'<li>{s}</li>' for s in sources) or '<li>Inga externa källor.</li>'}</ul>"
        "<p><em>Löptexten är AI-genererad utifrån underlaget ovan och ska granskas innan den används.</em></p>"
    )
    return ReportResponse(html_report=html)
