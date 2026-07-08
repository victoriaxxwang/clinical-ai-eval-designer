# Project Index — Clinical AI Eval Designer

The map of this repo. Read this first after a compaction or a break; it points to
everything else.

## What this is (one paragraph)
A Streamlit app (`app.py`) that turns a clinical AI model + its context into a
structured, citable **8-field validation specification**. It grounds every
citation by querying public registries **live** (ClinicalTrials.gov v2, openFDA,
PubMed) *before* prompting the model, then uses **Claude Fable 5** purely as a
constrained synthesis layer (no invented numbers, cite-or-flag, confidence +
expert-review tiers). Discovery was proven manually in **Claude Science**; the
app is the automated, programmatic mirror of that workflow.

## Key facts
- **Model:** `claude-fable-5` (auto-fallback `claude-opus-4-8`). Fable needs 30-day data retention.
- **Runtime engine:** Anthropic API + live registry APIs. **Not** a Claude Science API call (there is none).
- **Repo:** https://github.com/victoriaxxwang/clinical-ai-eval-designer
- **Run:** `python3 -m venv .venv && source .venv/bin/activate` → `pip install -r requirements.txt` → add key to `.streamlit/secrets.toml` → `streamlit run app.py`
- **Deadline:** 2026-07-13 (Built with Claude: Life Sciences hackathon, Build track)

## File map
| File | What it's for | Status |
|---|---|---|
| `app.py` | UI layer: inputs, constraint-layer prompt, Fable 5 call, bundle output | ✅ built, compiles; not yet run end-to-end |
| `engine.py` | **Core Deterministic Engine**: registry retrieval + query building (no UI, importable, unit-tested) | ✅ hardened, live-verified |
| `test_engine.py` | 8 critical tests: query determinism + JSON field-path parsing | ✅ 8/8 pass |
| `requirements.txt` | Deps: streamlit, anthropic, requests | ✅ |
| `requirements-dev.txt` | Dev tools: markdown (render_docs), pytest (tests) | ✅ |
| `README.md` | Public-facing: what it is + how to run | ✅ |
| `SUBMISSION.md` | Draft answers to the 5 hackathon questions (video script TBD) | ✅ draft |
| `DEMO_PLAN.md` | 3-min video blueprint | ✅ |
| `JOURNAL.md` | Dev log: blockers, decisions, running log | ✅ |
| `ARCHITECTURE.md` | **Canonical** — how it works: Phase 1 (built) + Phase 2 (future) + Path A/B appendix | ✅ v3, consolidated |
| `CORE_ENGINE_INTEGRATION_BLUEPRINT.md` | Path A/B code detail | ⚠️ candidate for deletion (now folded into ARCHITECTURE appendix) — confirm |
| `render_docs.py` | Render any `.md` → styled HTML in `docs_html/` (git-ignored). Run `pip install markdown` once, then `python render_docs.py` | ✅ |
| `GIT_DEPLOYMENT_GUIDE.md` | Git/deploy ops | ✅ |
| `INDEX.md` | This map | ✅ |

## Open to-dos
- [ ] Run `app.py` end-to-end with a real API key (nothing has actually generated yet)
- [ ] Push local git repo to GitHub (`git push -u origin main`)
- [x] Consolidate architecture into one canonical `ARCHITECTURE.md` (v3)
- [ ] Confirm `CORE_ENGINE_INTEGRATION_BLUEPRINT.md` can be deleted (now folded into the ARCHITECTURE appendix)
- [x] Harden Phase 1 retrieval (query construction, device-keyword selection) + add tests (8/8 pass); found `population` is a poor retrieval filter → drives subgroup reasoning instead
- [x] Emit Phase-1 bundle: spec + source records travel together (download)
- [ ] Add `st.session_state` cache so re-runs don't re-hit registries (rate-limit safety) — Phase 1 polish, do after first successful run
- [ ] Decide the JOURNAL safety-framing reframe (currently flagged, not applied)
- [ ] Write the final demo video talk-track script (after the app is finalized)

## Viewing docs as HTML
`ARCHITECTURE.html` is no longer committed. Instead, generate HTML on demand:
`pip install markdown` (once) → `python render_docs.py` → open `docs_html/*.html`.
For quick edits, VS Code's built-in Markdown preview (`Cmd+Shift+V`) needs no
files at all and updates live.
