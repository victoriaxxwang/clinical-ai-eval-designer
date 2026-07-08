# Core Engine Integration Blueprint

The literature/evidence search engine can run two ways. They are complementary,
not mutually exclusive — the shipped app uses **both** (Path B as the
deterministic backbone, Path A as an optional gap-filler).

| | Path A — `web_search` server tool | Path B — public registry APIs |
|---|---|---|
| Who runs the search | Anthropic's servers | Your Python (`requests`) |
| Cost | Consumes API credits | **Free** |
| Determinism | Best-effort, varies per run | **Deterministic** — same query → same records |
| Identifiers | Model-transcribed from web pages | Returned by the database (verifiable) |
| Coverage | The open web (FDA guidance PDFs, blogs) | Structured registries only |
| Best for | Filling gaps registries don't cover | The trustworthy, citable backbone |

**Recommendation:** Path B is the source of truth for citations; Path A
supplements. Never rely on Path A alone for the numbers a clinical team will act
on.

---

## Path A — Anthropic API `web_search` server tool

The model issues searches server-side; results come back as content blocks and
the model cites them. No client-side scraping loop.

**Tool declaration** (current version, Fable 5 / Opus 4.8 family):
```python
tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 6}]
```

**Clean Streamlit integration boilerplate:**
```python
import anthropic
import streamlit as st

client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

def synthesize_with_web_search(user_message: str, system_prompt: str) -> str:
    placeholder = st.empty()
    text = ""
    with client.beta.messages.stream(
        model="claude-fable-5",
        max_tokens=32000,
        betas=["server-side-fallback-2026-06-01"],   # opt-in refusal fallback
        fallbacks=[{"model": "claude-opus-4-8"}],     # Fable → Opus 4.8 on a false-positive
        output_config={"effort": "high"},
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 6}],
        system=[{"type": "text", "text": system_prompt,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for chunk in stream.text_stream:
            text += chunk
            placeholder.markdown(text + " ▌")
        placeholder.markdown(text)
    return text
```

Notes:
- **No `thinking` parameter.** Fable 5 has thinking always on; sending
  `thinking={...}` (enabled or disabled) returns 400. Control depth with
  `output_config.effort` (`low`→`max`).
- **Stream.** Long, high-effort turns can run minutes; streaming avoids HTTP
  timeouts.
- **`server_tool_use` / result blocks** stream past `text_stream` silently; if
  you want to show sources, read them off `stream.get_final_message().content`.

---

## Path B — public registries via `requests` (deterministic, free)

Direct HTTP to public APIs. No key, no cost, and identifiers come straight from
the database, so citations are verifiable by construction. This is the shipped
backbone (`app.py`).

**ClinicalTrials.gov API v2:**
```python
import requests

def search_clinicaltrials(term: str, max_studies: int = 6, timeout: int = 12):
    r = requests.get(
        "https://clinicaltrials.gov/api/v2/studies",
        params={"query.term": term, "pageSize": max_studies},
        timeout=timeout,
    )
    r.raise_for_status()
    rows = []
    for s in r.json().get("studies", []):
        ps  = s.get("protocolSection", {})
        idm = ps.get("identificationModule", {})
        dm  = ps.get("designModule", {})
        rows.append(
            f"{idm.get('nctId','')} | {idm.get('briefTitle','')} "   # briefTitle, not officialTitle
            f"| type={dm.get('studyType','')} "
            f"| n={dm.get('enrollmentInfo',{}).get('count','')}"
        )
    return "\n".join(rows)
```

The same pattern applies to:
- **openFDA** — `https://api.fda.gov/device/classification.json?search=device_name:"<term>"`
  and `.../device/510k.json` (product codes, K-numbers, device class).
- **PubMed E-utilities** — `esearch.fcgi` → id list → `esummary.fcgi` (real
  PMIDs, titles, journals, years).

**Verified working** (2026-07): live calls returned real records — NCT03831841,
live PMIDs, openFDA product code QEX. Field paths above are confirmed against the
live v2 schema.

**Graceful degradation:** wrap each source in try/except for `requests.Timeout`
and `requests.RequestException`; a nil result is reported as "no matching record
retrieved" and the model lowers confidence rather than inventing a benchmark.
Absence of a record is not evidence of absence.

---

## Replicating a "Claude Science" deep-research workflow in Claude Code

Claude Science (the interactive workbench) is where the manual proof-of-concept
happened; it has **no programmatic API** to call from an app. What we *can*
replicate locally is the *pattern* it embodies: retrieve real evidence → reason
under strict rules → self-review before emitting.

Local recipe (Claude Code + Python):
1. **Retrieve** with Path B (deterministic registry pulls) + optional Path A for
   web gaps. Assemble a single labelled `search_context` string.
2. **Synthesize** with `claude-fable-5`, passing `search_context` as the source
   of truth and the constraint-layer system prompt (no invented numbers,
   cite-or-flag, confidence tiers).
3. **Review with a guardrail pass** — a second, narrowly-scoped model call (the
   "reviewer agent") that checks the draft against the rules and returns only
   pass/fail + flagged fields:
   ```python
   REVIEWER_SYSTEM = (
       "You are a strict reviewer. Given a validation spec and its source "
       "records, flag: (1) any number not traceable to a cited record, "
       "(2) any HIGH-confidence field backed only by tangential evidence, "
       "(3) any overstated regulatory claim. Return a short list of flagged "
       "fields, or 'PASS'. Do not rewrite the spec."
   )
   ```
   Feed the flags back to step 2, revise only the flagged fields, re-review, and
   converge or escalate to a human after N loops (see the Autonomous
   Self-Correction Loop in `SYSTEM_ARCHITECTURE_FUTURE_STATE.md`).

This gives you the discovery-engine *behavior* — grounded retrieval + constrained
reasoning + independent self-review — without pretending the app calls Claude
Science. Honest framing for the write-up: *"an automated, programmatic mirror of
the Claude Science discovery workflow."*
