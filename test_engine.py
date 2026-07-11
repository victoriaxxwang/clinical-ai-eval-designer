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

import json
import os
import re

import pytest
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


# --- 1b. Disease-agnosticism: invariants must hold across ANY indication ----

# A deliberately diverse spread — cardiology, oncology, sepsis, dermatology,
# mental health, ophthalmology, radiology, pathology, wearables, obstetrics,
# gastroenterology, pulmonology. The engine is domain-agnostic, so we assert
# only invariants (valid/deterministic/filler-free queries), never a
# disease-specific keyword.
DIVERSE_CASES = [
    ("Detects atrial fibrillation from single-lead ECG", "AFib detection", "Ambulatory adults"),
    ("Detects lung nodules on low-dose chest CT", "Lung cancer screening", "Adult smokers"),
    ("Predicts sepsis onset from EHR vitals and labs", "Early sepsis prediction", "ICU patients"),
    ("Classifies skin lesions from dermoscopy", "Melanoma detection", "Dermatology clinic patients"),
    ("Detects depression from speech prosody", "Depression screening", "Primary care adults"),
    ("Detects diabetic retinopathy from fundus photographs", "DR screening", "Adults with diabetes"),
    ("Detects intracranial hemorrhage on head CT", "Acute stroke triage", "ED patients"),
    ("Grades prostate cancer from histopathology slides", "Prostate cancer grading", "Biopsy patients"),
    ("Estimates blood glucose from a wearable optical sensor", "Glucose monitoring", "Adults with diabetes"),
    ("Predicts preeclampsia from maternal serum biomarkers", "Preeclampsia risk", "Pregnant patients"),
    ("Detects polyps in colonoscopy video", "Colorectal cancer screening", "Screening-age adults"),
    ("Detects pneumonia on chest X-ray", "Pneumonia screening", "Hospitalized adults"),
]


@pytest.mark.parametrize("model,use_case,population", DIVERSE_CASES)
def test_queries_are_valid_for_any_indication(model, use_case, population):
    q1 = engine.build_queries(model, use_case, population)
    # deterministic for every domain
    assert q1 == engine.build_queries(model, use_case, population)
    # non-empty, bounded, focused search terms
    assert q1["ct"] and len(q1["ct"]) <= 200 and 1 <= len(q1["ct"].split()) <= 4
    assert q1["pubmed"] and len(q1["pubmed"]) <= 250
    # a usable device keyword: present, not a stopword/verb/generic
    assert q1["fda"] and q1["fda"] not in engine._STOP and len(q1["fda"]) > 2


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


def test_openfda_safety_parses_pma_maude_recall(monkeypatch):
    # The three post-market/Class-III endpoints each have a different JSON shape and
    # dedup key — this fails loudly the day any of those field paths moves.
    def fake_get(url, **k):
        if "pma.json" in url:
            return FakeResp({"results": [
                {"pma_number": "P123456", "supplement_number": "S001",
                 "decision_code": "APPR", "decision_date": "2020-01-01",
                 "product_code": "DXN", "applicant": "Acme Cardio",
                 "generic_name": "cardiac monitor"}]})
        if "event.json" in url:  # MAUDE: device is a nested list
            return FakeResp({"results": [
                {"event_type": "Malfunction", "date_received": "2021-05-05",
                 "report_number": "1234567-2021-00001",
                 "device": [{"generic_name": "cardiac monitor", "brand_name": "AcmeECG"}]}]})
        if "enforcement.json" in url:
            return FakeResp({"results": [
                {"classification": "Class II", "status": "Ongoing",
                 "reason_for_recall": "Software error causes false alarms",
                 "recalling_firm": "Acme Cardio", "recall_initiation_date": "20220202",
                 "recall_number": "Z-1234-2022",
                 "product_description": "cardiac monitor software"}]})
        return FakeResp(status=404)

    monkeypatch.setattr(engine.requests, "get", fake_get)
    text, status = engine.search_openfda_safety("cardiac")
    assert "PMA" in text and "P123456" in text            # Class III premarket approval
    assert "MAUDE" in text and "Malfunction" in text       # adverse-event signal, nested device
    assert "1234567-2021-00001" in text
    assert "Recall" in text and "Z-1234-2022" in text      # enforcement action
    assert "false alarms" in text                          # reason_for_recall surfaced
    assert status.startswith("✅") and "3 PMA/MAUDE/recall records" in status


def test_openfda_safety_survives_one_endpoint_outage(monkeypatch):
    # MAUDE times out, PMA answers, recall has zero matches (404) → the section still
    # returns PMA rather than going blank. Post-market safety must degrade, not vanish.
    def fake_get(url, **k):
        if "event.json" in url:
            raise requests.ConnectionError("MAUDE down")
        if "pma.json" in url:
            return FakeResp({"results": [
                {"pma_number": "P999", "generic_name": "widget", "decision_date": "2019-01-01"}]})
        return FakeResp(status=404)  # enforcement: valid query, no results

    monkeypatch.setattr(engine.requests, "get", fake_get)
    text, status = engine.search_openfda_safety("widget")
    assert "P999" in text
    assert status.startswith("✅")  # a partial result is still success, not failure


def test_openfda_safety_404_everywhere_is_no_match_not_failure(monkeypatch):
    # Every endpoint returns 404 (openFDA's "zero results" for a valid query) → must be
    # reported as "no matching", never as a request failure.
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(status=404))
    _, status = engine.search_openfda_safety("zzznotadevice")
    assert "no matching" in status and "failed" not in status


# --- 2c. Tier B (3): drug/biologic endpoints (Drugs@FDA / SPL label / FAERS) ----

def test_build_queries_emits_drug_terms():
    # A drug/biologic model: the distinctive drug NAME must survive into drug_terms,
    # and a device modality must never be mistaken for one.
    q = engine.build_queries(
        "AI model that predicts warfarin dosing from INR and comorbidities",
        "Anticoagulation dosing", "Adults on warfarin therapy")
    dt = q["drug_terms"]
    assert isinstance(dt, list) and 1 <= len(dt) <= 4
    assert "warfarin" in dt                    # the drug name is the key signal
    assert "photoplethysmography" not in dt     # a device modality is not a drug name


def test_openfda_drug_parses_drugsfda_label_faers(monkeypatch):
    # The three drug/biologic endpoints each have a different JSON shape and dedup key
    # (application_number / SPL id / safetyreportid) — this fails loudly the day any of
    # those field paths moves. Note openfda fields are LISTS; FAERS nests drug+reaction.
    def fake_get(url, **k):
        if "drugsfda.json" in url:
            return FakeResp({"results": [
                {"application_number": "NDA009218", "sponsor_name": "Bristol",
                 "openfda": {"brand_name": ["COUMADIN"], "generic_name": ["WARFARIN SODIUM"],
                             "substance_name": ["WARFARIN SODIUM"]},
                 "products": [{"brand_name": "COUMADIN", "marketing_status": "Prescription",
                               "route": "ORAL"}]}]})
        if "label.json" in url:
            return FakeResp({"results": [
                {"id": "spl-guid-0001",
                 "openfda": {"brand_name": ["COUMADIN"], "generic_name": ["WARFARIN SODIUM"],
                             "application_number": ["NDA009218"]},
                 "indications_and_usage": ["COUMADIN is indicated for prophylaxis of venous thrombosis."],
                 "boxed_warning": ["WARNING: BLEEDING RISK"]}]})
        if "event.json" in url:  # FAERS: patient.drug + patient.reaction are nested lists
            return FakeResp({"results": [
                {"safetyreportid": "US-2021-0001", "serious": "1", "receivedate": "20210303",
                 "patient": {"drug": [{"medicinalproduct": "WARFARIN",
                                       "openfda": {"generic_name": ["warfarin sodium"]}}],
                             "reaction": [{"reactionmeddrapt": "Haemorrhage"}]}}]})
        return FakeResp(status=404)

    monkeypatch.setattr(engine.requests, "get", fake_get)
    text, status = engine.search_openfda_drug("warfarin")
    assert "Drugs@FDA" in text and "NDA009218" in text and "COUMADIN" in text   # approval anchor
    assert "SPL label" in text and "prophylaxis" in text                         # indication surfaced
    assert "boxed_warning=YES" in text                                           # boxed warning flagged
    assert "FAERS" in text and "Haemorrhage" in text and "US-2021-0001" in text  # adverse-event signal
    assert status.startswith("✅") and "3 Drugs@FDA/label/FAERS records" in status


def test_openfda_drug_survives_one_endpoint_outage(monkeypatch):
    # SPL label times out, Drugs@FDA answers, FAERS has zero matches (404) → the section
    # still returns the approval record rather than going blank.
    def fake_get(url, **k):
        if "label.json" in url:
            raise requests.ConnectionError("label endpoint down")
        if "drugsfda.json" in url:
            return FakeResp({"results": [
                {"application_number": "NDA999", "sponsor_name": "Acme Pharma",
                 "openfda": {"generic_name": ["widgetazole"]}}]})
        return FakeResp(status=404)  # FAERS: valid query, no results

    monkeypatch.setattr(engine.requests, "get", fake_get)
    text, status = engine.search_openfda_drug("widgetazole")
    assert "NDA999" in text
    assert status.startswith("✅")  # a partial result is still success, not failure


def test_openfda_drug_404_everywhere_is_no_match_not_failure(monkeypatch):
    # Every endpoint returns 404 (openFDA's "zero results" for a valid query) → must be
    # reported as "no matching", never as a request failure.
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(status=404))
    _, status = engine.search_openfda_drug("zzznotadrug")
    assert "no matching" in status and "failed" not in status


def test_grounded_context_gates_drug_endpoints_by_intervention_type(monkeypatch):
    # The intervention-type gate must route deterministically: device (default) never
    # touches the drug endpoints; drug swaps device→drug; both queries everything. The
    # statuses list keeps its device-run shape so the index-based tests stay valid.
    calls = {"drug": 0}
    monkeypatch.setattr(engine, "search_clinicaltrials", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda_safety", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_literature", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_pubmed", lambda t, **k: ("", "⚠️ none"))

    def fake_drug(t, **k):
        calls["drug"] += 1
        return ("- Drugs@FDA | COUMADIN | application=NDA009218", "✅ openFDA drug: 1 record")
    monkeypatch.setattr(engine, "search_openfda_drug", fake_drug)

    # default = device → drug endpoints must NOT be queried
    ctx, statuses, _ = engine.build_grounded_context("m", "u", "p")
    assert calls["drug"] == 0
    assert "### openFDA drug" not in ctx
    assert len(statuses) == 4  # ct, classification, safety, literature (unchanged shape)

    # intervention_type="drug" → drug endpoints queried, section present, device omitted
    ctx2, statuses2, _ = engine.build_grounded_context("m", "u", "p", intervention_type="drug")
    assert calls["drug"] == 1
    assert "### openFDA drug/biologic" in ctx2 and "NDA009218" in ctx2
    assert "### openFDA (device" not in ctx2  # device classification skipped for a pure drug
    assert len(statuses2) == 3  # ct, drug, literature

    # "both" → device AND drug both queried
    _, statuses3, _ = engine.build_grounded_context("m", "u", "p", intervention_type="both")
    assert calls["drug"] == 2
    assert len(statuses3) == 5  # ct, classification, safety, drug, literature


def test_europepmc_extracts_pmid_and_doi(monkeypatch):
    # The whole point of Europe PMC: a DOI alongside the PMID in one call.
    payload = {"resultList": {"result": [
        {"source": "MED", "id": "42346460", "pmid": "42346460",
         "doi": "10.3390/s23208423", "title": "HRV and stress",
         "journalTitle": "Sensors", "pubYear": "2026"},
        {"source": "PPR", "id": "PPR12345", "doi": "10.1101/2026.01.01.123456",
         "title": "A preprint", "journalTitle": "medRxiv", "pubYear": "2026"},
    ]}}
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(payload))
    text, status = engine.search_europepmc("hrv stress")
    assert "PMID 42346460" in text and "DOI 10.3390/s23208423" in text
    assert "10.1101/2026.01.01.123456" in text  # preprint DOI surfaced too
    assert "2 with DOI" in status


def test_crossref_verify_true_false_none(monkeypatch):
    # 200 → resolves (True); 404 → definitively absent (False); network error → None.
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(status=200))
    assert engine.crossref_verify("10.1/real") is True
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(status=404))
    assert engine.crossref_verify("10.1/fake") is False

    def boom(*a, **k):
        raise requests.ConnectionError("crossref down")
    monkeypatch.setattr(engine.requests, "get", boom)
    assert engine.crossref_verify("10.1/whatever") is None  # unknown, not False
    assert engine.crossref_verify("") is None  # empty DOI short-circuits


def test_europepmc_verify_drops_unresolvable_doi(monkeypatch):
    # A DOI Crossref reports as 404 is dropped from its citation, but the PAPER is
    # kept (its PMID still resolves). A verified DOI is marked ✓Crossref.
    epmc_payload = {"resultList": {"result": [
        {"source": "MED", "id": "1", "pmid": "111", "doi": "10.1/good",
         "title": "Real paper", "journalTitle": "J", "pubYear": "2026"},
        {"source": "MED", "id": "2", "pmid": "222", "doi": "10.1/bad",
         "title": "Bad-DOI paper", "journalTitle": "J", "pubYear": "2026"},
    ]}}

    def fake_get(url, **k):
        if "europepmc" in url:
            return FakeResp(epmc_payload)
        # Crossref: the good DOI resolves (200), the bad one 404s.
        return FakeResp(status=200) if "10.1/good" in url else FakeResp(status=404)

    monkeypatch.setattr(engine.requests, "get", fake_get)
    text, status = engine.search_europepmc("q", verify=True)
    assert "DOI 10.1/good ✓Crossref" in text  # verified DOI marked
    assert "10.1/bad" not in text             # unresolvable DOI dropped
    assert "PMID 222" in text                 # ...but the paper is kept via its PMID
    assert "1 with DOI, 1 Crossref-verified" in status


# --- 2b. Tier B: multi-provider literature merge (OpenAlex + Semantic Scholar) ---

def test_normalize_doi_canonicalizes_for_dedup():
    # OpenAlex hands back a full resolver URL; Europe PMC / S2 hand back the bare DOI.
    # Both must collapse to the same lowercase key so the same paper dedupes to one.
    assert engine._normalize_doi("https://doi.org/10.1/AbC") == "10.1/abc"
    assert engine._normalize_doi("http://dx.doi.org/10.1/AbC") == "10.1/abc"
    assert engine._normalize_doi("doi:10.1/X") == "10.1/x"
    assert engine._normalize_doi("10.1/AbC") == "10.1/abc"
    assert engine._normalize_doi("") == "" and engine._normalize_doi(None) == ""


def test_openalex_records_parse(monkeypatch):
    # PMID arrives as a full pubmed URL; DOI as a resolver URL; journal is nested.
    payload = {"results": [
        {"doi": "https://doi.org/10.1/AbC",
         "ids": {"pmid": "https://pubmed.ncbi.nlm.nih.gov/999"},
         "title": "Wearable stress", "publication_year": 2025,
         "primary_location": {"source": {"display_name": "J Sensors"}},
         "id": "https://openalex.org/W1"},
    ]}
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(payload))
    recs = engine._openalex_records("stress")
    assert len(recs) == 1
    r = recs[0]
    assert r["pmid"] == "999"          # extracted from the URL tail
    assert r["doi"] == "https://doi.org/10.1/AbC"  # raw; normalized only on merge
    assert r["year"] == "2025" and r["journal"] == "J Sensors"
    assert r["source_db"] == "OpenAlex"


def test_semanticscholar_records_parse(monkeypatch):
    payload = {"data": [
        {"title": "Prosody depression", "year": 2024, "venue": "ICASSP",
         "externalIds": {"DOI": "10.2/xyz", "PubMed": "12345"}, "paperId": "abcd"},
    ]}
    monkeypatch.setattr(engine.requests, "get", lambda *a, **k: FakeResp(payload))
    recs = engine._semanticscholar_records("depression")
    assert len(recs) == 1
    r = recs[0]
    assert r["pmid"] == "12345" and r["doi"] == "10.2/xyz"
    assert r["journal"] == "ICASSP" and r["year"] == "2024"
    assert r["source_db"] == "Semantic Scholar"


def test_search_literature_merges_and_dedupes_across_providers(monkeypatch):
    # Same paper 'a' is found by Europe PMC (bare DOI) and OpenAlex (URL/uppercase DOI)
    # → must dedupe to ONE record tagged with BOTH sources. Paper 'b' is found by
    # Europe PMC (via DOI) and Semantic Scholar (via PMID only) → dedupe by PMID.
    # 'c' (OpenAlex-only) and 'd' (S2-only) are unique contributions that must survive.
    def epmc(t, max_results=15):
        return [
            {"pmid": "1", "doi": "10.1/a", "title": "A", "journal": "J", "year": "2026",
             "source_db": "Europe PMC", "alt_id": "MED:1"},
            {"pmid": "2", "doi": "10.1/b", "title": "B", "journal": "J", "year": "2026",
             "source_db": "Europe PMC", "alt_id": "MED:2"},
        ]

    def oa(t, max_results=15):
        return [
            {"pmid": "", "doi": "https://doi.org/10.1/A", "title": "A", "journal": "J",
             "year": "2026", "source_db": "OpenAlex", "alt_id": "W1"},  # dup of 'a'
            {"pmid": "3", "doi": "10.1/c", "title": "C", "journal": "J", "year": "2026",
             "source_db": "OpenAlex", "alt_id": "W2"},
        ]

    def s2(t, max_results=15):
        return [
            {"pmid": "2", "doi": "", "title": "B", "journal": "J", "year": "2026",
             "source_db": "Semantic Scholar", "alt_id": "S2:x"},  # dup of 'b' via PMID
            {"pmid": "4", "doi": "10.1/d", "title": "D", "journal": "J", "year": "2026",
             "source_db": "Semantic Scholar", "alt_id": "S2:y"},
        ]

    monkeypatch.setattr(engine, "_europepmc_records", epmc)
    monkeypatch.setattr(engine, "_openalex_records", oa)
    monkeypatch.setattr(engine, "_semanticscholar_records", s2)
    text, status = engine.search_literature("q")  # verify=False → no Crossref calls

    lines = [l for l in text.splitlines() if l.strip()]
    assert len(lines) == 4                       # deduped to exactly 4 papers
    assert text.count("DOI 10.1/a") == 1         # 'a' appears once, not twice
    a_line = next(l for l in lines if "10.1/a" in l)
    assert "Europe PMC" in a_line and "OpenAlex" in a_line  # both sources credited
    assert "10.1/c" in text and "10.1/d" in text  # provider-unique papers survive
    assert "4 articles from Europe PMC, OpenAlex, Semantic Scholar" in status


def test_search_literature_survives_a_provider_outage(monkeypatch):
    # Europe PMC down (or S2 429s) → the section still returns the others' results
    # and names the unreachable provider, instead of going blank.
    def boom(t, max_results=15):
        raise requests.ConnectionError("provider down")

    monkeypatch.setattr(engine, "_europepmc_records", boom)
    monkeypatch.setattr(engine, "_openalex_records",
                        lambda t, max_results=15: [
                            {"pmid": "3", "doi": "10.1/c", "title": "C", "journal": "J",
                             "year": "2026", "source_db": "OpenAlex", "alt_id": "W2"}])
    monkeypatch.setattr(engine, "_semanticscholar_records",
                        lambda t, max_results=15: [
                            {"pmid": "4", "doi": "10.1/d", "title": "D", "journal": "J",
                             "year": "2026", "source_db": "Semantic Scholar", "alt_id": "S2:y"}])
    text, status = engine.search_literature("q")
    assert "10.1/c" in text and "10.1/d" in text
    assert "unreachable: Europe PMC" in status
    assert status.startswith("✅")  # a partial result is still a success, not a failure


def test_coverage_gaps_note_names_unreachable_paid_dbs():
    note = engine.coverage_gaps_note()
    for db in ("Embase", "PsycINFO", "Cochrane", "Scopus", "Web of Science", "CINAHL"):
        assert db in note, f"coverage note must name the unreachable DB {db!r}"
    assert "not evidence of absence" in note.lower()
    # PMA/MAUDE/recall ARE queried now (Tier B 2) — the note must credit them as
    # searched, not still list them as a gap, or the honesty disclosure is stale.
    assert "PMA" in note and "MAUDE" in note and "recall" in note.lower()
    assert "PMA / MAUDE / recall endpoints" not in note  # the old "not queried" wording is gone


def test_coverage_gaps_note_tracks_intervention_type():
    # Device-only run: drug pathways are honestly listed as a GAP.
    dev = engine.coverage_gaps_note("device")
    assert "not queried" in dev
    assert "(Drugs@FDA, SPL labeling, FAERS) and non-US" in dev  # grouped as un-queried
    # Drug / both run: the drug pathways ARE searched, so they must be credited, not
    # still listed as an un-queried gap — otherwise the disclosure is stale.
    for it in ("drug", "both"):
        note = engine.coverage_gaps_note(it)
        assert "Drugs@FDA" in note and "FAERS" in note
        assert "(Drugs@FDA, SPL labeling, FAERS) and non-US" not in note


def test_grounded_context_returns_utc_snapshot_timestamp(monkeypatch):
    monkeypatch.setattr(engine, "search_clinicaltrials", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda_safety", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_literature", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_pubmed", lambda t, **k: ("", "⚠️ none"))
    ctx, statuses, ts = engine.build_grounded_context("m", "u", "p")
    # ISO-8601 UTC, e.g. 2026-07-08T14:33:07Z — the frozen snapshot instant.
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", ts)
    # metadata + coverage are emitted even when NOTHING was retrieved (self-describing bundle)
    assert "### Retrieval Metadata" in ctx and ts in ctx
    assert "### Coverage & Retrieval Gaps" in ctx


def test_build_grounded_context_labels_sections(monkeypatch):
    monkeypatch.setattr(engine, "search_clinicaltrials", lambda t, **k: ("- NCT1 | X", "✅ CT"))
    monkeypatch.setattr(engine, "search_openfda", lambda t, **k: ("", "⚠️ openFDA: none"))
    monkeypatch.setattr(engine, "search_openfda_safety", lambda t, **k: ("", "⚠️ openFDA safety: none"))
    monkeypatch.setattr(engine, "search_literature", lambda t, **k: ("- PMID 9 | DOI 10.1/x | Y", "✅ Literature"))
    ctx, statuses, ts = engine.build_grounded_context("m", "u", "p")
    assert "### ClinicalTrials.gov" in ctx and "### Literature" in ctx
    assert "### openFDA" not in ctx  # empty sources are omitted, not shown blank
    assert "### Retrieval Metadata" in ctx and ts in ctx  # snapshot time is embedded
    assert "### Coverage & Retrieval Gaps" in ctx  # honesty note always present
    assert len(statuses) == 4  # ct, openFDA classification, openFDA safety, literature


def test_grounded_context_falls_back_to_pubmed_when_literature_empty(monkeypatch):
    # All three merge-providers hiccup → PubMed keeps the literature section from blank.
    monkeypatch.setattr(engine, "search_clinicaltrials", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda_safety", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_literature", lambda t, **k: ("", "❌ Literature: all providers unreachable"))
    monkeypatch.setattr(engine, "search_pubmed", lambda t, **k: ("- PMID 7 | Z", "✅ PubMed: 1 articles"))
    ctx, statuses, ts = engine.build_grounded_context("m", "u", "p")
    assert "### Literature" in ctx and "PMID 7" in ctx
    assert statuses[3].startswith("✅ PubMed")  # literature slot (idx 3); fallback surfaced


# --- 2d. Tier B (4): MeSH normalization (condition → canonical heading + synonyms) --

def test_mesh_candidates_prefers_bigrams_then_unigrams():
    # Multi-word MeSH headings ("Lung Neoplasms") need a bigram to resolve, so the
    # candidate list must try consecutive-word phrases BEFORE single words.
    # _mesh_candidates now returns (candidates, new_bares) — the second element is the
    # set of model-description unigrams appended by the surface-buried-disease broadening.
    cands, new_bares = engine._mesh_candidates(
        "Lung cancer screening", "Detects lung nodules on chest CT", ["lung"])
    assert "lung cancer" in cands                 # condition-anchored bigram present
    assert " " in cands[0]                         # a multi-word phrase is tried first
    # every surviving unigram is ranked after all bigrams (specific → general)
    bigram_idx = [i for i, c in enumerate(cands) if " " in c]
    unigram_idx = [i for i, c in enumerate(cands) if " " not in c]
    assert not unigram_idx or max(bigram_idx) < min(unigram_idx)
    assert all(len(c) > 2 for c in cands)         # no 1-2 char junk
    assert len(cands) <= 8                         # still bounded (existing + model bares)
    # the appended model-desc bares are reported and are all part of the candidate list
    assert new_bares <= set(cands)                 # new bares are a subset of candidates
    assert "nodules" in new_bares                  # a buried model-desc word was surfaced


def test_normalize_mesh_resolves_synonym_to_canonical(monkeypatch):
    # "heart attack" (an entry-term synonym) must map to the canonical heading
    # Myocardial Infarction (D009203) with its synonyms, deduped against the
    # preferred label. Mirrors the live NCBI MeSH esearch→esummary shape.
    def fake_get(url, **k):
        if "esearch" in url:
            return FakeResp({"esearchresult": {"idlist": ["68009203"]}})
        return FakeResp({"result": {"68009203": {
            "ds_meshui": "D009203",
            "ds_meshterms": ["Myocardial Infarction", "Heart Attack", "Myocardial Infarct",
                             "Myocardial Infarction", "Cardiovascular Stroke", "Heart Attacks"]}}})
    monkeypatch.setattr(engine.requests, "get", fake_get)
    mesh = engine.normalize_mesh(["heart attack", "attack"])
    assert mesh["descriptor_id"] == "D009203"
    assert mesh["preferred"] == "Myocardial Infarction"
    assert "Heart Attack" in mesh["synonyms"]
    assert "Myocardial Infarction" not in mesh["synonyms"]   # preferred not duplicated
    assert mesh["input"] == "heart attack"                    # first candidate that resolved
    assert len(mesh["synonyms"]) <= engine.MESH_MAX_TERMS - 1  # bounded expansion


def test_normalize_mesh_rejects_qualifier_result(monkeypatch):
    # A generic word ("screening") can map to a MeSH QUALIFIER/subheading (a Q… id,
    # e.g. "diagnosis") — never a condition. normalize_mesh must reject any non-D/C
    # descriptor so a subheading can't misground the query.
    def fake_get(url, **k):
        if "esearch" in url:
            return FakeResp({"esearchresult": {"idlist": ["82000175"]}})
        return FakeResp({"result": {"82000175": {
            "ds_meshui": "Q000175", "ds_meshterms": ["diagnosis"]}}})
    monkeypatch.setattr(engine.requests, "get", fake_get)
    assert engine.normalize_mesh(["screening"]) is None


def test_mesh_candidates_uses_model_terms_when_usecase_is_generic():
    # A terse use_case ("DR screening") names no condition; the real one ("diabetic
    # retinopathy") lives in the model description. Anchoring bigrams on the model's
    # clinical terms must surface it, tried BEFORE the generic bare "screening".
    cands, _new_bares = engine._mesh_candidates(
        "DR screening", "Detects diabetic retinopathy from fundus photographs",
        ["diabetic", "retinopathy"], ["screening"])
    assert "diabetic retinopathy" in cands
    assert cands[0] == "diabetic retinopathy"   # condition bigram first, not "screening"


def test_normalize_mesh_skips_ambiguous_and_empty(monkeypatch):
    # An ambiguous/non-MeSH token (bare "stress", "MI") returns an empty idlist →
    # normalize_mesh must return None (graceful skip), never a garbage heading.
    monkeypatch.setattr(engine.requests, "get",
                        lambda *a, **k: FakeResp({"esearchresult": {"idlist": []}}))
    assert engine.normalize_mesh(["stress", "acute stress"]) is None
    assert engine.normalize_mesh([]) is None          # nothing to look up
    assert engine.normalize_mesh(["ab"]) is None       # too short → skipped, no call


def test_normalize_mesh_survives_lookup_outage(monkeypatch):
    # NLM/NCBI unreachable → None (fall back to raw keywords), never an exception.
    def boom(*a, **k):
        raise requests.ConnectionError("mesh down")
    monkeypatch.setattr(engine.requests, "get", boom)
    assert engine.normalize_mesh(["melanoma"]) is None


# --- 1c. Clinical-category filter + surface-buried-disease (engine hardening) --

def _mesh_resolver(monkeypatch, descriptor, terms):
    """Make normalize_mesh resolve its first candidate to a fixed descriptor+terms,
    bypassing the two E-utilities calls. The tree CATEGORY is controlled separately
    by mocking _mesh_tree_cats, so each test isolates the category gate cleanly."""
    def fake_get(endpoint, params):
        if endpoint == "esearch":
            return FakeResp({"esearchresult": {"idlist": ["1"]}})
        return FakeResp({"result": {"1": {"ds_meshui": descriptor,
                                          "ds_meshterms": terms}}})
    monkeypatch.setattr(engine, "_eutils_mesh_get", fake_get)


def test_accept_mesh_category_truth_table():
    # Pure gate. EXISTING disciplined candidates accept a real clinical heading —
    # C (disease), F/F03 (psychology/mental disorder), or D (drug) — and reject
    # body-parts (A), methods (G/L), people/groups (M). A NEW model-description bare
    # accepts a DISEASE (C) ONLY, so a buried condition surfaces but noise words don't.
    acc = engine._accept_mesh_category
    for cat in ({"C"}, {"F"}, {"F03"}, {"D"}):
        assert acc(cat, False) is True          # existing candidate keeps clinical/drug
    for cat in ({"A"}, {"G"}, {"L"}, {"M"}):
        assert acc(cat, False) is False         # existing candidate rejects junk
    assert acc({"C"}, True) is True             # new bare: disease surfaces
    for cat in ({"F"}, {"F03"}, {"D"}, {"A"}):
        assert acc(cat, True) is False          # new bare: everything non-disease dropped
    # Tree lookup unavailable (empty cats) → keep existing, never introduce a new bare.
    assert acc(set(), False) is True
    assert acc(set(), True) is False


def test_normalize_mesh_keeps_existing_clinical_headings(monkeypatch):
    # The filter must NOT break the working goldens: an existing candidate resolving
    # to a drug (warfarin, D) or a psychology heading (HRV → Stress, Psychological, F)
    # is kept exactly as before.
    _mesh_resolver(monkeypatch, "D014859", ["Warfarin", "Coumadin"])
    monkeypatch.setattr(engine, "_mesh_tree_cats", lambda did: {"D"})
    assert engine.normalize_mesh(["warfarin"])["preferred"] == "Warfarin"

    _mesh_resolver(monkeypatch, "D013315", ["Stress, Psychological", "Psychological Stress"])
    monkeypatch.setattr(engine, "_mesh_tree_cats", lambda did: {"F"})
    assert engine.normalize_mesh(["psychological stress"])["preferred"] == "Stress, Psychological"


def test_normalize_mesh_rejects_existing_anatomy_or_method(monkeypatch):
    # The mis-resolutions the filter exists to kill: a description that buried its
    # disease used to map to body-parts (Thorax, A) or methods (Machine Learning, G).
    # Even as an EXISTING candidate, a non-clinical/non-drug heading is now rejected.
    _mesh_resolver(monkeypatch, "D013909", ["Thorax"])
    monkeypatch.setattr(engine, "_mesh_tree_cats", lambda did: {"A"})
    assert engine.normalize_mesh(["thorax"]) is None

    _mesh_resolver(monkeypatch, "D000069550", ["Machine Learning"])
    monkeypatch.setattr(engine, "_mesh_tree_cats", lambda did: {"G", "L"})
    assert engine.normalize_mesh(["machine learning"]) is None


def test_normalize_mesh_surfaces_buried_disease_as_new_bare(monkeypatch):
    # A disease name buried in a mechanism-first description is appended as a NEW bare;
    # because it resolves to a disease heading (C), the category gate lets it through —
    # this is what finally lets a buried condition ground the query.
    _mesh_resolver(monkeypatch, "D011014", ["Pneumonia"])
    monkeypatch.setattr(engine, "_mesh_tree_cats", lambda did: {"C"})
    mesh = engine.normalize_mesh(["pneumonia"], new_bares={"pneumonia"})
    assert mesh is not None and mesh["preferred"] == "Pneumonia"


def test_normalize_mesh_drops_new_bare_that_is_not_a_disease(monkeypatch):
    # A broadened model-description bare that resolves to a NON-disease heading
    # (e.g. "learning" → Learning, F) must be dropped — new bares accept C only, so
    # noise words the description happens to contain can't misground the query.
    _mesh_resolver(monkeypatch, "D007858", ["Learning"])
    monkeypatch.setattr(engine, "_mesh_tree_cats", lambda did: {"F"})
    assert engine.normalize_mesh(["learning"], new_bares={"learning"}) is None


def test_build_queries_emits_mesh_new_bares_from_buried_disease(monkeypatch):
    # build_queries must expose the broadened bares so build_grounded_context can pass
    # them to normalize_mesh. A mechanism-first description that never names the disease
    # in the opening words still surfaces it as a candidate + a reported new bare.
    q = engine.build_queries(
        "A gradient-boosted model that ingests routine EHR vital-sign trends and "
        "laboratory results to flag inpatient pneumonia decompensation.",
        "Inpatient deterioration monitoring", "Admitted adults")
    assert "mesh_new_bares" in q
    assert q["mesh_new_bares"] == sorted(q["mesh_new_bares"])   # emitted sorted
    assert set(q["mesh_new_bares"]) <= set(q["mesh_candidates"])  # bares ⊆ candidates
    assert "pneumonia" in q["mesh_new_bares"]                   # buried disease surfaced


def test_build_queries_expands_condition_when_mesh_given():
    args = ("Classifies skin lesions from dermoscopy", "Melanoma detection", "Adults")
    base = engine.build_queries(*args)
    mesh = {"descriptor_id": "D008545", "preferred": "Melanoma",
            "synonyms": ["Malignant Melanoma", "Melanomas"], "input": "melanoma"}
    exp = engine.build_queries(*args, mesh=mesh)
    # without mesh: the raw-keyword query is unchanged (back-compat, no quotes/OR)
    assert '"Melanoma"' not in base["ct"] and " OR " not in base["ct"]
    # with mesh: a boolean OR-group over canonical + synonyms, method AND-ed in
    assert '"Melanoma"' in exp["ct"] and '"Malignant Melanoma"' in exp["ct"]
    assert " OR " in exp["ct"] and " AND " in exp["ct"]
    assert exp["ct"] == exp["pubmed"]
    assert "dermoscopy" in exp["ct"]                   # distinctive modality kept as focus
    # relevance-provider form is a plain bag: canonical first, no boolean operators
    assert exp["lit_bow"].startswith("Melanoma") and " OR " not in exp["lit_bow"]
    # candidates for the resolver are always surfaced (bigram-first)
    assert base["mesh_candidates"] and "melanoma" in base["mesh_candidates"]


def test_grounded_context_applies_and_records_mesh(monkeypatch):
    # End-to-end wiring: a resolved heading is recorded in the metadata (auditable),
    # Europe PMC receives the boolean OR-group (bool_term), and the relevance
    # providers receive the plain bag (term).
    captured = {}
    monkeypatch.setattr(engine, "normalize_mesh", lambda cands, **k: {
        "descriptor_id": "D013315", "preferred": "Stress, Psychological",
        "synonyms": ["Psychological Stress", "Stress, Emotional"], "children": [],
        "input": "psychological stress"})
    monkeypatch.setattr(engine, "search_clinicaltrials", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda_safety", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_pubmed", lambda t, **k: ("", "⚠️ none"))

    def fake_lit(term, **k):
        captured["term"] = term
        captured["bool_term"] = k.get("bool_term")
        return ("", "⚠️ none")
    monkeypatch.setattr(engine, "search_literature", fake_lit)

    ctx, _, _ = engine.build_grounded_context(
        "infers psychological stress from photoplethysmography", "stress detection", "adults")
    assert "MeSH normalization:" in ctx
    assert '"Stress, Psychological"' in ctx and "D013315" in ctx   # heading + descriptor logged
    assert " OR " in captured["bool_term"] and "Stress, Psychological" in captured["bool_term"]
    assert " OR " not in captured["term"]                          # relevance bag, no booleans


def test_grounded_context_notes_when_mesh_not_applied(monkeypatch):
    # No heading resolved → the metadata says so explicitly (honest, not silent).
    monkeypatch.setattr(engine, "normalize_mesh", lambda cands, **k: None)
    monkeypatch.setattr(engine, "search_clinicaltrials", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda_safety", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_literature", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_pubmed", lambda t, **k: ("", "⚠️ none"))
    ctx, _, _ = engine.build_grounded_context("m", "u", "p")
    assert "MeSH normalization: none" in ctx


# --- 2e. Step 0: eval-only ablation knobs (defaults reproduce the shipped app) --

def test_build_queries_mesh_expansion_levels():
    # The three MeSH expansion levels widen the CONDITION OR-group progressively;
    # the default arg reproduces the shipped "canonical+synonyms" exactly.
    args = ("Classifies skin lesions from dermoscopy", "Melanoma detection", "Adults")
    mesh = {"descriptor_id": "D008545", "preferred": "Melanoma",
            "synonyms": ["Malignant Melanoma", "Melanomas"],
            "children": ["Melanoma, Amelanotic"], "input": "melanoma"}
    canon = engine.build_queries(*args, mesh=mesh, mesh_expansion="canonical")
    syn = engine.build_queries(*args, mesh=mesh, mesh_expansion="canonical+synonyms")
    hier = engine.build_queries(*args, mesh=mesh, mesh_expansion="+hierarchy")
    # canonical = the preferred heading ONLY (no synonyms in the OR-group)
    assert '"Melanoma"' in canon["ct"] and '"Malignant Melanoma"' not in canon["ct"]
    # canonical+synonyms (shipped) adds the entry-term synonyms...
    assert '"Malignant Melanoma"' in syn["ct"]
    assert engine.build_queries(*args, mesh=mesh)["ct"] == syn["ct"]   # default == shipped
    # ...and +hierarchy adds the narrower child descriptor on top of the synonyms
    assert '"Melanoma, Amelanotic"' in hier["ct"] and '"Melanoma, Amelanotic"' not in syn["ct"]


def test_search_literature_sources_selects_providers(monkeypatch):
    called = []

    def mk(name):
        def fn(t, max_results=15):
            called.append(name)
            return [{"pmid": "", "doi": f"10.1/{name}", "title": name, "journal": "J",
                     "year": "2026", "source_db": name, "alt_id": name}]
        return fn
    monkeypatch.setattr(engine, "_europepmc_records", mk("Europe PMC"))
    monkeypatch.setattr(engine, "_openalex_records", mk("OpenAlex"))
    monkeypatch.setattr(engine, "_semanticscholar_records", mk("Semantic Scholar"))
    # only Europe PMC selected → the other two providers are never even queried
    _, status = engine.search_literature("q", sources=["europepmc"])
    assert called == ["Europe PMC"]
    assert "OpenAlex" not in status and "Semantic Scholar" not in status
    # None (the default) → all three, i.e. shipped behavior is unchanged
    called.clear()
    engine.search_literature("q")
    assert set(called) == {"Europe PMC", "OpenAlex", "Semantic Scholar"}


def test_grounded_context_eval_knobs_thread_through(monkeypatch):
    # verify_literature / providers / mesh_expansion must reach search_literature and
    # normalize_mesh unchanged — this is what the ablation harness turns.
    captured = {}
    monkeypatch.setattr(engine, "normalize_mesh",
                        lambda cands, **k: captured.update(
                            with_children=k.get("with_children")) or None)
    monkeypatch.setattr(engine, "search_clinicaltrials", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_openfda_safety", lambda t, **k: ("", "⚠️ none"))
    monkeypatch.setattr(engine, "search_pubmed", lambda t, **k: ("", "⚠️ none"))

    def fake_lit(term, **k):
        captured["verify"] = k.get("verify")
        captured["sources"] = k.get("sources")
        return ("", "⚠️ none")
    monkeypatch.setattr(engine, "search_literature", fake_lit)
    engine.build_grounded_context("m", "u", "p", verify_literature=False,
                                  providers=["europepmc"], mesh_expansion="+hierarchy")
    assert captured["verify"] is False
    assert captured["sources"] == ["europepmc"]
    assert captured["with_children"] is True   # "+hierarchy" asks the resolver for children


def test_mesh_children_parses_sparql_tree(monkeypatch):
    # _mesh_children walks the MeSH RDF SPARQL bindings → child preferred headings,
    # de-duplicated; a leaf (empty bindings) → []; a non-D id never hits the network.
    bindings = {"results": {"bindings": [
        {"child": {"value": "http://id.nlm.nih.gov/mesh/D003922"},
         "label": {"value": "Diabetes Mellitus, Type 1"}},
        {"child": {"value": "http://id.nlm.nih.gov/mesh/D003924"},
         "label": {"value": "Diabetes Mellitus, Type 2"}},
        {"child": {"value": "http://id.nlm.nih.gov/mesh/D003924"},  # dup → collapsed
         "label": {"value": "Diabetes Mellitus, Type 2"}},
    ]}}
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return FakeResp(bindings)
    monkeypatch.setattr(engine.requests, "get", fake_get)
    kids = engine._mesh_children("D003920")
    assert kids == ["Diabetes Mellitus, Type 1", "Diabetes Mellitus, Type 2"]
    assert calls and "id.nlm.nih.gov/mesh/sparql" in calls[0]
    # a leaf descriptor → empty bindings → no children
    monkeypatch.setattr(engine.requests, "get",
                        lambda url, **k: FakeResp({"results": {"bindings": []}}))
    assert engine._mesh_children("D003930") == []
    # a non-descriptor id (qualifier, empty) short-circuits without any network call
    calls.clear()
    monkeypatch.setattr(engine.requests, "get",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no HTTP")))
    assert engine._mesh_children("Q000706") == [] and engine._mesh_children("") == []


def test_mesh_children_survives_sparql_outage(monkeypatch):
    # SPARQL unreachable → [] (never raises), so "+hierarchy" degrades to synonyms.
    monkeypatch.setattr(engine.requests, "get",
                        lambda *a, **k: (_ for _ in ()).throw(requests.ConnectionError()))
    assert engine._mesh_children("D003920") == []


def test_normalize_mesh_populates_children_when_requested(monkeypatch):
    # with_children=True routes the resolved descriptor through _mesh_children;
    # with_children=False (the shipped default) leaves children empty and never calls it.
    def fake_get(endpoint, params):
        if endpoint == "esearch":
            return FakeResp({"esearchresult": {"idlist": ["68008545"]}})
        return FakeResp({"result": {"68008545": {
            "ds_meshui": "D008545", "ds_meshterms": ["Melanoma", "Malignant Melanoma"]}}})
    monkeypatch.setattr(engine, "_eutils_mesh_get", fake_get)
    # the clinical-category filter looks up the descriptor's MeSH tree via live SPARQL;
    # stub it so this offline test never touches the network (Melanoma is category C).
    monkeypatch.setattr(engine, "_mesh_tree_cats", lambda did: {"C"})
    seen = []
    monkeypatch.setattr(engine, "_mesh_children",
                        lambda did: seen.append(did) or ["Melanoma, Amelanotic"])
    res = engine.normalize_mesh(["melanoma"], with_children=True)
    assert res["preferred"] == "Melanoma" and res["children"] == ["Melanoma, Amelanotic"]
    assert seen == ["D008545"]        # the resolved descriptor id was passed through
    # default path does NOT fetch children
    seen.clear()
    res2 = engine.normalize_mesh(["melanoma"])
    assert res2["children"] == [] and seen == []


@pytest.mark.skipif(os.environ.get("RUN_LIVE_GOLDEN") != "1",
                    reason="hits live NLM/NCBI MeSH; set RUN_LIVE_GOLDEN=1 to run")
def test_mesh_live_resolves_known_synonym():
    """LIVE gate (opt-in). The real NCBI MeSH lookup maps the casual synonym
    'heart attack' to the canonical heading Myocardial Infarction (D009203)."""
    mesh = engine.normalize_mesh(["heart attack"])
    assert mesh and mesh["descriptor_id"] == "D009203"
    assert mesh["preferred"] == "Myocardial Infarction"
    assert any(s.lower() == "heart attack" for s in mesh["synonyms"])


@pytest.mark.skipif(os.environ.get("RUN_LIVE_GOLDEN") != "1",
                    reason="hits live NLM MeSH RDF SPARQL; set RUN_LIVE_GOLDEN=1 to run")
def test_mesh_children_live_tree_fetch():
    """LIVE gate (opt-in). The real MeSH RDF SPARQL endpoint returns a parent's
    narrower descriptors (Diabetes Mellitus → its type-1/type-2 children) and an
    empty list for a leaf term (Diabetic Retinopathy), which is what makes the
    eval-only '+hierarchy' expansion actually widen a broad condition and correctly
    no-op on a specific one."""
    kids = engine._mesh_children("D003920")            # Diabetes Mellitus (a parent)
    assert any("Type 2" in k for k in kids) and any("Type 1" in k for k in kids)
    assert engine._mesh_children("D003930") == []      # Diabetic Retinopathy (a leaf)


# --- 3. Golden retrieval-coverage gate (the HRV reference case) --------------
#
# Reframed per COMPARISON.md → Lesson 2: exact-PMID/DOI reproduction is the WRONG
# bar (ranked search over millions of papers won't reproduce a hand-curated set).
# So we split the golden target into two kinds of assertion:
#   • DETERMINISTIC set — the regulatory codes recoverable FROM THE INPUTS
#     (setting "wellness" → PWC, condition "stress" → SEN). Asserted EXACTLY.
#   • LITERATURE — asserted as a floor: "≥K on-topic, resolvable IDs", never the
#     exact golden PMIDs/DOIs.
# The other 5 golden FDA codes (HCC/QDA/QDB/QME/QZW) are curated ADJACENT
# precedents (ECG / camera-vitals / sleep-apnea) — a domain expansion not derivable
# from the model description alone — so they are deliberately NOT asserted here.

GOLDEN_CASE = {
    "model": ("Algorithm that infers psychological stress from heart-rate variability (HRV) "
              "derived from the optical photoplethysmography (PPG) sensor on a consumer "
              "wrist-worn wearable."),
    "use_case": "Continuous, passive stress detection in daily life",
    "population": "General adult consumers across a range of skin tones and activity levels",
    "setting": "Consumer wellness mobile app (non-diagnostic, direct-to-consumer)",
}

# Golden FDA codes the pipeline is expected to recover from the inputs alone.
DETERMINISTIC_FDA = {"PWC", "SEN"}
# Literature floor: at least this many on-topic, resolvable papers/DOIs.
MIN_RESOLVABLE_PAPERS = 5


def _load_golden_required():
    path = os.path.join(os.path.dirname(__file__), "golden_expected_ids.json")
    with open(path) as f:
        return json.load(f)["required"]


def test_golden_queries_target_the_deterministic_set():
    """OFFLINE gate. The golden HRV case must build queries that CAN recover the
    deterministically-recoverable golden codes — locks in fixes #1/#2b without a
    network call. If build_queries stops surfacing the setting/condition terms,
    the live recovery of PWC/SEN would silently break; this fails first, offline."""
    golden = _load_golden_required()
    assert DETERMINISTIC_FDA <= set(golden["fda_product_codes"])  # subset really is golden

    q = engine.build_queries(GOLDEN_CASE["model"], GOLDEN_CASE["use_case"],
                             GOLDEN_CASE["population"], GOLDEN_CASE["setting"])
    fda = q["fda_terms"]
    # setting "wellness" → PWC (General Wellness); condition "stress" → SEN (biofeedback)
    assert "wellness" in fda, f"setting term dropped from fda_terms: {fda}"
    assert "stress" in fda, f"condition term dropped from fda_terms: {fda}"
    # literature query stays focused on the condition, still bounded
    assert "stress" in q["ct"] and 1 <= len(q["ct"].split()) <= 4


@pytest.mark.skipif(os.environ.get("RUN_LIVE_GOLDEN") != "1",
                    reason="hits live registries; set RUN_LIVE_GOLDEN=1 to run")
def test_golden_live_retrieval_coverage():
    """LIVE gate (opt-in). Runs the real pipeline for the HRV case and asserts the
    reframed golden target: deterministic FDA codes EXACTLY, literature as a floor
    of resolvable IDs, and that a returned DOI actually resolves at Crossref."""
    ctx, _, _ = engine.build_grounded_context(
        GOLDEN_CASE["model"], GOLDEN_CASE["use_case"],
        GOLDEN_CASE["population"], "", GOLDEN_CASE["setting"])

    # (a) deterministic regulatory codes — EXACT, must all be present
    codes = set(re.findall(r"product_code=([A-Z0-9]{3})", ctx))
    missing = DETERMINISTIC_FDA - codes
    assert not missing, f"deterministic FDA codes missing from retrieval: {missing}"

    # (b) literature — a FLOOR of on-topic resolvable IDs, NOT the exact golden set
    pmids = re.findall(r"PMID (\d+)", ctx)
    dois = re.findall(r"10\.\d{4,9}/[^\s|]+", ctx)
    assert len(pmids) >= MIN_RESOLVABLE_PAPERS, f"too few PMIDs retrieved: {pmids}"
    assert len(dois) >= MIN_RESOLVABLE_PAPERS, f"too few DOIs retrieved: {dois}"
    assert all(re.match(r"10\.\d{4,9}/\S+", d) for d in dois)  # every DOI well-formed

    # (c) resolution proof — the pipeline's OWN Crossref pass (search_europepmc
    # verify=True) confirmed at least one DOI end-to-end and marked it ✓Crossref.
    # Asserting on that marker tests our real verification path and avoids a
    # redundant external call (which would only add to Crossref rate-limiting). If
    # Crossref was unreachable/throttled this run, nothing is marked → skip, not
    # fail, so infra flakiness ≠ a red build.
    if "✓Crossref" not in ctx:
        pytest.skip("Crossref unreachable/throttled this run; no DOI verified end-to-end")
