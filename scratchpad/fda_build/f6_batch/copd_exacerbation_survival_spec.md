# Clinical Validation Specification

**Generated:** 2026-07-11
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed (+ web search where noted)

## Inputs
- **AI model:** Hybrid tabular–imaging ensemble. A gradient-boosted decision tree over spirometry-derived features (post-bronchodilator FEV1/FVC, FEV1 %predicted, forced expiratory flow slopes) + longitudinal symptom scores, fused with a 2.5D CNN quantifying low-attenuation-area (LAA%) emphysema and airway wall thickness from paired inspiratory/expiratory chest CT. Imaging embeddings (global average pooling) are concatenated with tabular features; a stacked logistic-regression meta-learner produces the final output. A discrete-time hazard survival head predicts time-to-next-exacerbation.
- **Clinical use case:** Estimate 12-month risk of acute COPD exacerbation from lung-function testing, symptom diaries, and quantitative CT airway/emphysema metrics.
- **Patient population:** Adults ≥40 with spirometry-confirmed airflow obstruction and a prior exacerbation history.
- **Healthcare setting:** Outpatient pulmonology clinics and integrated care-management programs.
- **Intended clinical claim (INFERRED — team must confirm):** *"In adults ≥40 with spirometry-confirmed COPD and prior exacerbation history seen in outpatient pulmonology, the model stratifies patients by 12-month acute-exacerbation risk with calibrated, discriminative predictions that support (but do not replace) clinician judgment for intensifying preventive management."* This is a **prognostic risk-stratification / clinical decision-support** claim, NOT a diagnostic claim and NOT a treatment-directing autonomous claim. Stated as an assumption because the team left the claim unspecified.

## Output at a Glance

| Field | Output summary |
|---|---|
| 1. Study Design | Prospective, multi-site observational cohort with pre-specified 12-month exacerbation follow-up; externally validated. No on-point COPD-prediction trial retrieved. |
| 2. Sensor / Input Validation | PRE-CONDITION: spirometry (ATS/ERS quality) + CT acquisition harmonization (scanner/kernel/inspiration level) must be validated before any risk claim. |
| 3. Performance Benchmarks | Discrimination + calibration for prognostic model; NO retrieved regulatory or literature benchmark specific to this model — team/expert must set. |
| 4. Ground Truth | Adjudicated exacerbation events per consensus definition; label noise caps achievable performance. |
| 5. Sample Size | Event-driven (events-per-variable / calibration precision); NO retrieved number applies — must be computed. |
| 6. Subgroups | CT scanner/vendor/kernel shift; spirometry quality; GOLD stage; sex; race/ethnicity; smoking status — pre-specified. |
| 7. Regulatory Pathway | Likely SaMD, prognostic CDS. Closest device precedents are CT CAD (OEB). No exacerbation-prediction clearance retrieved; regulatory counsel required. |
| 8. Post-Deployment | Monitor calibration drift, CT/spirometry input drift, MAUDE-style malfunction reporting; retrain governance. |

## 1. Study Design
**Recommendation:** Prospective, multi-site **observational prognostic cohort** enrolling adults ≥40 with spirometry-confirmed COPD and prior exacerbation, with the model's 12-month risk output locked at baseline and blinded to treating clinicians, followed by pre-specified 12-month ascertainment of acute exacerbations. Include an **external/temporal validation** cohort at sites not contributing to training. Report per TRIPOD-AI. A pragmatic randomized implementation study (does acting on the score change outcomes?) is a *later* step, not the initial validation.
**Rationale:** Retrieved COPD/lung records are dominated by feasibility, rehabilitation, and home-monitoring designs — e.g. home monitoring in pulmonary fibrosis (NCT06883448; PMID 36206780), hybrid vs standard care RCT design in pulmonary fibrosis (PMID 42310732), COPD mindful-breath feasibility (NCT07195838), and a large observational asthma characterization cohort (NCT07556159, n=2500). These confirm that observational cohort and hybrid-care designs are the norm in this space but provide **no on-point prognostic exacerbation-prediction trial** to copy. The observational-cohort choice is standard for a prognostic model; the blinded-baseline design prevents the score from contaminating its own outcome.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 2. Sensor / Input Validation (Pre-Condition)
**Recommendation:** Treat both input streams as gating pre-conditions before any risk claim is credited:
- **Spirometry:** enforce ATS/ERS acceptability/repeatability criteria; log post-bronchodilator technique, device model, and calibration; exclude or flag non-quality-controlled sessions. Reference-equation choice (e.g. ERS lung-volume reference statement, PMID 7789503) affects %predicted values and must be fixed and reported.
- **Quantitative CT:** pre-specify and harmonize scanner vendor, reconstruction kernel, slice thickness, tube current, and — critically — **inspiration/expiration breath-hold level**, because LAA% and airway wall thickness are highly sensitive to lung volume, kernel, and dose. Require a phantom/QA program and cross-scanner reproducibility testing before the CNN outputs are trusted.
**Rationale:** MAUDE malfunction reports for peak-flow/spirometry devices (report #1044475-2014-00076, -00075) and the Class II recall of the Welch Allyn CP150 spirometry-option device for an omitted EMI absorber (Z-2323-2024), plus the GE CARESCAPE B450 network-overload recall (Z-0095-2019), are concrete evidence that measurement hardware fails in the field — so input validity cannot be assumed. Quantitative CT emphysema metrics are physics-dependent (kernel/dose/inspiration), not merely software outputs; the CT CAD precedent syngo.CT Lung CAD (K193216, code OEB) confirms CT-derived quantification is a regulated measurement, not a given.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 3. Performance Benchmarks
**Recommendation:** For a prognostic risk model, report BOTH **discrimination** (time-dependent AUC/C-index for the 12-month horizon) and **calibration** (calibration plot, calibration slope/intercept, and calibration-in-the-large), plus **clinical utility** (decision-curve / net-benefit) at the risk thresholds intended to trigger care-management escalation. Report the survival head's performance separately (time-dependent C-index, integrated Brier score). **No numeric target may be set from retrieved evidence.**
**Rationale:** **No established performance benchmark for COPD 12-month exacerbation prediction was retrieved** in this pipeline — the literature layer returned lung-disease ML methods papers (e.g. multi-disease lung classification, PMID 41857194; time-series lung-disease prediction, PMID 41377819) but none reporting a validated, on-point exacerbation-risk operating point for this population. Therefore discrimination and calibration targets **must be set by the study team / expert**, ideally against the best available published COPD exacerbation-risk models (to be retrieved via the un-searched licensed databases noted below). Prioritize calibration: a mis-calibrated risk score that drives resource allocation is directly harmful even at good AUC.
**Confidence:** LOW
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 4. Ground Truth Strategy
**Recommendation:** Define the outcome as **acute COPD exacerbation within 12 months** using a pre-specified consensus event definition (event-based: symptom worsening requiring systemic corticosteroids/antibiotics; and/or healthcare-utilization-based: ED visit/hospitalization), with **independent blinded adjudication** of ambiguous events and explicit handling of competing risks (death) and censoring. Capture severity tiers (moderate vs severe) separately.
**Rationale:** Exacerbation is a clinically defined, partly subjective label; ascertainment mixes patient-reported, pharmacy, and administrative signals. Because the reference standard is noisy, **achievable sensitivity/specificity and calibration are capped by label reliability** — inconsistent event definitions across sites will inflate apparent error. No retrieved record supplied a validated adjudication protocol for this model; adopt a published, pre-registered definition and report inter-adjudicator agreement. The large observational asthma cohort (NCT07556159) and pulmonary-fibrosis home-monitoring work (PMID 36206780) illustrate structured outcome capture but do not define the COPD exacerbation endpoint here.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 5. Sample Size
**Recommendation:** Size the study **on events, not patients** — driven by (a) events-per-candidate-predictor for the meta-learner/survival head to control overfitting, and (b) the precision needed on the calibration slope and time-dependent AUC at the intended decision threshold. Enroll enough patients that expected 12-month exacerbation events meet both, with margin for censoring/loss-to-follow-up. **The specific N must be formally computed (e.g. Riley et al. prognostic-model sample-size methods) — no retrieved record provides a valid N for this model.**
**Rationale:** Retrieved enrollments span n=10 (NCT03942302) to n=2500 (NCT07556159) and n=619 (NCT05339048) — these reflect unrelated designs and **cannot be transferred** as a target here. A hybrid model with high-dimensional imaging embeddings plus tabular features has many effective degrees of freedom, raising the events requirement. External-validation cohorts additionally need sufficient events for stable calibration estimates.
**Confidence:** LOW
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 6. Subgroup Requirements
**Recommendation:** Pre-specify subgroup performance (discrimination + calibration) for:
- **CT acquisition shift** — scanner vendor, reconstruction kernel, slice thickness/dose, and inspiration/expiration adequacy (the dominant physics threat to LAA%/airway-wall outputs).
- **Spirometry quality tier** — ATS/ERS-acceptable vs flagged sessions; device model.
- **COPD severity (GOLD spirometric stage)** and prior-exacerbation frequency.
- **Sex**, **age bands**, **race/ethnicity** (also implicating spirometry reference-equation choice, PMID 7789503), and **smoking status / pack-years**.
Require the model to meet calibration in each pre-specified subgroup, not just overall.
**Rationale:** The concrete population-specific validity threat here is **scanner/vendor/kernel/inspiration-level domain shift** on the quantitative-CT branch — a physics problem, confirmed as a regulated measurement concern by the CT CAD precedent (K193216, OEB) — plus **reference-equation/demographic effects on %predicted** on the spirometry branch. These are not optional fairness add-ons; they are where a fused model most plausibly breaks. No retrieved record supplies subgroup benchmarks, so thresholds must be expert-set.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 7. Regulatory Pathway
**Recommendation:** Most defensibly treat this as **Software as a Medical Device — a prognostic clinical decision-support tool**. Determine early with regulatory counsel whether it qualifies as non-device CDS (clinician can independently review the basis of the risk estimate) or as a regulated SaMD requiring clearance; a quantitative-CT branch that outputs measurements (LAA%, airway wall thickness) pushes toward device territory. The closest retrieved precedents are **CT image-analysis CAD devices** — syngo.CT Lung CAD (K193216, product code OEB) and Lung Vision System (K183593, code LLZ) — but **no retrieved clearance covers COPD exacerbation *risk prediction***, so these are analogous, not on-point. The Thoraflex Hybrid PMA (P210006, code QSK) is an aortic surgical graft and is **not relevant** despite the "hybrid" keyword match. Do not assert a cleared pathway.
**Rationale:** Retrieval returned device-classification and 510(k) records for CT CAD and post-market signals for spirometry hardware, but nothing establishing a predicate for a fused spirometry+CT exacerbation-risk predictor. **This pipeline did not query Drugs@FDA/SPL/FAERS or non-US regulators (EMA/MHRA/PMDA)** — irrelevant here (device, not drug), but non-US pathways would need separate assessment. Absence of a retrieved predicate is not proof none exists.
**Confidence:** LOW
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized

## 8. Post-Deployment Monitoring
**Recommendation:** Stand up continuous monitoring for: (1) **calibration drift** over time and across sites (recalibration triggers); (2) **input drift** on both streams — CT scanner/protocol changes, kernel updates, inspiration-quality degradation, and spirometer model/firmware/reference-equation changes; (3) **subgroup performance stability**; (4) a **malfunction/adverse-event reporting** channel analogous to MAUDE. Define a governance process (owner, thresholds, retraining/rollback plan) and treat any input-device recall as an automatic revalidation trigger.
**Rationale:** MAUDE spirometry malfunction reports (#1044475-2014-00076/-00075) and Class II recalls of spirometry-option and monitoring hardware (Welch Allyn CP150, Z-2323-2024; GE CARESCAPE B450, Z-0095-2019) are direct evidence that upstream measurement devices fail and get recalled in production — silently corrupting model inputs. A prognostic model whose CT metrics are physics-sensitive is especially exposed to protocol/scanner changes. These are safety/failure-mode signals, not efficacy evidence.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## What This Validation Certifies — and What It Does Not
**CERTIFIES:** That, when fed quality-controlled ATS/ERS-acceptable spirometry and harmonized inspiratory/expiratory CT, the model produces discriminative and calibrated 12-month acute-exacerbation risk estimates — overall and within pre-specified CT-acquisition, spirometry-quality, GOLD-stage, sex, age, race/ethnicity, and smoking subgroups — in adults ≥40 with spirometry-confirmed COPD and prior exacerbation history, in outpatient pulmonology / care-management settings, against an adjudicated consensus exacerbation endpoint.
**DOES NOT CERTIFY:**
- That acting on the risk score **improves patient outcomes** (that requires a separate randomized/pragmatic implementation trial).
- **Physiological ground truth** of the CT-derived emphysema/airway metrics (those depend on the input-validation pre-condition being independently met).
- **Regulatory clearance** or any specific FDA/EMA pathway — no on-point predicate was retrieved.
- **Generalization** beyond the studied scanners, spirometers, sites, and population (e.g. primary care, non-obstructed patients, unvalidated CT protocols, or patients without prior exacerbations).
- Performance beyond the **12-month horizon** or for exacerbation severities not adjudicated.

## Footer
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification / 510(k)/De Novo / PMA / MAUDE / recalls, openFDA drug/biologic pathways where applicable — Drugs@FDA / SPL labeling / FAERS, and the Europe PMC / OpenAlex / Semantic Scholar / PubMed literature layer) and, where noted, web search. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*