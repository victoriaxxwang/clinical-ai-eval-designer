# Architecture — Clinical AI Eval Designer

**Version:** 3 · 2026-07-08

### Changelog
- **v1 (2026-07-07)** — Initial. Runtime retrieval was the Anthropic API `web_search` server tool only.
- **v2 (2026-07-07)** — Added the live-registry pipeline (ClinicalTrials.gov / openFDA / PubMed); citations verifiable by construction.
- **v3 (2026-07-08)** — Consolidated into a single canonical doc under the **"Core First, Agents Later"** framing. Merged the former `SYSTEM_ARCHITECTURE_FUTURE_STATE.md` (Phase 2) and folded the integration code into an appendix. Structural checks reclassified as deterministic (not an agent).

> **Design principle — "Core First, Agents Later."** Build a bounded,
> deterministic core that is trustworthy on its own. Layer autonomous agents on
> top *only after* the core passes rigorous testing — never as a replacement for
> it, and always inheriting its constraints. If the core isn't trustworthy alone,
> no agent orchestration fixes it. **Phase-gate rule: no agent logic is written
> until Phase 1 is production-grade and validated.**

---

## The three roles of Claude

Three distinct products get called "Claude." Keep them separate in the write-up.

| Where | Which Claude | What it does |
|---|---|---|
| Discovery / R&D | **Claude Science** (workbench at claude.ai) | Manual proof-of-concept: the 48-paper HRV synthesis. Where the concept was proven. **Not called by the app.** |
| Building the app | **Claude Code** | Wrote `app.py`, the constraint-layer prompt, the registry pipeline. |
| Runtime engine | **Anthropic API — Claude Fable 5** | Synthesizes retrieved records into the constrained 8-field spec. |

**Honest framing:** the running app does **not** call Claude Science — there is
no programmatic Claude Science endpoint. The runtime is *direct registry APIs +
the Anthropic API (Fable 5)* — an automated, programmatic mirror of the Claude
Science discovery workflow. The registries, not the model's memory, are what make
citations real.

---

## Phase 1 — The Core Deterministic Engine (built, strict priority)

A straight-line pipeline. Same inputs → same retrieval → constrained synthesis.
No open-ended agent loops. This must be rock-solid before any Phase 2 work.

```
[ User input ]  (AI model · clinical use case · patient population · healthcare setting · optional URL)
        │
        ▼
1. Synthesis / retrieval layer  — deterministic, cost-free, verifiable
        • ClinicalTrials.gov API v2   → study designs, endpoints, enrollment (NCT IDs)
        • openFDA device APIs         → classification + 510(k)/De Novo (K-numbers, product codes)
        • PubMed E-utilities          → literature (real PMIDs)
        • optional reference URL      → clean text extraction
        │
        ▼
2. Grounded Reference Context  — labelled, size-capped raw records
        │
        ▼
3. Claude Fable 5  — the constraint + synthesis layer ONLY
        • system prompt = constraint layer: no invented numbers, cite-or-flag,
          confidence tiers, expert-review flags
        • maps real records into the 8-field structure (does not recall facts)
        │
        ▼
[ Structured 8-field validation spec ]  + confidence + certifies/does-not + real citations
```

**Determinism boundary.** The retrieval half is fully deterministic and free
(public APIs). The synthesis half is the model — bounded by the system prompt,
grounded by the retrieved records, honest about confidence. The design goal is
near-zero non-deterministic variance in *what evidence* enters the spec; the
model's job is to map and constrain that evidence, not to source it.

**Current implementation:** the deterministic retrieval layer lives in
`engine.py` (importable, no UI, unit-tested in `test_engine.py`) —
`build_queries`, `search_clinicaltrials`, `search_openfda`, `search_pubmed`,
`fetch_url_text`, `build_grounded_context`. `app.py` is the Streamlit UI +
`generate_spec` (the Fable 5 synthesis call). Phase 1 emits a **bundle**: the
spec plus the source records it was grounded on, so evidence travels with the
artifact (the clean seam into Phase 2). Code detail in the Appendix.

### What each field is grounded in
| Output field | Primary grounding source |
|---|---|
| Study Design | ClinicalTrials.gov (comparable designs, allocation, masking) |
| Sensor / Input Validation | PubMed + web (device/acquisition validity) |
| Performance Benchmarks | PubMed + web (reported metrics by regime) |
| Ground Truth Strategy | PubMed + trial reference standards |
| Sample Size | ClinicalTrials.gov enrollment of comparable studies |
| Subgroup Requirements | PubMed (population-specific validity threats) |
| Regulatory Pathway | openFDA (product codes, predicates, 510(k)/De Novo) |
| Post-Deployment Monitoring | PubMed + web (drift / monitoring precedent) |

### Honesty guardrails (what the app does *not* claim)
- Registry coverage is best-effort. A nil result is reported as "no matching record retrieved," and the model lowers confidence rather than asserting the benchmark doesn't exist.
- Web search returns real pages but not structured database records — the model prefers registry identifiers and never fabricates one.
- Every field carries a confidence tier and an expert-review flag. This is a grounded starting point, not a substitute for expert sign-off.

---

## Phase 2 — Asynchronous Agentic Expansion (future state)

Introduced **only after Phase 1 is validated and stable.** Two decoupled tracks
run in parallel or post-generation. Neither may invent facts — both inherit the
Phase-1 constraint layer.

### 1. Multi-Agent Critic & Self-Healing Loop (asynchronous verification)

An evaluation layer at the end of the deterministic line:

- **Clinical Integrity Agent (LLM).** The one component that genuinely needs a
  model. Checks the generated output against the raw retrieved literature / FDA
  guidance to flag missing citations, source misrepresentation, or a
  HIGH-confidence field backed only by tangential evidence.
- **Structural Constraints check (deterministic code, *not* an agent).** Field
  counts, schema, markdown-table formatting, prompt-rule compliance are format
  checks — a plain validator is cheaper and 100% reliable where an LLM would
  drift. Keeping this in the deterministic layer is *more* faithful to the
  Core-First philosophy than making it an agent.
- **Self-Correction Loop.** If either check flags a flaw, the system feeds the
  critique + draft back to the generator for a self-healing second pass before
  user exposure. Converges when checks pass, or escalates to a human after N
  iterations — never loops forever, never silently accepts. Implementation
  options: the SDK tool runner (code-orchestrated loop) or Managed Agents with an
  Outcome + rubric (platform runs iterate→grade→revise).

### 2. Autonomous Competitive Intelligence Agent (parallel track)

Runs an unstructured discovery workflow alongside the clinical core, **physically
separated** so market framing never contaminates the clinical spec.

- **Dynamic Market Scouting:** takes population + disease area, queries active
  market landscapes (ClinicalTrials.gov, openFDA clearances, public sources) for
  direct competitors.
- **Automated SWOT matrix:** synthesizes competitor profiles across *Patient
  Population Overlap*, *Clinical Advantages*, and *Strategic Disadvantages (Your
  Moat)* — e.g. high patient burden or slow enrollment in competing DCTs.
- **Value-Proposition Synthesis:** surfaces targeted strategic insight — e.g.
  *"Competitor X's recruitment weakness in this indication means your
  decentralized design gives a distinct speed advantage."*

Its guardrails are about sourcing and dating claims, not clinical safety — a
different rulebook from the core.

### The Phase-1 → Phase-2 seam (design decision to make now)
The critics need exactly two inputs: the **8-field draft** and the **raw source
records** it was grounded on. So Phase 1 should emit both as a single bundle
(persist `grounded_context` alongside the spec). Then Phase 2 verifies
draft-against-sources without re-fetching, and the interface between phases is
just "that bundle." Small change now; keeps the seam clean later.

### Guardrail inheritance (non-negotiable)
Every Phase-2 component inherits the Phase-1 constraint layer verbatim: no
invented numbers, cite-or-flag, confidence tiers, expert-review flags. Agents may
critique, reorganize, and broaden — never relax a core constraint. An agent that
would need to invent a threshold to "improve" the spec must instead flag it for
expert input.

---

## Appendix — Integration paths (code detail)

The retrieval engine can run two ways; the app uses **both** (B as the backbone,
A as an optional gap-filler).

| | Path A — `web_search` server tool | Path B — public registry APIs |
|---|---|---|
| Runs on | Anthropic's servers | Your Python (`requests`) |
| Cost | API credits | **Free** |
| Determinism | Best-effort | **Deterministic** |
| Identifiers | Model-transcribed | Returned by the database (verifiable) |
| Best for | Filling web gaps (FDA guidance PDFs) | The citable backbone |

### Path A — `web_search` server tool (Streamlit boilerplate)
```python
tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 6}]

with client.beta.messages.stream(
    model="claude-fable-5",
    max_tokens=32000,
    betas=["server-side-fallback-2026-06-01"],      # opt-in refusal fallback
    fallbacks=[{"model": "claude-opus-4-8"}],        # Fable → Opus 4.8
    output_config={"effort": "high"},                # Fable: no `thinking` param (400)
    tools=tools,
    system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": user_message}],
) as stream:
    for chunk in stream.text_stream:
        ...  # render incrementally
    final = stream.get_final_message()
```

### Path B — public registries via `requests` (deterministic, free)
```python
def search_clinicaltrials(term, max_studies=6, timeout=12):
    r = requests.get("https://clinicaltrials.gov/api/v2/studies",
                     params={"query.term": term, "pageSize": max_studies}, timeout=timeout)
    r.raise_for_status()
    for s in r.json().get("studies", []):
        ps  = s.get("protocolSection", {})
        idm = ps.get("identificationModule", {})   # nctId, briefTitle (NOT officialTitle — often missing)
        dm  = ps.get("designModule", {})           # studyType, enrollmentInfo.count, designInfo
        ...
```
Same pattern for **openFDA** (`/device/classification.json`, `/device/510k.json`
— product codes, K-numbers) and **PubMed** (`esearch.fcgi` → id list →
`esummary.fcgi` — real PMIDs). Wrap each in try/except for `requests.Timeout` /
`requests.RequestException`; a nil result → "no matching record retrieved" and
lower confidence. Field paths verified live 2026-07 (NCT03831841, live PMIDs,
openFDA product code QEX).
