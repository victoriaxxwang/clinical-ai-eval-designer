# Clinical AI Validation Specification — Warfarin Dosing Decision Support

**Golden reference — Case 3** (pilot slate). Drug / pharmacogenomics pathway; a
**regulatory-NULL** case (no FDA-authorized dosing algorithm exists — the mirror of HRV's null,
and a contrast to DR's positive). Generated in Claude Science; **every identifier independently
re-verified live 2026-07-09** (PMIDs via E-utils, DOIs via Crossref, K-numbers/product-codes/PMA
via openFDA, NDA + SPL via openFDA drugsfda/label, NCTs via ClinicalTrials.gov v2). The scored
answer key is `golden_expected_ids_warfarin.json`.

*Every identifier below was retrieved and resolved: PMIDs via PubMed E-utilities, DOIs via Crossref,
K-numbers/product codes via openFDA device endpoints, application numbers via openFDA Drugs@FDA, and
NCT IDs via ClinicalTrials.gov API v2. Numbers are labeled **[retrieved-from-source]** or
**[study-defined-placeholder]**.*

---

## 1. Study Design

**Recommendation:** Prospective randomized controlled trial comparing the algorithm-guided dosing
arm against a standard-of-care/clinical-algorithm control arm, with the primary endpoint measured as
anticoagulation control over the initiation period. Superiority design against a *clinical*
(non-genotype) dosing algorithm — not against fixed empiric dosing — is the informative comparison,
because the three pivotal RCTs showed the comparator choice determines the result.

**Rationale:** The pivotal literature is built on RCTs, not observational validation. EU-PACT
randomized genotype-guided vs. standard dosing and found benefit (PMID 24251363 · 10.1056/NEJMoa1311386);
COAG randomized genotype-guided vs. a *clinical* algorithm and found no benefit
(PMID 24251361 · 10.1056/NEJMoa1310669); GIFT randomized genotype-guided vs. clinically-guided dosing
in arthroplasty patients (PMID 28973620 · 10.1001/jama.2017.11469). The discordance between EU-PACT
(positive) and COAG (null) is attributable primarily to the control arm, so the control-arm
definition is the central design decision. Enrollment context: COAG NCT00839657, EU-PACT warfarin arm
NCT01119300, GIFT NCT01006733.

**Confidence:** HIGH
**Expert review needed:** Biostatistician + anticoagulation clinical pharmacologist to fix the
comparator arm and adjudicate whether the claim ("reach stable INR faster, reduce out-of-range time")
is tested against clinical-algorithm or empiric-dosing control.

---

## 2. Input / Signal Validation (pre-condition)

**Recommendation:** Before interpreting any dose recommendation, validate the three input signals
against reference standards: (a) **INR assay** — the output measurement the algorithm optimizes
toward — against a reference prothrombin-time method; (b) **genotype calls** (CYP2C9, VKORC1) against
a validated genotyping platform; (c) **clinical-variable data quality** (age, weight, height,
interacting drugs, indication).

**Rationale:** The INR itself is a regulated measurement device: prothrombin-time testing is FDA
product code **GJS**, class II, regulation **864.7750** [openFDA classification, retrieved]. Genotype
input has cleared reference devices under product code **ODW** (CYP2C9/VKORC1 genotyping system, class
II, reg **862.3360**): AutoGenomics INFINITI 2C9 & VKORC1 (K073014), Nanosphere Verigene warfarin
metabolism NAT (K070804), Trimgen eQ-PCR LC kit (K073071), and Osmetech/GenMark eSensor (K073720;
K110786, product code NSU / reg 862.2570). These cleared genotyping assays are the reference standard
for the pharmacogenomic input; the dosing algorithm sits *downstream* of them. CPIC 2017
(PMID 28198005 · 10.1002/cpt.668) specifies the allele set genotyping must cover.

**Confidence:** HIGH (input devices and their regulatory identity are verified)
**Expert review needed:** Clinical laboratory / assay-validation specialist to set the INR
concordance and genotype-call concordance acceptance criteria (values not yet fixed —
**[study-defined-placeholder]**).

---

## 3. Performance Benchmarks

**Recommendation:** Primary metric = **percent time in therapeutic range (PTTR / TTR)** computed by
the Rosendaal linear-interpolation method, plus percent of INRs in range and time to first
therapeutic/stable INR. Do **not** treat any specific PTTR percentage as an established regulatory
pass/fail threshold.

**Rationale:** TTR by linear interpolation is the standard anticoagulation-control endpoint and
derives from Rosendaal 1993 (PMID 8470047 · 10.1055/s-0038-1651587). It was the primary or key
endpoint in EU-PACT (PMID 24251363) and GIFT (PMID 28973620). Any numeric target (e.g. "≥65% TTR")
is **[study-defined-placeholder]** — no FDA-recognized numeric benchmark for a warfarin-dosing
algorithm was found this session.

**Confidence:** HIGH for the metric; LOW for any specific numeric threshold
**Expert review needed:** Set the pre-specified TTR margin and the initiation-window definition.

---

## 4. Ground Truth Strategy

**Recommendation:** Ground truth = measured INR trajectory (serially, per protocol) reduced to TTR,
supplemented by clinically-adjudicated endpoints (major bleeding, thromboembolism, INR ≥4). The
"correct dose" label is the *achieved anticoagulation outcome*, not a retrospectively-computed model
dose.

**Rationale:** All pivotal trials used achieved INR-derived control and adjudicated clinical events
as ground truth (PMID 24251361, PMID 24251363, PMID 28973620). The CPIC 2017 guideline
(PMID 28198005 · 10.1002/cpt.668) provides the genotype-to-starting-dose reference logic but is a
dosing *recommendation* framework, not an outcome ground truth. Gage 2008
(PMID 18305455 · 10.1038/clpt.2008.10) used observed stable dose as the derivation target.

**Confidence:** HIGH
**Expert review needed:** Endpoint-adjudication committee definition for bleeding/thromboembolic
events.

---

## 5. Sample Size

**Recommendation:** Power to the initiation-period TTR difference; the pivotal RCTs anchor the
plausible range. Final N is **[study-defined-placeholder]** pending the assumed control-arm TTR and
effect size.

**Rationale — enrollment context [retrieved from ClinicalTrials.gov]:**
- GIFT — NCT01006733, COMPLETED, enrollment **1,598**
- COAG — NCT00839657, COMPLETED, enrollment **1,015**
- EU-PACT warfarin arm — NCT01119300, COMPLETED, enrollment **455**
- EU-PACT programme (phenprocoumon/acenocoumarol arms) — NCT01119274 (970), NCT01119261 (970)
  *(non-warfarin coumarins — context only)*

These are the observed pivotal-trial enrollments, not a derived requirement for this system; treat
them as calibration anchors. IWPC derivation cohort: PMID 19228618 · 10.1056/NEJMoa0809329.

**Confidence:** MEDIUM (empirical anchors are solid; the specific power calculation is not yet done)
**Expert review needed:** Biostatistician to run the power calculation from the chosen effect size.

---

## 6. Subgroup Requirements

**Recommendation:** Pre-specify subgroup analyses by **CYP2C9 and VKORC1 genotype** and by
**ancestry/self-identified race**, and report calibration within each. This is not optional for a
pharmacogenomic dosing tool.

**Rationale:** Genotype-frequency and dose-response differences across ancestries are central to
warfarin pharmacogenomics; the IWPC algorithm (PMID 19228618) was derived across a multi-ancestry
cohort precisely to span genotypes, and CPIC 2017 (PMID 28198005) gives ancestry-aware dosing logic.
COAG's null result (PMID 24251361) was in part attributed to differential performance in a non-white
subgroup, making ancestry a mandatory, not exploratory, stratum.

**Confidence:** HIGH
**Expert review needed:** Pharmacogenomics expert to fix minimum per-genotype and per-ancestry
enrollment floors (**[study-defined-placeholder]**).

---

## 7. Regulatory Pathway

**Recommendation:** Treat as **Clinical Decision Support / Software as a Medical Device**. The correct
first regulatory question is whether the function meets the 21st Century Cures Act §520(o) non-device
CDS criteria (clinician able to independently review the basis of the recommendation); if it does not
qualify as non-device CDS, expect a device pathway. **A predicate search this session found NO
FDA-cleared/approved warfarin dose-recommendation algorithm** — this is a regulatory NULL result.

**Rationale (regulatory NULL, grounded):** openFDA 510(k) searches on `warfarin`, `warfarin dosing`,
`warfarin genotype`, and `anticoagulation dosing` returned only (a) **genotyping assays** (product
code ODW/NSU: K073014, K070804, K073071, K073720, K110786) and (b) a coagulation-management
instrument, CoagCare (K050821, product code KQG, reg 864.5400) — none is a dose-recommendation
algorithm. **PMA** was queried: openFDA `device/pma` returns 4 warfarin records — all cardiovascular
hardware (P990037 D-Stat hemostat, P000037 On-X valve low-dose-warfarin registry, P930038 Angio-Seal,
P130013 Watchman LAA closure) — **none a dosing algorithm**. **De Novo could not be checked**: openFDA
exposes no `/device/denovo` endpoint (404 even unfiltered), so that database was not queryable — the
null claim explicitly does **not** cover De Novo. The reference drug is **Coumadin, Drugs@FDA
application NDA009218, Bristol Myers Squibb** [retrieved via drugsfda] — this application record
resolves, but its openFDA *drug label* returns 404 (Coumadin predates structured product labeling), so
NDA009218 is not the retrievable source of the pharmacogenomic dosing content. The pharmacogenomic
dosing table lives on a **current warfarin sodium SPL label** that does resolve (openFDA set_id
`0cbce382-9c88-4f58-ae0f-532a841e8f95`, under application **ANDA040616**); the algorithm would be
decision support *around* the labeled drug, not a new drug submission.

**Confidence:** HIGH for the 510(k)+PMA null; the De Novo gap is stated, not claimed as searched; the
exact CDS-vs-device determination requires regulatory counsel.
**Expert review needed:** Regulatory affairs / FDA digital-health specialist for the §520(o) CDS
determination.

---

## 8. Post-Deployment Monitoring

**Recommendation:** Continuously monitor achieved TTR, out-of-range INR rate, over-anticoagulation
(INR ≥4) events, and bleeding/thromboembolic events, stratified by genotype and ancestry, with drift
detection against the trial-established control-arm performance. Monitor input-signal integrity
(INR-assay QC, genotype-call rate) as a leading indicator.

**Rationale:** The subgroup-dependence seen across EU-PACT/COAG/GIFT (PMID 24251363, PMID 24251361,
PMID 28973620) means real-world performance can diverge by population; monitoring must be stratified
on the same axes as §6. TTR is tracked by the Rosendaal method (PMID 8470047) via an
anticoagulation-clinic management workflow (CoagCare, K050821 / product code KQG). Thresholds for
drift alarms are **[study-defined-placeholder]**.

**Confidence:** MEDIUM
**Expert review needed:** Anticoagulation-stewardship + quality lead to set alarm thresholds and the
surveillance cadence.

---

# SOURCE INVENTORY

## Peer-reviewed literature

| Source (one-line description) | Identifier (PMID · DOI) | Grounded field(s) |
|---|---|---|
| Gage 2008 CPT — pharmacogenetic+clinical dose-prediction algorithm | PMID 18305455 · 10.1038/clpt.2008.10 | 1, 4 |
| IWPC 2009 NEJM — clinical vs pharmacogenetic dose estimation algorithm | PMID 19228618 · 10.1056/NEJMoa0809329 | 1, 5, 6 |
| COAG 2013 NEJM (Kimmel) — pharmacogenetic vs clinical algorithm RCT (null) | PMID 24251361 · 10.1056/NEJMoa1310669 | 1, 3, 4, 5, 6, 8 |
| EU-PACT 2013 NEJM (Pirmohamed) — genotype-guided dosing RCT (positive) | PMID 24251363 · 10.1056/NEJMoa1311386 | 1, 3, 4, 5, 8 |
| GIFT 2017 JAMA (Gage) — genotype-guided dosing, clinical-events RCT | PMID 28973620 · 10.1001/jama.2017.11469 | 1, 3, 4, 5, 6, 8 |
| CPIC 2017 CPT — CYP2C9/VKORC1 warfarin dosing guideline update | PMID 28198005 · 10.1002/cpt.668 | 2, 4, 6 |
| Rosendaal 1993 Thromb Haemost — TTR linear-interpolation method | PMID 8470047 · 10.1055/s-0038-1651587 | 3, 8 |

*(All 7 PMIDs resolved in PubMed; all 7 DOIs returned HTTP 200 from Crossref; Rosendaal's DOI, absent
from the PubMed record, was located and resolved via Crossref bibliographic search.)*

## FDA / regulatory records

| Record | Identifier (product code / K-number / Drugs@FDA application) | Grounded field(s) |
|---|---|---|
| Prothrombin-time (INR) test — reference for INR input signal | product code GJS · reg 864.7750 (class II) | 2, 8 |
| CYP2C9/VKORC1 genotyping system — reference for genotype input | product code ODW · reg 862.3360 (class II) | 2 |
| AutoGenomics INFINITI 2C9 & VKORC1 multiplex assay | K073014 (ODW) | 2 |
| Nanosphere Verigene warfarin metabolism NAT | K070804 (ODW) | 2 |
| Trimgen eQ-PCR LC warfarin genotyping kit | K073071 (ODW) | 2 |
| Osmetech eSensor warfarin sensitivity + XT-8 | K073720 (ODW) | 2 |
| GenMark eSensor warfarin sensitivity saliva test | K110786 · product code NSU · reg 862.2570 | 2 |
| CoagCare anticoagulation management system (mgmt instrument, not dosing algorithm) | K050821 · product code KQG · reg 864.5400 | 7, 8 |
| Coumadin (warfarin sodium) reference drug — Bristol Myers Squibb | Drugs@FDA NDA009218 | 4, 7 |
| Warfarin sodium SPL label carrying the PGx dosing table | set_id 0cbce382-9c88-4f58-ae0f-532a841e8f95 · ANDA040616 | 7 |

*Verification notes:* K-numbers and product-code classifications resolved via openFDA `device/510k`
and `device/classification`. Drugs@FDA application **NDA009218** resolved via openFDA `drug/drugsfda`.
The openFDA **drug label** endpoint returned **404 for NDA009218** (Coumadin predates structured
product labeling); a current *warfarin sodium* SPL label does resolve (openFDA set_id
`0cbce382-9c88-4f58-ae0f-532a841e8f95`, under **ANDA040616**) and carries the pharmacogenomic dosing
table. **PMA** (`device/pma`) returns 4 warfarin records, all cardiovascular hardware (P990037,
P000037, P930038, P130013) — none a dosing algorithm. **De Novo** (`/device/denovo`) is **not a
queryable openFDA endpoint** (404 unfiltered) — the null claim does not cover De Novo.

## Trial registry use (ClinicalTrials.gov API v2)

- Search `"COAG"/"Clarification of Optimal Anticoagulation through Genetics"` → **NCT00839657**
  (COMPLETED, 1,015) → informed fields **1, 5**.
- Search `"EU-PACT warfarin"` → **NCT01119300** warfarin arm (COMPLETED, 455); programme sibling arms
  NCT01119274 (phenprocoumon, 970) / NCT01119261 (acenocoumarol, 970) are **non-warfarin coumarins**
  (context only) → informed fields **1, 5**.
- Search `"GIFT warfarin"` → **NCT01006733** (COMPLETED, 1,598) → informed fields **1, 5**.

## Expected conclusions

1. **Regulatory class/pathway:** Clinical Decision Support / SaMD; gate on Cures Act §520(o)
   non-device-CDS criteria before assuming a device submission is required. Supporting device inputs
   are class II (INR test GJS/864.7750; genotyping ODW/862.3360).
2. **Regulatory NULL result:** **No FDA-cleared or -approved warfarin dose-recommendation algorithm
   was found this session.** Every warfarin-related 510(k) retrieved is a *genotyping assay* or a
   coagulation-management instrument — none is a dosing algorithm. PMA returns only cardiovascular
   hardware; De Novo was not queryable.
3. **Established numeric benchmark:** **None exists as a regulatory standard.** TTR (Rosendaal method)
   is the accepted *metric*, but any specific TTR percentage is study-defined, not an FDA-recognized
   threshold. The genotype-guided benefit itself is contested (COAG null vs EU-PACT/GIFT positive) —
   the comparator arm decides the result.

## Sources I wanted but could not access (coverage gaps)

- **openFDA De Novo (`/device/denovo`)** is not a queryable endpoint (404 unfiltered); the NULL
  predicate claim rests on the 510(k) + classification + PMA searches and does not cover De Novo.
- **Full-text of the pivotal RCTs and CPIC guideline** — only PubMed metadata and Crossref records
  were resolved; exact per-trial TTR values and effect sizes were not extracted from full text (hence
  numbers left as [study-defined-placeholder]).
- **FDA CDS guidance / §520(o) determination** — a policy question requiring regulatory counsel, not
  a database lookup; not resolvable to an identifier here.
- **Coumadin original NDA labeling PDF** — the openFDA label endpoint has no NDA009218 record
  (pre-SPL era); only a current ANDA warfarin SPL (ANDA040616) was accessible.
- **PharmGKB / WarfarinDosing.org algorithm coefficients** — not on the allowlisted API set; not
  retrieved.
