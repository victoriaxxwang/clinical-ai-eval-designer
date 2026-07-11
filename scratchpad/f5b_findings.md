# F5b — live before/after verdict (frozen vs wide-net, end-to-end)

*Option-1 Phase-2 experiment. Ran ONE mechanism-first, single-disease case
(heart-failure deterioration model) through BOTH engines all the way to the
generated 8-field spec + 3-persona critic panel, then diffed. The frozen engine
(`engine.py`) was never touched; the wide-net twin lives in
`experimental/engine_widenet.py`. Tripwire `2e6d49cdaa3106b6c29ee66b5df37e58`
clean at start and end of the run.*

**Case:** `heart_failure_mechanism_first` — disease named only in the last clause
of the model description; the use case names no disease (the buried-disease
scenario). Effort = medium. Both arms: no refusal.

## Headline

The two specs came out **near-identical in size and structure** (frozen 17,004
chars / wide-net 17,246; same 8 fields; **both flagged exactly 6 blockers**). The
difference is not *how much* was produced — it is **what evidence the whole
downstream chain got to reason over.** The story is in three layers.

## Layer 1 — Retrieval (stark)

| | Frozen (shipped) | Wide-net |
|---|---|---|
| Disease surfaced | ❌ never | ✅ "Heart Failure" (D006333) + 4 synonyms |
| Literature query | `gradient boosted ensemble ingests` | `("Heart Failure" OR "Cardiac Failure" OR …) AND gradient AND boosted` |
| Literature returned | 15 **off-target** ML papers (wind/solar forecasting, phishing detection, malware, fish aquaculture, atmospheric turbulence) | ~11 **real HF** papers (30-day HF readmission, HFpEF mortality, AI HF detection, gradient-boosting-for-HF) |

## Layer 2 — The spec (the honest nuance)

The frozen spec is still an **honest** document: the cite-or-flag discipline forces
it to disclose its own failure — it opens with *"the grounded context returned
largely off-topic records… Confidence is correspondingly reduced throughout."* It
never fabricates HF evidence it doesn't have. The difference is what each can
**cite**:

- **Frozen** — "closest analogues" are PMID 42327625 (**AKI** prediction) and
  PMID 36220875 (**diabetes**), which it must then disclaim as un-transplantable.
- **Wide-net** — cites real HF studies **by name** (Golas 2018 / PMID 29929496,
  Frizzell 2016 / 27784047, Mortazavi 2016 / 28263938, Angraal HFpEF 2019 /
  31606361, 2025 HF-risk-model review / 41357488) and grounds a realistic
  benchmark ("C-statistics ~0.6 range for HF readmission").

## Layer 3 — The critic panel (the "aha")

Same 6 blockers each, but **qualitatively different order**:

- **Frozen critics spend a whole blocker on the plumbing:** *"the predicate
  landscape was never actually searched… re-run with indication-based terms."*
  The shipped system's own panel independently detected the buried-disease miss —
  and demanded exactly what the wide-net engine does.
- **Wide-net critics skip that and escalate to HF-specific science:** SMOTE-induced
  miscalibration (grounded in the retrieved HF SMOTE paper, OpenAlex W3134537993),
  endpoint circularity (the model's own alerts trigger the rapid-response events
  that are its outcome), lead-time vs. the ward's real vitals cadence.

**One line:** the wide net turns the conversation from *"your search missed the
disease, re-run it"* into *"here are the real HF studies — now let's argue about
SMOTE calibration."* Same rigor budget, spent one level higher.

## The honest limitation

The recovery is **entirely in the literature layer.** The openFDA device sections
are **byte-for-byte identical** between the two arms, because the openFDA path is
driven by generic device keywords pulled from the model text
(`['gradient','acute','care','inpatient','boosted']`), **not** by the disease —
and the wide-net change never touched that path. Both specs therefore still
correctly say *"no on-point FDA predicate retrieved."*

**Wide-net fixes literature grounding, not FDA-predicate grounding.** FDA records
are indexed by device **product codes / indications**, not disease MeSH headings,
so recovering them needs an **indication → product-code bridge** (the mapping the
goldens already do by hand, e.g. sepsis EWS → product code SAK), not just a wider
net over the same text. This is a clean, honest Phase-2 next step — bigger than the
literature fix, and explicitly scoped as future work.

## Why this is a good result for the submission

It demonstrates **both** things at once:
1. **Honesty of the shipped system** — even mis-grounded, it flags its own
   under-grounding and never fabricates (the trust story).
2. **Value of the wide net** — it lifts the whole evidence chain onto the right
   disease, which in turn lifts the critic panel from plumbing critiques to
   clinical-science critiques.

**Outputs (scratchpad/):** `f5_frozen_context.txt` / `f5_widenet_context.txt`
(retrieval), `f5_frozen_spec.md` / `f5_widenet_spec.md` (specs),
`f5_frozen_panel.json` / `f5_widenet_panel.json` (panels), `f5b_summary.json`
(compact summary), `f5b_run.log` (run log). Harness: `f5_harness.py`.
