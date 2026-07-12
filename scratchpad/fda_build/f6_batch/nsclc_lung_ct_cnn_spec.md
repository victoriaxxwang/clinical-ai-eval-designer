# Clinical Validation Specification

**Generated:** 2026-07-11
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed (+ general regulatory knowledge where noted, flagged as lower confidence)

## Inputs
- **AI model:** Dual-branch nodule characterizer — inflated 3D ResNet-50 CNN on 64×64×64 (1 mm iso) voxel patches + hand-crafted radiomics branch (wavelet first-order, GLCM, GLRLM texture), gated multi-instance attention pooling at scan level, FC head emitting calibrated malignancy probability + auxiliary doubling-time regression. Upstream U-Net does candidate detection/segmentation.
- **Clinical use case:** Per-nodule calibrated malignancy-risk score + estimated growth rate to triage biopsy vs. surveillance on screen-detected indeterminate pulmonary nodules.
- **Patient population:** Adults 50–80, ≥20 pack-year smoking history, indeterminate pulmonary nodules on low-dose screening CT (LDCT).
- **Healthcare setting:** Outpatient lung cancer screening programs at tertiary imaging centers.
- **Intended clinical claim (INFERRED — stated as assumption):** *"For LDCT-detected indeterminate solid/subsolid nodules in a high-risk screening population, the model outputs a calibrated malignancy-risk score that risk-stratifies nodules to support (not replace) radiologist and multidisciplinary biopsy-vs-surveillance decisions."* I assume a **concurrent-read decision-support / risk-stratification** claim, NOT an autonomous diagnostic or biopsy-mandating claim, and NOT a standalone growth-rate measurement claim. This is the most defensible framing and it materially shapes fields 3, 7, and the certification statement.

## Output at a Glance

| Field | Output summary |
|---|---|
| 1. Study Design | Multi-center retrospective MRMC reader study on consecutive LDCT screening cohort with histopathology/≥2-yr-follow-up truth; prospective silent-mode before any workflow claim |
| 2. Sensor/Input Validation | Pre-condition: LDCT acquisition/reconstruction-kernel/slice-thickness/vendor validity + upstream U-Net detection sensitivity must be locked before risk-score claims |
| 3. Performance Benchmarks | AUC + calibration + decision-curve vs. Lung-RADS/Brock-type baseline; **no numeric benchmark retrieved from grounded context — team must pre-specify** |
| 4. Ground Truth | Tissue diagnosis where biopsied; ≥24-month imaging stability for non-biopsied; multi-reader adjudication. Label-noise ceiling explicit |
| 5. Sample Size | Event-driven (malignant nodules), MRMC-powered; **no retrieved n is on-point — must be computed by team statistician** |
| 6. Subgroups | Nodule type (solid/part-solid/GGN), size strata, vendor/kernel/dose, sex, and CT-relevant physiology; pre-specified |
| 7. Regulatory Pathway | Likely 510(k), CADx/nodule-characterization, precedent product code OEB (K193216); confirm predicate/De Novo with counsel |
| 8. Post-Deployment | Calibration drift, scanner-fleet shift, subgroup performance, MAUDE-style event capture, human-override tracking |

## 1. Study Design
**Recommendation:** A **multi-reader, multi-case (MRMC) retrospective study** on a consecutively-enrolled LDCT screening cohort is the primary vehicle, comparing radiologist decisions **with vs. without** the model (concurrent read), with a locked truth panel. This must be followed by a **prospective silent-mode (shadow) deployment** at ≥2 tertiary centers before any workflow-integrated claim. Because the intended output is a triage/risk score, the design must measure not just discrimination but **decision impact** (biopsy vs. surveillance reclassification) and downstream over-/under-referral.
**Rationale:** The retrieved lung-imaging AI precedents are CADe/CADx image devices (syngo.CT Lung CAD, K193216, product code OEB; Lung Vision System, K183593, code LLZ) — device-classification, not efficacy, records; they establish that this class is evaluated as software reader-support, consistent with an MRMC design. The retrieved literature is uniformly **early-stage algorithm-development work** on related dual-branch architectures (dual-branch cross-attention multi-subtype classification, PMID 42125996; dual-branch attention IASLC grading multicenter study, PMID 41933519; DecX-Net subsolid nodule segmentation, PMID 42235590; NGP-Net growth prediction, PMID 41557569) — these confirm technical plausibility and the multicenter norm but **none is a prospective clinical-utility trial**. The retrieved ClinicalTrials.gov records are all therapeutic NSCLC drug trials (e.g., NCT04738487, NCT07154706) and are **not applicable** to imaging-triage validation. No screening-triage clinical-utility trial was retrieved.
**Confidence:** MEDIUM — design class is well-supported by device precedent and literature norms; absence of a retrieved utility-trial template lowers it.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 2. Sensor / Input Validation (Pre-Condition)
**Recommendation:** Before ANY malignancy-risk claim, validate the **imaging input chain**: (a) LDCT acquisition parameters (dose level, slice thickness ≤ the resampling target, reconstruction kernel, vendor/model) across the actual scanner fleet; (b) the **1 mm isotropic resampling** step's behavior on native anisotropic/thick-slice screening data; (c) the **upstream U-Net detector's per-nodule sensitivity and false-positive rate** — because a nodule the detector misses is invisible to the risk model, detector recall is a hard ceiling on the whole pipeline; (d) segmentation reproducibility, since the radiomics branch (wavelet/GLCM/GLRLM) is highly sensitive to segmentation boundary and voxel-intensity discretization.
**Rationale:** Radiomics texture features are physics-dependent: kernel, dose, and reconstruction changes shift GLCM/GLRLM values independent of biology — a documented reproducibility threat, not an optics detail. The retrieved dual-energy CT nodule work (PMID 41365825) and multicenter grading study (PMID 41933519) implicitly rely on harmonized acquisition, reinforcing that input variance must be controlled/tested. The gated MIL pooling means scan-level output is driven by a single "most suspicious" nodule, so a detector miss or a segmentation error on that nodule dominates error — this coupling must be quantified end-to-end, not per-module in isolation.
**Confidence:** MEDIUM — radiomics acquisition-sensitivity is well-established generally; no retrieved record quantifies it for THIS pipeline.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 3. Performance Benchmarks
**Recommendation:** Pre-specify a primary discrimination metric (ROC-AUC for nodule malignancy) **and** a calibration metric (calibration slope/intercept, Brier score) — calibration is essential because the claim is a "calibrated risk score" driving triage. Add a **decision-curve / net-benefit** analysis and reclassification (NRI) versus a clinical baseline. The comparator baseline should be an established clinical risk tool (Lung-RADS categorization and/or a Brock/PanCan-type nodule malignancy model) — **note these standard tools were NOT in the grounded retrieval and must be sourced and version-locked by the team.**
**Rationale:** **No numeric performance benchmark (AUC, sensitivity, specificity target) was retrieved from the grounded context** — the literature records report architectures, not a regulatory or consensus threshold, and no 510(k) summary performance figure was returned. Therefore: *no established benchmark retrieved — performance targets must be set by the study team / expert*, ideally as non-inferiority-or-better vs. the pre-specified clinical baseline rather than an absolute AUC. Auxiliary doubling-time regression needs its own separate accuracy metric (e.g., agreement vs. volumetry on serial scans) and should NOT be claimed unless independently validated.
**Confidence:** LOW — no on-point benchmark numbers retrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 4. Ground Truth Strategy
**Recommendation:** Composite reference standard: (1) **histopathology** (biopsy/resection) for nodules that undergo tissue sampling — the highest-tier truth; (2) for non-sampled nodules, **≥24 months of imaging stability** as a surrogate for benignity, with volumetric confirmation; (3) benign/malignant adjudication by ≥2 blinded thoracic specialists with a documented tie-break. Record the truth tier per nodule and analyze robustness to truth definition.
**Rationale:** Screening cohorts are dominated by benign nodules, so most negatives are established by follow-up stability, not tissue — a **label-noise source that caps achievable specificity/PPV**: indolent malignancies and lost-to-follow-up cases bias the "benign" pool. This ceiling must be stated explicitly. The doubling-time auxiliary output requires **serial-scan volumetric truth**, a distinct and scarcer label than the malignancy label. No retrieved record supplies a validated reference-standard protocol for this population; LIDC-IDRI/NLST-style truth conventions are the field norm but were **not in the grounded retrieval** and must be confirmed.
**Confidence:** MEDIUM — approach is standard; specifics unretrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 5. Sample Size
**Recommendation:** Size the study as **event-driven on the number of confirmed malignant nodules** (the minority class), not total scans, and power the MRMC reader comparison for the primary AUC/net-benefit difference with the pre-specified baseline. Include enough nodules within each key subgroup (field 6) to estimate — not just pool — subgroup performance.
**Rationale:** **No applicable sample size was retrieved.** The ClinicalTrials.gov enrollments returned (n=107 NCT03786692; n=180 NCT07154706; n=1264 NCT04738487; n=432 NCT00290953) are therapeutic-trial populations and are **not valid references** for an imaging MRMC diagnostic study. Therefore *no established sample size retrieved — must be computed by the team's statistician* using the target effect size, expected malignancy prevalence in the screening cohort, reader variance, and multiplicity across subgroups.
**Confidence:** LOW — no on-point retrieved figure.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 6. Subgroup Requirements
**Recommendation:** Pre-specify and independently power (or at minimum pre-register as estimation targets) these subgroups: **nodule composition** (solid / part-solid / pure ground-glass) — the dominant performance-modifier; **nodule size strata** (e.g., Lung-RADS size bands); **scanner vendor / reconstruction kernel / dose level** (the acquisition-shift threat from field 2); **sex**; **age bands within 50–80**; and where available comorbid emphysema/fibrosis background. Report performance and calibration per subgroup, not just overall.
**Rationale:** The concrete population/physics validity threat here is **acquisition-and-morphology shift**, not demographics alone: subsolid and GGN nodules behave differently for both the U-Net detector and radiomics texture features (supported by dedicated subsolid-segmentation work, PMID 42235590, and IASLC-grade texture studies, PMID 41933519 / 41365825). The multicenter framing of those retrieved studies underscores that cross-site/scanner generalization must be tested as pre-specified subgroups.
**Confidence:** MEDIUM — threat structure well-supported by retrieved literature.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 7. Regulatory Pathway
**Recommendation:** Most defensible route is **510(k)** as computer-assisted-detection/characterization radiology software (CADx / nodule characterization), leveraging the retrieved lung-CAD precedent **product code OEB (syngo.CT Lung CAD, K193216)**; the Lung Vision navigation device (K183593, code LLZ) is a **different device type (bronchoscopic navigation) and is not a suitable predicate**. If the calibrated malignancy-risk + triage claim exceeds existing CADx predicates, a **De Novo** may be required. The auxiliary doubling-time output and any "biopsy-vs-surveillance" language materially raise the claim's risk tier and must be scrubbed with counsel — an autonomous/diagnostic claim would push toward higher scrutiny.
**Rationale:** The device-classification records confirm an established AI-lung-imaging 510(k) lane (OEB). MAUDE/PMA/recall records retrieved (dual-chamber pulse generators P980049, P050023; Atrium drains; OMNIlife liners) are **unrelated cardiac/orthopedic hardware** and carry no pathway relevance here — they are noise from the "dual"/"branch" query terms. Drug pathways (NSCLC trials) are irrelevant to a device. Per the coverage note, **Drugs@FDA/SPL/FAERS and non-US regulators (EMA/MHRA/PMDA) were not queried**, and no systematic predicate search was performed — treat the OEB precedent as a starting point, not a confirmed pathway.
**Confidence:** MEDIUM — precedent product code is real and on-point; predicate adequacy unconfirmed.
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized.

## 8. Post-Deployment Monitoring
**Recommendation:** Implement continuous monitoring for: (1) **calibration drift** of the risk score (recurrent calibration-slope checks) — critical since triage depends on calibrated probabilities; (2) **scanner-fleet / kernel / dose distribution shift** vs. the validation distribution, with automated input-conformance gating; (3) **subgroup performance tracking** (nodule type, vendor) to catch silent degradation; (4) **human-override and downstream-outcome capture** (biopsy yield, missed cancers, unnecessary biopsies); (5) a **device-event reporting channel** analogous to MAUDE for false-negative/false-positive harms.
**Rationale:** The retrieved MAUDE injury reports and Class II recalls (e.g., oxidation-failure liner recall Z-2480-2019) — though from unrelated devices — illustrate the **post-market failure-signal discipline** expected of cleared devices: monitoring, event capture, and recall readiness. For this model, the highest post-deployment risks are calibration decay and acquisition shift (fields 2/3), which are silent unless actively surveilled. No product-specific post-market data was retrieved.
**Confidence:** MEDIUM — monitoring principles supported; specifics are judgment.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## What This Validation Certifies — and What It Does Not
**CERTIFIES:** That, for LDCT-detected indeterminate pulmonary nodules in adults 50–80 with ≥20 pack-year history at tertiary screening centers using the validated scanner/kernel/dose configurations and pre-specified subgroups, the model's calibrated malignancy-risk score discriminates and calibrates at or above the pre-specified clinical baseline and improves reader triage decisions when used as concurrent decision support.
**DOES NOT CERTIFY:**
- The auxiliary **doubling-time / growth-rate** output, which requires separate serial-scan volumetric validation.
- **Autonomous** malignancy diagnosis or any mandate to biopsy/defer — the tool is reader support only.
- Performance on **nodule types, scanners, kernels, or dose settings** outside the validated distribution, or in non-screening/incidental-nodule populations.
- **Detector-missed nodules** — pipeline validity is capped by upstream U-Net sensitivity.
- **True physiological malignancy status** beyond the composite reference standard, whose label noise (follow-up-based benignity) caps achievable specificity/PPV.
- **Regulatory clearance** — this specifies the evidence a submission would need, not an FDA decision.
- Generalization to **non-US regulatory contexts** (EMA/MHRA/PMDA not queried).

## Footer
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification / 510(k)/De Novo / PMA / MAUDE / recalls, openFDA drug/biologic pathways where applicable — Drugs@FDA / SPL labeling / FAERS, and the Europe PMC / OpenAlex / Semantic Scholar / PubMed literature layer) and, where noted, web search. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*