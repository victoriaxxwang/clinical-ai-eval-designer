# Door B — Ablation findings (pilot-3 slate)

_2026-07-09. 3 cases (HRV / DR / warfarin) × 6 configs, scored **precision + recall**
vs the hand-verified goldens. Live retrieval snapshots cached under
`eval_results/contexts/` (git-ignored, regenerable). The scored table is the
auto-generated `eval_results/ablation_results.md` (rebuild anytime with
`python ablation_harness.py`); raw per-ID hits/misses are in
`ablation_results.json`. This file is the human interpretation — the harness
never overwrites it._

## Verdict per swept axis

### 1. Literature providers (+OpenAlex, +Semantic Scholar) — **EARNS ITS PLACE**
| Case | Europe PMC only | + OpenAlex | Golden paper OpenAlex recovers |
|---|---|---|---|
| warfarin | 0 | **2** | PMID 28198005 / DOI 10.1002/cpt.668 (pharmacogenomics) |
| DR | 0 | **2** | PMID 31304320 / DOI 10.1038/s41746-018-0040-6 (landmark IDx-DR, *npj Digit Med* 2018) |
| HRV | 0 | 0 | — (pure Lesson-2: golden papers rank in no provider) |

- On 2 of 3 cases, **OpenAlex recovers a genuinely load-bearing golden paper that
  Europe PMC's ranking misses**; on the third it's inert but never harmful.
- **Semantic Scholar adds nothing beyond OpenAlex** on any case (baseline ==
  `lit_epmc_openalex` everywhere). Keep it — harmless, may help future cases — but
  **OpenAlex is the discriminating provider**.
- **Decision:** keep the multi-provider literature layer. Tier B (1) validated.

### 2. MeSH expansion level (canonical / canonical+synonyms [shipped] / +hierarchy) — **INERT ON PILOT 3**
- Golden recall is **flat across all three levels on all three cases**.
- Reason: all three pilot conditions anchor on **leaf** MeSH terms → `+hierarchy`
  has no child descriptors to add → it no-ops **by design**.
- Synonyms *do* change retrieval **breadth** (HRV baseline 11 PMIDs vs canonical-only
  8) but none of the extra papers are golden here, so the score doesn't move.
- **Limitation, not a null result:** the MeSH axis is genuinely **untested** until a
  **broad-parent** condition (e.g. sepsis, pneumonia) enters the slate. Shipped
  default (canonical+synonyms) is safe — widens the net without hurting golden precision.

### 3. Crossref verify (on / off) — **PRECISION-NEUTRAL on goldens**
- `verify_off` == `baseline` on all three cases (drops **0** golden DOIs).
- It's a precision lever against unresolvable junk DOIs; the goldens' DOIs all
  resolve, so it neither helps nor hurts recall here. **Keep** — a correctness
  guarantee whose cost simply didn't bite.

## The real recall ceiling: query **targeting**, not config
Deterministic recall is **config-invariant** across the board — MeSH / provider /
verify barely touch it, because it comes from the openFDA keyword sweep + CT.gov
relevance rank, which the swept knobs don't reach. What lands vs. misses is about
query targeting:

| Category | Result | Note |
|---|---|---|
| Product codes | DR 1/1 · HRV 2/7 · warfarin 0/5 | Imaging class (PIB) maps cleanly; wellness classes (PWC/SEN) partial; genotyping codes (ODW/ODV/NSU/GJS/KQG) don't surface on drug terms |
| 510(k) K-numbers | warfarin 3/7 · DR 0/6 · HRV 0/1 | Genotyping 510(k)s partially rank; named follow-on clearances don't |
| De Novo | DEN180001 missed (0 DEN retrieved for DR) | `submission_type_id:3` check doesn't surface IDx-DR's grant on these terms |
| Pivotal trials | warfarin 0/3 · DR 0/4 | Named trials (COAG/EU-PACT/GIFT; DR pivotals) don't rank in generic relevance search |
| Originator NDA | NDA009218 missed | Drug sweep returns current-marketing NDAs, not the 1954 Coumadin originator |

**Interpretation:** named records don't rank in generic registry searches, and the
config axes we can sweep don't move that. The honest next lever is **query targeting**
(seed known device names / trial acronyms), **not** a config change. This is the
recall ceiling the ablation diagnosed.

## What ships
- **Keep the shipped defaults** (canonical+synonyms / all-3-providers / verify-on):
  validated safe; OpenAlex earns its place; MeSH + Crossref inert-but-harmless.
- **Next slate additions** (sepsis / AFib / pneumonia / …) should include at least one
  **broad-parent** condition to finally exercise the MeSH `+hierarchy` axis, and are
  the setting to test whether query targeting lifts the named-record recall ceiling.
