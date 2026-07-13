# Clinical AI Eval Designer

Turn what a clinical AI does — the model, the patient population, the care setting,
and the claim it makes — into a **structured, citable validation specification**:
eight fields (study design, sensor/input validation, performance benchmarks, ground
truth, sample size, subgroup requirements, regulatory pathway, post-deployment
monitoring), each with a recommendation, a cited rationale, a **HIGH / MEDIUM / LOW**
confidence flag, and the expert sign-off it still needs.

The tool is constrained by design: it does not invent thresholds, it does not claim
more than the evidence supports, and every citation is a **re-resolvable identifier**
— a PMID, an NCT number, an FDA K-number or product code — that you can look up
yourself.

**▶️ Watch the 3-minute demo:** https://youtu.be/znmxWjoSaGk

## How it works — one pipeline, three stages

1. **Retrieval — plain code, no model.** Before anything is written, the app queries
   ClinicalTrials.gov, openFDA, and the published literature directly. Because no
   model touches this step, every citation is verifiable by construction, not
   recalled from memory.
2. **Synthesis — Claude writes the spec.** Claude maps the retrieved records into the
   eight fields under one hard rule: no invented numbers — cite it, or flag it for the
   study team to set.
3. **Review — a three-persona panel.** An optional pass runs three reviewers
   (regulator, biostatistician, clinical scientist) who critique the spec under the
   same cite-or-flag rule, with a grounding audit that re-checks every identifier they
   name against the retrieved evidence — not the model's memory.

The result is reproducible and verifiable: a timestamped, fully-traceable snapshot
where every claim is tied to a source you can re-check. The principle it demonstrates
is the one the demo closes on — **verify, don't blindly trust.**

Built with the Anthropic API (Claude) for the Built with Claude: Life Sciences
hackathon.

---

## Run it locally

You'll paste four short commands into the macOS Terminal. From the project
folder:

**1. Create and activate an isolated Python environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**2. Install the dependencies**

```bash
pip install -r requirements.txt
```

**3. Add your Anthropic API key**

Create the secrets file Streamlit reads:

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then open `.streamlit/secrets.toml` in any text editor and replace the
placeholder with your real key from https://console.anthropic.com — the line
should read:

```toml
ANTHROPIC_API_KEY = "sk-ant-...."
```

**4. Launch the app**

```bash
streamlit run app.py
```

Your browser opens to the app. Fill in the fields, click **Generate**, and
download the resulting Markdown spec.

---

## Notes

- **Model:** Claude Fable 5, with automatic server-side fallback to Opus 4.8 if a
  request is declined. Fable requires 30-day data retention on your Anthropic
  organization — if every request errors with a 400, that's the first thing to check
  in your Anthropic Console.
- **Web search is off by default.** The spec is grounded in registry identifiers you
  can re-resolve; leaving web search off keeps every citation checkable. You can turn
  it on in the sidebar to widen the net, but web pages aren't registry-backed
  identifiers — so the review panel's grounding audit correctly flags them as
  unverifiable. It's your choice, surfaced rather than hidden.
- A full run can take a couple of minutes.
- Every output requires review by a qualified clinical/regulatory expert before any
  clinical or commercial use. The tool is a structured starting point, not a
  substitute for that judgment.
