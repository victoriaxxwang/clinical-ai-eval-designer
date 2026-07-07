# Architecture — Clinical AI Eval Designer

**Version:** 2 · 2026-07-07
**Rendered HTML:** `ARCHITECTURE.html` (same version)

### Changelog
- **v1 (2026-07-07)** — Initial architecture. Runtime retrieval was the Anthropic
  API `web_search` server tool only (grounded web search, not structured database
  queries). Documented the three roles of Claude and flagged that citation
  identifiers still needed verification.
- **v2 (2026-07-07)** — Added the live-registry data pipeline. The app now queries
  **ClinicalTrials.gov, openFDA, and PubMed directly** before prompting the model,
  and injects the retrieved records as *grounded reference context*. Identifiers
  (NCT / PMID / 510(k) K-numbers / product codes) now come back from the databases
  themselves, so citations are verifiable by construction. Web search is retained
  as an optional supplement for sources the registries don't cover.

> **Versioning convention:** each meaningful edit to the architecture bumps the
> version number in this header and adds a changelog entry. `ARCHITECTURE.md` and
> `ARCHITECTURE.html` always share the same version number — edit the `.md`, then
> re-render the `.html` to match.

---

## The three roles of Claude in this project

There are three distinct things people call "Claude," and conflating them will
get a claim challenged by judges who know the products. Keep them separate in the
write-up.

| Where | Which Claude | When | What it does |
|---|---|---|---|
| **Discovery / R&D** | **Claude Science** (interactive workbench at claude.ai) | Before the hackathon build | Manual proof-of-concept: the 48-paper HRV synthesis. Where you *found* that literature synthesis for a validation spec can be automated. **Not called by the app.** |
| **Building the app** | **Claude Code** | July 7 | Wrote `app.py`, the constraint-layer system prompt, the registry retrieval pipeline, repo structure. |
| **Runtime engine** | **Anthropic API — Claude Fable 5** | Every Generate click | Synthesizes the retrieved records into the constrained 8-field spec. |

**Honest framing:** the running app does **not** call Claude Science — there is
no programmatic Claude Science endpoint. Claude Science was the *discovery
engine* that proved the concept. The *productized* runtime is direct registry
APIs + the Anthropic API (Fable 5). The registries — not the model's memory — are
what make citations real.

---

## Runtime data pipeline (v2)

```
[ User Input ]  (AI model · clinical use case · patient population · healthcare setting)
      │
      ▼
1. Fetch raw data ──► [ External registry APIs ]
      │                 • ClinicalTrials.gov API v2  → study designs, endpoints, enrollment (NCT IDs)
      │                 • openFDA device APIs         → classification + 510(k)/De Novo (K-numbers, product codes)
      │                 • PubMed E-utilities          → literature (real PMIDs)
      ▼
2. Assemble "Grounded Reference Context"  (raw records, clearly labelled, capped in size)
      │
      ▼
3. Synthesize ──► [ Anthropic API — Claude Fable 5 ]
      │              • constraint layer (system prompt): no invented numbers,
      │                cite-or-flag, confidence + expert-review tiers
      │              • optional web_search server tool fills registry gaps (FDA guidance PDFs, etc.)
      │              • auto-fallback → Opus 4.8 on a safety false-positive
      ▼
[ Structured 8-field validation spec ]  + confidence flags + certifies/does-not + real citations
```

**Why this ordering matters:** the registries are queried *first*, and their
records are handed to Fable as source material. Fable's job is to *map and
synthesize* real records into the 8-field structure — not to recall facts. An
identifier it cites came back from a database this run, not from training memory.

---

## What each field is grounded in

| Output field | Primary grounding source |
|---|---|
| Study Design | ClinicalTrials.gov (comparable trial designs, allocation, masking) |
| Sensor / Input Validation | PubMed + web (device/acquisition validity literature) |
| Performance Benchmarks | PubMed + web (reported metrics by regime) |
| Ground Truth Strategy | PubMed + trial reference standards |
| Sample Size | ClinicalTrials.gov enrollment counts of comparable studies |
| Subgroup Requirements | PubMed (population-specific validity threats) |
| Regulatory Pathway | openFDA (product codes, predicates, 510(k)/De Novo) |
| Post-Deployment Monitoring | PubMed + web (drift / real-world monitoring precedent) |

---

## Honesty guardrails (what the app does *not* claim)

- Registry coverage is best-effort. A query that returns nothing is reported as
  "no matching record retrieved," and the model must lower its confidence rather
  than assert the benchmark doesn't exist.
- Web search results are real pages but not structured database records — the
  model is told to prefer registry identifiers and never fabricate one.
- Every field carries a confidence tier and an expert-review flag. The tool is a
  structured, grounded starting point — not a substitute for expert sign-off.

---

## Roadmap (next versions)

- **v3 (planned):** add ClinicalTrials.gov endpoint/statistical-plan extraction to
  auto-populate a Statistical Analysis Plan (SAP) skeleton.
- **v3+:** IRB submission template and Q-Sub outline pre-populated from the
  generated spec (the workflow-integration moat).
