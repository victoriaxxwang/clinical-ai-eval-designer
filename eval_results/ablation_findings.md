# Door B — Ablation findings (pilot-3 slate)

_2026-07-09 (Case 6 melanoma added 2026-07-09). 6 cases (HRV / DR / warfarin / sepsis / AFib / melanoma) × 6 configs, scored **precision + recall**
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
| sepsis | 0 | **2** | incl. PMID 26246167 / DOI 10.1126/scitranslmed.aab3719 (TREWScore, *Sci Transl Med* 2015) |
| HRV | 0 | 0 | — (pure Lesson-2: golden papers rank in no provider) |

- On 3 of 4 cases, **OpenAlex recovers a genuinely load-bearing golden paper that
  Europe PMC's ranking misses**; on the fourth (HRV) it's inert but never harmful.
- **Semantic Scholar adds nothing beyond OpenAlex** on any case (baseline ==
  `lit_epmc_openalex` everywhere). Keep it — harmless, may help future cases — but
  **OpenAlex is the discriminating provider**.
- **Decision:** keep the multi-provider literature layer. Tier B (1) validated.

### 2. MeSH expansion level (canonical / canonical+synonyms [shipped] / +hierarchy) — **STILL INERT — but Case 4 found *why*, and it's a bug**
- Golden recall is **flat across all three levels on all four cases**, sepsis included.
- On pilot 3 the reason was benign: all three conditions anchor on **leaf** MeSH terms
  → `+hierarchy` has no child descriptors to add → it no-ops **by design**.
- **Sepsis was added specifically to break that** — Sepsis (MeSH **D018805**) is a
  *broad parent* with 6 children (Bacteremia, Fungemia, Neonatal Sepsis, Parasitemia,
  Septic Shock, Viremia). It should have made `+hierarchy` diverge. It didn't — and the
  snapshot shows **MeSH normalization resolved to "none" at all three levels**, so
  hierarchy had nothing to expand. See the Case-4 finding below: the bare condition
  token never reached the MeSH lookup, so even a resolvable broad parent was missed.
- Synonyms *do* change retrieval **breadth** (HRV baseline 11 PMIDs vs canonical-only
  8) but none of the extra papers are golden here, so the score doesn't move.
- **Net:** the `+hierarchy` axis remains **genuinely untested end-to-end** — not because
  broad parents don't exist, but because a candidate-construction bug prevents the bare
  condition from being looked up. Fixing that (below) is the prerequisite for a real
  hierarchy test; **pneumonia (Case 8) is the next broad-parent and will hit the same wall.**
  Shipped default (canonical+synonyms) stays safe — widens the net without hurting precision.

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
| Product codes | DR 1/1 · HRV 2/7 · warfarin 0/5 · **sepsis 0/9** | Imaging class (PIB) maps cleanly; wellness classes (PWC/SEN) partial; genotyping codes (ODW/ODV/NSU/GJS/KQG) don't surface on drug terms; sepsis returns biomarker-assay codes (NTM/QFS/QUT, "…Sepsis Risk Assessment" in device_name) but **not the software code SAK** |
| 510(k) K-numbers | warfarin 3/7 · DR 0/6 · HRV 0/1 · **sepsis 0/0** | Genotyping 510(k)s partially rank; named follow-on clearances (incl. Bayesian Health K250680) don't |
| De Novo | DEN180001 missed (DR) · **DEN230036 missed (sepsis)** | `submission_type_id:3` check doesn't surface IDx-DR's or Prenosis ImmunoScore's grant on these terms |
| Pivotal trials | warfarin 0/3 · DR 0/4 · **sepsis 0/5** | Named trials (COAG/EU-PACT/GIFT; DR pivotals; TREWScore/Epic/Bayesian sepsis trials) don't rank in generic relevance search — sepsis worst-hit, 5 specific trials buried in an enormous sepsis corpus |
| Originator NDA | NDA009218 missed | Drug sweep returns current-marketing NDAs, not the 1954 Coumadin originator |

**Interpretation:** named records don't rank in generic registry searches, and the
config axes we can sweep don't move that. The honest next lever is **query targeting**
(seed known device names / trial acronyms), **not** a config change. This is the
recall ceiling the ablation diagnosed.

## Case 4 (sepsis) — two *query-construction* findings the ablation surfaced
Sepsis was added as the first **broad-parent + regulatory-positive-EHR** case. It behaved
as expected on literature (OpenAlex recovers TREWScore, above) but exposed **two distinct
bugs in how the engine builds its condition query** — both the same root cause: *the
atomic condition token can fall out of the query.* Neither is a config knob; both are
input/authoring lessons **and** candidate engine-hardening items.

**Finding A — mechanism-first phrasing collapses retrieval to 0 (the headline).**
A natural, mechanism-led description — *"Algorithm that continuously analyzes routinely-
collected EHR time-series … to predict … sepsis"* — buries the word **"sepsis" past
position 12**, and `build_queries` takes the condition from `_keywords(model_desc, 12)`.
So "sepsis" never entered the MeSH candidates, the openFDA terms, or the query. Result:
query = *"continuously analyzes routinely collected"*, MeSH = none, openFDA terms = junk,
**0 recall everywhere** — even though SAK is literally a sepsis device and Sepsis-3 is
landmark. *Worked around on the input side* by re-authoring the case **condition-forward**
(*"Sepsis early-warning algorithm that…"*), which is how the swept numbers above were
produced. **This affects real users who describe their system mechanism-first**, and is
why Cases 5–10 are all authored condition-forward.

**Finding B — the bare condition token gets crowded off the MeSH candidate list.**
*Even after* the condition-forward rewrite, MeSH still resolved to **none**. Cause:
`_mesh_candidates(…, max_candidates=5)` emits condition-*anchored bigrams first*
(`inpatient sepsis`, `sepsis early`, `early warning`, `warning clinical`,
`warning continuously`) and appends the **bare** token (`sepsis`) only *after* — so on a
verbose input the 5-slot cap fills with bigrams and **"sepsis" is truncated off before it
is ever looked up**. Proven live: `normalize_mesh(['sepsis'])` → **D018805 "Sepsis" + 6
children** (Bacteremia, Fungemia, Neonatal Sepsis, Parasitemia, Septic Shock, Viremia),
but `normalize_mesh([the 5 shipped bigrams])` → **None**. This is *why* the `+hierarchy`
axis no-ops on the one case built to exercise it (§2), and **pneumonia (Case 8) will hit
the identical wall**.

**Engine-hardening decision (deferred to its own work item):** both findings point to one
small fix — **guarantee the bare condition token is always tried** (prepend it to the MeSH
candidates and seed it into the query from the `use_case`, independent of model_desc word
order). Per the locked cadence, a shipped-engine change requires a full test re-run +
pilot-3 regression, so it is **not** bundled here. Logged for Victoria to schedule as a
standalone window. Until then: author every case condition-forward and accept that the
broad-parent hierarchy axis is not yet exercisable end-to-end.

## Case 5 (AFib) — leaf-term hierarchy no-op + the targeting ceiling, on a *positive* case
AFib (DTC wearable single-lead-ECG + PPG irregular-rhythm notification) is the first
**regulatory-POSITIVE device case with a null twist**: the QDA/QDB Class II codes exist with
active 510(k) lineages, but there is no authorization for an autonomous DTC *diagnosis* and
no PMA. It was authored **condition-forward** (Finding A avoided by construction). All 38
golden identifiers re-verified live 2026-07-09 before the sweep.

**Literature — OpenAlex is the discriminator again (now 4 of 5 cases).** Baseline recovers
exactly one golden paper, the landmark **Apple Heart Study** (PMID 31722151 / DOI
10.1056/NEJMoa1901183) — and `lit_epmc_only` drops it to **0**, while `lit_epmc_openalex`
restores it. Same signature as DR (IDx-DR), warfarin (PMID 28198005), and sepsis (TREWScore):
Europe PMC alone misses the single most important paper; OpenAlex is the add that recovers it.
Crossref-verify and the MeSH level leave the lit set unchanged (2 golden hits either way).

**MeSH `+hierarchy` no-ops — as designed (leaf term).** "Atrial Fibrillation" (MeSH D001281)
is a **leaf** descriptor (no narrower children), so `mesh_hierarchy == baseline` here. This is
the *benign* no-op the design predicted (INDEX: AFib=LEAF), distinct from sepsis's Finding-B
no-op (there the token never reached lookup). The genuine broad-parent hierarchy test still
awaits pneumonia (Case 8) **after** the engine-hardening fix lands.

**Deterministic 0/16 — the targeting ceiling, confirmed on a positive case.** Every scored
FDA/NCT identifier missed across all six configs: product codes QDA/QDB (0/2), De Novos
DEN180044/DEN180042 (0/2), the eight named 510(k) predicates (0/8), and the four pivotal
NCTs (0/4). The QDA/QDB *classification* device-names ("Electrocardiograph Software For
Over-The-Counter Use" / "Photoplethysmograph Analysis Software") don't contain the condition,
so a generic "atrial fibrillation + wearable" openFDA/CT.gov search never ranks them. This is
the **same query-targeting ceiling** as warfarin/DR/sepsis — and it now holds even when the
regulatory answer is a clean *positive*, reinforcing that the missing lever is seeding known
device names / product codes / trial acronyms, **not** any config knob.

## Case 6 (melanoma) — the OpenAlex pattern's *boundary*, a 2nd broad-parent no-op, and the first PMA case
Melanoma (photograph-in image-AI skin-lesion malignancy / biopsy-referral decision support) is
the slate's **first case with PMA numbers** (P090012 MelaFind, P150046 Nevisense) and a
**regulatory-POSITIVE case with a MODALITY-null twist**: three adjunctive Class II codes exist
(QZS via De Novo DEN230008; OYD/ONV under 21 CFR 878.1820) but *each uses a different physical
signal* — none is a photograph-input image-AI classifier, the exact system under eval. Authored
**condition-forward** (Finding A avoided). All 44 identifiers (17 PMID / 17 DOI / 3 codes / 1
DEN / 2 PMA / 2 scored NCT + 2 context-only) re-verified live 2026-07-09 before the sweep.

**Literature 0 across all six configs — the boundary of the OpenAlex story.** Unlike DR /
warfarin / sepsis / AFib, baseline recovers **zero** golden papers here, so the provider axis
has nothing to discriminate: `lit_epmc_only` and `lit_epmc_openalex` are both 0, same as
baseline. Melanoma joins **HRV** as the 2nd case where query targeting zeroes literature recall
*before* providers can matter. The correct cross-case statement is therefore: **OpenAlex is the
discriminator in every case whose golden literature is retrievable at all (4 of 6); in the other
2 (HRV, melanoma) the ceiling is query targeting and no provider/MeSH/verify knob moves it.**
Why melanoma zeroes out: its golden lit is a curated **landmark + reporting-standard** set
(Esteva *Nature* 2017, the ISIC data papers, DECIDE-AI, TRIPOD+AI) that the live
"skin-lesion malignancy" query doesn't rank into the top-15 recent hits — a golden=landmark
vs. retrieval=recent mismatch, not a provider gap.

**MeSH `+hierarchy` inert on a 2nd broad-parent — and inert at the *retrieval* level, not just
the score.** "Melanoma" (MeSH D008545) sits under the broader "Skin Neoplasms" (D012878), so
this is the second broad-parent point after sepsis. `mesh_hierarchy` is **identical to baseline**
— and not merely because lit recall is 0: the retrieved *set sizes* are unchanged too (pmids
n=14, dois n=15 in both). So `+hierarchy` adds nothing even where a broad parent genuinely has
children. (Caveat: with 0 golden lit overlap, the *score* can't move regardless; pneumonia
Case 8 — broad-parent **with** retrievable golden lit — remains the decisive `+hierarchy` test,
after the engine fix.)

**Deterministic 2/8 — targeting ceiling, but the first case it partly *hits*.** The query
surfaces the adjacent skin-device neighborhood and lands **OYD (MelaFind) + its PMA P090012**
(2 of 8), but misses the newest/most-specific grants — **QZS / DEN230008** (DermaSensor, the
2024 De Novo) and **ONV / P150046** (Nevisense, electrical-impedance) — plus both 2024+ pivotal
NCTs (0/2). Same lever as every prior case: the classification device-names don't carry the
condition, so a generic "melanoma / skin-lesion" openFDA search ranks the older/broader entries
and never reaches the two newest devices. The 2/8 (vs. AFib's 0/16, sepsis's 0/8) comes only
because the older MelaFind entry happens to sit on the generic query — not because config helped.

**Process note (my verify tool caught a real ambiguity).** The independent sweep flagged 4
literature IDs shared melanoma↔sepsis. They are **DECIDE-AI** (PMID 35585198) and **TRIPOD+AI**
(PMID 38626948) — discipline-wide reporting *standards*, not disease-specific findings, cited in
both specs' Field-1 study-design inventory. Handled exactly like shared FDA device-class codes:
a named `METHODOLOGY_SHARED` allowlist marks these as expected shared vocabulary, while any
*other* cross-case literature overlap still FAILs the sweep.

## What ships
- **Keep the shipped defaults** (canonical+synonyms / all-3-providers / verify-on):
  validated safe on 6 cases; OpenAlex earns its place **wherever golden lit is retrievable at
  all (4 of 6; HRV + melanoma zero out at query targeting first)**; MeSH + Crossref
  inert-but-harmless (MeSH `+hierarchy` now inert on **two** broad-parents, sepsis and melanoma).
- **Two engine-hardening items are now queued** from Case 4 (see above): (A) seed the
  condition from `use_case` so mechanism-first phrasing can't zero out retrieval, and
  (B) always try the bare condition token in MeSH so broad parents resolve. One small
  fix covers both; scheduled as its own window (ship + full regression), **not** bundled.
- **Remaining slate (Cases 5–10)** are authored **condition-forward** so Finding A can't
  bite. **Pneumonia (Case 8)** is the second broad-parent — it will re-confirm Finding B
  until the engine fix lands, after which it becomes the real `+hierarchy` test.
