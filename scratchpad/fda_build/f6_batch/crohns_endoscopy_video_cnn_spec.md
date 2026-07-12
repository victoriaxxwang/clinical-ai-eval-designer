# Clinical Validation Specification

**Generated:** 2026-07-11
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed (+ web search where noted)

## Inputs
- **AI model:** Multimodal late-fusion network: (a) ResNet-34 endoscopic-image branch scoring mucosal ulceration/stenosis/inflammatory extent per frame from ileocolonoscopy video, recurrent-pooled to a segment-level activity index; (b) tabular branch over fecal calprotectin, CRP, hemoglobin, albumin; (c) transformer encoder over free-text pathology/clinical notes; fused via gated attention. Dual output: 12-month relapse probability + auxiliary endoscopic-severity index.
- **Clinical use case:** Forecast Crohn's disease flares over a 12-month horizon and quantify mucosal inflammatory activity from combined endoscopic, biomarker, and text inputs.
- **Patient population:** Adults with established IBD (Crohn's disease) in clinical remission or mild activity.
- **Healthcare setting:** Gastroenterology specialty clinics and IBD centers.
- **Intended clinical claim (INFERRED — team must confirm):** *"In adults with established Crohn's disease in remission/mild activity, this software estimates the probability of clinical relapse within 12 months and provides a mucosal-activity index, as an adjunct to clinician assessment for risk stratification and surveillance planning — not as a standalone diagnostic or treatment-decision device."* I am assuming an **adjunctive prognostic/decision-support** claim, which is the most defensible framing; a standalone or autonomous claim would demand substantially heavier evidence.

## Output at a Glance

| Field | Output summary |
|---|---|
| 1. Study Design | Prospective, multi-site cohort with ≥12-month follow-up locking predictions before outcome ascertainment; retrospective training/tuning acceptable but not pivotal. No on-point trial precedent retrieved. |
| 2. Sensor/Input Validation | Three input pipelines must each be validated first: endoscopic video acquisition (scope vendor/resolution/bowel-prep), lab-assay harmonization (calprotectin platform variance), and NLP text-source consistency. Pre-condition to any prognostic claim. |
| 3. Performance Benchmarks | No regulatory relapse-prediction benchmark retrieved. Endoscopic-severity sub-task can anchor to DL-vs-expert scoring literature (PMID 42238140). Relapse AUC/calibration targets must be team-set. |
| 4. Ground Truth Strategy | Two references: relapse (composite clinical/endoscopic/biomarker-driven outcome) and endoscopic severity (blinded central reads vs validated indices). Label noise caps achievable performance. |
| 5. Sample Size | No retrieved study sizes the relapse endpoint; must be event-driven on 12-month relapse incidence. Retrieved IBD cohorts (n=240, n=60) are far too small for a pivotal prognostic study. |
| 6. Subgroups | Pre-specify skin-tone-independent but device-dependent endoscopic subgroups (scope vendor, bowel-prep quality), disease phenotype/location, prior biologic exposure, assay platform, note-source site. |
| 7. Regulatory Pathway | Likely FDA SaMD; no CADx/prognostic IBD predicate retrieved among returned 510(k)s. Novel prognostic claim points toward De Novo. Regulatory counsel required. |
| 8. Post-Deployment Monitoring | Monitor input drift (scope/assay/EHR changes), calibration decay, subgroup performance; MAUDE/recall precedents show software-driven device failures are real (Z-1277-2013). |

## 1. Study Design
**Recommendation:** A **prospective, multi-site observational cohort** in which the model's 12-month relapse prediction and severity index are generated and **locked at baseline endoscopy**, then compared against prospectively ascertained relapse over ≥12 months. Retrospective data may be used for development and internal tuning, but the pivotal validation must be prospective and geographically external to training sites. Predictions must be masked from treating clinicians during the outcome window (or, if unmasked for a decision-support arm, the study must measure and adjust for the treatment-paradox / intervention effect, since acting on a high-risk prediction changes the outcome it predicts).
**Rationale:** No retrieved trial validates a multimodal relapse-prediction model. The two IBD studies returned are a day-hospital management observational study (NCT07167186, n=240, outcomes = change in patient skills/management, not prediction) and a dietary RCT (NCT06698601, n=60, fecal-calprotectin endpoint) — neither is a design precedent, but the latter confirms **fecal calprotectin as an accepted objective inflammation endpoint**, relevant to your outcome definition. A systematic review of DL in IBD endoscopic scoring (PMID 42238140, Cureus 2026) confirms the endoscopic sub-task is an active, evaluable area but is diagnostic/cross-sectional, not prognostic. The prognostic (time-to-relapse) claim is the novel and harder element and drives the prospective design.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 2. Sensor / Input Validation (Pre-Condition)
**Recommendation:** Validate each of the **three input pipelines independently before any fused prognostic claim is trusted:**
1. **Endoscopic video:** Characterize performance across scope vendor/model, image resolution, frame rate, illumination (white-light vs virtual chromoendoscopy), and — critically — **bowel-preparation quality**, which directly corrupts mucosal-visualization inputs. Require a documented acquisition standard and an automated frame-quality gate that rejects/flags non-diagnostic frames before ResNet scoring.
2. **Laboratory markers:** Fecal calprotectin is notoriously **assay- and platform-dependent**; CRP assay standardization and albumin/hemoglobin unit harmonization must be specified. The model must not silently ingest values across incompatible assays.
3. **Free-text notes:** NLP branch is exposed to **site-specific documentation style**, template artifacts, and copy-forward text — a documented input-validity threat. Validate on notes from sites not seen in training.
**Rationale:** openFDA classifies the video-capture layer as a real device class — Endoscopic Video Imaging System, product code **OCS, class 2, reg 876.1500** — underscoring that the imaging input is itself a regulated measurement chain, not a neutral pixel source. If the acquisition device varies, the ResNet's frame scores vary; this is physics/optics, not a modeling footnote. Fecal-calprotectin variability is implicit in its use as an endpoint (NCT06698601). No retrieved record establishes input-validity thresholds for this pipeline, so these must be set by the team.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 3. Performance Benchmarks
**Recommendation:** Report **two distinct benchmark sets.** For the **auxiliary endoscopic-severity index**, anchor agreement against validated human-scored indices (e.g., SES-CD) using weighted kappa / correlation and expert-reader comparison — the DL-endoscopy literature provides a comparator range. For the **primary 12-month relapse prediction**, report discrimination (AUROC), **calibration (calibration curve, Brier score, and calibration-in-the-large — mandatory for a probabilistic prognostic output)**, sensitivity/specificity at a pre-specified operating threshold, and net clinical benefit (decision-curve analysis). **No FDA performance standard and no regulatory relapse-prediction benchmark were retrieved — the relapse AUC/calibration targets must be set prospectively by the study team and clinical experts, not borrowed.**
**Rationale:** PMID 42238140 (systematic review of DL endoscopic severity assessment, Cureus 2026) supports that the severity sub-task has an established evaluation paradigm, but I cannot cite a specific numeric performance figure from the metadata retrieved — treat any headline number as requiring source verification. PMID 32195365 (npj Digital Medicine 2020, AI/ML in autoimmune disease) confirms ML prognosis in this space is early-stage. Nothing retrieved sets a relapse-prediction threshold. Calibration is emphasized because a poorly calibrated relapse probability driving surveillance intensity is directly harmful.
**Confidence:** LOW
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 4. Ground Truth Strategy
**Recommendation:** Define **two reference standards.**
- **Relapse (primary):** A pre-specified **composite clinical outcome** — e.g., physician-confirmed flare requiring treatment escalation, corroborated by objective markers (fecal calprotectin rise, endoscopic recurrence, hospitalization/surgery). Adjudicate by a blinded committee to reduce subjectivity.
- **Endoscopic severity (auxiliary):** **Central, blinded multi-reader scoring** against a validated index (SES-CD), with inter-reader agreement reported. The model's severity index is capped by reader agreement.
**Label reliability is a ceiling:** relapse labels built on clinician judgment or symptom-driven definitions are noisy and inconsistent across sites; achievable sensitivity/specificity cannot exceed the reliability of that composite. State the label definition and its measured reliability explicitly; degrade expected performance accordingly.
**Rationale:** NCT06698601 validates fecal calprotectin as an objective inflammation anchor; ECCO guidance (PMID 36528797, J Crohn's Colitis 2022) is a source for outcome/malignancy-surveillance definitions. The DL-endoscopy review (PMID 42238140) implies central expert reads are the field-standard reference for severity. No retrieved record fixes a single canonical relapse definition — this is a known heterogeneity in IBD trials and must be pre-specified.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 5. Sample Size
**Recommendation:** Size the study as **event-driven on 12-month relapse count**, not total enrollment. Because relapse is the primary endpoint, the binding quantity is the number of relapse events needed to estimate AUROC/calibration with acceptable precision and to power pre-specified subgroup contrasts — with enrollment then back-calculated from the expected 12-month relapse incidence in a remission/mild-activity cohort. **No retrieved study provides a validated relapse incidence or a powering basis for this endpoint — the incidence assumption and target event count must be set by the study team from institutional or literature data and stated explicitly.**
**Rationale:** The retrieved cohorts — NCT07167186 (n=240) and NCT06698601 (n=60) — are informative-scale but neither was designed to validate a multimodal relapse-prediction model, and both are almost certainly **underpowered** for a calibrated prognostic model with mandatory subgroup analyses. Multimodal models with three input branches also carry high overfitting risk, raising the effective sample requirement. No numeric target can be responsibly asserted here.
**Confidence:** LOW
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 6. Subgroup Requirements
**Recommendation:** Pre-specify subgroup performance (with calibration reported per subgroup) for:
- **Endoscopic-device strata:** scope vendor/model, resolution, white-light vs chromoendoscopy — the imaging-physics analogue of the population validity threat (here it is *scanner/scope shift*, not skin tone).
- **Bowel-prep quality tiers** — directly modulates image-branch validity.
- **Disease phenotype/location** (ileal vs colonic vs ileocolonic; stricturing/penetrating vs inflammatory) — supported as clinically distinct by anatomy/surgical literature (PMID 24436656; PMID 41113555 on stricture imaging).
- **Prior/current biologic exposure** and baseline activity level (remission vs mild).
- **Laboratory-assay platform** for fecal calprotectin/CRP.
- **NLP note-source site/EHR** — documentation-style shift.
- Demographics (age band, sex) as feasible.
**Rationale:** Each stratum is a concrete input-validity threat specific to this multimodal pipeline: the ResNet is exposed to scope/vendor/prep shift; the tabular branch to assay platform shift; the transformer to site documentation shift. PMID 42238140 flags generalization gaps in DL endoscopy. No retrieved record supplies subgroup performance targets — these must be pre-specified and expert-set.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 7. Regulatory Pathway
**Recommendation:** Treat as **Software as a Medical Device (SaMD)** making an adjunctive prognostic/decision-support claim. **No prognostic or CADx IBD software predicate was retrieved** among the returned 510(k)s — the "multimodal" matches are unrelated (CURRY neuroimaging K001781; Cutera cellulite K080300/K092195), and the gastroenterology entries are physical devices (endoscopic video system OCS; overtube FED; morcellator PTE), not AI prognostic software. A novel 12-month relapse-prediction claim with no clear predicate points toward a **De Novo** request (or a 510(k) only if a suitable AI/ML predicate can be identified outside this retrieval). If the team narrows to *decision support* meeting FDA's non-device Clinical Decision Support criteria (transparent inputs, clinician able to independently review the basis, non-time-critical), part of the function might fall outside device regulation — but the endoscopic-severity image analysis likely remains a device function. **Regulatory counsel must resolve this; do not assert a pathway from this retrieval alone.**
**Rationale:** openFDA device classifications retrieved are physical GI devices, and the coverage note confirms **FDA AI/ML SaMD-specific listings, the AI/ML action plan, and non-US regulators were not queried** — so absence of a predicate here is not evidence one does not exist. MAUDE/recall records for software-driven device malfunctions (Olympus UES-40 software upgrade recall Z-1277-2013; Auriga power-degradation Z-1396-2019) illustrate that FDA treats software-caused failures as reportable device events, reinforcing device-track expectations.
**Confidence:** LOW
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized

## 8. Post-Deployment Monitoring
**Recommendation:** Implement continuous monitoring for:
- **Input drift:** new scope models/firmware, bowel-prep protocol changes, calprotectin/CRP assay switches, EHR template/documentation changes — each can silently invalidate a branch. Tie to an automated input-quality gate (from Field 2).
- **Calibration decay:** track observed-vs-predicted 12-month relapse over rolling cohorts; recalibrate on a pre-defined trigger.
- **Subgroup performance surveillance:** re-check the Field 6 strata over time.
- **Adverse-event / failure reporting:** a MAUDE-equivalent internal pathway for prediction-linked harm (missed flare after low-risk output; unnecessary escalation after high-risk output).
- **Outcome feedback loop** distinguishing true model drift from the treatment-paradox effect once clinicians act on outputs.
**Rationale:** Retrieved MAUDE malfunction reports (endoscopic guidewire OCY, 1037905-2020-00191/00201) and software-upgrade recalls (Z-1277-2013) show that GI device and software failures are recurrent and reportable in the real world; a deployed SaMD needs the analogous surveillance. The coverage note confirms FAERS/other post-market drug endpoints were not queried, so this is a device-side monitoring frame only. No retrieved record specifies monitoring thresholds — team must set them.
**Confidence:** MEDIUM
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized

## What This Validation Certifies — and What It Does Not
**CERTIFIES:** That a passing prospective multi-site study would establish that, in adults with established Crohn's disease in clinical remission/mild activity seen at gastroenterology/IBD centers using the validated endoscopic-acquisition, assay, and documentation inputs specified, the model's locked baseline output discriminates and is calibrated for 12-month clinical relapse (against the pre-specified composite reference) and agrees with blinded expert endoscopic severity scoring — within the tested device/assay/site subgroups and to the ceiling set by label reliability.

**DOES NOT CERTIFY:**
- Any physiological or causal truth about *why* a patient will relapse — only association with a defined composite outcome.
- Performance beyond the tested population (pediatric, ulcerative colitis, moderate-to-severe active disease, non-IBD-center settings).
- Performance on scope vendors, calprotectin assay platforms, or EHR/documentation styles not represented in validation.
- Standalone or autonomous use — the inferred claim is adjunctive; the model does not replace clinician judgment or endoscopic assessment.
- Regulatory clearance or authorization of any kind (pathway unresolved; regulatory counsel required).
- That acting on predictions improves patient outcomes — that requires a separate interventional/impact study, not this predictive-accuracy validation.
- Equivalence to clinical-grade endpoints where label noise caps achievable sensitivity/specificity.

## Footer
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification / 510(k)/De Novo / PMA / MAUDE / recalls, openFDA drug/biologic pathways where applicable — Drugs@FDA / SPL labeling / FAERS, and the Europe PMC / OpenAlex / Semantic Scholar / PubMed literature layer) and, where noted, web search. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*