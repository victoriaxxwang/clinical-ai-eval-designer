# Door B — Ablation findings (pilot-3 slate)

_2026-07-09 (Case 10 fall-risk added 2026-07-09 — **SLATE COMPLETE, 10 of 10**). 10 cases (HRV / DR / warfarin / sepsis / AFib / melanoma / depression / pneumonia / pembrolizumab / fall-risk) × 6 configs, scored **precision + recall**
vs the hand-verified goldens. Live retrieval snapshots cached under
`eval_results/contexts/` (git-ignored, regenerable). The scored table is the
auto-generated `eval_results/ablation_results.md` (rebuild anytime with
`python ablation_harness.py`); raw per-ID hits/misses are in
`ablation_results.json`. This file is the human interpretation — the harness
never overwrites it._

## Bottom line (10 cases, up front)
_The one-screen version; the per-axis verdicts and per-case detail follow._

- **Slate:** 10 hand-verified goldens spanning device / drug / biologic / hybrid,
  regulatory-positive / null / mixed, and leaf vs broad-parent conditions;
  ~470 scored identifiers, all re-resolved live against their issuing registries.
  Scored **precision + recall**, never raw counts (counts always crown the widest,
  noisiest net — the exact failure these layers exist to prevent).
- **Headline — recall is capped by query *targeting*, not by any swept config.**
  Deterministic FDA/NCT recall is **config-invariant on all 10 cases**, and 6 of 10
  also zero out on literature before any provider / MeSH / verify knob can matter.
  Named records (pivotal NCTs, specific 510(k)s, De Novo grants) and
  **function-named FDA codes** (e.g. "Prioritization Software," which carries no
  disease token) don't rank in a generic disease search. The lever is a curated
  known-record **seed layer = a Phase-2 feature, not a config knob.**
- **What earns its place:** the multi-provider literature layer — **OpenAlex**
  recovers a load-bearing golden paper in exactly the **4 of 10** cases whose golden
  literature is retrievable at all (DR / warfarin / sepsis / AFib); Semantic Scholar
  is redundant-but-harmless; Crossref-verify is precision-neutral (drops **0** golden
  DOIs). **Keep the shipped defaults** (canonical+synonyms / all-3-providers / verify-on).
- **Honest negative — the MeSH `+hierarchy` axis remains UNVALIDATED.** It no-ops on
  all four broad-parent terms that reached the slate, but on the two built to test it
  decisively (sepsis, pneumonia) the no-op is caused by **Finding B** (the bare
  condition token is crowded off the MeSH candidate list before lookup), *not* by the
  axis being genuinely inert. It cannot be judged until the engine fix lands.
- **Next (its own window): the engine-hardening fix** — seed the bare condition from
  `use_case` (closes **Finding A**, mechanism-first phrasing zeroing retrieval) and
  always try the **bare condition token** in the MeSH lookup (closes **Finding B**),
  then **re-run pneumonia** to finally exercise `+hierarchy`. This is the single
  load-bearing prerequisite for judging the hierarchy axis end-to-end.

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

## Case 7 (depression) — the targeting ceiling as a *feature*: it lands the named landscape, misses the cross-indication precedent
Depression (a PHQ-9 / speech / passive-sensing **screening-triage** SaMD that flags adults for
assessment, does not diagnose) is a **regulatory-NULL case for the system under eval**: an openFDA
sweep returns **no product code, 510(k), De Novo, or PMA for a depression screening/detection
algorithm**. The scored FDA landscape is deliberately adjacent — depression *treatment* stimulators
(JXK, MUZ), a depression *therapy* software code (SAP; clearance K231209 Rejoyn), a behavioral-health
*pilot placeholder* (SIE), and the **De Novo precedent pathway drawn from other psychiatric
indications**: DEN200069 Cognoa ASD → code QPF (autism; 510(k) K243558 Canvas Dx) and DEN110019 NEBA
→ code NCG (ADHD-EEG). Authored **condition-forward** (Finding A avoided). All 42 identifiers
(15 PMID / 15 DOI / 6 codes / 2 K / 2 DEN / 2 NCT) re-verified live 2026-07-09 before the sweep.

**Deterministic 4/12 — the most *legible* targeting-ceiling result yet.** The query lands exactly
the three **depression-NAMED** codes — **JXK, MUZ, SAP** (3 of 6) — plus the small pilot trial
**NCT07220343** (n=25). It misses **precisely** the identifiers whose names *don't carry the word
"depression"*: **QPF and NCG** (the De Novo precedent codes live under **autism** and **ADHD-EEG**,
invisible to a depression query), the named grants **DEN200069 / DEN110019** (0 DEN retrieved at
all) and **K231209 / K243558** (0 of 6 retrieved K-numbers are golden), and the larger trial
**NCT06792175** (n=500). This is the targeting ceiling stated crisply: **a keyword search recovers
the on-condition landscape but cannot reach the *cross-indication regulatory precedent* that is the
entire analytical point of a null case.** No config touches it — baseline == every other config at
4/12. (This is the value-add a human/curated layer provides over generic retrieval, not a knob.)

**Literature 0 across all six configs — depression joins HRV + melanoma at the ceiling.** Baseline
recovers **zero** golden papers (~29 retrieved), so the provider axis again has nothing to
discriminate: `lit_epmc_only` (28 retrieved) and `lit_epmc_openalex` (29) are both 0, same as
baseline. The updated cross-case statement is now: **OpenAlex is the discriminator in every case
whose golden literature is retrievable at all (4 of 7 — DR, warfarin, sepsis, AFib); in the other 3
(HRV, melanoma, depression) the ceiling is query targeting and no provider/MeSH/verify knob moves
it.** Why depression zeroes out: its golden lit is a curated **methodology + reference-instrument**
set (STARD, TRIPOD+AI, DECIDE-AI, QUADAS-2, Riley sample-size, the PHQ-9 validation + IPD
meta-analysis, and the Obermeyer fairness precedent) — the same golden=landmark/standard vs.
retrieval=recent mismatch as HRV and melanoma, not a provider gap.

**MeSH `+hierarchy` inert again.** `mesh_hierarchy` == `mesh_canonical` == baseline (identical
retrieved-set sizes and 0 golden lit). "Depression" (D003863) / "Depressive Disorder" (D003866) do
carry children, but as with melanoma, with 0 golden-lit overlap the score cannot move regardless, so
this is **not** a decisive `+hierarchy` test. **Pneumonia (Case 8)** — a broad parent *with*
retrievable golden lit — remains the one that will actually exercise the axis, after the engine fix.

**Process note (verify tool caught two more methodology overlaps).** The independent sweep flagged
depression↔melanoma sharing **QUADAS-2** (PMID 22007046) and depression↔sepsis sharing **DECIDE-AI
(BMJ 2022)** (PMID 35584845). Both are discipline-wide reporting/risk-of-bias *standards*, not
disease-specific findings — added to the `METHODOLOGY_SHARED` allowlist (which now holds DECIDE-AI in
both its Nat-Med and BMJ instances, TRIPOD+AI, and QUADAS-2). Any *other* cross-case literature
overlap still FAILs the sweep.

## Case 8 (pneumonia) — the decisive `+hierarchy` test is *blocked by Finding B*, exactly as predicted
Pneumonia CXR triage/CADe (software that reads frontal chest radiographs to flag findings suspicious
for pneumonia and prioritize the worklist — *not* autonomous diagnosis) was reserved as **the one
case that could actually exercise the MeSH `+hierarchy` axis**: it is the slate's 2nd broad-parent
condition (MeSH **Pneumonia D011014**, 9 narrower children incl. Community-Acquired / Bacterial /
Aspiration) *and* — unlike melanoma/depression — its golden literature is a real imaging corpus, so
in principle a widened OR-group could pull in more of it. It is **regulatory-POSITIVE at the class
level with a pneumonia-specificity null twist**: the operative pathway exists and is directly
retrievable — Class II 510(k), **QFM** (21 CFR 892.2080, CADt prioritization) with **QAS**
(notification variant) and the **892.2090** CADe/CADx family (**QDQ / QBS**), plus a real cleared
predicate pool (K211733 Lunit / K241439 VUNO / K222179 Annalise / K232410 SmartChest / K192320
HealthCXR / K193300 AIMI-Triage) — but **no cleared device or code names *pneumonia* as its target
finding** (they target pneumothorax / effusion / trauma / general triage). Authored
**condition-forward** (Finding A avoided). All 62 identifiers (26 PMID / 26 DOI / 4 codes / 6 K)
re-verified live 2026-07-09 before the sweep.

**Everything zeros — and every zero is query *targeting*, config-invariant.** Deterministic **0/10**
and literature **0/26** across all six configs.

**(1) `+hierarchy` == baseline — Finding B confirmed a 2nd time; the axis is *still* untested.** This
is the headline. Pneumonia was built to test `+hierarchy`, and `mesh_hierarchy` == `mesh_canonical`
== `baseline` (identical retrieved sets, 0 golden lit). The snapshot's metadata line reads
`MeSH normalization: none … raw keywords used`. Root cause is exactly Case-4 Finding B: the pipeline's
`_mesh_candidates(max_candidates=5)` fills all five slots with condition-anchored **bigrams** —
`['chest radiograph', 'radiograph pneumonia', 'pneumonia triage', 'triage cade', 'triage analyzes']`
— and the **bare token "pneumonia" is crowded off the list before the NCBI lookup**. None of those
five bigrams is a MeSH heading, so `normalize_mesh` resolves to nothing and `+hierarchy` has **no
parent to expand**. Proven directly: `normalize_mesh(['pneumonia'])` returns the broad parent with
**9 children**, but the five bigrams the shipped path actually generates return none. So the case
reserved to exercise the axis **cannot** exercise it until the engine fix lands — Finding B now
blocks the `+hierarchy` conclusion on *both* broad-parents that were supposed to test it (sepsis and
pneumonia). This makes the deferred engine-hardening fix the single load-bearing prerequisite for
ever validating `+hierarchy`.

**(2) Deterministic FDA 0/10 — the CAD-software codes are unreachable by a disease query, by
construction.** The openFDA sweep searched device_name for `['analyzes', 'high', 'volume', 'hospital',
'chest']` and returned generic radiography-**hardware** codes (FMS, JEH, JWO, KDI, …) — **never** the
CAD-**software** codes QFM/QAS/QDQ/QBS, and **0** of the 6 named 510(k)s. The reason is structural and
worth stating plainly: FDA names these codes by *function*, not disease — QFM is "Radiological
Computer-Assisted **Prioritization** Software For Lesions," which contains **no disease token at
all**. A condition-forward query (or any disease keyword) therefore *cannot* surface QFM; only a
"computer-assisted / prioritization / triage" function token would. (A minor query-hygiene wart rides
along — `device` fell through to the filler verb "analyzes" because the CADt modality isn't in the
`_MODALITY` allowlist — but fixing that would not help, since the target device_names carry no disease
word to match on either.) This is the same **named-record / function-named-code targeting ceiling**
seen on every deterministic case since sepsis, here in its cleanest form.

**(3) Literature 0/26 — pneumonia joins the ceiling; providers have nothing to discriminate.** The
lit/ct query is clean and condition-forward (`chest radiograph pneumonia triage`), yet baseline
recovers **zero** golden papers (~26–28 retrieved), so `lit_epmc_only` and `lit_epmc_openalex` are
both 0 — no provider signal. The golden set is a curated **imaging-methodology + reporting-standard**
corpus (CLAIM, STARD-AI, the MRMC/CADe-CADx evaluation framework, dataset-shift + lifecycle-monitoring
papers, and a few pneumonia-detection-accuracy studies) — the same *golden = landmark/standard* vs.
*retrieval = recent-topical* mismatch as HRV/melanoma/depression, not a provider gap. **Updated
cross-case statement: OpenAlex is the discriminator in every case whose golden literature is
retrievable at all (4 of 8 — DR, warfarin, sepsis, AFib); the other 4 (HRV, melanoma, depression,
pneumonia) are capped by query targeting and no provider/MeSH/verify knob moves them.**

**Process note.** Pneumonia's scored literature is **fully disjoint** from all seven prior cases — the
independent sweep found **zero** cross-case pmid/doi/nct overlap (no new `METHODOLOGY_SHARED` entries
needed), even though it shares the *discipline* (imaging AI) with DR and melanoma. Clean separation.

## Case 9 (pembrolizumab) — the landmark-RCT-lit hypothesis, tested and *rejected*; a positive case that lands exactly one device on two axes
Pembrolizumab CDx selection (a **companion-diagnostic algorithm-plus-assay** that reads tumor tissue
to select cancer patients for pembrolizumab — the patient-selection decision support, *not* an
autonomous image diagnosis) is the slate's first **hybrid device + biologic** case, authored
`intervention_type="both"` so the sweep fires *both* the device pathway (the CDx assays) and the
drug/biologic pathway (the KEYTRUDA BLAs). It is **regulatory-POSITIVE** — the PD-L1 IHC companion
diagnostics are PMA-approved and pembrolizumab itself is BLA-licensed — **with a standalone-image-
predictor null twist** (no cleared device is an autonomous *image* classifier for this selection
task). Authored condition-forward. All 39 scored identifiers — 12 PMID / 12 DOI / 4 NCT / 3 CDx
product codes (PLS/PQP/QKQ) / 5 PMAs (P150013/P160002/P170019/P190032/P200006) / DEN170058 / 2 BLAs
(BLA125514/BLA761467 carried in `fda_nda_numbers`) — re-verified live 2026-07-09 before the sweep.
(The three gate-rejected candidates P170028 / OWH / QPV were kept **out** of the scored key, in a
non-scored `gate_rejected_not_scored` block.)

This case was reserved to test **one specific hypothesis**: unlike the curated-standards corpora of
HRV/melanoma/depression/pneumonia, pembrolizumab's golden literature is **landmark KEYNOTE RCTs**
(NEJM/JCO) — the kind of highly-cited paper a relevance-ranked search *might* actually surface. If
any zero-lit case were going to break the query-targeting ceiling, it was this one.

**The hypothesis is rejected — pembrolizumab joins the ceiling.** Literature **0/12 golden** of ~28
retrieved across all six configs; `lit_epmc_only` (26 retrieved) and `lit_epmc_openalex` (28) both 0,
so **OpenAlex has nothing to discriminate here either**. The reason is instructive and *not* "the
papers are too obscure": the query is **diagnostic-forward** (companion-diagnostic / patient-selection
/ PD-L1), while the KEYNOTE papers are indexed as **drug-efficacy** trials — so even landmark,
heavily-cited RCTs don't rank into a query about the *selection algorithm* rather than the *drug's
outcome*. The mismatch is topical, not popularity. **Cross-case statement is unchanged: OpenAlex is
the discriminator in exactly the 4 cases whose golden lit is retrievable at all (DR, warfarin, sepsis,
AFib); now 5 of 9 cases — HRV, melanoma, depression, pneumonia, and pembrolizumab — are capped at
query targeting before any provider/MeSH/verify knob can matter.**

**Deterministic 2/15, config-invariant — and the two hits are the *same device*.** The only golden
identifiers recovered are product code **PQP** (1/3) and PMA **P200006** (1/5) — both of which belong
to the **one** PD-L1 IHC pharmDx assay that a "cancer / PD-L1 / companion diagnostic" query naturally
ranks into. So a *positive* regulatory case surfaces exactly one device, landing it on both its
product-code axis and its PMA axis. Everything else misses for the by-now-familiar targeting reasons:
the other CDx assays (different codes PLS/QKQ, PMAs P150013/P160002/P170019/P190032), **DEN170058**
(0 DEN retrieved), the four KEYNOTE **NCTs** (0/4 — retrieved a single unrelated recent trial), and —
notably — **both KEYTRUDA BLAs** (0/2; the drug/drugsfda sweep returned `application=M019`, not
BLA125514/761467). The BLA miss is the drug-side face of the same ceiling: a diagnostic-forward query
never keys on "pembrolizumab / KEYTRUDA," so the biologic application doesn't surface even with the
drug pathway enabled.

**(MeSH) `+hierarchy` == baseline again** — inert, consistent with every prior case; with 0 golden
lit the axis can't move the score here regardless. Nothing about pembrolizumab changes the deferred-
engine-fix conclusion.

**Process note.** Pembrolizumab's only cross-case literature overlap is **TRIPOD+AI** (PMID 38626948 /
DOI 10.1136/bmj-2023-078378), already on the `METHODOLOGY_SHARED` allowlist from melanoma↔sepsis — a
discipline-wide reporting standard, *expected* to recur, **not** a copy-paste collision. No new
allowlist entries needed; the independent sweep passes (39/39 re-resolved live, offline consistency
PASS).

## Case 10 (fall-risk) — the regulatory-NULL control, and the tenth confirmation of the ceiling

Fall-risk is the slate's clearest **regulatory-NULL** case, reserved to test the opposite corner from
pembrolizumab's positive control: the system under evaluation is an **inpatient fall-risk _prediction_
algorithm** (EHR-driven decision support), and **no FDA authorization exists for it** — no 510(k), no
De Novo, no PMA for the predictive model itself. The golden's FDA identifiers are therefore **adjacent
prevention _hardware_**, carried deliberately as the regulatory landscape, not as an authorization for
the algorithm: product codes SEC (Class II wearable fall-injury-prevention airbag, 21 CFR 890.3780),
PJO / PJP / KMI / SBO (Class I bed-exit / patient-position / pressure-sensor hardware, 880.2400), plus
three named devices — DEN240021 (Active Protective Tango Belt), K141877 (Leaf patient-monitoring),
K233096 (PressureAlert). The correct answer for the *system under eval* is **"no authorization,"** and
the eval reports exactly that.

**Deterministic 3/8, config-invariant — and every hit is adjacent hardware, never an authorization.**
The only golden identifiers recovered are product codes **SEC / PJO / PJP** (3 of 5); **KMI and SBO
miss**, and **DEN240021 (0/1) plus both K-numbers (0/2) never rank** (0 retrieved on each). This is the
regulatory-null thesis landing cleanly: a "fall-risk prediction / inpatient" query surfaces only the
most *literally-named* prevention codes (SEC = "fall injury prevention"; PJO/PJP = generic bed/position
hardware) and **nothing that _is_ the predictive system — because nothing is**. The named devices miss
for the same query-targeting reason as every prior case (the Tango Belt, Leaf, and PressureAlert don't
key on a *prediction* query), which is exactly why a curated known-record seed layer is Phase 2, not a
knob. The 3 codes that do land are the regulatory *context*, correctly flagged as adjacent, not as
approval of the model.

**Literature ~3%, config-invariant, OpenAlex inert.** One golden paper is recovered — **PMID 30777849
/ DOI 10.2196/11505** (a JMIR digital-health fall study), the *same* paper on both the PMID and DOI
axes — of ~28 retrieved; `lit_epmc_only` returns the identical hit, so **OpenAlex has nothing to
discriminate here**. The other 29 golden papers are the by-now-familiar mismatch: the fall-risk golden
is a **methodology / reporting-standard + geriatric fall-scale (Morse, Hendrich, STRATIFY) + validation
-methodology** corpus, indexed as scale-derivation and prognostic-methodology work, while the query is a
condition-forward *prediction-algorithm* search — the landmark/standards-vs-recent-topical gap seen on
melanoma, depression, and pneumonia. **Fall-risk is the tenth case, and the sixth to zero out at query
targeting before any provider/MeSH/verify knob can matter** (HRV, melanoma, depression, pneumonia,
pembrolizumab, fall-risk).

**(MeSH) `+hierarchy` == baseline again** — inert, consistent with all nine prior cases; with a single
golden lit hit the axis cannot move the score regardless of whether the cause here is Finding B or plain
query targeting. Nothing about fall-risk changes the deferred-engine-fix conclusion.

**Process note.** Fall-risk had **three** cross-case literature overlaps, all *expected* shared
vocabulary rather than copy-paste: **TRIPOD+AI** (PMID 38626948 / DOI 10.1136/bmj-2023-078378, already
allowlisted — the discipline-wide reporting standard now recurring across four cases), plus two
**canonical methodology-caution landmarks** newly added to `METHODOLOGY_SHARED` — **Obermeyer 2019**
(PMID 31649194 / DOI 10.1126/science.aax2342, *Science*; shared depression↔fall-risk — the field's
single reference point for algorithmic bias / subgroup equity) and **Wong 2021 Epic Sepsis external
validation** (PMID 34152373 / DOI 10.1001/jamainternmed.2021.2626, *JAMA Intern Med*; shared
sepsis↔fall-risk — the field's canonical deployed-model-degradation caution). Each is cited for the
*same cross-cutting methodological role* every time it appears; an independent methodologist authoring
each spec fresh arrives at the same citation, so these are shared vocabulary, not collisions. The
independent sweep passes (68/68 scored ids re-resolved live, offline consistency PASS, all 10 cases).

## What ships
- **Keep the shipped defaults** (canonical+synonyms / all-3-providers / verify-on):
  validated safe on all 10 cases; OpenAlex earns its place **wherever golden lit is retrievable at
  all (4 of 10 — DR/warfarin/sepsis/AFib; HRV + melanoma + depression + pneumonia + pembrolizumab +
  fall-risk zero out at query targeting first)**; MeSH + Crossref inert-but-harmless.
- **The MeSH `+hierarchy` axis remains UNVALIDATED** — it is a no-op on all four broad terms that
  reached the slate (sepsis, melanoma, depression, pneumonia), but for the two that *should* have
  tested it decisively (sepsis, pneumonia) the no-op is caused by **Finding B**, not by the axis
  being genuinely inert. **`+hierarchy` cannot be judged until the engine fix lands.**
- **The engine-hardening fix is now the single load-bearing prerequisite** (from Cases 4 + 8):
  (A) seed the condition from `use_case` so mechanism-first phrasing can't zero out retrieval, and
  (B) always try the **bare condition token** in MeSH so broad parents resolve. One small fix covers
  both; scheduled as its own window (ship + full regression), **not** bundled. After it lands,
  **re-run pneumonia** — it is the case that will finally exercise `+hierarchy` for real.
- **Deterministic recall is capped by query *targeting*, not config**, on all 10 cases: named
  records (pivotal NCTs, specific 510(k)s, De Novo grants) and **function-named FDA codes** (QFM et al.,
  named by function not disease) don't rank in generic registry searches. Fall-risk sharpens this into
  a **regulatory-null** corollary: when the system under eval has no authorization of its own, the eval
  surfaces only *adjacent* device codes and correctly reports "no approval for this model." The lever
  for the named-record misses is a curated known-record seed layer, a Phase-2 feature — **not** a
  retrieval knob.
