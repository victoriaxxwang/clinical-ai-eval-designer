# Clinical Validation Specification

**Generated:** 2026-07-11
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed (+ web search where noted)

## Inputs
- **AI model:** Ensemble (5×) DenseNet-121 classifier on frontal chest radiographs (512×512), with a U-Net lung-field segmentation preprocessing step and Grad-CAM localization of cavitation / upper-lobe infiltrate / miliary patterns; outputs a single abnormality probability suggestive of pulmonary TB.
- **Clinical use case:** Automated triage/screening of frontal CXRs — returns a probability score + spatial heatmap for confirmatory human/microbiological review.
- **Patient population:** Adults and adolescents in symptomatic or contact-based TB screening, high-incidence regions.
- **Healthcare setting:** Community screening campaigns and primary-care clinics using portable digital radiography.
- **Intended clinical claim (inferred — team to confirm):** *"As a computer-aided triage tool, the model flags chest radiographs with findings suggestive of active pulmonary TB, prioritizing which patients proceed to confirmatory bacteriological testing (e.g., Xpert MTB/RIF)."* This is a **triage/screening claim, not a diagnostic claim** — the model does not diagnose TB and does not replace microbiological confirmation. I am assuming this framing because the use case is screening in high-incidence settings where WHO positions CAD as a pre-bacteriological triage step.

## Output at a Glance
| Field | Output summary |
|---|---|
| 1. Study Design | Prospective/retrospective multi-site diagnostic accuracy study vs. bacteriological reference, in intended screening population with portable DR |
| 2. Sensor/Input Validation | Portable DR acquisition variability (detector vendor, kVp/exposure, rotation, portable vs. fixed) must be validated before classifier claims; segmentation-failure QA pre-condition |
| 3. Performance Benchmarks | WHO TPP triage targets (≥90% sens / ≥70% spec) as reference goalposts; literature AUROCs ~0.90+ but no FDA benchmark retrieved |
| 4. Ground Truth | Bacteriological confirmation (Xpert MTB/RIF DEN130032/K143302, culture) as primary reference; radiologist read is a noisy ceiling |
| 5. Sample Size | No established N retrieved — must be powered for pre-specified sens/spec CIs; disease prevalence drives PPV; team/statistician to set |
| 6. Subgroups | HIV status, prior TB, age (adolescent vs adult), DR vendor/portable unit, disease severity/smear status pre-specified |
| 7. Regulatory Pathway | Radiological CAD triage software; no TB-CAD 510(k) retrieved in this pull — likely De Novo/510(k) triage-software category; WHO prequalification path for target markets |
| 8. Post-Deployment Monitoring | Drift monitoring across new DR units/sites, MAUDE-style safety reporting, missed-case audit vs. bacteriological outcomes |

## 1. Study Design
**Recommendation:** A multi-site diagnostic accuracy study enrolling the *intended screening population* (symptomatic + contact-based, high-incidence), reading each subject's frontal CXR through the model and comparing against a bacteriological reference standard. Prefer a prospective consecutive-enrollment design; a retrospective cohort with pre-specified inclusion is acceptable for initial validation but must reflect the deployment triage flow. Population-based cohort designs are precedented for CAD-TB screening evaluation (Emerg Microbes Infect, 2025, PMID 40260691), and algorithm-vs-radiologist comparative designs are precedented for CXR deep learning (Rajpurkar/CheXNeXt, PLoS Med 2018, PMID 30457988; Clin Infect Dis 2018, PMID 30418527).
**Rationale:** The claim is triage, so the design must measure operating-point sensitivity/specificity at the deployed threshold, not just AUROC, and must capture the full spectrum of disease severity seen in field screening (including paucibacillary/subclinical cases that CXR-only tools miss). International multicenter validation across sites/vendors is precedented (Diagnostics 2026, PMID 42072763) and is necessary because single-site accuracy does not transfer. A systematic review confirms wide heterogeneity in reported ML-TB accuracy (Nurs Health Sci 2025, PMID 40058367), reinforcing multi-site prospective evaluation.
**Confidence:** MEDIUM — design precedents are strong and on-point, but no single retrieved trial matches this exact ensemble/portable-DR configuration.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 2. Sensor / Input Validation (Pre-Condition)
**Recommendation:** Before any TB-classification claim, establish image-acquisition validity for **portable digital radiography** as actually deployed: characterize performance across detector vendors/models, exposure (kVp/mAs) ranges, patient rotation/positioning, field-of-view cropping, and portable-vs-fixed acquisition. Separately validate the U-Net lung-segmentation stage — quantify segmentation-failure rate and its downstream effect, and require an automatic QA gate that rejects/flags images where segmentation fails or the FOV is out of distribution.
**Rationale:** This model's accuracy is physically bounded by input quality; portable DR in field campaigns produces more positioning/exposure variability than the curated corpora used for pretraining. Recalls in the retrieved set involve x-ray hardware faults (Villa Radiology Juno DRF / Apollo, Z-1063-2017 / Z-1064-2017, Class II) — a reminder that the imaging chain itself is a regulated failure surface. The segmentation-preprocessing dependency is a named domain-shift threat: masking non-thoracic pixels normalizes FOV in-distribution but can fail silently on atypical portable geometry. Acquisition/vendor shift is the concrete physics threat here (analogous to scanner/reconstruction-kernel shift in CT) and must be a pre-specified subgroup (see Field 6).
**Confidence:** MEDIUM — the threat is well-established in imaging-AI literature; no retrieved record quantifies portable-DR shift for THIS model.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 3. Performance Benchmarks
**Recommendation:** Anchor to the **WHO Target Product Profile for TB triage tests** — commonly cited minimum ≥90% sensitivity and ≥70% specificity against a bacteriological reference (web/WHO-derived, **not** in the retrieved registry records — verify against current WHO TPP before use). Report AUROC, sensitivity/specificity at the *pre-specified deployment threshold* (with 95% CIs), and PPV/NPV at local prevalence. Do **not** adopt any single literature AUROC as a pass/fail bar.
**Rationale:** Retrieved literature reports high discrimination — e.g., deep-learning active-TB detection (PMID 30418527), ensemble architectures (Sci Rep 2026, PMID 41513737), and population-based CAD screening performance (PMID 40260691) — but these are heterogeneous and not regulatory standards; the systematic review (PMID 40058367) explicitly cautions on pooled accuracy variability. **No FDA-cleared TB-CAD performance benchmark was retrieved in this pull.** The team must pre-register its operating point and justify the sensitivity/specificity trade-off for a triage-not-diagnosis role.
**Confidence:** LOW — the WHO TPP numbers are widely used but were not confirmed in the retrieved records; no regulatory benchmark retrieved.
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized.

## 4. Ground Truth Strategy
**Recommendation:** Use **bacteriological confirmation as the primary reference standard** — nucleic-acid amplification (Xpert MTB/RIF; retrieved product codes PEU/MWA, DEN130032, K143302, Cepheid) and/or mycobacterial culture — applied to all CXR-positive and an appropriate sample of CXR-negative subjects. Radiologist consensus read may serve as a *secondary* index but must not be the primary truth. Pre-specify handling of clinically-diagnosed but bacteriologically-negative TB.
**Rationale:** The classifier detects *radiographic patterns*, which are an imperfect surrogate for active infection; a radiology-only reference would inflate agreement and cap achievable accuracy at inter-reader reliability. Molecular assays are the accepted confirmatory axis (retrieved microbiology codes PEU/MWA). **Label-reliability ceiling:** CXR-based labels are noisy for paucibacillary/subclinical TB, and culture itself misses some active disease — achievable sensitivity/specificity is bounded by this, and verification bias must be addressed if not all negatives are cultured.
**Confidence:** HIGH — bacteriological reference standard is established and the confirmatory devices are directly retrieved.
**Expert review:** Expert sign-off — output is well-grounded; expert confirms or adjusts.

## 5. Sample Size
**Recommendation:** **No established sample size was retrieved — this must be set by the study team/statistician.** Power the study for the CI width around the pre-specified sensitivity and specificity targets (Field 3), and separately for the lowest-prevalence subgroup that must retain valid estimates (Field 6). Because PPV in field screening depends heavily on TB prevalence, enrollment must yield enough confirmed positives to estimate sensitivity precisely — not just total N.
**Rationale:** Retrieved studies vary widely in enrollment and are not designed to define a target N for this configuration; using any of their sample sizes as a benchmark would be inventing a number. Prevalence-driven positive-case yield is the binding constraint in screening.
**Confidence:** LOW — no retrieved record supports a specific N.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 6. Subgroup Requirements
**Recommendation:** Pre-specify and power (or at minimum report with CIs) subgroups: **HIV status** (HIV-associated TB often has atypical/normal CXR), **prior TB / fibrotic scarring** (a major false-positive source), **adolescent vs. adult**, **smear-positive vs. smear-negative / bacillary burden** (severity spectrum), and **DR device vendor / portable unit** (acquisition shift, Field 2). Report per-subgroup sensitivity/specificity, not just pooled.
**Rationale:** Concrete physiology/physics threats here: HIV and prior-TB scarring change the radiographic phenotype and are known to degrade CAD-TB performance; portable-DR vendor variation is the acquisition-shift threat. Multi-pathology multicenter validation precedent (PMID 42072763) and privileged-supervision generalization work (PMID 41957286) underscore that generalization must be demonstrated, not assumed.
**Confidence:** MEDIUM — clinical rationale is strong; specific subgroup thresholds not retrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 7. Regulatory Pathway
**Recommendation:** Treat this as **radiological computer-assisted triage/detection software (SaMD)**. In the retrieved openFDA pull, **no TB-specific CAD 510(k)/De Novo device was returned** — the retrieved device codes (PEU, MWA) are molecular assays, and the retrieved PMA/recalls are unrelated hardware; so no direct US predicate for this model was retrieved. For the intended high-incidence deployment markets, the **WHO prequalification / WHO 2021 CAD-for-TB screening policy** pathway is likely the operative route (web/WHO-derived — verify). If US market entry is intended, expect a radiological triage-software category (De Novo or 510(k) against a triage-software predicate) — regulatory counsel must confirm the exact product code and pathway; do not assert a cleared pathway.
**Rationale:** The claim is triage-not-diagnosis, which aligns with the CADt regulatory concept. The absence of a retrieved TB-CAD predicate is a coverage gap (this pipeline did not query non-US regulators — EMA/MHRA/PMDA — nor Drugs@FDA), not evidence none exists.
**Confidence:** LOW — no on-point device precedent retrieved; pathway is inferred.
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized.

## 8. Post-Deployment Monitoring
**Recommendation:** Implement (a) continuous input-drift monitoring as new DR units/sites are added (acquisition distribution vs. validation set); (b) periodic re-audit of model-negative patients against bacteriological/clinical outcomes to detect missed cases; (c) threshold/calibration monitoring, since prevalence and case-mix shift across campaigns; (d) a structured adverse-event/failure reporting process analogous to MAUDE (retrieved reports illustrate the hardware failure modes — e.g., report 2443168-1994-00001) covering both software mis-triage and imaging-chain faults.
**Rationale:** Screening deployment across heterogeneous portable units guarantees distribution shift; the segmentation and ensemble components can degrade silently. Post-market safety signals in the retrieved set (recalls Z-1063-2017/Z-1064-2017; MAUDE community/radiograph entries) are safety/failure-mode references — used here for monitoring design, not efficacy.
**Confidence:** MEDIUM — monitoring principles are standard; specifics not retrieved for this model.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## What This Validation Certifies — and What It Does Not
**CERTIFIES:** That, in the specified high-incidence adult/adolescent screening population imaged on portable digital radiography, the ensemble DenseNet-121 model flags chest radiographs with findings suggestive of active pulmonary TB at a pre-specified operating point, with sensitivity/specificity (and pre-specified subgroups: HIV, prior TB, age, bacillary burden, DR vendor) estimated against a bacteriological reference standard, for use as a triage step ahead of confirmatory testing.

**DOES NOT CERTIFY:**
- That the model diagnoses TB or replaces bacteriological confirmation (Xpert/culture).
- Detection of paucibacillary/subclinical TB with normal or atypical CXR (label-ceiling limited).
- Equivalence to expert radiologist interpretation for the full range of thoracic pathology.
- Performance on pediatric (<adolescent) patients, non-screening/diagnostic populations, or fixed-DR/CT modalities.
- Generalization to DR vendors/sites not represented in the validation set.
- Any regulatory clearance (US or ex-US) or WHO prequalification — those are separate determinations.

## Footer
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification / 510(k)/De Novo / PMA / MAUDE / recalls, openFDA drug/biologic pathways where applicable — Drugs@FDA / SPL labeling / FAERS, and the Europe PMC / OpenAlex / Semantic Scholar / PubMed literature layer) and, where noted, web search. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*