# Claude Science — Batch 2, TEN individual prompts (one per fresh session)

Purpose: independently confirm the engine-hardening fix (surface-buried-disease +
clinical-category filter + make `+hierarchy` testable). Each case targets a PRE-ASSIGNED
condition so the 10 collectively cover the hierarchy test: 8 broad-parent diseases (rich
MeSH child trees) + 1 symptom-only boundary case + 1 leaf for the no-op contrast.

Claude Science writes everything (mechanism-first description, clinical framing, MeSH
judgment); Victoria only assigns the disease. Run each block in its OWN fresh Claude
Science conversation. Bring back the labelled output for all 10.

Assignments:
 1 Diabetes Mellitus (metabolic)   2 Heart Failure (cardiovascular)
 3 Hepatitis (infectious)          4 Dementia (neurologic)
 5 Anemia (hematologic)            6 Leukemia (oncologic)
 7 Stroke (cerebrovascular)        8 Major Depressive Disorder (mental health)
 9 SYMPTOM-ONLY (undifferentiated) 10 Psoriasis (dermatologic — likely leaf, no-op check)

====================================================================================
SHARED RULES (identical in every prompt below; already embedded in each one)
====================================================================================
- Mechanism-first phrasing: lead with the ML method + data; name the disease LATE.
- Realistic population + setting detail.
- NO citations / PMIDs / DOIs / FDA numbers / trial IDs.
- Output the exact labelled block so the fields parse.

------------------------------------------------------------------------------------
CASE 1 of 10  — target condition: DIABETES MELLITUS (metabolic)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disease only LATER, never in the opening
   words. Right style: "A gradient-boosted model that ingests routine structured EHR data —
   vital-sign trends, laboratory results, nursing flowsheet entries — and outputs a calibrated
   probability that a patient will progress to [disease]."
2. The target condition for THIS case is: DIABETES MELLITUS (category: metabolic).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">

------------------------------------------------------------------------------------
CASE 2 of 10  — target condition: HEART FAILURE (cardiovascular)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disease only LATER, never in the opening
   words. Right style: "A gradient-boosted model that ingests routine structured EHR data —
   vital-sign trends, laboratory results, nursing flowsheet entries — and outputs a calibrated
   probability that a patient will progress to [disease]."
2. The target condition for THIS case is: HEART FAILURE (category: cardiovascular).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">

------------------------------------------------------------------------------------
CASE 3 of 10  — target condition: HEPATITIS (infectious / hepatic)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disease only LATER, never in the opening
   words. Right style: "A gradient-boosted model that ingests routine structured EHR data —
   vital-sign trends, laboratory results, nursing flowsheet entries — and outputs a calibrated
   probability that a patient will progress to [disease]."
2. The target condition for THIS case is: HEPATITIS (category: infectious / hepatic).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">

------------------------------------------------------------------------------------
CASE 4 of 10  — target condition: DEMENTIA (neurologic)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disease only LATER, never in the opening
   words. Right style: "A gradient-boosted model that ingests routine structured EHR data —
   vital-sign trends, laboratory results, nursing flowsheet entries — and outputs a calibrated
   probability that a patient will progress to [disease]."
2. The target condition for THIS case is: DEMENTIA (category: neurologic).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">

------------------------------------------------------------------------------------
CASE 5 of 10  — target condition: ANEMIA (hematologic)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disease only LATER, never in the opening
   words. Right style: "A gradient-boosted model that ingests routine structured EHR data —
   vital-sign trends, laboratory results, nursing flowsheet entries — and outputs a calibrated
   probability that a patient will progress to [disease]."
2. The target condition for THIS case is: ANEMIA (category: hematologic).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">

------------------------------------------------------------------------------------
CASE 6 of 10  — target condition: LEUKEMIA (oncologic)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disease only LATER, never in the opening
   words. Right style: "A gradient-boosted model that ingests routine structured EHR data —
   vital-sign trends, laboratory results, nursing flowsheet entries — and outputs a calibrated
   probability that a patient will progress to [disease]."
2. The target condition for THIS case is: LEUKEMIA (category: oncologic).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">

------------------------------------------------------------------------------------
CASE 7 of 10  — target condition: STROKE (cerebrovascular)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disease only LATER, never in the opening
   words. Right style: "A convolutional neural network that analyzes non-contrast head CT
   images and outputs a probability that the study shows an acute [disease]."
2. The target condition for THIS case is: STROKE (category: cerebrovascular).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">

------------------------------------------------------------------------------------
CASE 8 of 10  — target condition: MAJOR DEPRESSIVE DISORDER (mental health)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disorder only LATER, never in the opening
   words. Right style: "A natural-language-processing model that analyzes clinician progress
   notes and patient-reported questionnaire responses and outputs a probability that a patient
   is experiencing [disorder]."
2. The target condition for THIS case is: MAJOR DEPRESSIVE DISORDER (category: mental health).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disorder named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">

------------------------------------------------------------------------------------
CASE 9 of 10  — SYMPTOM-ONLY (no named diagnosis — boundary test)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests.
2. SYMPTOM-ONLY: this case must describe ONLY presenting SYMPTOMS (e.g., unintentional weight
   loss, fatigue, intermittent fever, night sweats, malaise) WITHOUT ever naming a diagnosis or
   disease. The model predicts risk/urgency from an undifferentiated symptom presentation.
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — symptoms only, NO diagnosis named>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: symptom-only (no named diagnosis)
MESH_HEADING: <your best guess at the MeSH heading for the single most prominent presenting symptom>
MESH_IS_BROAD_PARENT: <yes | no>
MESH_EXAMPLE_CHILDREN: <2-3 examples if broad parent; else "none">

------------------------------------------------------------------------------------
CASE 10 of 10  — target condition: PSORIASIS (dermatologic — leaf / no-op check)
------------------------------------------------------------------------------------
I'm stress-testing a clinical-AI evaluation tool that reads a description of a clinical AI/ML
model and its intended use, then retrieves supporting FDA + medical-literature citations to
ground a validation write-up. Please write ONE realistic but challenging test case, following
these rules EXACTLY:

RULES:
1. MECHANISM-FIRST PHRASING (critical): lead the model description with the machine-learning
   METHOD and the DATA it ingests; name the target disease only LATER, never in the opening
   words. Right style: "A convolutional neural network that analyzes dermoscopic skin images
   and outputs a probability that a lesion represents [disease]."
2. The target condition for THIS case is: PSORIASIS (category: dermatologic).
3. Realistic clinical detail in population and setting.
4. Do NOT include any citations, PMIDs, DOIs, FDA numbers, or trial IDs.

OUTPUT EXACTLY THIS BLOCK (keep the labels verbatim):

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, mechanism-first — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the primary condition, plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; else "none">
