# Clinical Validation Specification

**Generated:** 2026-07-11
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed (+ web search where noted)

## Inputs
- **AI model:** Time-aware LSTM (gap-modulated forget gate, masking-and-decay embedding for missingness) with multi-head self-attention over hidden states and a sigmoid head; outputs a rolling 48-hour AKI risk score refreshed at each new lab result. Trained with focal loss; calibrated by isotonic regression on a held-out temporal split.
- **Clinical use case:** Continuous prediction of impending acute kidney injury (AKI) from streaming serum creatinine, hourly urine output, vital signs, nephrotoxic medication events, and fluid balance.
- **Patient population:** Adult inpatients without pre-existing ESRD, admitted for medical or surgical care.
- **Healthcare setting:** Acute-care wards and ICUs with real-time EHR integration.
- **Intended clinical claim (INFERRED — team did not specify):** *Assumed claim:* "In adult inpatients without ESRD, the model identifies patients at elevated risk of developing KDIGO-defined AKI within the next 48 hours earlier than standard creatinine-based recognition, with calibrated risk estimates, to prompt clinical review." This is a **prognostic/early-warning decision-support claim**, not a diagnostic claim and not a claim of improved renal outcomes. I flag any stronger claim (mortality reduction, dialysis avoidance) as unsupported by the retrieved evidence.

## Output at a Glance

| Field | Output summary |
|---|---|
| 1. Study Design | Retrospective multi-site temporal-split silent validation → prospective silent deployment; then interventional (ideally cluster-randomized) trial for any outcome/care claim |
| 2. Sensor / Input Validation | No physical sensor; input-validity threat is EHR data provenance — creatinine assay harmonization, urine-output charting fidelity, med-administration timestamp accuracy, missingness mechanism |
| 3. Performance Benchmarks | No FDA benchmark retrieved; must pre-specify AUROC + AUPRC + calibration + lead-time + alert burden; team sets targets with experts |
| 4. Ground Truth Strategy | KDIGO creatinine/urine-output criteria; label reliability capped by creatinine sampling cadence and UO charting — a hard ceiling |
| 5. Sample Size | No retrieved AKI-model sizing; drive by event count for rare-outcome AUPRC/subgroup precision, not by total N; must be computed |
| 6. Subgroup Requirements | Pre-specify CKD stage, baseline creatinine availability, ward vs ICU, surgical vs medical, age, sex, race/eGFR-equation effects, AKI etiology |
| 7. Regulatory Pathway | Likely FDA SaMD; AKI in-vitro precedent PIG is an assay, not analogous — closest is software CDS; De Novo/510(k) analysis needed; regulatory counsel required |
| 8. Post-Deployment Monitoring | Calibration drift, alert-fatigue/override tracking, data-pipeline breakage, MAUDE-style safety reporting, subgroup performance surveillance |

## 1. Study Design
**Recommendation:** Three-stage design. (1) **Retrospective multi-site temporal validation** on the frozen model using a strict temporal split (train on earlier admissions, validate on later ones) across ≥2 institutions with different EHR vendors. (2) **Prospective silent-mode deployment** — model runs live and logs predictions but does not surface alerts — to confirm real-time performance, data-pipeline latency, and calibration under streaming conditions. (3) Only for any claim about *changed care or outcomes*, a **prospective interventional study, ideally cluster-randomized by ward/unit**, since patient-level randomization is contaminated by clinician learning and shared staff.
**Rationale:** The retrieved trial landscape contains no AKI early-warning prediction-model trial; the closest AKI-related record is an observational marker-prognostication design (NCT05441787, inflammatory markers to predict poor trauma outcomes, n=89, COMPLETED) and NCT03058328 (observational biomarker kinetics, n=40) — both illustrate that prognostic-marker work in this space is typically observational and modestly sized, but none validate a streaming EHR AKI model. Trauma/wound trials retrieved (NCT01545232 PROPPR, n=680; NCT05198544 DFU, n=15) are off-target artifacts of the injury query and do not inform this design. Cluster randomization is standard for ward-level alerting tools because contamination is otherwise unavoidable; this is a design principle, not a retrieved number.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 2. Sensor / Input Validation (Pre-Condition)
**Recommendation:** There is no physical sensor, but input validity is still a **hard pre-condition** and must be established before any downstream risk claim. Validate, per site, before performance testing: (a) **serum creatinine assay harmonization** — IDMS-traceability, enzymatic vs Jaffe method, and analyzer differences that shift absolute creatinine and therefore KDIGO thresholds; (b) **urine-output data fidelity** — whether hourly UO is genuinely charted hourly or back-filled/imputed, catheter vs non-catheter patients, and how "missing" UO is distinguished from "zero"; (c) **medication-administration timestamp accuracy** — ordered vs administered vs charted time for nephrotoxins; (d) **the missingness mechanism itself** — because the model's masking-and-decay embedding *learns from* when labs are drawn, informative sampling (sicker patients get drawn more) can leak outcome information and inflate apparent performance. Quantify measurement/timestamp error and missingness patterns as a formal input-validation report.
**Rationale:** openFDA shows AKI-relevant device precedent is an *in-vitro assay* (Acute Kidney Injury Test System, product_code PIG, class 2, reg 862.1220) — underscoring that creatinine/biomarker measurement is itself regulated and non-trivial, and that assay variability directly propagates into any creatinine-based label. The retrieved recalls (Cytocell Z-2210-2023: inverted DNA probes during manufacture; Fujifilm Z-0249-2022: mislabeled expiration date) are off-domain but illustrate the general principle that upstream input/labeling errors invalidate everything downstream. No record specific to EHR data-quality validation for AKI models was retrieved; this reasoning is first-principles.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 3. Performance Benchmarks
**Recommendation:** Pre-specify a **primary discrimination + calibration + clinical-utility triad** rather than AUROC alone: (a) **AUROC** and, critically, **AUPRC** given severe class imbalance (AKI incidence is a low base rate on general wards); (b) **calibration** (calibration curve, slope/intercept, Brier score) since the model claims calibrated probabilities via isotonic regression — calibration must be re-checked on the prospective split, as isotonic fits degrade under distribution shift; (c) **lead time / early-warning gain** — how many hours before KDIGO-defined AKI the alert fires versus creatinine-based recognition; (d) **alert burden / positive predictive value at the deployed threshold** and number-needed-to-alert. **No FDA-recognized performance threshold for AKI prediction models was retrieved — these targets must be set by the study team with clinical and biostatistics experts**, ideally benchmarked against a published external model in a pre-registered analysis plan.
**Rationale:** No retrieved record establishes a quantitative AKI-prediction benchmark. The literature layer is dominated by wound-healing reviews (e.g., PMID 30475656, PMID 32764269) irrelevant to AKI performance targets. Widely cited external AKI-model benchmarks exist in the broader literature but were **not** in this retrieval, so I will not quote numbers. Reporting a real-time predictive-alarm PPV is essential because at low prevalence a high-AUROC model can still overwhelm clinicians with false positives.
**Confidence:** LOW
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 4. Ground Truth Strategy
**Recommendation:** Define AKI by **KDIGO consensus criteria** (serum-creatinine rise ≥0.3 mg/dL within 48 h, or ≥1.5× baseline within 7 days, or urine output <0.5 mL/kg/h ≥6 h), with a pre-specified, auditable baseline-creatinine rule (e.g., lowest recent inpatient value or a defined outpatient window) and pre-registered handling of patients lacking a baseline. Adjudicate a random sample by nephrology chart review to estimate label error. **State the ceiling explicitly:** because creatinine is drawn intermittently and lags injury, and because urine output is inconsistently charted, the reference standard itself is noisy — achievable sensitivity/specificity are capped by label reliability, and apparent "early" prediction may partly reflect delayed creatinine sampling rather than true anticipation.
**Rationale:** The AKI assay precedent (product_code PIG, reg 862.1220) confirms creatinine/biomarker measurement is the regulated substrate of the label; assay variability (Field 2) feeds directly into KDIGO thresholds. No retrieved trial operationalizes KDIGO labeling for a streaming model, so the adjudication protocol must be expert-defined. Physiological wound/injury references retrieved do not bear on renal ground truth.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 5. Sample Size
**Recommendation:** Size the study on **number of AKI events**, not total admissions. Drive powering by (a) the precision needed on AUPRC at the low AKI base rate, (b) calibration-curve stability, and (c) the smallest subgroup requiring an independent performance estimate (see Field 6) — subgroup event counts, not overall N, are the binding constraint. Pre-register a target margin (e.g., confidence-interval half-width on AUROC/AUPRC) and back-calculate required events per site. **No sample-size precedent for an AKI early-warning model was retrieved; this calculation must be performed by a biostatistician and cannot be inferred from the retrieved trials**, which are small and off-target (n=18–680, none AKI-prediction).
**Rationale:** Retrieved enrollments (NCT01545232 n=680; NCT05441787 n=89; NCT03058328 n=40) reflect trauma/biomarker studies with different endpoints and give no usable basis for sizing a rare-event streaming classifier. Rare-outcome classifiers are event-limited, so a large admission cohort may still be underpowered for subgroups.
**Confidence:** LOW
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 6. Subgroup Requirements
**Recommendation:** Pre-specify subgroup analyses with adequate event counts for: (a) **baseline CKD stage / baseline eGFR**, since risk dynamics and creatinine kinetics differ; (b) **presence vs absence of a reliable baseline creatinine** — a documented failure mode; (c) **ward vs ICU** (monitoring intensity and sampling frequency differ, which the missingness embedding will exploit); (d) **surgical vs medical** admissions; (e) **AKI etiology** (sepsis-associated, nephrotoxic, post-operative, cardiorenal); (f) **age, sex, and race** — race is a *physiology-of-measurement* threat here, because creatinine-based eGFR/labeling conventions have historically embedded race coefficients, so the reference standard itself can differ by race; and (g) **urine-output-availability strata** (catheterized vs not). Each must be pre-specified as a subgroup, not a post-hoc slice.
**Rationale:** The concrete population-validity threat for THIS model is not optics but **informative missingness × care intensity** and **creatinine-based label variation across race and CKD status** — both physiology/measurement issues. PMID 41877236 (sex and gender bias in major trauma care, 2026) documents that systematic sex/gender bias exists in acute-care evidence and supports mandatory sex-stratified reporting. No AKI-model subgroup benchmark was retrieved; thresholds are expert-set.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 7. Regulatory Pathway
**Recommendation:** Treat this as **Software as a Medical Device (clinical decision support)** and obtain a formal classification determination. The device likely does **not** qualify for the FDA CDS non-device exemption, because a continuously computed time-driven risk score in acute/ICU settings gives limited opportunity for the clinician to independently review the basis of each alert — a key exemption criterion. Expect a **510(k) or De Novo** software pathway depending on whether an appropriate predicate exists. **No AKI predictive-software clearance was retrieved in this pipeline** (the AKI record retrieved, product_code PIG, is an in-vitro *assay*, class 2, reg 862.1220 — not a valid software predicate). Retrieved software/device precedents (thrombectomy device POL; Guardian System PMA P150009; sequence analyzers PFF/PFS) are not analogous. A predicate/precedent search in openFDA product codes for clinical-alarm and predictive-notification software must be performed before claims language is drafted.
**Rationale:** openFDA returned no AKI early-warning software predicate; absence is not proof none exists, and the Coverage note confirms this pipeline did not query all regulatory endpoints. The claim wording (Field: Inputs) determines the pathway — an outcome/mortality claim escalates evidence requirements sharply beyond a risk-flagging claim.
**Confidence:** LOW
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized

## 8. Post-Deployment Monitoring
**Recommendation:** Stand up a monitoring program covering: (a) **calibration drift** — recompute calibration slope/intercept on rolling windows, since isotonic calibration decays under case-mix and practice shift; (b) **data-pipeline integrity** — automated checks for unit changes, assay-method switches, feed latency, and silent field dropouts that would corrupt inputs; (c) **alert-fatigue metrics** — override rates, alert volume per patient-day, and time-to-response; (d) **subgroup performance surveillance** matching Field 6 strata; (e) **safety-event reporting** analogous to MAUDE, treating missed-AKI and harmful-false-alarm events as reportable. Pre-specify retraining/rollback triggers.
**Rationale:** The retrieved MAUDE injury reports (PICC CLEAR SEQUENCE KIT, report numbers 1030451-2023-00006/00007) and recalls (Cytocell Z-2210-2023, Fujifilm Z-0249-2022) illustrate the general post-market failure classes — device-associated injury and upstream manufacturing/labeling errors — that a monitoring plan must catch; the software analogues here are pipeline corruption and mislabeled inputs. No AKI-model post-market surveillance record was retrieved; this plan is first-principles and must be operationalized with experts.
**Confidence:** MEDIUM
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized

## What This Validation Certifies — and What It Does Not
**CERTIFIES:** A passing three-stage study would establish that, in adult non-ESRD inpatients on the specific wards/ICUs and EHR systems studied, the frozen model produces calibrated 48-hour AKI risk scores that discriminate patients who will meet KDIGO-defined AKI criteria — with pre-specified AUROC/AUPRC, calibration, and lead-time performance holding within named subgroups — under real-time streaming data conditions.

**DOES NOT CERTIFY:**
- That earlier warning changes clinician behavior or improves renal outcomes, dialysis rates, or mortality (requires a separate interventional/cluster-randomized trial).
- Physiological ground truth — the KDIGO reference is itself noisy (intermittent creatinine, incomplete urine-output charting), capping achievable accuracy.
- Generalization to other EHR vendors, creatinine assays, care settings, pediatric/ESRD patients, or populations not enrolled.
- That apparent lead time reflects true anticipation rather than sampling artifacts from informative missingness.
- Any regulatory clearance — classification and pathway remain to be determined with counsel.
- Freedom from performance decay after deployment (addressed only by ongoing monitoring).

## Footer
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification / 510(k)/De Novo / PMA / MAUDE / recalls, openFDA drug/biologic pathways where applicable — Drugs@FDA / SPL labeling / FAERS, and the Europe PMC / OpenAlex / Semantic Scholar / PubMed literature layer) and, where noted, web search. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*