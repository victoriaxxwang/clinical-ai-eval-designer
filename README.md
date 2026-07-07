# Clinical AI Eval Designer

Turn what a clinical AI model does — plus its clinical context — into a
**structured, citable validation specification**: study design, sensor
validation, performance benchmarks, ground-truth strategy, sample size,
subgroup requirements, regulatory pathway, and post-deployment monitoring.

Every field is flagged by **confidence** (HIGH / MEDIUM / LOW) and by the kind
of **expert review** it needs before it can be used. The tool is constrained by
design: it does not invent thresholds, it does not claim more than the
literature supports, and it grounds citations in real literature via web search.

Built with the Anthropic API (Claude Fable 5) for the Built with Claude: Life
Sciences hackathon.

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

Your browser opens to the app. Fill in the four fields, click **Generate**, and
download the resulting Markdown spec.

---

## Notes

- **Model:** Claude Fable 5, with automatic server-side fallback to Opus 4.8 if
  a request is declined. Fable requires 30-day data retention on your Anthropic
  organization — if every request errors with a 400, that's the first thing to
  check in your Anthropic Console.
- **Web search** is on by default so citations point at real literature and
  regulatory records. Turn it off in the sidebar for a faster (but ungrounded)
  draft.
- **Effort** defaults to `high`. Higher-effort runs are more thorough but slower
  and more expensive; a full run with web search can take a few minutes.
- Every output requires review by a qualified clinical/regulatory expert before
  any clinical or commercial use. The tool is a structured starting point, not a
  substitute for that judgment.
```
