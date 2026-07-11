# Claude Science — Batch 2B, DISCOVERY meta-prompt (Claude Science picks the diseases)

Purpose: a *discovery* companion to Batch 2A. In 2A we hand-picked the 10 diseases to
guarantee coverage of the hierarchy feature. Here we do the opposite — Claude Science
invents its own 10 conditions, blind to our choices, to simulate what real users might
bring. Catches blind spots: diseases/phrasings we never thought to test.

How to run: paste the ONE block below into a SINGLE fresh Claude Science session. It
returns all 10 cases at once. (You *may* split across sessions for more variety, but one
session is fine for this scan.) Bring back the whole output; Claude parses the labeled
fields and runs all 10 through the engine here.

Difference from 2A: no disease is pre-assigned, and phrasing is left natural (a mix of
styles, the way real teams actually describe their models) rather than forced
mechanism-first. Everything else — labeled output block, no citations — is the same.

---8<--- PASTE EVERYTHING BELOW THIS LINE INTO ONE FRESH CLAUDE SCIENCE CONVERSATION ---8<---

I'm stress-testing a clinical-AI evaluation tool. It reads a plain-language description of a
clinical AI/ML model plus its intended use, and then automatically maps it to the right medical
vocabulary and retrieves supporting evidence. I want to see how it copes with a realistic,
UNSCRIPTED spread of cases — so I'd like YOU to choose the conditions, not me.

Please invent **10 realistic test cases** for clinical AI/ML models, following the rules below.

WHAT I'M AFTER:

1. YOU PICK THE CONDITIONS. Choose 10 conditions that reflect what real clinical teams actually
   build AI models for. Aim for genuine variety:
   - Span many specialties (e.g. cardiology, oncology, infectious disease, neurology, endocrine,
     renal, pulmonary, GI, dermatology, psychiatry, obstetrics, ophthalmology, emergency, etc.).
   - Mix common, bread-and-butter conditions with a few less-obvious ones.
   - Do NOT make them all cancers or all the "textbook famous" AI use-cases — spread it out.
   - Include a mix of broad conditions AND specific ones (don't force either).

2. NATURAL PHRASING. Describe each model the way a real engineering or clinical team would pitch
   it. Some teams lead with the disease; some lead with the method and data. Give me a MIX of both
   styles across the 10 — I want realistic variety, not a single template.

3. REALISTIC CLINICAL DETAIL in the population and setting fields.

FOR EACH OF THE 10 CASES, OUTPUT EXACTLY THIS BLOCK, keeping the field labels verbatim so I can
parse them:

CASE: <short kebab-case label>
INTERVENTION_TYPE: <device | drug | both>
MODEL_DESC: <2-4 sentences describing the model — natural phrasing>
USE_CASE: <1-2 sentences: the clinical decision it supports>
POPULATION: <the patient population, with realistic inclusion/exclusion detail>
SETTING: <where in the care pathway it is deployed>
CANONICAL_CONDITION: <the single primary condition this case targets, in plain words>
MESH_HEADING: <your best guess at the exact canonical NLM MeSH heading for that condition>
MESH_IS_BROAD_PARENT: <yes | no — does this heading have narrower child conditions in the MeSH tree?>
MESH_EXAMPLE_CHILDREN: <if broad parent: 2-3 example narrower conditions; if leaf: "none">

Please make the 10 cases genuinely varied and clinically plausible. Do NOT include any citations,
PMIDs, DOIs, FDA numbers, or trial IDs — I only need the case descriptions and your MeSH judgment
for each.

---8<--- END OF PASTE ---8<---
