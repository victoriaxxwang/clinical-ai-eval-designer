# Grounded Clinical AI Validation Specification
## System under evaluation: Image-based skin-lesion malignancy risk / biopsy-referral decision support

*All identifiers below were retrieved and verified this session: PMIDs against PubMed E-utilities,
DOIs independently against Crossref, FDA records against openFDA (device classification / 510(k) /
De Novo / PMA endpoints), and NCT numbers against the ClinicalTrials.gov v2 API. Numeric values are
labeled **[retrieved-from-source]** or **[study-defined-placeholder]**. No unverified identifier appears.*

---

### 1. Study Design

**Recommendation.** Evaluate as a diagnostic-accuracy + clinical-utility study, not a standalone
classifier benchmark. Two tiers: (a) a **retrospective/prospective diagnostic-accuracy study** on
consecutively enrolled lesions of concern with histopathology ground truth (STARD 2015 / QUADAS-2
design), and (b) a **prospective reader/decision study** measuring how the tool changes the
non-specialist's biopsy/refer decision (unaided vs aided arms), reported per DECIDE-AI. Because the
claim is a decision-support claim for non-specialists, the pivotal endpoint is the *change in the
human decision*, not the model's isolated AUC.

**Rationale.** Reporting and quality frameworks are established: STARD 2015 for diagnostic-accuracy
reporting (PMID 26511519 · DOI 10.1136/bmj.h5527), QUADAS-2 for risk-of-bias appraisal of such
studies (PMID 22007046 · DOI 10.7326/0003-4819-155-8-201110180-00009), TRIPOD+AI for prediction-model
reporting (PMID 38626948 · DOI 10.1136/bmj-2023-078378), and DECIDE-AI for early-stage clinical
evaluation of decision-support AI (PMID 35585198 · DOI 10.1038/s41591-022-01772-9). Prior
human-vs-machine and human–computer-collaboration studies in this exact domain establish the
reader-study design as the field norm (Haenssle 2018, PMID 29846502; Tschandl 2019, PMID 31201137;
Tschandl 2020 collaboration, PMID 32572267). The FDA De Novo that created this device class
(DEN230008) is explicitly an *adjunctive second-read* indication, reinforcing that the human-in-loop
decision is the object of study.

**Confidence: HIGH.**

**Expert review needed.** Biostatistician + dermatologist to fix the co-primary endpoints (accuracy
vs decision-change) and the enrollment frame (consecutive lesions of concern vs enriched).

---

### 2. Input / Signal Validation — image-quality gate before output is interpreted

**Recommendation.** Validate the **image-acquisition/quality gate as a distinct pre-condition** with
its own acceptance criteria *before* any malignancy score is interpreted: (i) an automatic
image-quality classifier (focus, illumination, framing, lesion centering, scale) with a
pass/repeat/reject decision, (ii) demonstration that the gate's pass-rate and the downstream accuracy
are stable across device/camera models and across the full Fitzpatrick I–VI range, and (iii)
capture-artifact robustness testing (e.g. ink markings, hair, rulers). Report the fraction of
encounters rejected by the gate and the accuracy conditional on "pass."

**Rationale.** Input-signal integrity is a documented failure mode specific to image-based skin AI:
surgical/ink skin markings alone significantly changed a melanoma CNN's output (Winkler 2019,
PMID 31411641 · DOI 10.1001/jamadermatol.2019.1735), and systematic review of algorithm-based
smartphone skin-cancer apps found performance highly sensitive to image acquisition and poor
real-world reliability (Freeman 2020, PMID 32041693 · DOI 10.1136/bmj.m127). The reference dermatoscopic
dataset used to train much of the field (HAM10000, PMID 30106392 · DOI 10.1038/sdata.2018.161) is
curated/high-quality, so a real-world quality gate is needed to bridge the acquisition gap.

**Confidence: HIGH** (that a gate is required); **MEDIUM** (on specific gate thresholds — none is an
established standard).

**Expert review needed.** Imaging physicist / device engineer to define quality metrics and the
reject threshold; these are **[study-defined-placeholder]**, not regulatory numbers.

---

### 3. Performance Benchmarks

**Recommendation.** Pre-register co-primary operating points as **[study-defined-placeholder]** targets
and justify them clinically, e.g. a high-melanoma-sensitivity operating point (rule-out for
non-specialists) with an explicitly reported specificity/biopsy-ratio trade-off, plus per-cancer-type
sensitivity (melanoma, BCC, SCC). Benchmark against (a) the unaided non-specialist and (b) the
aided non-specialist — superiority of the aided decision is the claim to be proven. Do **not** state
any fixed sensitivity/specificity as an established regulatory standard.

**Rationale.** No numeric accuracy threshold is mandated by the FDA classification for this device
type (product codes QZS/OYD/ONV are all *adjunctive*, explicitly "not for standalone diagnosis").
Diagnostic-accuracy evidence for computer-assisted dermoscopy is summarized in the Cochrane review
(Dinnes 2018, PMID 30521691 · DOI 10.1002/14651858.CD013186), and the human/machine comparative
performance literature (Esteva 2017, PMID 28117445 · DOI 10.1038/nature21056; Tschandl 2019,
PMID 31201137 · DOI 10.1016/S1470-2045(19)30333-X) provides the comparator context but *not* an
accepted pass/fail cut-off. The USPSTF 2023 evidence review (PMID 37071090 · DOI 10.1001/jama.2023.3262)
underlines that even the upstream clinical question (visual skin-cancer screening) has limited
outcome evidence, so benchmarks must be framed as study-defined and clinically justified.

**Confidence: HIGH** (that no established numeric benchmark exists); **LOW** (any specific target
number — investigator-set).

**Expert review needed.** Dermatology + primary-care clinicians to set the clinically acceptable
missed-melanoma rate and biopsy-ratio ceiling.

---

### 4. Ground Truth Strategy

**Recommendation.** **Histopathology as the primary reference standard** for biopsied lesions, read
by ≥2 dermatopathologists with adjudication of discordance, plus a **pre-specified plan for
non-biopsied lesions** (clinical + dermoscopic follow-up at a defined interval as a composite
reference to mitigate verification/work-up bias). Report the reference-standard concordance itself.

**Rationale.** Melanocytic-lesion histopathology has documented interobserver variability —
pathologists' diagnoses of melanocytic proliferations were only moderately concordant (Elmore 2017,
PMID 28659278 · DOI 10.1136/bmj.j2813) — so a single-reader gold standard is insufficient. QUADAS-2
(PMID 22007046) and STARD 2015 (PMID 26511519) both require explicit handling of partial verification
(only biopsied lesions get histology). The training-data provenance (HAM10000, PMID 30106392) mixes
histopathology, follow-up, expert consensus and confocal microscopy as ground truth, so the validation
must state which tier applies to each lesion.

**Confidence: HIGH.**

**Expert review needed.** Dermatopathologist to define the adjudication protocol and the follow-up
interval that counts as a negative reference.

---

### 5. Sample Size

**Recommendation.** Power on the co-primary endpoints, enriched for melanoma prevalence and
**stratified to guarantee minimum event counts in each Fitzpatrick band** (see §6). Anchor plausible
magnitude to real device programs rather than an invented number: the DermaSensor primary-care
utility study enrolled **N = 1028 [retrieved-from-source, NCT06690086]** and its postmarket
surveillance study targets **N = 396 [retrieved-from-source, NCT06666790]**. Treat the specific
per-subgroup n as **[study-defined-placeholder]** until the biostatistician fixes the missed-melanoma
margin.

**Rationale.** Sample size follows from the pre-set sensitivity margin and melanoma prevalence in the
enrollment frame; no fixed n is mandated. Registered trials in this device family provide realistic
order-of-magnitude anchors (NCT06690086 completed, N=1028; NCT06666790 recruiting, N=396), both
verified on ClinicalTrials.gov this session. The rarity of melanoma among lesions of concern means
subgroup power, not overall power, is the binding constraint.

**Confidence: MEDIUM** (method is standard; the number is study-specific).

**Expert review needed.** Biostatistician to compute n from the chosen sensitivity margin, expected
prevalence, and required per-subgroup precision.

---

### 6. Subgroup Requirements

**Recommendation.** Pre-specify and power (or at minimum precisely estimate) performance across
**Fitzpatrick I–VI skin tones**, body site (acral, mucosal, nail, sun-exposed vs not), age, sex,
lesion subtype (melanoma / BCC / SCC / benign mimics), and acquisition device. Report per-subgroup
sensitivity with confidence intervals and a pre-registered non-inferiority check on dark-skin
subgroups. Publish the skin-tone distribution of both training and test data.

**Rationale.** Skin-tone performance disparity is a demonstrated, quantified problem in dermatology
AI: the DDI diverse-skin-tone benchmark showed degraded model performance on darker skin
(Daneshjou 2022, PMID 35960806 · DOI 10.1126/sciadv.abq6147), and the structural under-representation
of dark skin in dermatology ML datasets was documented by Adamson & Smith (PMID 30073260 ·
DOI 10.1001/jamadermatol.2018.2348). This makes Fitzpatrick-stratified reporting a validity
requirement, not an equity add-on, given the stated I–VI population.

**Confidence: HIGH.**

**Expert review needed.** Dermatologist with pigmented-skin expertise to set minimum acceptable
dark-skin performance and confirm Fitzpatrick labeling method.

---

### 7. Regulatory Pathway

**Recommendation.** Target the **De Novo → Class II** pathway under **21 CFR 878.1830**, product code
**QZS** — "Software-Aided Adjunctive Diagnostic Device For Use By Physicians On Lesions Suspicious For
Skin Cancer," explicitly for a *physician not trained in skin-cancer diagnosis* as an adjunctive
second read. This classification was created by **De Novo DEN230008** (DermaSensor, decision date
2024-01-12) and is the closest regulatory match to the intended non-specialist decision-support claim.
File as a De Novo if the specific technology/indication differs enough that QZS predicate does not
fit; otherwise a 510(k) to the QZS predicate. **[all retrieved-from-source: openFDA]**

**Rationale — including the regulatory NULL result.** openFDA classification confirms three relevant
Class II product codes, each *adjunctive, not standalone*: **QZS** (878.1830, DEN230008); **OYD**
(878.1820, "Optical Diagnostic Device For Melanoma Detection," MelaFind, PMA **P090012**); and **ONV**
(878.1820, "Electrical Impedance Spectrometer," Nevisense, PMA **P150046**). A March 2026 Federal
Register reclassification (referenced in the OYD/ONV classification records) moved optical
melanoma-detection devices into Class II. **Critical NULL result:** searching openFDA 510(k), De Novo
and PMA endpoints for "dermoscop*", "photograph", and photographic image-analysis skin devices
returned **no authorization for a device whose input is dermoscopic/clinical photographs analyzed by
image AI** — every cleared device in this space uses a *different physical signal*: MelaFind =
multispectral optical imaging; Nevisense = electrical impedance spectroscopy; DermaSensor =
elastic-scattering spectroscopy. **A photograph-in / malignancy-risk-out AI classifier of the type
described has no existing FDA-authorized predicate in the same signal modality**, which pushes the
system toward De Novo and makes §2 (signal validation) and §3 (benchmarks) pivotal.

**Confidence: HIGH** (class, codes, and the modality NULL result are all directly verified in openFDA).

**Expert review needed.** Regulatory affairs specialist to decide De Novo vs 510(k)-to-QZS and to
confirm predicate applicability for a photographic-input device.

---

### 8. Post-Deployment Monitoring

**Recommendation.** Implement a prospective post-market surveillance plan: (i) real-world
sensitivity/specificity drift tracking against biopsy outcomes, (ii) the image-quality-gate
pass/reject rate as a data-integrity monitor, (iii) subgroup (Fitzpatrick/site) performance dashboards
with pre-set alarm thresholds, and (iv) a change-control plan for model updates. Register the
surveillance study. A directly analogous program exists: the **DermaSensor Postmarket Surveillance
Study, NCT06666790 [retrieved-from-source]**, is the template.

**Rationale.** DECIDE-AI (PMID 35585198 · DOI 10.1038/s41591-022-01772-9) frames ongoing human-factors
and safety monitoring for decision-support AI; input-drift monitoring is justified by the demonstrated
fragility of image-based classifiers to acquisition artifacts (Winkler 2019, PMID 31411641) and
real-world app underperformance (Freeman 2020, PMID 32041693). A registered postmarket study in this
exact device family (NCT06666790, verified on ClinicalTrials.gov) shows this is the expected practice.

**Confidence: HIGH** (that monitoring is required); **MEDIUM** (specific alarm thresholds are
**[study-defined-placeholder]**).

**Expert review needed.** Post-market safety / regulatory team to set drift-alarm thresholds and the
model-update change-control protocol.

---

## SOURCE INVENTORY

### Peer-reviewed literature

| Source (one-line description) | Identifier (PMID · DOI) | Grounded field(s) |
|---|---|---|
| Esteva et al. 2017, Nature — dermatologist-level skin-cancer classification with a deep CNN | PMID 28117445 · DOI 10.1038/nature21056 | 3, 5 |
| Haenssle et al. 2018, Ann Oncol — "man vs machine": CNN vs 58 dermatologists (dermoscopy) | PMID 29846502 · DOI 10.1093/annonc/mdy166 | 3 |
| Tschandl et al. 2019, Lancet Oncol — human readers vs ML on pigmented lesions (ISIC) | PMID 31201137 · DOI 10.1016/S1470-2045(19)30333-X | 3, 4 |
| Tschandl et al. 2020, Nat Med — human–computer collaboration in skin-cancer recognition | PMID 32572267 · DOI 10.1038/s41591-020-0942-0 | 1, 3 |
| Tschandl et al. 2018, Sci Data — HAM10000 dermatoscopic image dataset | PMID 30106392 · DOI 10.1038/sdata.2018.161 | 2, 4 |
| Daneshjou et al. 2022, Sci Adv — dermatology-AI performance on diverse (DDI) skin-tone dataset | PMID 35960806 · DOI 10.1126/sciadv.abq6147 | 6 |
| Adamson & Smith 2018, JAMA Dermatol — ML and health-care disparities in dermatology | PMID 30073260 · DOI 10.1001/jamadermatol.2018.2348 | 6 |
| Winkler et al. 2019, JAMA Dermatol — surgical skin markings bias a melanoma CNN | PMID 31411641 · DOI 10.1001/jamadermatol.2019.1735 | 2, 8 |
| Whiting et al. 2011, Ann Intern Med — QUADAS-2 diagnostic-accuracy quality tool | PMID 22007046 · DOI 10.7326/0003-4819-155-8-201110180-00009 | 1, 4 |
| Bossuyt et al. 2015, BMJ — STARD 2015 diagnostic-accuracy reporting standard | PMID 26511519 · DOI 10.1136/bmj.h5527 | 1, 4 |
| Collins et al. 2024, BMJ — TRIPOD+AI prediction-model reporting guidance | PMID 38626948 · DOI 10.1136/bmj-2023-078378 | 1 |
| Vasey et al. 2022, Nat Med — DECIDE-AI early clinical evaluation of decision-support AI | PMID 35585198 · DOI 10.1038/s41591-022-01772-9 | 1, 8 |
| Dinnes et al. 2018, Cochrane — computer-assisted (dermoscopy/spectroscopy) diagnosis of melanoma | PMID 30521691 · DOI 10.1002/14651858.CD013186 | 3, 5 |
| Freeman et al. 2020, BMJ — systematic review of algorithm-based smartphone skin-cancer apps | PMID 32041693 · DOI 10.1136/bmj.m127 | 2, 3, 8 |
| USPSTF 2023, JAMA — skin-cancer screening recommendation statement | PMID 37071089 · DOI 10.1001/jama.2023.4342 | 3 |
| USPSTF 2023, JAMA — skin-cancer screening evidence report / systematic review | PMID 37071090 · DOI 10.1001/jama.2023.3262 | 3, 4 |
| Elmore et al. 2017, BMJ — pathologist concordance on melanocytic lesions | PMID 28659278 · DOI 10.1136/bmj.j2813 | 4 |

### FDA regulatory records

| Record | Identifier (product code / K-number / DEN-number / PMA-number) | Grounded field(s) |
|---|---|---|
| Software-aided adjunctive skin-cancer classifier, Class II, 21 CFR 878.1830 (device-class definition) | product code **QZS** | 7 |
| DermaSensor — De Novo that established product code QZS (2024-01-12) | **DEN230008** | 7 |
| Optical diagnostic device for melanoma detection, Class II, 21 CFR 878.1820 | product code **OYD** | 7 |
| MelaFind (Strata/Mela Sciences) — multispectral optical imaging, code OYD | PMA **P090012** | 7 |
| Electrical impedance spectrometer, Class II, 21 CFR 878.1820 | product code **ONV** | 7 |
| Nevisense (SciBase AB) — electrical impedance spectroscopy, code ONV | PMA **P150046** | 7 |

### Trial registry use (ClinicalTrials.gov)

- **NCT06690086** (COMPLETED, N=1028, observational) — DermaSensor primary-care-physician use study — informed **Field 5 (sample size anchor)** and **Field 1 (design)**.
- **NCT06666790** (RECRUITING, N=396, interventional) — DermaSensor postmarket surveillance study — informed **Field 8 (post-deployment monitoring)** and **Field 5**.
- Broader searches ("melanoma dermoscopy AI biopsy", "teledermatology skin cancer primary care algorithm") surfaced additional AI-dermatology studies (e.g. NCT06080711, NCT03362138) confirming the reader/decision-study design norm for **Field 1**; not used as numeric anchors.
- All NCT numbers cited were re-resolved individually against the ClinicalTrials.gov v2 API this session.

### Expected conclusions

- **Regulatory class / pathway:** Class II, product code **QZS** (21 CFR 878.1830), via **De Novo**
  (predicate DEN230008) or 510(k) to the QZS predicate. Related adjunctive codes OYD (P090012) and
  ONV (P150046) are Class II under 878.1820.
- **Regulatory NULL result:** **No FDA authorization exists for a device that estimates skin-lesion
  malignancy by AI analysis of dermoscopic/clinical *photographs*.** Every FDA-authorized device in
  this space uses a different physical signal (multispectral optics / electrical impedance /
  elastic-scattering spectroscopy). A photograph-input image-AI classifier has no same-modality
  authorized predicate — verified against openFDA 510(k)/De Novo/PMA this session.
- **Established numeric benchmark:** **None.** No sensitivity/specificity or biopsy-ratio threshold is
  mandated by the FDA classification or set as a field standard; all cleared devices are labeled
  *adjunctive, not standalone*. Every performance/sample-size/threshold number in this spec is
  therefore **[study-defined-placeholder]** except the enrollment counts drawn from NCT06690086
  (1028) and NCT06666790 (396), which are **[retrieved-from-source]**.

### Sources I wanted but could not access (coverage gaps)

- **Drugs@FDA / drug labeling:** not queried — the system under evaluation is a software/imaging
  medical device, not a drug or biologic; no drug-label grounding was applicable this session.
- **Full-text of the pivotal DermaSensor / MelaFind / Nevisense clinical studies:** only registry
  metadata and openFDA classification/summary records were reachable; the primary trial publications'
  reported sensitivity/specificity numbers were **not** retrieved, so no device-specific accuracy
  numbers are asserted.
- **FDA De Novo decision summary / 510(k) summary PDFs:** openFDA returned structured metadata for
  DEN230008 (summary text field empty in the API); the narrative decision summary document was not
  retrieved this session, so predicate-comparison specifics are left to regulatory expert review.
- **March 2026 Federal Register reclassification rule (doc 2026-05772):** referenced inside the
  openFDA classification records but the Federal Register document itself was not fetched; the
  Class II status of OYD/ONV is taken from the openFDA classification fields, not the rule text.
