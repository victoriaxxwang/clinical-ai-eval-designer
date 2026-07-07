# Hackathon Demo & Pitch Blueprint (Max 3 Minutes)

## 📌 Core Thesis & Hook
- **The Angle:** The product moat is not the AI capability or the retrieval—it is the constraint layer *plus* grounding. Unconstrained AI is dangerous in clinical workflows; this tool enforces safety at the model level and grounds every citation in real registry data before the model ever reads it.
- **Discovery Engine → Productized Runtime:** Claude Science was our **Discovery Engine**—the environment where we manually validated the literature-synthesis workflow (the 48-paper HRV proof-of-concept). The product is an **automated, programmatic mirror** of that workflow: a pipeline that queries live registry APIs (PubMed, ClinicalTrials.gov, openFDA) to ingest real, verifiable identifiers, using **Claude Fable 5 purely as the intelligent constraint-and-synthesis layer**.
- **Verifiable by construction:** Because the citations are grounded in real registry records *before* the model reads them, the output validation protocol is **verifiable by construction**—Fable maps and constrains real evidence; it does not recall or invent it. Every identifier (PMID, NCT, 510(k) K-number) came back from a database this run.
- **Target Audience:** Anthropic & Gladstone Institutes Judges.

## ⏱️ Scene-by-Scene Breakdown (Target: 180 Seconds)

### Phase 1: The Problem & The Hook (0:00 - 0:45)
- **Visual:** Slide or direct camera address showing the friction in Clinical AI validation.
- **Talk Track:** "Clinical AI teams build brilliant models that work technically but fail clinically because they lack structured validation evidence. Synthesizing the necessary benchmarks from literature takes weeks and changes by population and indication. The problem isn't the AI model—it's knowing what the model needs to prove."

### Phase 2: The Core Product Demo (0:45 - 2:00)
- **Visual:** Screen share of the running Streamlit app interface.
- **Action:** Enter a novel disease indication/sensor type to show the app generalizing live. Generate the structured 8-field report.
- **Key Highlights to Point Out:** Show the explicit confidence flags (High/Medium/Low), the rigorous citable references, and the hard guardrails against invented thresholds.

### Phase 3: The Multi-Layer Moat & Future Roadmap (2:00 - 3:00)
- **Visual:** Quick architectural chart or summary slide.
- **Talk Track:** 
  - *Phase 1 (Now):* Expert clinical rules encoded as a constraint layer, **plus a live grounding pipeline that is already built**. The app queries PubMed, ClinicalTrials.gov, and openFDA at runtime and hands the real records to Fable 5—an automated, programmatic mirror of the Claude Science discovery workflow. Citations are verifiable by construction.
  - *Phase 2 (90-Day):* Turn the grounded spec into downstream deliverables—**Statistical Analysis Plan (SAP) skeletons, IRB submission templates, and FDA Q-Sub outlines** pre-populated from the 8 fields. Once a team's IRB packet is generated from our spec, the switching cost rises steeply.
  - *Closing Line:* "The retrieval is table stakes. This tool knows what to retrieve, what to do with it, and how to make it safe for high-stakes clinical deployment."

## 🔄 Evolution Notes & Iterations
- [July 7]: Initialized script structure based on the "Constraint Layer as a Product" thesis. Decoupled clinical logic from UI to prevent safety filter interruptions.
