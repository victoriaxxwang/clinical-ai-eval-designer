# Claude Science — Batch 2 RESULTS (collected 2026-07-10)

Raw verbatim Claude Science outputs. Two sub-batches:
- **Set A** — 10 pre-assigned diseases, one fresh session each (confirmation / controlled).
  Prompts: `claude_science_batch2_prompts_10.md`.
- **Set B** — Claude Science chose its own 10 diseases, one session (discovery / blind).
  Prompt: `claude_science_batch2B_metaprompt.md`.

NOT yet run through the engine — that is Chunk C. Parse the labeled fields; check (a) buried
disease surfaces, (b) engine resolves to the same canonical MeSH heading CS named, (c) +hierarchy
fires on the broad parents, no-ops on leaves.

Flagged discrepancies to examine during analysis (CS was internally inconsistent — good signal):
- **Psoriasis**: Set B says MESH_IS_BROAD_PARENT **no** (leaf); Set A says **yes** (child Arthritis, Psoriatic).
- **Major Depressive Disorder**: Set B says **no** (leaf); Set A says **yes** (child Seasonal Affective Disorder).
- **Pre-Eclampsia** (Set B): CS flagged Eclampsia is a *sibling* not a child; HELLP Syndrome is the clean child.

====================================================================================
SET B — DISCOVERY (Claude Science picked its own 10 conditions; single session)
====================================================================================

CS preamble: "I read the brief. This is a case-authoring task, so I'll produce the 10 blocks
directly — no data retrieval needed. I aimed for a genuine spread across specialties, a mix of
disease-led and method-led pitches, and a deliberate balance of broad-parent MeSH headings vs.
true leaf terms so your tool gets tested on both."

--- B1 ---
CASE: (heart-failure-rehospitalization)
INTERVENTION_TYPE: device
MODEL_DESC: A gradient-boosted risk model that ingests the discharge medication list, echocardiographic ejection fraction, renal panel, and prior admission history from the EHR to estimate 30-day rehospitalization risk. It re-scores each patient nightly during the index stay and flags rising-risk trajectories to the care-transitions team. Outputs are calibrated probabilities plus the top contributing features.
USE_CASE: Helps the inpatient team decide who needs intensified transitional care (early follow-up, home telemonitoring, diuretic titration) before discharge.
POPULATION: Adults ≥18 admitted with a primary diagnosis of decompensated heart failure across both reduced and preserved EF phenotypes; excludes patients discharged to hospice or transferred to another acute facility.
SETTING: Inpatient cardiology and general medicine wards at a multi-site health system, scoring within the EHR.
CANONICAL_CONDITION: Heart failure
MESH_HEADING: Heart Failure
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Heart Failure, Systolic; Heart Failure, Diastolic

--- B2 ---
CASE: (sepsis-early-warning)
INTERVENTION_TYPE: both
MODEL_DESC: A recurrent-neural-network early-warning system trained on streaming vitals, lab trends, and nursing flowsheet data to predict the onset of sepsis several hours before it becomes clinically obvious. It emits a continuously updated hazard score and fires a best-practice alert when the score crosses a site-tuned threshold. The alert bundles a suggested workup and antibiotic-timing prompt.
USE_CASE: Prompts clinicians to draw cultures, start fluids, and administer empiric antibiotics earlier for patients deteriorating toward sepsis.
POPULATION: Adult inpatients on general wards and step-down units; excludes ICU-boarding patients already on vasopressors and comfort-care patients.
SETTING: Acute-care hospital wards with real-time EHR integration and paging.
CANONICAL_CONDITION: Sepsis
MESH_HEADING: Sepsis
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Neonatal Sepsis; Shock, Septic

--- B3 ---
CASE: (pulmonary-embolism-ctpa)
INTERVENTION_TYPE: device
MODEL_DESC: A 3D convolutional network that reads CT pulmonary angiography studies and localizes filling defects in the pulmonary arterial tree. It produces a study-level positive/negative call with vessel-level heatmaps and pushes suspected-positive scans to the top of the radiology worklist. Confidence is reported per detected clot.
USE_CASE: Reprioritizes worklists so acute pulmonary embolism is read and communicated faster in busy emergency imaging queues.
POPULATION: Adults presenting to the ED with suspected PE who undergo CTPA; excludes non-contrast and technically inadequate (motion/contrast-timing) studies.
SETTING: Emergency department imaging, triage-integrated with the PACS worklist.
CANONICAL_CONDITION: Pulmonary embolism
MESH_HEADING: Pulmonary Embolism
MESH_IS_BROAD_PARENT: no
MESH_EXAMPLE_CHILDREN: none

--- B4 ---
CASE: (ischemic-stroke-lvo)
INTERVENTION_TYPE: device
MODEL_DESC: An imaging model that analyzes non-contrast head CT and CT angiography to flag suspected large-vessel occlusion consistent with acute ischemic stroke. It sends an automated mobile notification to the on-call stroke and neurointervention teams with the suspected occlusion site. The system is designed to shorten door-to-treatment intervals.
USE_CASE: Accelerates activation of the endovascular thrombectomy pathway for patients with acute ischemic stroke.
POPULATION: Adults presenting with acute focal neurological deficits within an eligible time window who receive CT/CTA; excludes primary intracerebral hemorrhage and prior large established infarct.
SETTING: Comprehensive and primary stroke-center emergency departments with hub-and-spoke transfer.
CANONICAL_CONDITION: Ischemic stroke
MESH_HEADING: Ischemic Stroke
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Embolic Stroke; Thrombotic Stroke; Lacunar Stroke

--- B5 ---
CASE: (ibd-colonoscopy-severity)
INTERVENTION_TYPE: device
MODEL_DESC: A deep-learning classifier applied to colonoscopy withdrawal video and biopsy-linked features to distinguish active mucosal inflammation from quiescent disease and to standardize endoscopic severity scoring. It overlays a per-frame inflammation index and produces a segment-level summary at the end of the exam. The goal is to reduce inter-endoscopist variability.
USE_CASE: Supports the gastroenterologist in grading disease activity and deciding whether to escalate or de-escalate therapy in inflammatory bowel disease.
POPULATION: Adults with established Crohn disease or ulcerative colitis undergoing surveillance or activity-assessment colonoscopy; excludes patients with poor bowel prep or acute severe colitis deferred from scope.
SETTING: Outpatient endoscopy suites at academic and community GI practices.
CANONICAL_CONDITION: Inflammatory bowel disease
MESH_HEADING: Inflammatory Bowel Diseases
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Crohn Disease; Colitis, Ulcerative

--- B6 ---
CASE: (thyroid-nodule-ultrasound)
INTERVENTION_TYPE: device
MODEL_DESC: A convolutional model that takes B-mode thyroid ultrasound images and outputs a malignancy-risk category aligned to a standardized reporting lexicon, along with automated measurement of nodule composition, echogenicity, margins, and calcifications. It suggests whether a nodule meets size/risk thresholds for fine-needle aspiration. Findings are packaged into a structured report draft.
USE_CASE: Helps radiologists decide which thyroid nodules warrant biopsy versus surveillance, reducing unnecessary aspirations.
POPULATION: Adults with one or more thyroid nodules ≥1 cm detected on diagnostic neck ultrasound; excludes purely cystic lesions and post-thyroidectomy remnants.
SETTING: Outpatient radiology and endocrine ultrasound clinics.
CANONICAL_CONDITION: Thyroid nodule
MESH_HEADING: Thyroid Nodule
MESH_IS_BROAD_PARENT: no
MESH_EXAMPLE_CHILDREN: none

--- B7 ---
CASE: (glaucoma-fundus-screening)
INTERVENTION_TYPE: device
MODEL_DESC: A retinal fundus-image algorithm that estimates the probability of glaucomatous optic neuropathy from cup-to-disc ratio, neuroretinal rim thinning, and RNFL cues, returning a refer/no-refer recommendation. It is packaged for use with low-cost non-mydriatic cameras by non-specialist staff. A saliency map highlights the optic nerve head features driving the score.
USE_CASE: Enables community screening so that people likely to have glaucoma are referred to ophthalmology for confirmatory testing.
POPULATION: Adults ≥40, or younger adults with family history or high myopia, screened in primary-care and optometry settings; excludes eyes with media opacity precluding disc visualization.
SETTING: Primary-care clinics and community optometry screening programs, with teleophthalmology referral.
CANONICAL_CONDITION: Glaucoma
MESH_HEADING: Glaucoma
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Glaucoma, Open-Angle; Glaucoma, Angle-Closure

--- B8 ---
CASE: (psoriasis-smartphone-severity)
INTERVENTION_TYPE: device
MODEL_DESC: A smartphone-image model that quantifies erythema, induration, and scaling from patient- or clinician-captured skin photos to produce an objective severity score and affected body-surface-area estimate. It tracks change across visits and generates a longitudinal severity trend. The tool is intended to make remote monitoring more consistent.
USE_CASE: Supports dermatologists in objectively grading psoriasis severity and deciding when to step therapy up or down in a telehealth workflow.
POPULATION: Adults and adolescents with plaque psoriasis enrolled in remote-monitoring programs; excludes primarily pustular or erythrodermic presentations and heavily tattooed target areas.
SETTING: Teledermatology and outpatient dermatology follow-up.
CANONICAL_CONDITION: Psoriasis
MESH_HEADING: Psoriasis
MESH_IS_BROAD_PARENT: no
MESH_EXAMPLE_CHILDREN: none

--- B9 ---
CASE: (mdd-antidepressant-selection)
INTERVENTION_TYPE: both
MODEL_DESC: A machine-learning model that combines baseline symptom-scale scores, clinical history, and prior pharmacotherapy exposures to predict the likelihood of remission on specific first-line antidepressant classes. It returns a ranked list of options with predicted response probabilities and highlights features suggesting poor tolerability. It is framed as decision support, not autonomous prescribing.
USE_CASE: Helps clinicians choose an initial antidepressant more likely to achieve remission for a given patient with major depression.
POPULATION: Adults with a new or recurrent episode of moderate-to-severe major depressive disorder initiating pharmacotherapy; excludes bipolar disorder, active psychosis, and acute suicidality requiring inpatient care.
SETTING: Primary-care and outpatient psychiatry clinics.
CANONICAL_CONDITION: Major depressive disorder
MESH_HEADING: Depressive Disorder, Major
MESH_IS_BROAD_PARENT: no
MESH_EXAMPLE_CHILDREN: none

--- B10 ---
CASE: (pre-eclampsia-first-trimester)
INTERVENTION_TYPE: both
MODEL_DESC: A first-trimester risk model integrating maternal characteristics, mean arterial pressure, biochemical markers, and uterine-artery Doppler indices to estimate the probability of developing pre-eclampsia later in pregnancy. It outputs a calibrated risk stratum and flags candidates who may benefit from prophylaxis. The score is generated at the routine early-pregnancy visit.
USE_CASE: Identifies high-risk pregnancies early so clinicians can offer low-dose aspirin prophylaxis and intensified surveillance.
POPULATION: Pregnant people at their first-trimester screening visit across nulliparous and multiparous groups; excludes multifetal gestations and those already on aspirin for another indication.
SETTING: Outpatient obstetric and maternal-fetal medicine clinics.
CANONICAL_CONDITION: Pre-eclampsia
MESH_HEADING: Pre-Eclampsia
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: HELLP Syndrome; Eclampsia

CS closing notes (verbatim):
- Specialty coverage: cardiology, critical care/infectious disease, pulmonary-vascular, neurology, GI, endocrine, ophthalmology, dermatology, psychiatry, and obstetrics — no oncology on purpose, since you flagged the "all cancers / all textbook" failure mode.
- Phrasing mix: disease-led pitches (heart failure, stroke, IBD, glaucoma) vs. method-led pitches (sepsis RNN, CTPA CNN, thyroid ultrasound, smartphone psoriasis, first-trimester risk model).
- MeSH broad-vs-leaf balance: 6 broad parents (Heart Failure, Sepsis, Ischemic Stroke, Inflammatory Bowel Diseases, Glaucoma, Pre-Eclampsia) and 4 true leaves (Pulmonary Embolism, Thyroid Nodule, Psoriasis, Depressive Disorder, Major).
- Intervention types: mostly device (SaMD), with three `both` cases tied to a drug decision (antibiotic timing, antidepressant selection, aspirin prophylaxis).
- Judgment call: for Pre-Eclampsia listed Eclampsia as example child for readability, but in current MeSH tree Eclampsia is a sibling not a strict narrower term under Pre-Eclampsia (HELLP Syndrome is the clean child).

====================================================================================
SET A — CONFIRMATION (pre-assigned diseases; one fresh session each)
====================================================================================

--- A1 — assigned: DIABETES MELLITUS ---
CASE: (diabetes)
INTERVENTION_TYPE: device
MODEL_DESC: A gradient-boosted ensemble that ingests longitudinal structured EHR data — fasting and random glucose values, HbA1c trends, BMI trajectory, blood-pressure and lipid-panel results, medication fills, and problem-list ICD codes — and emits a calibrated 3-year probability of incident disease. Feature attributions are surfaced per prediction so clinicians can see which laboratory and vital-sign trends drove the score. The model is retrained quarterly and outputs are stratified into low/intermediate/high risk tiers. The condition it is designed to anticipate is diabetes mellitus.
USE_CASE: Flags primary-care patients who are not yet diagnosed but are at elevated near-term risk, prompting the care team to order confirmatory glycemic testing and initiate lifestyle or pharmacologic prevention.
POPULATION: Adults aged 18–75 with at least two primary-care encounters in the prior 24 months and no existing diagnosis of diabetes; excludes patients with a prior diabetes ICD code, active pregnancy, prescriptions for antihyperglycemic agents, or fewer than one recorded HbA1c or glucose value in the lookback window.
SETTING: Ambulatory primary-care clinics within an integrated health system, deployed as a background risk score in the outpatient EHR.
CANONICAL_CONDITION: Diabetes mellitus
MESH_HEADING: Diabetes Mellitus
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Diabetes Mellitus, Type 1; Diabetes Mellitus, Type 2; Diabetes, Gestational

--- A2 — assigned: HEART FAILURE ---
CASE: (heart-failure)
INTERVENTION_TYPE: device
MODEL_DESC: A recurrent neural network that ingests longitudinal structured EHR streams — serial vital-sign trends, serum electrolyte and natriuretic-peptide laboratory results, daily weights, diuretic administration records, and nursing flowsheet entries on dyspnea and edema — and updates a calibrated risk score at each new observation. The model learns temporal patterns of hemodynamic decompensation from routinely collected inpatient data and outputs a probability that a hospitalized patient will progress to acute decompensated heart failure within the next 48 hours. It requires no dedicated sensors or manual data entry beyond standard documentation.
USE_CASE: The score supports care-team triage decisions — prompting earlier cardiology consultation, closer telemetry monitoring, or intensification of decongestive therapy in patients flagged as rising risk.
POPULATION: Adults aged 18 and older admitted to non-ICU general medical and cardiology step-down units, with at least 24 hours of inpatient observation. Excludes patients on comfort-care/hospice status, those with end-stage renal disease on chronic dialysis, and admissions shorter than 24 hours where insufficient longitudinal data are available.
SETTING: Inpatient general medical and cardiology step-down wards of an acute-care hospital.
CANONICAL_CONDITION: Heart failure
MESH_HEADING: Heart Failure
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Heart Failure, Systolic; Heart Failure, Diastolic; Cardio-Renal Syndrome

--- A3 — assigned: HEPATITIS ---
CASE: (hepatitis)
INTERVENTION_TYPE: device
MODEL_DESC: A gradient-boosted ensemble that ingests routine structured EHR data — serial liver-function panels (ALT, AST, alkaline phosphatase, total and direct bilirubin), complete blood counts, coagulation indices (INR), medication-administration records, and nursing flowsheet vitals — and learns temporal trends across sequential inpatient measurements. The model outputs a calibrated probability that a patient's evolving biochemical and clinical trajectory reflects acute hepatocellular inflammation, flagging cases likely to represent new-onset or worsening hepatitis before a clinician manually reconciles the trend.
USE_CASE: Surfaces a ranked daily worklist alert prompting the care team to order confirmatory serologic and viral testing and to review potentially hepatotoxic medications, supporting earlier hepatology consultation.
POPULATION: Hospitalized adults (≥18 years) on general medical-surgical and step-down units with at least two liver-function panels drawn ≥12 hours apart during the encounter. Excludes patients with a documented pre-admission diagnosis of chronic liver disease or cirrhosis, those admitted directly for known viral hepatitis, liver-transplant recipients, and patients on comfort-care/hospice pathways.
SETTING: Inpatient acute-care wards (non-ICU) at a multi-site academic health system, integrated into the EHR clinical-decision-support layer.
CANONICAL_CONDITION: Hepatitis (liver inflammation)
MESH_HEADING: Hepatitis
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Hepatitis, Viral, Human (e.g., Hepatitis B, Hepatitis C); Hepatitis, Autoimmune; Hepatitis, Alcoholic

--- A4 — assigned: DEMENTIA ---
CASE: (dementia)
INTERVENTION_TYPE: device
MODEL_DESC: A recurrent neural network with an attention layer that ingests longitudinal primary-care records — structured problem lists, medication fills, serial vital signs, routine laboratory panels, and free-text visit notes rendered into embeddings — and models each patient's trajectory over successive encounters. It emits a calibrated 24-month probability that a currently cognitively unimpaired older adult will cross the threshold to clinically diagnosed dementia. Risk estimates are refreshed after every new encounter and surfaced to clinicians as a tiered score with the top contributing features.
USE_CASE: Flags higher-risk patients in a primary-care panel for earlier cognitive assessment and specialist referral, supporting proactive triage rather than a definitive diagnosis.
POPULATION: Community-dwelling adults aged 60 and older with at least three years of continuous primary-care coverage and no prior coded diagnosis of dementia or mild cognitive impairment; excludes patients with a pre-existing major neurocognitive disorder diagnosis, active delirium, or fewer than two documented encounters in the look-back window.
SETTING: Outpatient primary care within an integrated health system.
CANONICAL_CONDITION: dementia
MESH_HEADING: Dementia
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Alzheimer Disease; Frontotemporal Dementia; Lewy Body Disease

--- A5 — assigned: ANEMIA ---
CASE: (anemia)
INTERVENTION_TYPE: device
MODEL_DESC: A gradient-boosted ensemble that ingests routine structured EHR data — serial complete blood count indices (hemoglobin, hematocrit, MCV, RDW), reticulocyte counts, iron-panel and ferritin values, vital-sign trends, and nursing flowsheet entries — and outputs a calibrated probability that a patient is currently anemic or will develop clinically significant anemia within the next 72 hours. Features are updated at each new lab result, and the model emits a continuous risk score with an accompanying trend indicator. The score is surfaced in the clinician dashboard to flag patients whose trajectory suggests declining red-cell mass before a critical hemoglobin threshold is crossed.
USE_CASE: Supports the decision of whether to order confirmatory hematologic workup or initiate earlier transfusion planning and hematology consultation in patients showing early, sub-threshold signs of falling hemoglobin.
POPULATION: Hospitalized adults (≥18 years) admitted to medical and surgical inpatient wards with at least two CBC draws during the encounter; inclusion requires a baseline hemoglobin recorded within 24 hours of admission. Excludes patients on active hospice/comfort-care pathways, those with a diagnosis of an acute massive hemorrhage on admission, and pregnant patients managed on dedicated obstetric services.
SETTING: Inpatient medical and surgical wards of an academic tertiary-care hospital, integrated into the EHR clinical decision-support layer.
CANONICAL_CONDITION: anemia
MESH_HEADING: Anemia
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Anemia, Iron-Deficiency; Anemia, Hemolytic; Anemia, Aplastic

--- A6 — assigned: LEUKEMIA ---
CASE: (leukemia)
INTERVENTION_TYPE: device
MODEL_DESC: A gradient-boosted ensemble that ingests routine structured EHR data — serial complete-blood-count indices (white-cell count, hemoglobin, platelet count, blast percentage when reported), peripheral-blood differential trends, basic metabolic and LDH/uric-acid chemistries, and coded encounter and medication history — and computes a calibrated probability that a patient's abnormal hematologic trajectory reflects an emerging clonal marrow disorder. Feature attributions and the longitudinal trend curve are surfaced alongside the risk score so a clinician can see which laboratory patterns drove the estimate. The score is refreshed each time new laboratory results post, and threshold crossings trigger a passive best-practice advisory rather than an automatic order. The condition the model is designed to flag early is leukemia.
USE_CASE: Supports the primary-care or general-internal-medicine clinician's decision to expedite a peripheral-smear review and hematology referral for a patient whose routine labs suggest an evolving leukemic process, rather than deferring to the next routine visit.
POPULATION: Adults aged 18 and older with at least two outpatient CBCs drawn 30 or more days apart in the preceding 24 months. Excludes patients with an existing hematologic-malignancy diagnosis, active cytotoxic chemotherapy, recent hematopoietic stem-cell transplant, or pregnancy; also excludes encounters where CBC values are missing or flagged as specimen-error.
SETTING: Outpatient primary-care and general internal-medicine clinics within an integrated health system, with results delivered through the inpatient/outpatient EHR at the time of lab resulting.
CANONICAL_CONDITION: leukemia
MESH_HEADING: Leukemia
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Leukemia, Myeloid, Acute; Leukemia, Lymphocytic, Chronic, B-Cell; Leukemia, Myelogenous, Chronic, BCR-ABL Positive

--- A7 — assigned: STROKE ---
CASE: (acute-ischemic-stroke)
INTERVENTION_TYPE: device
MODEL_DESC: A deep convolutional neural network that ingests non-contrast head CT series in DICOM format and computes voxel-level features across the cerebral vasculature and parenchyma. The algorithm fuses these features with CT angiography source images, when available, to flag large-vessel occlusion and quantify hypodense tissue. It outputs a study-level probability score and a triage flag indicating suspected acute ischemic stroke.
USE_CASE: The tool prioritizes worklists and pushes a mobile notification to the on-call neurovascular team so that candidates for thrombectomy or thrombolysis are reviewed sooner. It is an adjunct for triage and does not replace radiologist interpretation.
POPULATION: Adults (≥18 years) presenting to the emergency department with acute neurological deficits and suspected stroke, imaged within the standard acute workup window. Inclusion: non-contrast head CT (with or without concurrent CTA) ordered as part of a stroke alert. Exclusion: prior craniectomy or major skull hardware, severe motion or metallic artifact degrading the study, and known intracranial mass or recent neurosurgery.
SETTING: Emergency department and comprehensive/primary stroke center radiology workflow, integrated with PACS and worklist triage.
CANONICAL_CONDITION: stroke
MESH_HEADING: Stroke
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Ischemic Stroke, Hemorrhagic Stroke, Embolic Stroke

--- A8 — assigned: MAJOR DEPRESSIVE DISORDER ---
CASE: (depression risk AI)
INTERVENTION_TYPE: device
MODEL_DESC: A natural-language-processing model that ingests free-text clinician progress notes, intake narratives, and structured patient-reported questionnaire responses (e.g., item-level symptom severity and sleep/appetite entries) collected during routine primary-care encounters. Using a transformer-based text encoder combined with gradient-boosted classifiers over the questionnaire features, the model produces a calibrated probability that the patient is currently experiencing a clinically significant episode of major depressive disorder, along with a short list of contributing text spans for clinician review.
USE_CASE: The output flags patients who may warrant a structured diagnostic interview and severity assessment, supporting the primary-care clinician's decision to initiate follow-up evaluation, treatment, or behavioral-health referral. It is intended as a decision-support aid, not an autonomous diagnostic device.
POPULATION: Adults aged 18-75 presenting for routine or follow-up visits in primary care with at least one documented progress note and a completed self-report symptom questionnaire in the encounter. Inclusion requires sufficient English free-text documentation; exclusion criteria include an existing charted diagnosis of bipolar disorder or a primary psychotic disorder, active substance-intoxication presentations, and patients under acute suicidal-crisis management where immediate escalation protocols supersede screening.
SETTING: Outpatient primary care / integrated behavioral-health clinics within a multi-site health system.
CANONICAL_CONDITION: Major depressive disorder
MESH_HEADING: Depressive Disorder, Major
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Seasonal Affective Disorder (the primary narrower term under this heading in the MeSH tree)

--- A9 — assigned: SYMPTOM-ONLY ---
CASE: (undifferentiated fever triage)
INTERVENTION_TYPE: device
MODEL_DESC: A gradient-boosted decision-tree ensemble (XGBoost) ingests longitudinal structured EHR data — serial vital signs, trended CBC and comprehensive metabolic panel values, weight measurements over time, and medication-order history — alongside free-text triage and encounter notes vectorized through a fine-tuned clinical-language embedding layer. Features are aggregated over rolling 90- and 365-day windows to capture trajectory rather than single-timepoint values. The model outputs a continuous 0–1 risk score and a discrete triage-urgency tier from a presentation of persistent unexplained fatigue, unintentional weight loss, intermittent low-grade fever, drenching night sweats, and generalized malaise. No diagnostic label is assigned; the output quantifies the probability that the undifferentiated symptom cluster warrants expedited specialist work-up.
USE_CASE: Supports the primary-care clinician's decision on whether to fast-track a patient with undifferentiated constitutional symptoms to urgent diagnostic evaluation versus routine watchful-waiting follow-up.
POPULATION: Community-dwelling adults aged 40–85 presenting to primary care with ≥2 constitutional symptoms persisting >3 weeks and at least one documented objective marker (e.g., ≥5% unintentional body-weight loss over 6 months or recorded temperature ≥37.8°C). Excludes patients with an active malignancy diagnosis in the prior 5 years, current pregnancy, documented acute infection explaining symptoms at presentation, or fewer than two EHR encounters in the preceding 12 months (insufficient longitudinal data).
SETTING: Outpatient primary care / general practice clinics within an integrated health system, at the point of triage or initial encounter.
CANONICAL_CONDITION: symptom-only (no named diagnosis)
MESH_HEADING: Fatigue
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Mental Fatigue, Muscle Fatigue

--- A10 — assigned: PSORIASIS ---
CASE: (psoriasis)
INTERVENTION_TYPE: device
MODEL_DESC: A convolutional neural network that ingests standardized clinical photographs of affected skin together with structured patient-reported symptom data (itch, scaling, joint stiffness) and computes per-lesion feature embeddings. A gradient-boosted classifier on those embeddings outputs a calibrated probability that the imaged plaques represent a chronic immune-mediated papulosquamous dermatosis, along with an estimated body-surface-area involvement score. The model is trained on multi-site dermatology image archives with dermatologist-adjudicated labels and is intended as an adjunct, not a standalone diagnostic. The condition it is designed to flag is psoriasis.
USE_CASE: Supports primary-care and teledermatology triage by prioritizing patients whose lesions are likely psoriatic (and moderate-to-severe by surface area) for expedited dermatology referral and consideration of systemic or biologic therapy.
POPULATION: Adults aged 18–75 presenting with persistent (>6 weeks) erythematous, scaling plaques in an ambulatory setting. Inclusion: at least one photographable lesion on trunk, extremities, or scalp; smartphone or clinic camera image meeting minimum resolution. Exclusion: pregnancy, active skin infection or open ulceration at the imaging site, prior systemic immunosuppressant use in the last 90 days, isolated facial/genital-only involvement, and skin tones under-represented in the training set flagged for manual review.
SETTING: Primary care and teledermatology triage clinics (outpatient / ambulatory), including store-and-forward remote review.
CANONICAL_CONDITION: psoriasis
MESH_HEADING: Psoriasis
MESH_IS_BROAD_PARENT: yes
MESH_EXAMPLE_CHILDREN: Arthritis, Psoriatic (the primary narrower MeSH descriptor); clinically recognized subtypes that a broad-parent match should also capture include pustular psoriasis and guttate psoriasis
