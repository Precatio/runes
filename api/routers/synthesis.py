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
from src import synthesis as syn
from src.inscription_types import CATEGORIES, category_check
from src.reading import compare as compare_reading, validate as validate_reading
from api.routers.research import _categories as research_categories
from src.research_gaps import carver_home
from src.stats import METRIC_LABELS, METRICS, summarize
from src.styles import SOURCE as STYLE_SOURCE, dating_text

router = APIRouter()


def _as_object(value) -> dict:
    """The model sometimes wraps its JSON object in a list; anything else counts as no answer."""
    if isinstance(value, list):
        value = next((v for v in value if isinstance(v, dict)), {})
    return value if isinstance(value, dict) else {}


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
    # AI:ns stilbedömning från 2D-analysen (valfritt): predicted_style, confidence, reasoning
    two_d: Optional[dict] = None
    # Projektets sparade 3D-analyser [{id, feature_type, slices, savedAt}] och vilken som ska jämföras
    analyses: List[dict] = Field(default_factory=list)
    analysis_id: Optional[str] = None
    # Mätkorpusen [{signum, feature_type, means, slices}] – jämförelsen görs här, inklusive sten mot sten
    corpus: List[dict] = Field(default_factory=list)
    corpus_note: Optional[str] = None  # t.ex. "logga in för att jämföra med korpusen"
    # Appens egen läsning från Språk & Fonetik: {transliteration, normalization}
    reading: Optional[dict] = None
    # Berggrunden på platsen ur SGU:s karta (nätverksanrop, några sekunder första gången)
    include_geology: bool = True


class Evidence(BaseModel):
    source: str
    description: str
    weight: Optional[float] = None


class AttributionCandidate(BaseModel):
    name: str
    strength: str  # "stark" | "måttlig" | "svag"
    evidence: List[Evidence]
    reasoning: str = ""
    score: Optional[float] = None
    sources: List[str] = Field(default_factory=list)
    literature: Optional[dict] = None  # stämmer / nytt / motsäger mot Rundata
    geography: Optional[dict] = None
    styles: Optional[dict] = None  # ristarens stilgrupper och datering
    stone_tests: Optional[dict] = None  # permutationstest mot kandidatens uppmätta stenar
    material: Optional[dict] = None  # stenens bergart mot ristarens stenar
    language: Optional[dict] = None  # språkdrag (fonetisk stil och språkbruk) mot ristarens inskrifter
    category: Optional[dict] = None  # inskriftens typ (minne, bro, bön, magisk …) mot ristarens
    first_in: List[str] = Field(default_factory=list)  # källor där kandidaten kommer först


class SynthesisResponse(BaseModel):
    candidates: List[AttributionCandidate]
    conflicts: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    outcome: Optional[dict] = None
    analysis_used: Optional[dict] = None
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


def _legacy_slices(slices: List[SliceData]) -> list[dict]:
    return [{metric: getattr(sl, field) for field, metric in SLICE_FIELDS.items()} for sl in slices]


def _selected_analysis(req: SynthesisRequest) -> Optional[dict]:
    if not req.analyses:
        return None
    if req.analysis_id:
        for a in req.analyses:
            if a.get("id") == req.analysis_id:
                return a
    wanted = req.feature_type or "rune"
    same = [a for a in req.analyses if (a.get("feature_type") or "unknown") == wanted]
    return (same or req.analyses)[-1]


def collect_evidence(req: SynthesisRequest) -> dict:
    s = store()
    rec = s.get(req.signum)
    evidence: dict = {"signum": rec["signum"] if rec else req.signum, "rundata": None,
                      "orthography": None, "groove": None, "measurements": None, "tool_heuristic": None,
                      "measurements_by_feature": None, "_rec": rec}
    home = carver_home(s.inscriptions)
    if rec:
        evidence["rundata"] = {
            "carvers": rec["carvers"], "carver_raw": rec["carver_raw"], "style": rec["style"],
            "style_uncertain": rec["style_uncertain"], "dating": rec["dating"], "material": rec["material"],
            "place": rec["place"], "parish": rec["parish"], "context": context_text(rec),
            "style_dating": dating_text(rec["style"]),
        }
        evidence["orthography"] = syn.orthography(orthography_model(), rec, home)
    # Our own reading stands in when Rundata has no usable text (new finds, short or missing texts)
    if req.reading and req.reading.get("transliteration"):
        evidence["reading_validation"] = validate_reading(req.reading["transliteration"], rec, s.inscriptions,
                                                          req.reading.get("others") or [])
    reading_ok = (evidence.get("reading_validation") or {}).get("reliable")
    if req.reading and reading_ok and not (evidence["orthography"] or {}).get("usable"):
        own = syn.orthography_from_reading(orthography_model(), req.reading, req.signum, home, rec)
        if own and own["usable"]:
            evidence["orthography"] = own
    if req.reading and rec and rec.get("transliteration") and req.reading.get("transliteration"):
        c = compare_reading(req.reading["transliteration"], rec["transliteration"],
                    req.reading.get("normalization") or "", rec.get("normalization", ""))
        evidence["reading_check"] = {k: c[k] for k in ("char_agreement", "word_agreement", "coverage", "summary")}

    # Measurements: the real slices of the selected analysis; the old per-save summaries only as fallback
    selected = _selected_analysis(req)
    query_slices = syn.complete(selected.get("slices") or []) if selected else []
    if not query_slices and req.slices:
        query_slices = syn.complete(_legacy_slices(req.slices))
    if query_slices:
        summary = {m: summarize([x[m] for x in query_slices]) for m in METRICS}
        evidence["measurements"] = summary
        angle = summary["apex_vinkel_deg"]["mean"]
        if angle is not None:
            evidence["tool_heuristic"] = tool_heuristic(angle, req.stoneType, req.weathering)
    if req.analyses:
        evidence["measurements_by_feature"] = syn.measurement_summary(req.analyses)
    feature_type = (selected or {}).get("feature_type") or req.feature_type or "rune"
    evidence["_query"] = query_slices
    evidence["analysis_used"] = {"id": (selected or {}).get("id"), "feature_type": feature_type,
                                 "n": len(query_slices), "saved_at": (selected or {}).get("savedAt")}

    if req.include_geology:
        evidence["geology"] = syn.site_geology(rec)
    if req.two_d and req.two_d.get("predicted_style"):
        ai_style = str(req.two_d["predicted_style"])
        rd_style = (evidence.get("rundata") or {}).get("style")
        evidence["style_check"] = {
            "ai_style": ai_style,
            "ai_confidence": req.two_d.get("confidence"),
            "rundata_style": rd_style,
            "agrees": bool(rd_style) and ai_style == rd_style,
            "note": "AI-bedömning från foto/ristningskarta, okalibrerad.",
        }
    if req.corpus and query_slices:
        g = syn.groove(query_slices, feature_type, req.corpus, s.get, req.signum)
        evidence["_candidate_stones"] = g.pop("_stones", {})
        evidence["groove"] = g
    elif (req.groove_attribution or {}).get("ranking"):
        # Older clients send a ready attribution; its weight follows its cross-validation
        ga = req.groove_attribution
        ev = ga.get("evaluation") or {}
        rel = max(0.0, (ev["top1_accuracy"] - ev["chance_top1"]) / (1 - ev["chance_top1"])) if ev else 0.0
        evidence["groove"] = {"ranking": ga["ranking"][:5], "evaluation": ev or None,
                              "reference_size": ga.get("reference_size"), "reliability": round(rel, 3)}
    return evidence


def enrich_candidates(evidence: dict, candidates: list[dict]) -> list[dict]:
    """Prövar kandidaterna mot litteraturen och de tre främsta mot geografi, stilgrupper och
    kandidatens uppmätta stenar."""
    s = store()
    rec = evidence.get("_rec")
    home = carver_home(s.inscriptions)
    stones = evidence.get("_candidate_stones") or {}
    for c in candidates:
        c["literature"] = syn.literature_verdict(rec, c["name"])
    names = orthography_model().names
    for c in candidates[:3]:
        if rec:
            c["geography"] = syn.geography(rec, c["name"], s.inscriptions, home)
            c["styles"] = syn.carver_styles(rec, c["name"], s.inscriptions)
            c["material"] = syn.material_check(rec, c["name"], s.inscriptions)
            c["language"] = syn.language_check(rec, c["name"], s.inscriptions, names)
            row = next((r for r in research_categories()["carvers"] if r["carver"] == c["name"]), None)
            c["category"] = category_check(rec, row, CATEGORIES)
        if stones.get(c["name"]) and evidence.get("_query"):
            c["stone_tests"] = syn.stone_tests(evidence["_query"], stones[c["name"]])
    return candidates


def public_evidence(evidence: dict) -> dict:
    return {k: v for k, v in evidence.items() if not k.startswith("_")}


def build_candidates(evidence: dict) -> List[AttributionCandidate]:
    return [AttributionCandidate(**c) for c in build_candidate_dicts(evidence)]


def build_candidate_dicts(evidence: dict) -> list[dict]:
    return enrich_candidates(evidence, syn.build_candidates(evidence))


def evidence_text(evidence: dict, req: SynthesisRequest, candidates: Optional[list] = None,
                  conflict_list: Optional[list] = None) -> str:
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
    if o and o.get("source"):
        lines.append("Bygger på appens egen AI-läsning av bilden (Rundata saknar användbar text) – osäkrare.")
    if evidence.get("reading_check"):
        lines.append(f"Appens läsning mot Rundata: {evidence['reading_check']['summary']}")
    if o:
        ev = o["evaluation"] or {}
        lines.append(f"Metodens träffsäkerhet (korsvaliderad): rätt ristare först i {ev.get('top1_accuracy', 0):.0%} "
                     f"av fallen bland {ev.get('n_carvers')} ristare (slump {ev.get('chance_top1', 0):.0%}).")
        if not o.get("usable", True):
            lines.append(f"Bara {o.get('n_words')} läsbara ord – för kort text, vägs inte in.")
        for r in o["ranking"]:
            extra = f", precision {r['precision']:.0%}" if "precision" in r else ""
            lines.append(f"- {r['carver']}: likhet {r['similarity']:.2f}{extra}")
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

    sc = evidence.get("style_check")
    if sc:
        lines.append("\n--- STILGRUPP: AI-BEDÖMNING (2D) MOT RUNDATA ---")
        verdict = ("stämmer med Rundata" if sc["agrees"] else
                   "skiljer sig från Rundata" if sc["rundata_style"] else "Rundata saknar stilgrupp")
        lines.append(f"AI (okalibrerad, från bild): {sc['ai_style']}; Rundata: {sc['rundata_style'] or 'uppgift saknas'} – {verdict}.")

    geo = evidence.get("geology")
    if geo:
        lines.append("\n--- BERGGRUND PÅ PLATSEN (SGU) ---")
        lines.append(geo["text"] + " " + geo["caveat"])
    for c in candidates or []:
        checks = [x["text"] for x in (c.get("literature"), c.get("geography"), c.get("styles"), c.get("material"),
                                      c.get("language"), c.get("category"), c.get("stone_tests")) if x]
        if checks:
            lines.append(f"\n--- KONTROLLER FÖR {c['name'].upper()} ({c['strength']}a belägg) ---")
            lines += checks
    if conflict_list:
        lines.append("\n--- MOTSÄGELSER MELLAN KÄLLORNA ---")
        lines += conflict_list

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
    return _as_object(json.loads(resp.text))


@router.post("/analyze", response_model=SynthesisResponse)
def analyze_synthesis(
    request: SynthesisRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key"),
):
    evidence = collect_evidence(request)
    cand_dicts = build_candidate_dicts(evidence)
    conflict_list = syn.conflicts(evidence, cand_dicts)
    missing = syn.missing_notes(evidence, request.corpus_note)
    result = syn.outcome(evidence.get("_rec"), cand_dicts, conflict_list)
    candidates = [AttributionCandidate(**c) for c in cand_dicts]
    block = evidence_text(evidence, request, cand_dicts, conflict_list)

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

    # Deterministic texts when there is no AI
    material = (f"Material enligt Rundata: {rd['material']}." if rd and rd["material"] else "Material saknas i Rundata.") \
        + f" Angiven stenart: {request.stoneType}; vittring: {request.weathering}."
    dating = (f"Rundata: {rd['dating'] or 'ingen datering'}. {rd['style_dating']}" if rd else "Stenen finns inte i Rundata.")
    if cand_dicts and cand_dicts[0].get("styles"):
        dating += f" {cand_dicts[0]['name']}: {cand_dicts[0]['styles']['text']}"
    theory = result["text"] + (" " + " ".join(conflict_list) if conflict_list else " Inga motsägelser mellan källorna.")
    return SynthesisResponse(
        candidates=candidates,
        conflicts=conflict_list,
        missing=missing,
        outcome=result,
        analysis_used=evidence.get("analysis_used"),
        geology_analysis=parsed.get("geology_analysis") or material,
        theory_analysis=parsed.get("theory_analysis") or theory,
        dating_analysis=parsed.get("dating_analysis") or dating,
        summary=parsed.get("summary") or result["text"],
        evidence=public_evidence(evidence),
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
def generate_report(
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
