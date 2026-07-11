# Claude Science — Batch 2 case-generation prompt (paste the block below)

Purpose: generate diverse, challenging test cases to independently confirm the
engine-hardening fix (surface-buried-disease + clinical-category filter + make
`+hierarchy` testable). Target 6–8 cases (8 recommended). Bring back the raw output;
Claude will parse the labelled fields and run the whole set through the harness.

Key properties the prompt enforces: mechanism-first phrasing (disease named LATE),
≥4 broad-parent diseases (so `+hierarchy` has children to expand to), category
diversity incl. one mental-health condition, and exactly one symptom-only case.

---8<--- PASTE EVERYTHING BELOW THIS LINE INTO A FRESH CLAUDE SCIENCE CONVERSATION ---8<---

I'm stress-testing a clinical-AI evaluation tool. It reads a plain-language description of a
clinical AI/ML model plus its intended use, and then automatically retrieves supporting
regulatory records (FDA) and medical literature to ground a validation write-up. I need a set
of realistic but deliberately challenging test cases. Please generate **8 test cases** that
meet the exact specification below.

WHAT MAKES A CASE USEFUL (please honor ALL of these):

1. MECHANISM-FIRST PHRASING (most important). Write each model description the way a real
   engineering team would pitch it — lead with the machine-learning METHOD and the DATA it
   ingests, and name the target disease only LATER in the description, never in the opening
   words.
   - GOOD (disease named late): "A gradient-boosted model that ingests routine structured EHR
     data — vital-sign trends, laboratory results, and nursing flowsheet entries — and outputs a
     calibrated hourly probability that an admitted patient will progress to heart failure
     decompensation."
   - BAD (disease named first): "A heart failure model that uses EHR data..."

2. DISEASE DIVERSITY + BROAD "PARENT" CONDITIONS. At least 4 of the 8 cases must target a broad
   PARENT condition that has named clinical sub-types in the MeSH vocabulary (examples: Diabetes
   Mellitus, Heart Failure, Pneumonia, Hepatitis, Leukemia, Lymphoma, Dementia, Anemia, Stroke,
   Chronic Kidney Disease, Inflammatory Bowel Disease) — NOT an already-specific leaf condition.
   Spread the 8 cases across these categories: metabolic, infectious, cardiovascular, oncologic,
   neurologic, and mental-health (include at least ONE mental-health condition such as Major
   Depressive Disorder or Bipolar Disorder).

3. EXACTLY ONE SYMPTOM-ONLY CASE. Make one of the 8 describe only presenting SYMPTOMS (e.g.
   fever, cough, fatigue, abdominal pain) without ever naming a diagnosis — to test how the tool
   behaves when no disease is stated.

4. REALISTIC CLINICAL DETAIL in the population and setting fields.

FOR EACH CASE, OUTPUT EXACTLY THIS BLOCK, keeping the field labels verbatim so I can parse them:

CASE: <short kebab-case label, e.g. heart-failure-ehr>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences, MECHANISM-FIRST — disease named late>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <the patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the single primary condition this case targets, in plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading for that condition>
MESH_IS_BROAD_PARENT: <yes | no — is this a broad heading with narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; if leaf: "none">

Please make the 8 cases genuinely varied and clinically plausible. Do NOT include any citations,
PMIDs, DOIs, FDA numbers, or trial IDs — I only need the case descriptions and your MeSH
judgment for each.

---8<--- END OF PASTE ---8<---
