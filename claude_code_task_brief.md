# Task Brief — Extend the Deterministic Retrieval Layer (disease-agnostic)

**For:** Claude Code
**Target files:** `engine.py` (add functions), `test_engine.py` (add tests), `ARCHITECTURE.md` (update diagram + determinism note)
**Companion artifact:** `retrieval_sources_manifest.json` — the canonical list of endpoints, params, and the identifier each returns. Treat that file as the source of truth for URLs/params; this brief is the *what and why*.

**Design constraint (inherit verbatim):** Core First, Agents Later. Everything below is Phase-1 deterministic retrieval — public APIs, no LLM, no agent loop. No invented values; a nil result returns `"no matching record retrieved"` and the caller lowers confidence.

> **Review notes (Victoria + Claude Code, before implementing):**
> - **SKIP `ictrp`** (WHO global trials) for now — flaky API, not clean JSON. Revisit only if non-US trials matter.
> - **SKIP direct `medrxiv`** API — it's a date-window API, not keyword search. Get preprints via the Europe PMC preprint filter instead.
> - **MeSH normalization (§5) LAST** — highest complexity; disease-agnostic (not stress-specific), so it stays on the list but doesn't block anything.
> - **Do this only AFTER** the current app runs end-to-end with a real API key and produces a real 8-field spec.

---

## 0. Reframe to encode first (ARCHITECTURE.md)

Change the determinism claim from implied bit-identical to **"reproducible + verifiable, not bit-identical."** Live registries update. Determinism is guaranteed by three mechanisms, which every new function MUST honor:
1. **Pinned query string** (built deterministically — see §5 MeSH).
2. **Explicit sort key + hard result cap.** Never rely on a database's default relevance ranking; always pass an explicit sort param and a fixed `max_*`/`limit`. This is the single most important rule — default rank is the silent source of run-to-run drift.
3. **Snapshot into the bundle:** persist raw records + a UTC `retrieval_timestamp` alongside the spec. Verifiability = every captured identifier re-resolves later, not that ranking is frozen.

---

## 1. Add: Crossref verification pass (highest priority)

**Why:** the pipeline retrieves PMIDs but never confirms a DOI resolves to the intended paper. This function is what upgrades "grounded" to "verified."

```
def verify_doi(doi, timeout=12) -> dict:
    # GET https://api.crossref.org/works/{doi}
    # return {"doi": doi, "resolves": bool, "title": <registered title>, "year": ..., "container": <journal>}
    # on 404 -> resolves=False ; on Timeout/RequestException -> resolves=None (unknown, do not assert false)
```
Caller rule: a citation whose `resolves is False` is **dropped from the grounded context**, not passed to synthesis. `resolves is None` (network) keeps the record but tags it `verification="unavailable"`.

Add an `Accept: application/json` header. Optional contact param only if the app already has a configured contact email; do not hardcode one.

---

## 2. Add: openFDA device — PMA, MAUDE, recall

**Why:** current layer has classification + 510(k) only. Disease-agnostic means some inputs are Class III (PMA), and the Post-Deployment Monitoring field has no safety source without MAUDE/recall.

```
def search_openfda_pma(product_code, limit=6, timeout=12) -> list      # /device/pma.json ; returns pma_number
def search_openfda_maude(product_code, limit=10, timeout=12) -> list   # /device/event.json ; returns mdr_report_key
def search_openfda_recall(product_code, limit=6, timeout=12) -> list   # /device/recall.json ; returns recall number
```
Reuse the existing openFDA helper/pattern. Same try/except — nil-safe contract. See manifest ids `openfda_device_pma`, `openfda_device_event`, `openfda_device_recall` for exact search-field syntax.

---

## 3. Add: drug/biologic regulatory toggle

**Why:** the app is disease-agnostic but the regulatory layer is device-only; a drug input has zero regulatory grounding today.

```
def search_drugsfda(name, limit=6, timeout=12) -> list       # /drug/drugsfda.json ; returns application_number (NDA/BLA)
def search_drug_label(name, limit=3, timeout=12) -> list     # /drug/label.json ; returns SPL set id + indications
def search_drug_faers(name, limit=10, timeout=12) -> list    # /drug/event.json ; returns safetyreportid
```
These are gated by the intervention toggle (§6), not always run.

---

## 4. Add: Europe PMC (literature force-multiplier)

**Why:** one call returns PMID + PMCID + DOI + abstract + OA full-text link. It doubles as literature retrieval AND identifier cross-mapping, cutting total call count and giving Crossref-ready DOIs directly.

```
def search_europepmc(term, cap=8, timeout=12) -> list
    # GET https://www.ebi.ac.uk/europepmc/webservices/rest/search
    #   params: query=term, format=json, pageSize=cap, resultType=core
    # each record -> {"pmid","pmcid","doi","title","abstract","year","source"}
```
Keep the existing PubMed functions (they remain the canonical index); Europe PMC augments and cross-maps.

---

## 5. Add: MeSH normalization for build_queries (deepest determinism fix — DO LAST)

**Why:** `build_queries` currently turns free-text user input into keywords ad hoc, so "stress" vs "psychological stress" vs "mental stress" retrieve different sets — non-deterministic by construction.

```
def normalize_to_mesh(free_text, timeout=12) -> dict
    # E-utils esearch db=mesh, term=free_text
    # return {"input": free_text, "mesh_terms": [...], "mesh_ids": [...], "fallback_used": bool}
    # if no MeSH match -> fallback_used=True, mesh_terms=[free_text] (never fail closed)
```
Then refactor `build_queries` to prefer MeSH descriptors when available, appending a `[MeSH Terms]` tag for PubMed and using the plain descriptor string for CT.gov/openFDA. Record which terms were MeSH-mapped vs fallback in the bundle, so query construction is auditable.

---

## 6. Wire the disease-type toggles

`build_queries` / the orchestrator must branch on two inputs (add or infer from the existing form: AI model, clinical use case, patient population, healthcare setting):
- **intervention_type** — {device, drug_biologic, both} — selects §2 vs §3 endpoint set.
- **construct_type** — {physiological, behavioral} — if behavioral, emit an explicit **`manual_retrieval_flag`** naming PsycINFO/CINAHL as uncovered (see §7). Do not silently omit.

The **always-run** set (every disease, every intervention): `pubmed_esearch/esummary`, `europepmc`, `ctgov_v2`, `crossref`. See manifest `always_run_regardless_of_disease`.

---

## 7. Honesty guardrail — the coverage boundary (must surface in output)

Cochrane, Embase, PsycINFO, Web of Science, Scopus, and ex-US regulators (EMA/EUDAMED/MHRA/PMDA/TGA) have **no free no-auth API** and cannot enter this layer. The bundle MUST carry a `coverage_gaps` list enumerating which of these were relevant-but-unqueried for this run (e.g. behavioral construct -> PsycINFO). This keeps the existing "best-effort coverage" guardrail truthful rather than implying exhaustiveness.

---

## 8. Bundle schema additions (the Phase-1->Phase-2 seam)

Extend the emitted bundle with:
```
{
  "retrieval_timestamp": "<UTC ISO8601>",
  "queries": {"raw_input":..., "mesh_mapped":[...], "fallback_terms":[...]},
  "records": [ {source, identifier, id_type, resolves, ...} ],   # every record tagged with its verifiability status
  "coverage_gaps": ["PsycINFO (behavioral construct not covered by no-auth APIs)", ...],
  "toggles": {"intervention_type":..., "construct_type":..., "jurisdiction":...}
}
```
This is exactly the two inputs the Phase-2 critics need (draft + sources) plus the provenance to verify without re-fetching.

---

## 9. Tests (test_engine.py)

For each new function: (a) a live smoke test asserting the identifier field is present and non-empty on a known-good query (mark network-dependent), (b) a nil-result test asserting the `"no matching record retrieved"` contract on a nonsense query, (c) a timeout/exception test asserting nil-safe return. For `verify_doi`: assert a known DOI resolves True and a malformed one resolves False. For `normalize_to_mesh`: assert a known term (e.g. "hypertension") returns a MeSH id and a nonsense term sets `fallback_used=True`.

**Acceptance:** every retrieved record in a bundle carries a resolvable identifier or is dropped; `coverage_gaps` is non-empty whenever a [C]-tier source was relevant; no function raises on network failure.
