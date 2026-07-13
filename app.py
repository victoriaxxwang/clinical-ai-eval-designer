"""
Clinical AI Eval Designer — Streamlit UI
========================================

The presentation layer. All deterministic retrieval lives in `engine.py` (the
Core Deterministic Engine); this file handles inputs, the constraint-layer
prompt, the Fable 5 call, and rendering.

Pipeline: user input → engine.build_grounded_context() (live registry pulls) →
Claude Fable 5 synthesizes the constrained 8-field spec → output bundle
(spec + the source records it was grounded on).
"""

import datetime
import os
import sys

import anthropic
import streamlit as st

import critic_panel
import engine

# The wide-net twin lives in experimental/ and is a drop-in replacement for
# engine (identical build_grounded_context signature + return shape). It reads
# the disease out of the input text and aims every citation search at the real
# condition; the sidebar toggle selects between the two at grounding time.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "experimental"))
import engine_widenet

# ---------------------------------------------------------------------------
# The constraint layer (the product). See engine.py for the retrieval layer.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a clinical validation strategist. Clinical AI teams come to you with a model that works technically but that they cannot yet deploy, because they do not know what evidence it must generate before a health system, regulator, or payer will accept it. Your job is to turn their model + clinical context into a structured, citable validation specification.

You generalize to ANY disease indication, model type, sensor, and clinical setting the user enters. Do not assume any particular example domain.

=========================
GROUNDED REFERENCE CONTEXT
=========================
The user message may begin with a "GROUNDED REFERENCE CONTEXT" block containing raw records retrieved live from public registries: ClinicalTrials.gov (study designs, endpoints, enrollment), openFDA device classification and 510(k)/De Novo precedents (regulatory pathway), openFDA PMA / MAUDE adverse-event reports / recalls (Class III pathway and POST-MARKET SAFETY signals — use these for safety, failure-mode, and post-deployment-monitoring reasoning, NOT as efficacy evidence), openFDA drug/biologic records where the intervention is a drug or biologic (Drugs@FDA approvals for the approval pathway, SPL labeling for the on-label indication and boxed warnings, and FAERS adverse-event reports for post-market safety — again a safety/labeling signal, NOT efficacy evidence for THIS model), and the merged literature layer (Europe PMC / OpenAlex / Semantic Scholar / PubMed). When it is present:
- Treat these records as your PRIMARY citations. Cite the real identifiers exactly as given — NCT numbers, PMIDs, 510(k) K-numbers, product codes, regulation numbers. Do not alter or invent identifiers.
- Map the retrieved study designs, endpoints, enrollment sizes, and regulatory precedents directly into the relevant fields.
- Set Confidence from how well the retrieved evidence matches THIS model and population: strong, on-point matches → HIGH; only tangential matches → MEDIUM; little or nothing retrieved → LOW.
- Absence of a record is NOT evidence of absence. Say "no matching record was retrieved" rather than "none exists," unless you can genuinely support the stronger claim.
- The block ends with a "Coverage & Retrieval Gaps" note listing databases this pipeline did NOT search (licensed sources with no public API, plus other regulatory endpoints). Honor it: never claim a comprehensive or systematic search, and where a field would depend on one of those un-searched sources, say so as an explicit limitation.
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

- Confidence: HIGH | MEDIUM | LOW. In the Confidence row's Detail cell, prefix the level with a colored circle and a space — "🟢 HIGH", "🟡 MEDIUM", or "🔴 LOW".
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

### Clinical Validation Specification

**Generated:** {today}
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed{web_search_note}

#### Input at a Glance
A markdown table with three columns — | # | Input | Value | — one row per input, numbered 1 through 5 in this exact order: AI model, Clinical use case, Patient population, Healthcare setting, Intended clinical claim. Put the user-provided text in the Value column; if a field was inferred, put the inferred value and note "(inferred — stated as assumption)".

#### Output at a Glance
A markdown table with three columns — | # | Output | Output summary | — one row per field below, numbered 1 through 8 to match the field numbers.

#### 1. Study Design
A markdown table with three columns — | # | Element | Detail | — with EXACTLY these four rows, numbered 1 through 4 in this order: Recommendation, Rationale, Confidence, Expert review. Put the label in the Element column and the content in the Detail column. The Rationale row carries inline citations to retrieved records.

#### 2. Sensor / Input Validation (Pre-Condition)
(same four-row | # | Element | Detail | table; if the model has no sensor input, say so in the Recommendation row and explain what input-validity threat replaces it)

#### 3. Performance Benchmarks
#### 4. Ground Truth Strategy
#### 5. Sample Size
#### 6. Subgroup Requirements
#### 7. Regulatory Pathway
#### 8. Post-Deployment Monitoring

(Every one of fields 2–8 uses the SAME four-row | # | Element | Detail | table as field 1 — numbered 1 Recommendation, 2 Rationale, 3 Confidence, 4 Expert review.)

#### What This Validation Certifies — and What It Does Not
**CERTIFIES:** one precise sentence describing exactly what a passing study would establish (claim, conditions, devices, population, subgroups).

**DOES NOT CERTIFY:** a markdown table with two columns — | # | Not certified | — one numbered row per item a passing study would NOT establish (e.g. physiological ground truth, clinical-grade equivalence, regulatory clearance, generalization beyond the study population).

## Footer
Italicize this exact note, adapted to the sources you actually used:
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification / 510(k)/De Novo / PMA / MAUDE / recalls, openFDA drug/biologic pathways where applicable — Drugs@FDA / SPL labeling / FAERS, and the Europe PMC / OpenAlex / Semantic Scholar / PubMed literature layer){web_search_footer}. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*

Write densely and specifically for THIS input. No filler. If the input is under-specified, state the assumption you are making rather than inventing facts."""


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


def get_client():
    key = st.secrets.get("ANTHROPIC_API_KEY", None)
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


def generate_spec(client, user_message, effort, use_web_search):
    """Stream the spec from Claude Fable 5, grounded in the injected context."""
    tools = []
    if use_web_search:
        tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 6}]

    # Only advertise web search in the spec's Source line + footer when it is actually on.
    web_search_note = " (+ web search where noted)" if use_web_search else ""
    web_search_footer = " and, where noted, web search" if use_web_search else ""
    system_text = (
        SYSTEM_PROMPT
        .replace("{today}", str(datetime.date.today()))
        .replace("{web_search_note}", web_search_note)
        .replace("{web_search_footer}", web_search_footer)
    )

    messages = [{"role": "user", "content": user_message}]
    placeholder = st.empty()
    accumulated = ""
    final = None

    # NOTE: Claude Fable 5 requires 30-day data retention enabled on the Anthropic
    # org. If every request 400s, check that setting — a 400 is NOT a refusal, so the
    # server-side fallback below won't catch it.
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
                "text": system_text,
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
    return accumulated, final, placeholder


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Clinical AI Eval Designer", page_icon="🔍", layout="wide")

st.title("Clinical AI Eval Designer")
st.markdown(
    "**Verify, don't blindly trust · Grounded in authoritative registries & databases · "
    "Structured for a real clinical decision**\n\n"
    "Turns what your clinical AI does into a structured, citable **validation "
    "specification** — every field flagged by confidence and by the expert review "
    "it still needs."
)

with st.sidebar:
    st.header("Settings")
    # Reasoning effort is fixed at "high" — thorough synthesis without exposing a
    # knob a viewer would have to reason about. (Was a low→max slider.)
    effort = "high"
    use_widenet = st.toggle(
        "Disease-aware grounding (wide-net)",
        value=True,
        help="On by default. Reads the disease out of your description and aims all "
        "citation searches at the real condition. Turn off to see the baseline engine "
        "that grounds on device/ML keywords only — useful for a side-by-side comparison.",
    )
    use_web_search = st.toggle(
        "Supplement with web search",
        value=False,
        help="Off by default so every citation stays traceable to the live registry "
        "evidence. Turn on to let the model fill gaps the registries don't cover "
        "(e.g. FDA guidance PDFs) — note web-sourced citations aren't registry-verified, "
        "and the review panel will flag them as ungrounded.",
    )
    st.divider()
    st.markdown("**Model: Claude Fable 5**, with automatic **Opus 4.8** fallback")
    with st.expander(":gray[Why two models?]"):
        st.caption(
            "Every request goes to Claude Fable 5 first. If Fable's safety classifier "
            "declines a clinical request — common for life-sciences work — Opus 4.8 "
            "serves it automatically in the same call. The constraint layer is identical "
            "either way, so there's no visible failure."
        )

st.subheader("Describe your model and its clinical context")
st.caption(
    "Fill in what your model does and where it runs. Fields left blank are treated "
    "as under-specified — the spec will state its assumption rather than invent facts."
)

with st.form("spec_form"):
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
    population = st.text_input(
        "Patient population",
        placeholder="e.g. Adults undergoing routine chest CT for unrelated reasons",
    )
    setting = st.text_input(
        "Healthcare setting",
        placeholder="e.g. Radiology / opportunistic screening in a general hospital",
    )
    intervention_choice = st.radio(
        "What does the AI evaluate or act on? (routes the FDA search)",
        options=["Device / software", "Drug / biologic", "Both"],
        horizontal=True,
        help="Most clinical AI is software/a device (default) → the FDA device files "
             "(classification, 510(k), PMA, MAUDE, recalls). Choose Drug / biologic (or "
             "Both) if the model doses, selects, or predicts response to a medication — "
             "then Drugs@FDA, SPL labeling, and FAERS are searched as well.",
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
        # A new generation is starting: drop any previous spec + panel from memory
        # immediately so the old (now-stale) results don't linger, faded, behind the
        # ~90s stream. They're re-populated below once this generation succeeds.
        for _k in ("spec_markdown", "spec_bundle", "spec_filename", "panel_result"):
            st.session_state.pop(_k, None)

        # 1. Retrieve real records from the registries (the Core Deterministic Engine).
        intervention_type = {
            "Device / software": "device",
            "Drug / biologic": "drug",
            "Both": "both",
        }.get(intervention_choice, "device")
        _fda_scope = ("device classification, 510(k), PMA/MAUDE/recall" if intervention_type == "device"
                      else "Drugs@FDA/label/FAERS" if intervention_type == "drug"
                      else "device + drug/biologic pathways")
        with st.spinner(f"Searching ClinicalTrials.gov, openFDA ({_fda_scope}), and literature "
                        "(Europe PMC + OpenAlex + Semantic Scholar, Crossref-verified)…"):
            _eng = engine_widenet if use_widenet else engine
            grounded_context, statuses, retrieval_timestamp = _eng.build_grounded_context(
                model_desc, use_case, population, optional_url, setting, intervention_type
            )
        with st.expander("🗂️ Live data retrieved (grounding context)", expanded=False):
            st.caption(
                ("🎯 Grounding mode: **wide-net (disease-aware)**" if use_widenet
                 else "🔑 Grounding mode: **baseline (keyword)**")
                + f" · 📸 Retrieval snapshot (UTC): **{retrieval_timestamp}** — frozen "
                "once generated. A reviewer cites this snapshot, not a live re-query."
            )
            for s in statuses:
                st.write(s)
            if not any(s.startswith("✅") for s in statuses):
                st.info("No registry records retrieved — the model will flag the evidence base as thin.")
            st.code(grounded_context)

        # 2. Synthesize with Fable, grounded in the retrieved records.
        user_message = wrap_with_context(
            build_user_message(model_desc, use_case, population, setting, claim),
            grounded_context,
        )
        with st.spinner("Synthesizing the specification from retrieved evidence… "
                        "this can take a few minutes at higher effort."):
            try:
                markdown_text, final, spec_placeholder = generate_spec(
                    client, user_message, effort, use_web_search
                )
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
            # Build the Phase-1 bundle: the spec + the source records it was grounded on.
            bundle = markdown_text
            bundle += (
                f"\n\n---\n\n*📸 Retrieval snapshot (UTC): {retrieval_timestamp} — frozen once "
                "generated. Registries update over time, so this bundle (spec + the exact records "
                "below) is the citable artifact; a live re-query may return a different, equally "
                "valid set.*"
            )
            if grounded_context:
                bundle += (
                    "\n\n---\n\n## Appendix — Source Records (grounded reference context)\n\n"
                    "*Raw records retrieved from public registries and handed to the model as the "
                    "sole source of truth for this spec. Retained so the spec and its evidence "
                    "travel together (and so a reviewer can verify each citation).*\n\n"
                    + grounded_context
                )
            # Remember the spec + its bundle + evidence so both the spec render and the
            # review panel (drawn below, OUTSIDE this submit branch) survive Streamlit's
            # rerun on any later button click instead of vanishing.
            st.session_state["spec_markdown"] = markdown_text
            st.session_state["spec_bundle"] = bundle
            st.session_state["spec_filename"] = f"validation_spec_{datetime.date.today()}.md"
            st.session_state["grounded_context"] = grounded_context
            # Clear the streamed-in copy; the persistent block below is now the single
            # place the spec is drawn, so it can't show twice on this run.
            spec_placeholder.empty()


# ---------------------------------------------------------------------------
# Persistent spec render — draws the spec + its download button from session
# memory on EVERY run (not just the generation run), so clicking "Convene review
# panel" below (which reruns the whole page) can't make the spec disappear.
# ---------------------------------------------------------------------------
def _cap_heading_sizes(md):
    """Render-time safety net so no spec heading renders larger than the app's
    own section headers: downgrade any h1/h2 the model emitted (# -> ###, ## ->
    ####) so the spec title lands level with the app headers and the 1-8
    sub-sections sit one notch below. Idempotent — a spec already at ###/####
    (from the current prompt) is left untouched, so old cached specs and new
    generations render at the same sizes."""
    out = []
    for line in md.split("\n"):
        if line.startswith("# ") or line.startswith("## "):
            out.append("##" + line)
        else:
            out.append(line)
    return "\n".join(out)


if st.session_state.get("spec_markdown"):
    st.markdown(_cap_heading_sizes(st.session_state["spec_markdown"]))
    if st.session_state.get("spec_bundle"):
        st.download_button(
            "⬇ Download spec + sources (bundle)",
            data=st.session_state["spec_bundle"],
            file_name=st.session_state.get("spec_filename", "validation_spec.md"),
            mime="text/markdown",
            type="primary",
        )


# ---------------------------------------------------------------------------
# Critic Panel — a simulated advisory review of the generated spec.
# Rendered OUTSIDE the submit branch, gated on a spec existing in session memory,
# so clicking the button (which reruns the page) doesn't wipe the spec.
# ---------------------------------------------------------------------------
_PERSONA_LABEL = {
    "regulator": "🏛️ Regulator (FDA-reviewer mindset)",
    "biostatistician": "📊 Biostatistician",
    "clinical_scientist": "🔬 Clinical Scientist",
}
_SEVERITY_LABEL = {"blocking": "🔴 Blocking", "minor": "🟡 Minor"}


def render_grounding_audit(result, grounded_context):
    """Show the anti-fabrication net: every registry ID the panel cited, checked
    against the retrieved evidence. Warn-only — the panel is advisory."""
    audit = critic_panel.grounding_audit(grounded_context, result)
    if not audit:
        return
    present = [a for a in audit if a["in_evidence"]]
    missing = [a for a in audit if not a["in_evidence"]]
    header = (f"🔍 Grounding audit — {len(audit)} identifier(s) cited · "
              f"{len(present)} ✓ in evidence · {len(missing)} ⚠ not in evidence")
    with st.expander(header, expanded=False):
        st.caption(
            "Every study / trial / device identifier the panel named, checked against "
            "the retrieved records. A ⚠ is **not** automatically fabrication — the panel "
            "deliberately names missing identifiers to flag gaps in the plan. It's a "
            "\"verify this\" marker; the only real concern is a ⚠ the panel presented as "
            "proof rather than as a gap. (Free-text FDA product codes aren't audited.)"
        )
        if missing:
            st.markdown("**⚠ Not in the retrieved evidence:**")
            for a in missing:
                st.markdown(f"- `{a['id']}` — {a['kind']}")
        if present:
            st.markdown("**✓ Confirmed in the retrieved evidence:**")
            for a in present:
                st.markdown(f"- `{a['id']}` — {a['kind']}")


def render_panel(result, grounded_context):
    st.warning(
        "⚠️ This is a **simulated advisory review** to help you stress-test your plan "
        "before a real review. It is **not** an official regulatory determination and "
        "does not guarantee any outcome."
    )
    for member in result.get("panel", []):
        label = _PERSONA_LABEL.get(member.get("persona"), member.get("persona", "Reviewer"))
        with st.expander(label, expanded=True):
            if member.get("strength"):
                st.markdown(f"**✅ Strength:** {member['strength']}")
            for crit in member.get("critiques", []):
                sev = _SEVERITY_LABEL.get(crit.get("severity"), crit.get("severity", ""))
                st.markdown(f"**{sev}** — {crit.get('issue', '')}")
                if crit.get("evidence_basis"):
                    st.caption(f"Basis: {crit['evidence_basis']}")
    fixes = result.get("fix_before_submission", [])
    if fixes:
        with st.container(border=True):
            st.markdown("### 🔴 Fix before submission")
            for i, f in enumerate(fixes, 1):
                st.markdown(f"{i}. {f}")
    render_grounding_audit(result, grounded_context)


if st.session_state.get("spec_markdown"):
    st.divider()
    st.subheader("📋 Simulated advisory review panel")
    st.caption(
        "Convene three Claude-played experts — a Regulator, a Biostatistician, and a "
        "Clinical Scientist — to stress-test the spec above before a real reviewer sees "
        "it. They may only cite the evidence that was retrieved; they never invent studies."
    )
    if st.button("Convene review panel", type="primary"):
        client = get_client()
        if client is None:
            st.error("No Anthropic API key found — add it to `.streamlit/secrets.toml` and rerun.")
        else:
            with st.spinner("Convening the review panel…"):
                try:
                    parsed, final, raw = critic_panel.run_panel(
                        client,
                        st.session_state.get("grounded_context", ""),
                        st.session_state["spec_markdown"],
                    )
                except anthropic.APIStatusError as e:
                    st.error(f"API error {e.status_code}: {e.message}")
                    parsed, final, raw = None, None, ""
                except anthropic.APIConnectionError:
                    st.error("Network error reaching the Anthropic API. Check your connection and retry.")
                    parsed, final, raw = None, None, ""
            if final is not None and final.stop_reason == "refusal":
                st.error(
                    "The review panel request was declined by the model's safety system, and "
                    "the fallback model also declined. Try again, or rephrase the clinical context."
                )
            elif parsed is None:
                st.warning("The panel returned a response that couldn't be parsed as a review. Try again.")
                if raw:
                    with st.expander("Raw panel response (debug)"):
                        st.code(raw)
            else:
                st.session_state["panel_result"] = parsed

    if st.session_state.get("panel_result"):
        render_panel(st.session_state["panel_result"],
                     st.session_state.get("grounded_context", ""))
