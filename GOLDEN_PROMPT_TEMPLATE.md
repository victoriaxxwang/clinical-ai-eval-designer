# Golden-Case Prompt Template (Claude Science)

Purpose: generate each **golden reference spec** in the SAME format as
`golden_validation_spec_HRV.md`, so the ablation harness can score every case
consistently. Run each case in a **fresh Claude Science conversation**. Copy the
**entire** output back and save it as `golden_validation_spec_<CASE>.md`.
Victoria provides the prose + source inventory; Claude builds the
`golden_expected_ids_<CASE>.json` answer key from it.

---

## THE PROMPT (paste this whole block, then fill in ONE "System under evaluation")

You are helping build a **grounded clinical AI validation specification** that will be used as a
reference answer key. I will describe a clinical AI system under evaluation. Produce a structured
8-field validation specification in which **every citation is a real, verifiable identifier**.
Accuracy of identifiers matters more than breadth — a wrong or unverifiable identifier is worse
than a missing one.

**System under evaluation:** <<DROP IN ONE OF THE CASE DESCRIPTIONS BELOW>>

**Grounding rules (strict):**
- Ground every recommendation in real sources retrieved and verified THIS session: PubMed (PMID)
  and Crossref-resolved DOIs for literature; openFDA for FDA records (product codes, 510(k)
  K-numbers, De Novo DEN-numbers, PMA numbers); ClinicalTrials.gov for trial / enrollment context;
  Drugs@FDA / drug labeling for drug or biologic products.
- **Verify every identifier resolves before including it** (PMID → PubMed; DOI → Crossref;
  K/DEN/PMA → openFDA; product code → openFDA classification). If an identifier cannot be verified,
  DROP it. Do not include any citation you did not resolve this session.
- Do **not** invent numeric thresholds as established standards. Label every number as either
  *retrieved-from-source* or *study-defined-placeholder*.
- Where a relevant database is not accessible to you, say so explicitly rather than guessing.

**Output format — follow exactly.** First, the 8 numbered fields. Each field has:
**Recommendation**, **Rationale** (with inline citations), **Confidence** (HIGH / MEDIUM / LOW),
and **Expert review needed**. The 8 fields are:

1. Study Design
2. Input / Signal Validation — the pre-condition: does the input measurement itself (sensor signal,
   image quality, lab assay, genotype call, etc.) agree with a reference standard before the
   algorithm's output is interpreted?
3. Performance Benchmarks
4. Ground Truth Strategy
5. Sample Size
6. Subgroup Requirements
7. Regulatory Pathway
8. Post-Deployment Monitoring

Then end with a **SOURCE INVENTORY** — this section is the most important part. It must contain:

- A table of **peer-reviewed literature**, columns exactly:
  `| Source (one-line description) | Identifier (PMID · DOI) | Grounded field(s) |`
- A table of **FDA regulatory records**, columns exactly:
  `| Record | Identifier (product code / K-number / DEN-number / PMA-number) | Grounded field(s) |`
- A short note on **Trial registry** use (which ClinicalTrials.gov searches informed which fields).
- An **Expected conclusions** list: the regulatory class/pathway; any regulatory NULL result
  (e.g. "no FDA authorization exists for X"); and whether an established numeric benchmark exists.
- A **Sources I wanted but could not access** list (databases you could not reach — the coverage gaps).

Use the exact table columns above so the output is machine-parseable.

---

## CASE DESCRIPTIONS — drop ONE into "System under evaluation" per run

### Case 1 — HRV stress detection (ALREADY DONE — do not re-run)
Existing golden: `golden_validation_spec_HRV.md`. Listed here only as the format anchor.

### Case 2 — Diabetic-retinopathy screening (imaging device) — DONE
Golden: `golden_validation_spec_DR.md` + `golden_expected_ids_DR.json` (regulatory *positive*).
An AI algorithm that analyzes color retinal fundus photographs to detect **referable
(more-than-mild) diabetic retinopathy** in adults with diabetes, deployed as an autonomous /
point-of-care screening tool in primary-care and non-ophthalmology settings. Intended claim:
flag patients who should be referred to an eye-care professional. Input: fundus images from a
non-mydriatic retinal camera, with an image-quality/gradeability gate. Population: adults with
type 1 or type 2 diabetes, across skin tones and camera models.

### Case 3 — Warfarin dosing (drug / pharmacogenomics) — DONE
Golden: `golden_validation_spec_warfarin.md` + `golden_expected_ids_warfarin.json` (regulatory
*null*, first drug case).
An algorithm that recommends an **initial warfarin dose (and early dose adjustment)** to reach and
maintain therapeutic anticoagulation (target INR), using clinical variables (age, weight, height,
concomitant medications, indication) and optionally pharmacogenomic inputs (CYP2C9, VKORC1
genotype). Intended claim: decision support to help clinicians reach stable INR faster and reduce
out-of-range time. Setting: inpatient initiation and outpatient anticoagulation-clinic management.
Population: adults starting warfarin, spanning genotypes and ancestries.

---

**PILOT-3 SLATE LOCKED 2026-07-09.** Cases 1–3 span the three retrieval paths
(wellness-sensor null / imaging-device positive / drug null). The cases below are the
expansion toward the full 10; run them only as the harness needs more coverage. Case 4 (sepsis)
is queued to keep Claude Science warm while the harness is built.

### Case 4 — Sepsis early-warning prediction (EHR-based predictive SaMD)
An algorithm that continuously analyzes routinely-collected electronic health record data (vital
signs, laboratory results, nursing assessments, demographics) to **predict the onset of sepsis (or
septic shock) in hospitalized adults hours before clinical recognition**, deployed as an inpatient
early-warning / clinical decision support tool that alerts clinicians to initiate sepsis workup and
treatment. Intended claim: earlier identification of patients at high risk of sepsis to prompt
timely intervention. Input: structured EHR time-series data only (no new sensor, image, or genomic
assay). Setting: inpatient medical-surgical wards and ICUs. Population: hospitalized adults across
care settings, sexes, ages, races/ethnicities, and admitting diagnoses. *(Opens a new axis: a
predictive model on EHR data, with the Epic Sepsis Model external-validation failure as a rich
Input-Validation + Post-Deployment-Monitoring test.)*

---

## What to copy back for each case
1. Save the **entire** Claude Science output as `golden_validation_spec_<CASE>.md`
   (e.g. `golden_validation_spec_DR.md`, `golden_validation_spec_warfarin.md`).
2. Paste it back to Claude in the app-building session. Claude converts the SOURCE INVENTORY into
   `golden_expected_ids_<CASE>.json` (the scored answer key) and confirms every identifier resolves.
3. Do **not** hand-build the JSON — that is Claude's step, so the answer key can't drift from the spec.
