# Clinical Validation Specification

**Generated:** 2026-07-11
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed (+ web search where noted)

## Inputs
- **AI model:** EfficientNet-B4 ordinal-regression classifier on macula-centered color fundus photographs (456×456, CLAHE + circular FOV crop, test-time augmentation, attention-gated lesion evidence maps, upstream quality-assessment gating sub-network). Outputs a 5-level DR severity grade.
- **Clinical use case:** Grade fundus photographs on the 5-point severity scale and flag cases at/above the referral threshold for specialist review.
- **Patient population:** Adults with diabetes mellitus in routine annual eye-screening.
- **Healthcare setting:** Primary-care and community optometry screening with tele-ophthalmology overread.
- **Intended clinical claim (inferred — stated as assumption):** *Assumption:* the most defensible claim is a **diagnostic-aid / autonomous-screening claim for detecting more-than-mild diabetic retinopathy (mtmDR / referable DR) from gradable fundus images in previously undiagnosed adults with diabetes**, matching the cleared indication of the FDA precedents (IDx-DR, EyeArt, AEYE-DS). It is NOT a claim to grade DME, glaucoma, or other retinal disease, and NOT a treatment claim.

## Output at a Glance

| Field | Output summary |
|---|---|
| 1. Study Design | Prospective, multi-site, masked comparison vs. adjudicated reference standard in the intended screening population; mirrors the pivotal design of the PIB-code predicates. |
| 2. Sensor / Input Validation | Camera/model-agnostic image-acquisition validation + prospective validation of the ungradable-gating sub-network is a hard pre-condition (see MAUDE/recall signals on fundus imaging). |
| 3. Performance Benchmarks | mtmDR sensitivity/specificity vs. reference; no regulatory numeric standard retrieved — team must pre-specify targets against predicate labeling. |
| 4. Ground Truth | Adjudicated reading-center grading on a validated scale (ICDR / ETDRS-based), ideally with a stereo/wide-field or OCT-supported reference; label noise caps achievable performance. |
| 5. Sample Size | Powered on lower-bound of sensitivity AND specificity CIs; must enrich for referable/severe cases. No retrieved N — must be computed by team. |
| 6. Subgroups | Pre-specified: camera model/vendor, image quality strata, skin/fundus pigmentation, cataract/media opacity, prior DR history, glycemic severity. |
| 7. Regulatory Pathway | US Class II, product code **PIB**, 510(k) via predicates K203629 / K223357 / K240058. |
| 8. Post-Deployment Monitoring | Ungradable rate, referral rate, camera-drift, subgroup performance, false-negative surveillance; MAUDE/recall precedents define failure modes. |

---

## 1. Study Design
**Recommendation:** Run a **prospective, multi-site, pre-registered pivotal study** in the *actual* intended-use population (adults with diabetes presenting for screening at primary-care/community-optometry sites), operating the full pipeline (quality gate → grade → referral flag) on images captured by the operators and cameras used in real deployment. Compare each subject's device output against an independent, masked, adjudicated reference standard. Report the referable-DR (mtmDR) diagnostic accuracy as the primary analysis and the 5-level grading agreement as secondary. Include the ungradable output as a defined study outcome, not an exclusion. Pre-register on ClinicalTrials.gov.

**Rationale:** The three cleared PIB-code precedents were all authorized on prospective pivotal accuracy studies in intended-use screening populations: IDx-DR (510(k) K203629, product code PIB, Digital Diagnostics), EyeArt v2.2.0 (K223357, Eyenuk), AEYE-DS (K240058, Aeye Health). The retrieved literature is almost entirely retrospective public-dataset development work (e.g., EfficientNet-B5 severity from fundus, OpenAlex W3114803724; ensemble EfficientNet, PMID 39695310; calibration benchmark, PMID 42078464) — useful for algorithm development but categorically insufficient for a clinical/regulatory claim because it does not test the acquisition chain or the intended population prospectively. No matching prospective pivotal NCT for THIS model was retrieved; the team should design to the predicate template. A calibration-focused benchmark (PMID 42078464) supports adding a prospective **calibration** analysis given the ordinal-regression design.
**Confidence:** HIGH (design template) / MEDIUM (specifics)
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 2. Sensor / Input Validation (Pre-Condition)
**Recommendation:** Before any accuracy claim is trusted, establish two things prospectively: (a) **image-acquisition validity across every camera make/model and operator type** intended for deployment — the device claim must be tied to a named list of validated fundus cameras and capture protocols, not "fundus images" in the abstract; and (b) **prospective validation of the quality-assessment gating sub-network** — measure the ungradable rate, and critically, the rate of *false-pass* (poor-quality images the gate lets through) and *false-fail* images, because a mis-gated image poisons the downstream grade. Validate laterality handling (which eye is which) explicitly.

**Rationale:** Post-market signals show that fundus imaging failures are real and consequential: a Class II recall of NIDEK fundus-camera filing software where **the left-eye image could be saved as the right-eye image** (recall Z-2046-2013) — a direct laterality/labeling threat to any per-eye grading system — and MAUDE injury reports involving fundus lenses/instruments (MW5105451; 2955842-2022-15143). CLAHE + circular-crop preprocessing and 456×456 downsampling can interact with sensor resolution, illumination, and compression differently across camera vendors; this is a physics threat, not a tuning detail. The predicates are cleared for specific camera systems, reinforcing that camera scope is part of the indication.
**Confidence:** HIGH
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 3. Performance Benchmarks
**Recommendation:** Pre-specify co-primary endpoints of **sensitivity and specificity for referable (more-than-mild) DR**, each with a two-sided 95% CI, and require the CI lower bound to exceed a team-set target. Report per-image ungradable rate as a bounded operational endpoint. Report 5-level grading agreement (quadratic-weighted kappa) and calibration (given ordinal regression) as secondary. **No regulatory numeric performance standard was retrieved** for product code PIB — FDA cleared the predicates on sponsor-defined targets, not a fixed threshold. The historically-referenced screening target (≈85% sensitivity / ≈85% specificity from the IDx-DR pivotal literature) is a *literature/precedent* figure, **not a regulatory standard**, and must be confirmed by the team against current predicate labeling and set by expert consensus.

**Rationale:** Retrieved literature reports high internal accuracy (ensemble EfficientNet, PMID 39695310; multi-tasking EfficientNet-B5, OpenAlex W4285153837) but on retrospective curated datasets — these are development benchmarks, not deployable targets, and typically overstate field performance. The calibration benchmark (PMID 42078464) warns that frozen/transfer models can be miscalibrated, directly relevant to an ordinal-regression output. Any number entered as a target must be pre-registered, not derived post hoc.
**Confidence:** MEDIUM
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized

## 4. Ground Truth Strategy
**Recommendation:** Use an **independent masked reading center** grading on a validated scale (International Clinical DR severity scale / ETDRS-based), with ≥2 graders plus adjudication of disagreements, and a pre-specified reference imaging protocol richer than the device input — e.g., stereoscopic or wide-field photography and/or OCT to establish DME status where referable DR includes DME. Lock the reference standard and grader training before enrollment. Report inter-grader reliability; achievable device sensitivity/specificity is **capped by reference-standard reliability** — if adjudicated kappa is modest, state that the model cannot be credited beyond that ceiling.

**Rationale:** The DR severity scale is ordinal and grader-dependent; the model's ordinal-regression objective assumes a monotonic truth that only a rigorous reference standard can supply. Meta-analytic evidence combining OCT + fundus (PMID 40171193) and fusion approaches (MultiRetNet Fundus-OCT, PMID 42346900) supports OCT-supported reference for the DME component. Reading-center adjudication is the reference method used by the cleared predicates. Label noise is the binding ceiling constraint here.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 5. Sample Size
**Recommendation:** Power the study on the **lower confidence bound of BOTH sensitivity and specificity** for referable DR (co-primary), which requires **enrichment for referable/severe cases** since these are minority events in a screening population — otherwise the sensitivity CI will be uninformative. Compute N from the pre-specified target performance, expected prevalence of referable DR in the screening population, expected ungradable rate, and desired CI half-width, then inflate for per-subject clustering (two eyes) and for adequately-sized subgroups (field 6). **No sample-size figure was retrieved** from the records for this indication — this must be computed by the study statistician; do not adopt a number from the development literature.

**Rationale:** No retrieved NCT or predicate summary in this block states an enrollment number for THIS model, so any N would be invented. The controlling design fact is that referable-DR prevalence in routine screening is low, so total N is driven by the need to accumulate enough true-positive cases to bound sensitivity — the predicates addressed this via prospective enrollment at multiple sites and, where needed, case enrichment.
**Confidence:** LOW
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 6. Subgroup Requirements
**Recommendation:** Pre-specify and independently power (or at minimum pre-specify with reporting) these subgroups: (1) **camera make/model and site** — the single most important shift for an imaging model; (2) **image-quality strata** (borderline-gradable vs. high-quality); (3) **fundus/skin pigmentation** — retinal pigmentation and media differences alter fundus color/contrast and interact with CLAHE preprocessing (a physiology/physics threat, not optional); (4) **media opacity / cataract**, common in this population and a major cause of ungradable images; (5) **prior DR / diabetes duration and glycemic severity**; (6) **age and diabetes type**. Report performance and ungradable rate per subgroup.

**Rationale:** Imaging-model failure is dominated by domain shift across scanner/vendor and by physiological variation in the imaged tissue; the NIDEK recall (Z-2046-2013) and the vendor-specific clearances of the predicates show acquisition variability is the live threat. Preprocessing (CLAHE, circular crop) can behave differently across pigmentation and media clarity, so pigmentation must be a pre-specified subgroup, not a post-hoc check. No subgroup performance breakdown was retrieved from the literature records, so these must be generated de novo.
**Confidence:** MEDIUM
**Expert review:** Expert working session — assumptions need expert judgment before finalizing

## 7. Regulatory Pathway
**Recommendation:** Pursue **US FDA 510(k), Class II, product code PIB** ("Diabetic Retinopathy Detection Device," Ophthalmic panel), citing predicate(s) **K203629 (IDx-DR)**, **K223357 (EyeArt v2.2.0)**, and/or **K240058 (AEYE-DS)**. Decide early whether the claim is **autonomous detection** (as IDx-DR/EyeArt/AEYE-DS were cleared) or **assistive/adjunct to tele-ophthalmology overread**, because the intended-use statement, the labeled camera list, and the pivotal design all flow from that choice. The device is a medical-device claim, not a wellness claim. (Note: product code OXW is an electrical stimulator for DR treatment — not relevant.)

**Rationale:** All three retrieved predicates sit under PIB and establish a well-trodden De Novo-then-510(k) lineage for autonomous DR screening, making a novel pathway unnecessary. This block did **not** query non-US regulators (EMA/MHRA/PMDA) or drug/biologic pathways, so any ex-US or CE strategy is out of scope here and must be assessed separately. The claim language, autonomous-vs-assistive framing, and camera scope require regulatory counsel.
**Confidence:** HIGH (pathway) / MEDIUM (claim scope)
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized

## 8. Post-Deployment Monitoring
**Recommendation:** Establish continuous monitoring for: (1) **ungradable/rejection rate** per site and per camera — a rising rate signals acquisition or gate drift; (2) **referral rate drift** vs. pivotal baseline; (3) **camera/software change control** — any firmware or capture-software update triggers re-validation (the NIDEK laterality recall, Z-2046-2013, arose from imaging software behavior); (4) **subgroup performance surveillance** across pigmentation/quality/camera; (5) **false-negative surveillance** — link flagged-not-referred patients to downstream ophthalmology outcomes so missed referable DR is detectable; (6) **MAUDE reporting** consistent with fundus-device adverse-event precedents (MW5105451; 2955842-2022-15143). Pre-specify recalibration triggers given ordinal-regression calibration sensitivity (PMID 42078464).

**Rationale:** Post-market records for fundus devices show the dominant real-world harms are laterality/labeling errors and image-handling failures (recall Z-2046-2013) rather than pure model error — monitoring must therefore watch the acquisition and gating chain, not just the classifier. False-negative surveillance is the safety-critical loop for a screening triage tool where a missed referral is the high-consequence event.
**Confidence:** MEDIUM
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized

---

## What This Validation Certifies — and What It Does Not
**CERTIFIES:** That, on gradable macula-centered color fundus photographs captured with the specific validated camera(s) and operators in adults with diabetes attending routine primary-care/community-optometry screening, the system detects more-than-mild (referable) diabetic retinopathy with sensitivity and specificity whose 95% CI lower bounds meet the pre-specified targets, against an adjudicated reading-center reference standard, with a bounded ungradable rate and demonstrated performance across pre-specified camera, image-quality, and fundus-pigmentation subgroups.

**DOES NOT CERTIFY:**
- Accuracy on images from cameras, resolutions, or capture protocols not in the validated set.
- Detection of DME, glaucoma, AMD, or any retinal disease other than the DR grades claimed.
- Performance in populations outside the studied one (non-diabetic, pediatric, symptomatic/referred rather than screening cohorts).
- That the 5-level grade equals ophthalmologist grading in ungradable or borderline-quality images (those are gated out, not solved).
- Physiological or histological ground truth — it certifies agreement with a photographic reference standard, itself capped by grader reliability.
- Any treatment benefit, patient-outcome improvement, or reduction in vision loss.
- Regulatory clearance — a passing study supports, but does not constitute, FDA 510(k) authorization.
- Any ex-US regulatory status (EMA/MHRA/PMDA not queried by this pipeline).

## Footer
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification / 510(k)/De Novo / PMA / MAUDE / recalls, openFDA drug/biologic pathways where applicable — Drugs@FDA / SPL labeling / FAERS, and the Europe PMC / OpenAlex / Semantic Scholar / PubMed literature layer) and, where noted, web search. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*