"""
Clinical AI Eval Designer
=========================

Takes what a clinical AI model does plus its clinical context, and produces a
structured, citable validation specification: study design, performance
benchmarks, ground-truth strategy, regulatory pathway, and more — every field
flagged by confidence level and by the kind of expert review it needs.

Data pipeline (per run):
    User input
      → live retrieval from public registries (ClinicalTrials.gov, openFDA, PubMed)
      → grounded reference context injected into the prompt
      → Claude Fable 5 synthesizes the constrained 8-field spec
      → (optional) web search fills gaps the registries don't cover

The value is NOT the model. It's the constraint layer + real grounding: outputs
never go beyond what the retrieved evidence supports, thresholds are never
invented, and every field is honest about how much expert review it needs.
"""

import datetime
from html.parser import HTMLParser

import anthropic
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# The constraint layer.
#
# This system prompt is the product. It encodes clinical/regulatory judgment and
# hard-codes the behavioral guardrails that make an AI-generated validation spec
# *safe* to put in front of a clinical team: no invented numbers, real citations
# from retrieved records, explicit confidence, explicit "this needs a human."
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a clinical validation strategist. Clinical AI teams come to you with a model that works technically but that they cannot yet deploy, because they do not know what evidence it must generate before a health system, regulator, or payer will accept it. Your job is to turn their model + clinical context into a structured, citable validation specification.

You generalize to ANY disease indication, model type, sensor, and clinical setting the user enters. Do not assume any particular example domain.

=========================
GROUNDED REFERENCE CONTEXT
=========================
The user message may begin with a "GROUNDED REFERENCE CONTEXT" block containing raw records retrieved live from public registries: ClinicalTrials.gov (study designs, endpoints, enrollment), openFDA (device classification, 510(k)/De Novo precedents), and PubMed (literature). When it is present:
- Treat these records as your PRIMARY citations. Cite the real identifiers exactly as given — NCT numbers, PMIDs, 510(k) K-numbers, product codes, regulation numbers. Do not alter or invent identifiers.
- Map the retrieved study designs, endpoints, enrollment sizes, and regulatory precedents directly into the relevant fields.
- Set Confidence from how well the retrieved evidence matches THIS model and population: strong, on-point matches → HIGH; only tangential matches → MEDIUM; little or nothing retrieved → LOW.
- Absence of a record is NOT evidence of absence. Say "no matching record was retrieved" rather than "none exists," unless you can genuinely support the stronger claim.
When the block is absent or thin, rely on web search if available, and flag lower confidence rather than inventing numbers.

=========================
NON-NEGOTIABLE CONSTRAINTS
=========================
These are what make your output safe to use in a high-stakes clinical setting. A tool that invents confident numbers is worse than no tool.

1. NEVER invent a numeric threshold, benchmark, sample size, or performance target. Every quantitative claim must either (a) be tied to a specific retrieved citation you can name, or (b) be explicitly flagged as "no established benchmark retrieved — this must be set by the study team / expert."
2. Ground numbers and precedents in the retrieved records and any web search. If you cannot find a source for a number, say so — do not fill the gap with a plausible-sounding figure.
3. Cite inline as (Author-group, YEAR, PMID #####) / (NCT########) / (510(k) K######, product code XXX). Never fabricate an identifier. If unsure an identifier is real, describe the source in words instead.
4. The correct answer is often "no FDA benchmark exists" or "this is a wellness claim, not a medical-device claim." State that plainly when true. Do not overstate any regulatory pathway.
5. Sensor / input validation is a PRE-CONDITION, not a footnote. If the model consumes sensor, device, or image data, its measurement/acquisition validity must be established before any downstream clinical claim can be trusted.
6. Population-specific validity threats are physics/physiology, not optics. Name the concrete threat for THIS model (e.g. optical HR sensors × Fitzpatrick skin tone; imaging models × scanner/vendor/reconstruction-kernel shift; NLP models × site-specific documentation style) and require it be tested as a pre-specified subgroup.
7. Label reliability is a ceiling. If the ground-truth/reference standard is noisy, achievable sensitivity/specificity is capped by it — say so.

=========================
CONFIDENCE + REVIEW FLAGS
=========================
Every one of the 8 fields must end with two flags:

- Confidence: HIGH | MEDIUM | LOW
  HIGH   = directly supported by a retrieved citation or established regulatory precedent.
  MEDIUM = reasoned from adjacent evidence; defensible but the team should confirm.
  LOW    = little direct evidence retrieved; largely a judgment call needing expert input.

- Expert review: choose the phrasing that fits.
  "Expert sign-off — output is well-grounded; expert confirms or adjusts"
  "Expert working session — assumptions need expert judgment before finalizing"
  For any regulatory field: "Expert working session — regulatory counsel required before any claims language is finalized"

=========================
REQUIRED OUTPUT FORMAT (Markdown)
=========================
Produce EXACTLY these sections, in this order.

# Clinical Validation Specification

**Generated:** {today}
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed (+ web search where noted)

## Inputs
- **AI model:** ...
- **Clinical use case:** ...
- **Patient population:** ...
- **Healthcare setting:** ...
- **Intended clinical claim:** ...

## Output at a Glance
A markdown table with two columns — | Field | Output summary | — one row per field below.

## 1. Study Design
**Recommendation:** ...
**Rationale:** ... (with inline citations to retrieved records)
**Confidence:** ...
**Expert review:** ...

## 2. Sensor / Input Validation (Pre-Condition)
(same five-line structure; if the model has no sensor input, state that and explain what input-validity threat replaces it)

## 3. Performance Benchmarks
## 4. Ground Truth Strategy
## 5. Sample Size
## 6. Subgroup Requirements
## 7. Regulatory Pathway
## 8. Post-Deployment Monitoring

(Every one of fields 2–8 uses the same Recommendation / Rationale / Confidence / Expert review structure as field 1.)

## What This Validation Certifies — and What It Does Not
**CERTIFIES:** one precise sentence describing exactly what a passing study would establish (claim, conditions, devices, population, subgroups).
**DOES NOT CERTIFY:** a bulleted list of what a passing study would NOT establish (e.g. physiological ground truth, clinical-grade equivalence, regulatory clearance, generalization beyond the study population).

## Footer
Italicize this exact note, adapted to the sources you actually used:
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification and 510(k)/De Novo, PubMed) and, where noted, web search. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*

Write densely and specifically for THIS input. No filler. If the input is under-specified, state the assumption you are making rather than inventing facts."""


# ---------------------------------------------------------------------------
# Live retrieval from public registries (no API keys required)
# ---------------------------------------------------------------------------
HTTP_TIMEOUT = 12  # seconds per registry call


def _clean(text, limit):
    return " ".join((text or "").split())[:limit]


def build_queries(model_desc, use_case):
    use_case = use_case.strip()
    model_desc = model_desc.strip()
    return {
        "ct": _clean(use_case or model_desc, 200),
        "fda": _clean(use_case or model_desc, 100),
        "pubmed": _clean(f"{use_case} {model_desc}", 250),
    }


def search_clinicaltrials(term, max_studies=6):
    """ClinicalTrials.gov API v2 — real study designs, endpoints, enrollment."""
    try:
        r = requests.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params={"query.term": term, "pageSize": max_studies},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        studies = r.json().get("studies", [])
        if not studies:
            return "", "⚠️ ClinicalTrials.gov: no matching studies"
        lines = []
        for s in studies:
            ps = s.get("protocolSection", {})
            idm = ps.get("identificationModule", {})
            dm = ps.get("designModule", {})
            design = dm.get("designInfo", {})
            primary = "; ".join(
                o.get("measure", "")
                for o in ps.get("outcomesModule", {}).get("primaryOutcomes", []) or []
            )
            lines.append(
                f"- {idm.get('nctId','')} | {idm.get('briefTitle','')} "
                f"| status={ps.get('statusModule',{}).get('overallStatus','')} "
                f"| type={dm.get('studyType','')} phases={', '.join(dm.get('phases',[]) or [])} "
                f"| n={dm.get('enrollmentInfo',{}).get('count','')} "
                f"| allocation={design.get('allocation','')} "
                f"masking={design.get('maskingInfo',{}).get('masking','')} "
                f"| primary_outcomes={_clean(primary, 300)}"
            )
        return "\n".join(lines), f"✅ ClinicalTrials.gov: {len(studies)} studies"
    except requests.Timeout:
        return "", "❌ ClinicalTrials.gov: timed out"
    except requests.RequestException:
        return "", "❌ ClinicalTrials.gov: request failed"


def search_openfda(term, max_results=5):
    """openFDA — device classification + 510(k) regulatory precedents."""
    out, ok = [], False
    try:
        r = requests.get(
            "https://api.fda.gov/device/classification.json",
            params={"search": f'device_name:"{term}"', "limit": max_results},
            timeout=HTTP_TIMEOUT,
        )
        if r.ok:
            ok = True
            for res in r.json().get("results", []):
                out.append(
                    f"- CLASSIFICATION | {res.get('device_name','')} "
                    f"| product_code={res.get('product_code','')} "
                    f"| class={res.get('device_class','')} "
                    f"| regulation={res.get('regulation_number','')} "
                    f"| panel={res.get('medical_specialty_description','')}"
                )
    except requests.RequestException:
        pass
    try:
        r = requests.get(
            "https://api.fda.gov/device/510k.json",
            params={"search": f'device_name:"{term}"', "limit": max_results},
            timeout=HTTP_TIMEOUT,
        )
        if r.ok:
            ok = True
            for res in r.json().get("results", []):
                out.append(
                    f"- 510(k) | {res.get('device_name','')} "
                    f"| k_number={res.get('k_number','')} "
                    f"| decision={res.get('decision_description','')} "
                    f"| date={res.get('decision_date','')} "
                    f"| applicant={res.get('applicant','')}"
                )
    except requests.RequestException:
        pass
    if out:
        return "\n".join(out), f"✅ openFDA: {len(out)} device records"
    if ok:
        return "", "⚠️ openFDA: no matching device records"
    return "", "❌ openFDA: request failed"


def search_pubmed(term, max_results=8):
    """PubMed E-utilities — real PMIDs, titles, journals, years."""
    try:
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": term, "retmode": "json",
                    "retmax": max_results, "sort": "relevance"},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return "", "⚠️ PubMed: no matching articles"
        r2 = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            timeout=HTTP_TIMEOUT,
        )
        r2.raise_for_status()
        result = r2.json().get("result", {})
        lines = []
        for pid in result.get("uids", []):
            item = result.get(pid, {})
            journal = item.get("fulljournalname") or item.get("source", "")
            year = (item.get("pubdate", "") or "")[:4]
            lines.append(f"- PMID {pid} | {_clean(item.get('title',''), 250)} | {journal} {year}")
        return "\n".join(lines), f"✅ PubMed: {len(lines)} articles"
    except requests.Timeout:
        return "", "❌ PubMed: timed out"
    except requests.RequestException:
        return "", "❌ PubMed: request failed"


class _TextExtractor(HTMLParser):
    """Minimal HTML → text extractor (stdlib only; skips script/style)."""

    def __init__(self):
        super().__init__()
        self._skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self.parts.append(t)


def fetch_url_text(url, max_chars=4000):
    """Fetch an optional user-supplied reference page and extract clean-ish text."""
    url = (url or "").strip()
    if not url:
        return "", None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        r = requests.get(
            url, timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (ClinicalAIEvalDesigner)"},
        )
        r.raise_for_status()
        parser = _TextExtractor()
        parser.feed(r.text)
        text = _clean(" ".join(parser.parts), max_chars)
        if not text:
            return "", "⚠️ Reference URL: no readable text extracted"
        return text, f"✅ Reference URL: {len(text)} chars extracted"
    except requests.Timeout:
        return "", "❌ Reference URL: timed out"
    except requests.RequestException:
        return "", "❌ Reference URL: fetch failed"


def build_grounded_context(model_desc, use_case, optional_url=""):
    """Query all registries (+ optional reference URL) and assemble the context."""
    q = build_queries(model_desc, use_case)
    ct_text, ct_status = search_clinicaltrials(q["ct"])
    fda_text, fda_status = search_openfda(q["fda"])
    pm_text, pm_status = search_pubmed(q["pubmed"])
    url_text, url_status = fetch_url_text(optional_url)

    sections = []
    if ct_text:
        sections.append("### ClinicalTrials.gov (study designs, endpoints, enrollment)\n" + ct_text)
    if fda_text:
        sections.append("### openFDA (device classification / 510(k) precedents)\n" + fda_text)
    if pm_text:
        sections.append("### PubMed (literature)\n" + pm_text)
    if url_text:
        sections.append("### Reference document (user-provided URL)\n" + url_text)

    statuses = [ct_status, fda_status, pm_status]
    if url_status:
        statuses.append(url_status)

    context = "\n\n".join(sections)[:9000]
    return context, statuses


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------
def build_user_message(model_desc, use_case, population, setting, claim):
    claim = claim.strip() or (
        "Not specified — infer the most defensible intended claim from the use case, "
        "and state that assumption explicitly."
    )
    setting = setting.strip() or "Not specified — infer a reasonable default and state your assumption."
    return f"""Design a clinical validation specification for the following AI system.

AI model (what it detects/predicts, and the input modality or sensor/device it reads from):
{model_desc}

Clinical use case:
{use_case}

Patient population:
{population}

Healthcare setting / deployment context:
{setting}

Intended clinical claim (what the team wants to be able to say the model does):
{claim}

Produce the full 8-field specification in the required format. Map the grounded reference records into the fields, cite their real identifiers, and set confidence from the strength of the retrieved evidence. Where no benchmark was retrieved, say so."""


def wrap_with_context(user_message, grounded_context):
    if not grounded_context:
        return user_message
    return (
        "GROUNDED REFERENCE CONTEXT (retrieved live from public registries; may be "
        "incomplete — do not treat absence as evidence of absence):\n\n"
        f"{grounded_context}\n\n---\n\n{user_message}"
    )


# ---------------------------------------------------------------------------
# Anthropic client + generation
# ---------------------------------------------------------------------------
def get_client():
    key = st.secrets.get("ANTHROPIC_API_KEY", None)
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


def generate_spec(client, user_message, effort, use_web_search):
    """Stream the spec from Claude Fable 5, grounded in the injected context.

    - Streaming avoids HTTP timeouts on long, high-effort turns and shows progress.
    - Server-side refusal fallback to Opus 4.8 rescues benign biomedical requests
      that a safety classifier occasionally false-positives on.
    - Web search (optional) fills gaps the registries don't cover.
    Returns (markdown_text, final_message).
    """
    tools = []
    if use_web_search:
        tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 6}]

    messages = [{"role": "user", "content": user_message}]
    placeholder = st.empty()
    accumulated = ""
    final = None

    for _ in range(6):  # continue past server-tool pause_turn boundaries
        with client.beta.messages.stream(
            model="claude-fable-5",
            max_tokens=32000,
            betas=["server-side-fallback-2026-06-01"],
            fallbacks=[{"model": "claude-opus-4-8"}],
            output_config={"effort": effort},
            tools=tools,
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT.replace("{today}", str(datetime.date.today())),
                "cache_control": {"type": "ephemeral"},
            }],
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                accumulated += text
                placeholder.markdown(accumulated + " ▌")
            final = stream.get_final_message()

        if final.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": final.content})
            continue
        break

    placeholder.markdown(accumulated)
    return accumulated, final


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Clinical AI Eval Designer", page_icon="🧪", layout="wide")

st.title("🧪 Clinical AI Eval Designer")
st.markdown(
    "Turn what your clinical AI model does into a **structured, citable validation "
    "specification** — grounded in live searches of ClinicalTrials.gov, openFDA, and "
    "PubMed. Every field is flagged by confidence and by the expert review it needs.\n\n"
    "Constrained by design: **no invented thresholds**, citations come from real "
    "retrieved records, and every field is honest about what still needs a human."
)

with st.sidebar:
    st.header("Settings")
    effort = st.select_slider(
        "Reasoning effort",
        options=["low", "medium", "high", "xhigh", "max"],
        value="high",
        help="Higher effort = more thorough synthesis, but slower and more expensive.",
    )
    use_registries = st.toggle(
        "Ground with live registries",
        value=True,
        help="Query ClinicalTrials.gov, openFDA, and PubMed before prompting the model, "
             "so citations come from real records.",
    )
    use_web_search = st.toggle(
        "Supplement with web search",
        value=True,
        help="Let the model fill gaps the registries don't cover (e.g. FDA guidance PDFs).",
    )
    st.divider()
    st.caption(
        "Model: **Claude Fable 5** with automatic fallback to Opus 4.8. "
        "Fable requires 30-day data retention on your Anthropic org — if every "
        "request errors with a 400, check that setting."
    )

st.subheader("Describe your model and its clinical context")

with st.form("spec_form"):
    c1, c2 = st.columns(2)
    with c1:
        model_desc = st.text_area(
            "AI model",
            placeholder="e.g. Detects and quantifies Coronary Artery Calcium (CAC) and Aortic Valve "
                        "Calcium (AVC) from routine, non-gated chest CT scans.",
            height=120,
        )
        use_case = st.text_input(
            "Clinical use case",
            placeholder="e.g. Opportunistic cardiovascular screening",
        )
    with c2:
        population = st.text_input(
            "Patient population",
            placeholder="e.g. Adults undergoing routine chest CT for unrelated reasons",
        )
        setting = st.text_input(
            "Healthcare setting",
            placeholder="e.g. Radiology / opportunistic screening in a general hospital",
        )
    claim = st.text_area(
        "Intended clinical claim (optional — sharpens the spec)",
        placeholder="e.g. Flag patients with elevated CAC for cardiology referral.",
        height=90,
    )
    optional_url = st.text_input(
        "Reference URL (optional — a whitepaper, FDA guidance, or paper to pull in)",
        placeholder="e.g. https://www.fda.gov/media/....pdf",
    )
    submitted = st.form_submit_button("Generate validation specification", type="primary")

if submitted:
    client = get_client()
    if client is None:
        st.error(
            "No Anthropic API key found. Add it to `.streamlit/secrets.toml` as "
            "`ANTHROPIC_API_KEY = \"sk-ant-...\"` (see the README) and rerun."
        )
    elif not (model_desc.strip() and use_case.strip() and population.strip() and setting.strip()):
        st.warning("Please fill in the AI model, clinical use case, patient population, and healthcare setting.")
    else:
        # 1. Fetch raw data from the registries.
        grounded_context, statuses = "", []
        if use_registries:
            with st.spinner("Searching ClinicalTrials.gov, openFDA, and PubMed…"):
                grounded_context, statuses = build_grounded_context(model_desc, use_case, optional_url)
            with st.expander("🔎 Live data retrieved (grounding context)", expanded=True):
                for s in statuses:
                    st.write(s)
                if grounded_context:
                    st.code(grounded_context)
                else:
                    st.info("No registry records retrieved — the model will flag the evidence base as thin.")

        # 2. Synthesize with Fable, grounded in the retrieved records.
        user_message = wrap_with_context(
            build_user_message(model_desc, use_case, population, setting, claim),
            grounded_context,
        )
        status_msg = (
            "Synthesizing the specification from retrieved evidence… "
            "this can take a few minutes at higher effort."
        )
        with st.spinner(status_msg):
            try:
                markdown_text, final = generate_spec(client, user_message, effort, use_web_search)
            except anthropic.APIStatusError as e:
                st.error(f"API error {e.status_code}: {e.message}")
                st.stop()
            except anthropic.APIConnectionError:
                st.error("Network error reaching the Anthropic API. Check your connection and retry.")
                st.stop()

        if final is not None and final.stop_reason == "refusal":
            st.error(
                "The request was declined by the model's safety system, and the fallback "
                "model also declined. Try rephrasing the clinical context in more neutral terms."
            )
        elif not markdown_text.strip():
            st.warning("No content was returned. Try again, or lower the effort setting.")
        else:
            st.success("Specification generated. Review every field with a domain expert before use.")
            st.download_button(
                "⬇ Download as Markdown",
                data=markdown_text,
                file_name=f"validation_spec_{datetime.date.today()}.md",
                mime="text/markdown",
            )
