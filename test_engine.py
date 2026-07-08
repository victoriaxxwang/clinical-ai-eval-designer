"""
Critical tests for the Core Deterministic Engine.

Two kinds, matching the two ways the engine can silently break:

1. Query construction (pure, no network) — the determinism + relevance gate.
   If these drift, the grounding degrades quietly.
2. Response parsing (network mocked) — the JSON-field-path gate. Registry APIs
   change their schemas; these fail loudly the day a field path moves, instead
   of the app returning blank grounding with no error.

Run:  pip install pytest  →  python -m pytest -q
"""

import requests

import engine


class FakeResp:
    def __init__(self, json_data=None, status=200, text=""):
        self._json = json_data or {}
        self.status_code = status
        self.ok = status < 400
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(f"status {self.status_code}")


# --- 1. Query construction (pure) ------------------------------------------

def test_build_queries_is_deterministic():
    args = ("Detects CAC from chest CT", "Cardiovascular screening", "Adults")
    assert engine.build_queries(*args) == engine.build_queries(*args)


def test_fda_keyword_is_never_a_verb_or_filler():
    # "Infers" is the first word but is a verb — must not become the device keyword.
    q = engine.build_queries(
        "Infers stress from photoplethysmography on a wearable",
        "Acute stress detection", "Adults")
    assert q["fda"] not in engine._STOP
    assert q["fda"] == "photoplethysmography"


def test_queries_are_bounded_and_stripped():
    q = engine.build_queries("word " * 200, "use " * 200, "pop " * 200)
    assert len(q["ct"]) <= 200 and len(q["pubmed"]) <= 250
    # Only the top few keywords survive — not every repeated token.
    assert len(q["ct"].split()) <= 4


def test_keywords_splits_hyphens_and_drops_stopwords():
    kws = engine._keywords("photoplethysmography-derived heart-rate for the model", 6)
    assert "photoplethysmography" in kws and "derived" in kws
    assert "for" not in kws and "the" not in kws and "model" not in kws


# --- 2. Response parsing (network mocked) -----------------------------------

def test_clinicaltrials_extracts_nct_id(monkeypatch):
    payload = {"studies": [{"protocolSection": {
        "identificationModule": {"nctId": "NCT01234567", "briefTitle": "A Trial"},
        "statusModule": {"overallStatus": "COMPLETED"},
        "designModule": {"studyType": "INTERVENTIONAL",
                         "enrollmentInfo": {"count": 110}, "designInfo": {}},
        "outcomesModule": {"primaryOutcomes": [{"measure": "AUC"}]},
    }}]}
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(payload))
    text, status = engine.search_clinicaltrials("anything")
    assert "NCT01234567" in text and "n=110" in text
    assert status.startswith("✅")


def test_pubmed_extracts_real_pmids(monkeypatch):
    def fake_get(url, **k):
        if "esearch" in url:
            return FakeResp({"esearchresult": {"idlist": ["42346460"]}})
        return FakeResp({"result": {"uids": ["42346460"],
                                    "42346460": {"title": "HRV and stress",
                                                 "fulljournalname": "J Test", "pubdate": "2026 Jan"}}})
    monkeypatch.setattr(engine.requests, "get", fake_get)
    text, status = engine.search_pubmed("hrv stress")
    assert "PMID 42346460" in text and "2026" in text


def test_openfda_404_is_no_match_not_failure(monkeypatch):
    # openFDA returns HTTP 404 for a valid query with zero results — must be
    # reported as "no matching", never as a request failure.
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(status=404))
    _, status = engine.search_openfda("zzznotadevice")
    assert "no matching" in status and "failed" not in status


def test_build_grounded_context_labels_sections(monkeypatch):
    monkeypatch.setattr(engine, "search_clinicaltrials", lambda t, **k: ("- NCT1 | X", "✅ CT"))
    monkeypatch.setattr(engine, "search_openfda", lambda t, **k: ("", "⚠️ openFDA: none"))
    monkeypatch.setattr(engine, "search_pubmed", lambda t, **k: ("- PMID 9 | Y", "✅ PubMed"))
    ctx, statuses = engine.build_grounded_context("m", "u", "p")
    assert "### ClinicalTrials.gov" in ctx and "### PubMed" in ctx
    assert "### openFDA" not in ctx  # empty sources are omitted, not shown blank
    assert len(statuses) == 3
