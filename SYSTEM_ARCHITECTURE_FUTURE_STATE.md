# System Architecture — Future State

**Design principle: "Core First, Agents Later."**

Build a bounded, deterministic core that is trustworthy on its own. Only then
layer autonomous agents *on top of* that core — never as a replacement for it.
The core is what makes the output safe; agents make it broader and more
self-correcting, but they must inherit the core's constraints, not bypass them.

---

## Why this ordering

A clinical validation spec is a high-stakes artifact. An unconstrained agent that
"figures it out" is exactly the failure mode this product exists to prevent. So:

1. **Phase 1 (built / hardening):** a deterministic engine whose behavior is
   predictable, grounded, and auditable.
2. **Phase 2 (proposed):** agents that critique and improve the Phase-1 output,
   each with a narrow mandate and hard guardrails — plus a separate competitive
   intelligence track for the business layer.

If Phase 1 isn't trustworthy alone, no amount of agent orchestration fixes it.

---

## Phase 1 — The Core Bounded-Deterministic Engine (current)

A straight-line pipeline. Same inputs → same retrieval → constrained synthesis.
No open-ended agent loops.

```
[ User input ]  (AI model · clinical use case · patient population · healthcare setting · optional URL)
        │
        ▼
[ Programmatic retrieval ]  — deterministic, cost-free, verifiable
        • ClinicalTrials.gov API v2   → study designs, endpoints, enrollment (NCT IDs)
        • openFDA device APIs         → classification + 510(k)/De Novo (K-numbers, product codes)
        • PubMed E-utilities          → literature (real PMIDs)
        • optional reference URL      → clean text extraction
        │
        ▼
[ Grounded Reference Context ]  — labelled, size-capped raw records
        │
        ▼
[ Claude Fable 5 ]  — the constraint + synthesis layer ONLY
        • system prompt = constraint layer: no invented numbers, cite-or-flag,
          confidence tiers, expert-review flags
        • maps real records into the 8-field structure
        │
        ▼
[ Structured 8-field validation spec ]  + confidence + certifies/does-not + real citations
```

**Determinism boundary:** the retrieval half is fully deterministic and free
(public APIs). The synthesis half is the model — bounded by the system prompt,
grounded by the retrieved records, and honest about confidence. The model never
sources facts from memory; it maps records it was handed.

**Current implementation:** `app.py` — functions `search_clinicaltrials`,
`search_openfda`, `search_pubmed`, `fetch_url_text`, `build_grounded_context`,
`generate_spec`. See `CORE_ENGINE_INTEGRATION_BLUEPRINT.md` for code.

---

## Phase 2 — Asynchronous Agentic Expansion (proposed)

Agents that run *after* the Phase-1 draft exists and critique it. This is the
Multi-Agent Critic Framework. Each agent has one job and one lens; none can
invent facts (they inherit the Phase-1 constraint layer).

### The Multi-Agent Critic Framework

```
[ Phase-1 draft spec ]
        │
        ├─► Clinical Integrity Agent    ──┐
        ├─► Structural Constraints Agent ──┤──► [ Aggregated critique ]
        │                                  │
        ▼                                  ▼
[ Autonomous Self-Correction Loop ]  ◄─────┘
        │  (revise → re-critique → converge or escalate)
        ▼
[ Hardened spec + change log ]
```

**1. Clinical Integrity Agent**
- Mandate: does every quantitative claim trace to a retrieved citation? Are
  confidence tiers justified by the strength of the evidence actually retrieved?
  Are population-specific validity threats named correctly (physics/physiology,
  not optics)?
- Fails the draft on: any unsourced number, over-stated regulatory pathway, or a
  HIGH-confidence field backed by only tangential evidence.

**2. Structural Constraints Agent**
- Mandate: format and completeness. All 8 fields present, each with
  Recommendation / Rationale / Confidence / Expert-review. "Certifies / does not
  certify" section present and specific. No placeholder text.
- Fails the draft on: a missing field, a malformed flag, or generic boilerplate.

**3. Autonomous Self-Correction Loop**
- Feeds both agents' critiques back to the synthesis model, which revises only
  the flagged fields, then re-runs the critics.
- Converges when both critics pass, or escalates to a human after N iterations
  (never loops forever, never silently accepts).
- Implementation options (Anthropic API): the SDK **tool runner** for a
  code-orchestrated loop, or **Managed Agents** with an Outcome + rubric so the
  platform runs the iterate→grade→revise loop against explicit pass criteria.

### Autonomous Competitive Intelligence Agent (separate track)

Business-layer intelligence, decoupled from the clinical core. Runs on its own
cadence; never touches the validation spec's evidence.

- **Dynamic Market Scouting:** monitors ClinicalTrials.gov, openFDA clearances,
  and public sources for competing validation approaches and newly cleared
  devices in the same product code / indication.
- **Automated SWOT matrix:** for a given indication, assembles
  Strengths / Weaknesses / Opportunities / Threats from what was scouted (e.g.
  "3 competitors cleared via 510(k) predicate X; no De Novo precedent = Threat +
  Opportunity").
- **Value-proposition synthesis:** turns the SWOT into a positioning statement
  for that indication — what evidence would differentiate a new entrant.

This track uses the same retrieval primitives as the core, plus web search, but
its output is a market brief, not a clinical artifact — so its guardrails are
about sourcing and dating claims, not clinical safety.

---

## Guardrail inheritance (the non-negotiable)

Every Phase-2 agent inherits the Phase-1 constraint layer verbatim: no invented
numbers, cite-or-flag, confidence tiers, expert-review flags. Agents may
*critique, reorganize, and broaden* — they may never *relax* a core constraint.
An agent that would need to invent a threshold to "improve" the spec must instead
flag it for expert input. That rule is what keeps the agentic layer safe.
