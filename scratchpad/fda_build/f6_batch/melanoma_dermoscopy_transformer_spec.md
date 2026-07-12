# Clinical Validation Specification

**Generated:** 2026-07-11
**Source:** Live retrieval — ClinicalTrials.gov, openFDA, PubMed (+ web search where noted)

## Inputs
- **AI model:** ViT-hybrid (CNN stem → vision-transformer encoder) classifying dermoscopic images with paired metadata tokens (site, age, sex); outputs a malignancy probability, seven-point-checklist attribute predictions (atypical network, blue-white veil, irregular streaks), and a Monte Carlo–dropout uncertainty flag that abstains on low-confidence cases. Self-supervised contrastive pretraining; balanced sampling across skin-tone and lesion-type strata.
- **Clinical use case:** Binary benign vs. malignant classification of pigmented lesions with interpretable morphologic attributes and an uncertainty flag.
- **Patient population:** Adults presenting with suspicious or changing pigmented skin lesions.
- **Healthcare setting:** Dermatology outpatient clinics and teledermatology triage services.
- **Intended clinical claim:** *Not specified by team.* **Assumed most-defensible claim:** "As an adjunct to a qualified clinician, the model identifies dermoscopic images of pigmented lesions that warrant biopsy/specialist review, with sensitivity for melanoma non-inferior to a reference reader panel and a documented abstention behavior." This is an **assist/triage** claim, NOT an autonomous diagnosis or "rule-out biopsy" claim — the latter carries much higher regulatory and safety burden and is not supported by retrieved evidence.

## Output at a Glance

| Field | Output summary |
|---|---|
| 1. Study Design | Prospective, multi-reader multi-case (MRMC) reader study on consecutively enrolled lesions with histopathology ground truth; enrichment for melanoma. Retrieved dermoscopy trials are single-arm observational — insufficient alone. |
| 2. Sensor/Input Validation | Dermoscope acquisition validity (polarized vs. non-polarized, magnification, device model, image QC) is a pre-condition; must be established before any classification claim. |
| 3. Performance Benchmarks | No dermoscopy-specific regulatory benchmark retrieved; melanoma **sensitivity** is the governing metric. Targets must be set by the study team against a reader panel. |
| 4. Ground Truth | Histopathology from excision/biopsy is reference standard; noisy for borderline melanocytic lesions (dysplastic nevi) — this caps achievable performance. |
| 5. Sample Size | No powered estimate retrieved; must be computed for the melanoma-sensitivity endpoint with expert biostatistics input. |
| 6. Subgroups | Fitzpatrick skin tone, anatomic site (acral/nail/mucosal), age, lesion subtype, dermoscope type — all pre-specified. |
| 7. Regulatory Pathway | Likely US De Novo / class II with special controls (SaMD, CADx); no matching dermoscopy 510(k) retrieved in this pull. Regulatory counsel required. |
| 8. Post-Deployment Monitoring | Drift monitoring, abstention-rate tracking, missed-melanoma surveillance; MAUDE precedents retrieved are for dermatology *lasers*, not AI. |

## 1. Study Design
**Recommendation:** Run a **prospective, multi-reader multi-case (MRMC) reader study** on consecutively enrolled adults with pigmented lesions clinically selected for dermoscopy, with definitive histopathology as ground truth and enrichment for melanoma to power the sensitivity endpoint. Compare (a) clinician-alone vs. (b) clinician + model (adjunct) to establish the assist claim, and report standalone model performance as a secondary analysis. Pre-register the abstention rule and analyze abstained cases separately (they cannot be silently excluded from the denominator). For teledermatology, run a parallel arm on store-and-forward image quality representative of that channel.
**Rationale:** All retrieved dermoscopy/oncology-imaging studies are **single-arm OBSERVATIONAL** designs benchmarking AI vs. expert/pathology — e.g., AI-vs-endoscopist/pathologist comparison (NCT04864587), AUC-vs-pathology designs (NCT06703112), and CNN detection cohorts (NCT05193656, NCT03857373). These establish diagnostic accuracy but not the *clinician-with-AI* effect that an adjunct claim requires; an MRMC design is needed to capture reader interaction. No dermoscopy melanoma RCT or MRMC study was retrieved in this pull.
**Confidence:** MEDIUM — design is standard for CADx and consistent with retrieved observational precedents, but no on-point dermoscopy study was retrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 2. Sensor / Input Validation (Pre-Condition)
**Recommendation:** Before any classification metric is trusted, validate the **image-acquisition chain**: dermoscope make/model, contact vs. non-contact, **polarized vs. non-polarized illumination**, magnification, color calibration, resolution, and compression. Define an automated input-quality gate (focus, glare, framing, hair/bubble artifact) and report its rejection rate. Establish performance stability across ≥2–3 dermoscope devices spanning the clinic and teledermatology fleet, and test store-and-forward JPEG compression typical of the triage channel. Lesion-selection bias (which lesions get imaged) must also be documented as an input-validity threat.
**Rationale:** The model reads dermoscopic images, so acquisition physics directly drives feature distribution; polarization and device differences change vascular/network appearance the model keys on. The openFDA device terms included "dermoscopic," but the retrieval returned no dermoscopy imaging-device classification — acquisition standards must therefore be set by the team, not assumed. This is a pre-condition, not a footnote.
**Confidence:** MEDIUM — the threat is physically established; no device-specific standard retrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 3. Performance Benchmarks
**Recommendation:** Treat **melanoma sensitivity** (miss rate) as the governing safety metric, with specificity/false-positive (unnecessary-biopsy) rate as the co-primary efficiency metric; report AUROC, sensitivity/specificity at the deployed operating threshold, PPV/NPV at realistic melanoma prevalence, and separate metrics on abstained vs. non-abstained cases. **No dermoscopy-specific regulatory benchmark or numeric target was retrieved in this pull** — do not adopt any fixed sensitivity/specificity number as a standard. The operating threshold and non-inferiority margin vs. the reader panel must be **pre-specified by the study team and clinical experts**. Retrieved literature (e.g., gastric CNN detection, PMID 29335825; IPMN risk stratification, PMID 33465354) reports AUC-type metrics but is off-domain and not a valid benchmark for melanoma dermoscopy.
**Rationale:** Regulatory acceptance for a melanoma triage adjunct hinges on not missing melanoma; specificity governs biopsy burden. No dermoscopy melanoma performance figure was retrieved, so any number here would be invented — which is prohibited.
**Confidence:** LOW — no on-point benchmark retrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 4. Ground Truth Strategy
**Recommendation:** Use **histopathology of the excised/biopsied lesion** as the primary reference standard, read by ≥2 dermatopathologists with adjudication for discordance; for clinically benign lesions not biopsied, require a documented benign disposition with adequate clinical follow-up (e.g., stable at defined interval) to avoid verification bias. Explicitly quantify **inter-pathologist agreement**, because borderline melanocytic lesions (dysplastic/atypical nevi, spitzoid, early melanoma) have substantial reader disagreement — this label noise **caps** achievable sensitivity/specificity and must be reported as a ceiling. The seven-point-checklist auxiliary outputs need their own attribute-level reference labels from expert dermoscopists.
**Rationale:** Retrieved oncology-AI designs anchor to pathology (NCT06703112 "Pathological diagnosis"; NCT04864587 AI-vs-pathologist), confirming histopathology as the accepted reference. Verification bias (biopsying only suspicious lesions) is a known threat for this indication.
**Confidence:** MEDIUM — reference standard is well-established by precedent; label-noise magnitude for this specific population not retrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 5. Sample Size
**Recommendation:** **No powered sample-size estimate was retrieved and none can be responsibly invented here.** It must be computed by a biostatistician for the primary melanoma-sensitivity (non-inferiority) endpoint, driven by: expected melanoma prevalence/enrichment, the pre-specified non-inferiority margin, reader count and case count for the MRMC variance structure, the abstention rate (abstained cases inflate required enrollment), and subgroup targets (adequate melanoma counts within each skin-tone and site stratum). For scale context only, retrieved observational CNN cohorts enrolled n=5000 (NCT05193656, NCT03857373), n=584 (NCT06703112), and n=392 (NCT06540846) — these are context, not a basis for your power calculation.
**Rationale:** Sensitivity for a low-prevalence outcome (melanoma) with subgroup guarantees typically drives large enrollment or enrichment; the exact number depends on team-set parameters.
**Confidence:** LOW — no powered figure retrieved for this indication.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 6. Subgroup Requirements
**Recommendation:** Pre-specify and independently power (or at minimum report with CIs) the following subgroups: **Fitzpatrick skin tone I–VI** (physiologic threat — pigment competes with lesion melanin in dermoscopy; darker skin and acral/nail/mucosal melanomas are under-represented in typical training data); **anatomic site** (acral, subungual, mucosal, facial — morphology and metadata-token behavior differ); **age and sex**; **lesion subtype** (nevus vs. melanoma subtype, plus confounders like seborrheic keratosis, pigmented BCC, hemangioma); and **dermoscope/polarization type**. The model's balanced-sampler and metadata-token design must be validated to actually reduce (not just claim to reduce) skin-tone disparity — report per-tone sensitivity, not aggregate only.
**Rationale:** Population-specific validity here is physiology, not optics: pigmentation directly alters dermoscopic feature contrast, and acral/nail/mucosal sites are where AI dermoscopy tools most often fail. No retrieved record characterized skin-tone subgroup performance for this model class, so it must be tested prospectively.
**Confidence:** MEDIUM — threat is physiologically established; no subgroup performance data retrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## 7. Regulatory Pathway
**Recommendation:** Treat this as **Software as a Medical Device (computer-assisted detection/diagnosis, CADx)** in the US. The most likely route is a **De Novo request** (if no suitable predicate) or **510(k)** if an existing pigmented-lesion CADx predicate applies, in either case with **special controls** (clinical validation, labeling, human-factors, and cybersecurity). **No dermoscopy/pigmented-lesion AI classification 510(k), De Novo, or product code was retrieved in this pull** — the returned classifications (SDP ISH probe; PWD flow cytometry, K183592 / DEN160047; QFK tumor gene profiling) are in vitro hematology/oncology diagnostics, not dermoscopy imaging, and are **not valid predicates**. A dedicated FDA device-database and web search for pigmented-lesion CADx precedents is required. The assumed *adjunct/triage* claim is materially lower-risk than an autonomous "no-biopsy-needed" claim; the latter would raise the evidentiary bar substantially. This pipeline did not query non-US regulators (EMA/MHRA/PMDA), so EU MDR / UKCA classification is out of scope here and must be assessed separately.
**Rationale:** Per the retrieval-gap note, FDA drug/biologic and non-US regulator endpoints were not searched, and no on-point device precedent surfaced. Any pathway statement beyond "SaMD CADx, De Novo/510(k) with special controls" would overstate the evidence.
**Confidence:** LOW — no matching device precedent retrieved; pathway inferred from SaMD/CADx conventions.
**Expert review:** Expert working session — regulatory counsel required before any claims language is finalized.

## 8. Post-Deployment Monitoring
**Recommendation:** Deploy with a live monitoring plan covering: (1) **missed-melanoma surveillance** — reconcile model-benign dispositions against subsequent biopsy/pathology and registry data; (2) **abstention-rate and input-quality drift** — alarm if MC-dropout abstention or image-QC rejection rates shift across sites/devices; (3) **population/device drift** — new dermoscope models, teledermatology image characteristics, case-mix shifts; (4) **per-skin-tone and per-site performance tracking** so disparities don't emerge silently post-launch; (5) a complaint/adverse-event reporting channel consistent with device post-market requirements. Note that the retrieved MAUDE/recall records (dermatology **surgical lasers** — report 2914019-2008-00005/-00010; recalls Z-1396-2019, Z-1381-2019) are hardware-device signals, not AI-software failures — useful only as a reminder that dermatology-device post-market reporting is active, not as failure-mode analogs for this model.
**Rationale:** Software CADx failure modes (data drift, silent subgroup degradation, over-abstention) differ from the hardware/sterility failures in the retrieved MAUDE/recall records; monitoring must be designed for the model's actual failure surface, with missed melanoma as the sentinel harm.
**Confidence:** MEDIUM — monitoring principles are standard; no AI-specific post-market signal for this indication retrieved.
**Expert review:** Expert working session — assumptions need expert judgment before finalizing.

## What This Validation Certifies — and What It Does Not
**CERTIFIES:** That, on prospectively enrolled adults with clinically suspicious pigmented lesions imaged on the validated dermoscope fleet, the model — used as an adjunct to a qualified clinician — detects melanoma with sensitivity non-inferior to a reference reader panel against histopathologic ground truth, with characterized specificity, a defined and separately-analyzed abstention behavior, and reported performance within pre-specified skin-tone, anatomic-site, and device subgroups.
**DOES NOT CERTIFY:**
- Autonomous diagnosis or any "biopsy not needed" / rule-out claim.
- Performance on lesion types, body sites (e.g., acral/nail/mucosal), or skin tones not adequately represented in the enrolled cohort.
- Performance on dermoscope models, polarization modes, or teledermatology image pipelines not tested.
- That the seven-point-checklist attribute outputs are individually clinically reliable (auxiliary outputs need their own validation).
- Accuracy beyond the ceiling imposed by inter-pathologist label disagreement on borderline melanocytic lesions.
- Regulatory clearance/approval (US or ex-US) or reimbursement.
- Generalization to primary-care or non-dermatology settings, or to non-pigmented / amelanotic malignancies.

## Footer
*Output generated from live retrieval (ClinicalTrials.gov, openFDA device classification / 510(k)/De Novo / PMA / MAUDE / recalls, openFDA drug/biologic pathways where applicable — Drugs@FDA / SPL labeling / FAERS, and the Europe PMC / OpenAlex / Semantic Scholar / PubMed literature layer) and, where noted, web search. Cited identifiers should be verified before use. Benchmark numbers are literature-derived, not regulatory standards. Every field requires expert review before clinical or commercial application.*