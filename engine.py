"""
Core Deterministic Engine
=========================

The Phase-1 retrieval layer, deliberately kept free of any Streamlit / UI code so
it can be unit-tested and reused by future Phase-2 agents. Everything here is a
pure function of its inputs plus deterministic public-API calls: same input →
same query → same records.

Public API:
    build_queries(model_desc, use_case, population) -> dict
    search_clinicaltrials(term) -> (text, status)
    search_openfda(keyword)     -> (text, status)
    search_pubmed(term)         -> (text, status)
    fetch_url_text(url)         -> (text, status|None)
    build_grounded_context(model_desc, use_case, population, optional_url="")
        -> (context_text, statuses)   # the Phase-1 "source records" half of the bundle
"""

from html.parser import HTMLParser

import requests

HTTP_TIMEOUT = 12  # seconds per registry call

# Filler words stripped from queries so registry searches focus on real signal.
_STOP = {
    "the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "with", "from",
    "that", "were", "was", "is", "are", "be", "by", "using", "use", "used",
    "routine", "unrelated", "reasons", "reason", "originally", "performed",
    "detect", "detects", "detection", "quantify", "quantifies", "predict",
    "predicts", "model", "models", "algorithm", "tool", "based", "via", "e.g",
    "patients", "patient", "adults", "adult",
    # action verbs — never a good device keyword
    "infer", "infers", "inferred", "classify", "classifies", "estimate",
    "estimates", "flag", "flags", "identify", "identifies", "measure",
    "measures", "assess", "assesses", "predicting", "detecting",
    # generic, non-distinctive nouns — poor device/modality keywords
    "color", "colour", "image", "images", "photograph", "photographs",
    "scan", "scans", "data", "system", "software", "signal", "signals",
    "device", "devices",
}


def _clean(text, limit):
    return " ".join((text or "").split())[:limit]


def _keywords(text, n):
    """Deterministic keyword extraction: lowercase, de-punctuate, drop stopwords
    and short tokens, de-dup preserving order, keep the first ``n``."""
    out, seen = [], set()
    normalized = (text or "").replace("-", " ").replace("/", " ")
    for raw in normalized.split():
        t = raw.strip(".,;:()[]{}\"'").lower()
        if len(t) <= 2 or t in _STOP or t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= n:
            break
    return out


def build_queries(model_desc, use_case, population=""):
    """Route each registry to a focused, deterministic query.

    - ClinicalTrials.gov / PubMed: the top few disease + modality keywords
      (filler removed). Kept deliberately short — every extra term is AND-ed by
      these APIs, so more terms means *lower* recall, not higher precision.
    - openFDA: a single strongest device keyword (token match works far better
      than a full phrase against `device_name`).
    - `population` is intentionally NOT used as a retrieval filter: qualifiers
      like "untrained general adults" over-constrain the search to zero hits.
      Population drives the model's subgroup reasoning instead (passed in the
      prompt), which is where it actually belongs.
    """
    combined = _keywords(f"{use_case} {model_desc}", 4)
    # Device keyword for openFDA: prefer the model's distinctive term (its sensor
    # / modality / anatomy) over a term it merely shares with the use case. E.g.
    # a PPG stress model → "photoplethysmography", not "stress"; a CAC-on-CT model
    # → "coronary", not "cardiovascular".
    uc_kws = set(_keywords(use_case, 8))
    model_kws = _keywords(model_desc, 8)
    device = next((k for k in model_kws if k not in uc_kws), "")
    if not device:
        device = model_kws[0] if model_kws else (_keywords(use_case, 1) or [""])[0]
    query = _clean(" ".join(combined), 200)
    return {
        "ct": query,
        "pubmed": query,
        "fda": device,
    }


def search_clinicaltrials(term, max_studies=6):
    if not term:
        return "", "⚠️ ClinicalTrials.gov: empty query"
    try:
        r = requests.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params={"query.term": term, "pageSize": max_studies},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        studies = r.json().get("studies", [])
        if not studies:
            return "", "⚠️ ClinicalTrials.gov: no matching studies"
        lines = []
        for s in studies:
            ps = s.get("protocolSection", {})
            idm = ps.get("identificationModule", {})
            dm = ps.get("designModule", {})
            design = dm.get("designInfo", {})
            primary = "; ".join(
                o.get("measure", "")
                for o in ps.get("outcomesModule", {}).get("primaryOutcomes", []) or []
            )
            lines.append(
                f"- {idm.get('nctId','')} | {idm.get('briefTitle','')} "
                f"| status={ps.get('statusModule',{}).get('overallStatus','')} "
                f"| type={dm.get('studyType','')} phases={', '.join(dm.get('phases',[]) or [])} "
                f"| n={dm.get('enrollmentInfo',{}).get('count','')} "
                f"| allocation={design.get('allocation','')} "
                f"masking={design.get('maskingInfo',{}).get('masking','')} "
                f"| primary_outcomes={_clean(primary, 300)}"
            )
        return "\n".join(lines), f"✅ ClinicalTrials.gov: {len(studies)} studies"
    except requests.Timeout:
        return "", "❌ ClinicalTrials.gov: timed out"
    except requests.RequestException:
        return "", "❌ ClinicalTrials.gov: request failed"


def search_openfda(keyword, max_results=5):
    if not keyword:
        return "", "⚠️ openFDA: empty query"
    out, ok = [], False
    for endpoint, label, fields in (
        ("classification", "CLASSIFICATION",
         lambda x: f"| product_code={x.get('product_code','')} | class={x.get('device_class','')} "
                   f"| regulation={x.get('regulation_number','')} | panel={x.get('medical_specialty_description','')}"),
        ("510k", "510(k)",
         lambda x: f"| k_number={x.get('k_number','')} | decision={x.get('decision_description','')} "
                   f"| date={x.get('decision_date','')} | applicant={x.get('applicant','')}"),
    ):
        try:
            r = requests.get(
                f"https://api.fda.gov/device/{endpoint}.json",
                params={"search": f"device_name:{keyword}", "limit": max_results},
                timeout=HTTP_TIMEOUT,
            )
            if r.ok:
                ok = True
                for res in r.json().get("results", []):
                    out.append(f"- {label} | {res.get('device_name','')} {fields(res)}")
            elif r.status_code == 404:
                ok = True  # openFDA returns 404 for a valid query with zero results
        except requests.RequestException:
            pass
    if out:
        return "\n".join(out), f"✅ openFDA: {len(out)} device records"
    if ok:
        return "", "⚠️ openFDA: no matching device records"
    return "", "❌ openFDA: request failed"


def search_pubmed(term, max_results=8):
    if not term:
        return "", "⚠️ PubMed: empty query"
    try:
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": term, "retmode": "json",
                    "retmax": max_results, "sort": "relevance"},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return "", "⚠️ PubMed: no matching articles"
        r2 = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            timeout=HTTP_TIMEOUT,
        )
        r2.raise_for_status()
        result = r2.json().get("result", {})
        lines = []
        for pid in result.get("uids", []):
            item = result.get(pid, {})
            journal = item.get("fulljournalname") or item.get("source", "")
            year = (item.get("pubdate", "") or "")[:4]
            lines.append(f"- PMID {pid} | {_clean(item.get('title',''), 250)} | {journal} {year}")
        return "\n".join(lines), f"✅ PubMed: {len(lines)} articles"
    except requests.Timeout:
        return "", "❌ PubMed: timed out"
    except requests.RequestException:
        return "", "❌ PubMed: request failed"


class _TextExtractor(HTMLParser):
    """Minimal HTML → text extractor (stdlib only; skips script/style)."""

    def __init__(self):
        super().__init__()
        self._skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self.parts.append(t)


def fetch_url_text(url, max_chars=4000):
    url = (url or "").strip()
    if not url:
        return "", None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT,
                         headers={"User-Agent": "Mozilla/5.0 (ClinicalAIEvalDesigner)"})
        r.raise_for_status()
        parser = _TextExtractor()
        parser.feed(r.text)
        text = _clean(" ".join(parser.parts), max_chars)
        if not text:
            return "", "⚠️ Reference URL: no readable text extracted"
        return text, f"✅ Reference URL: {len(text)} chars extracted"
    except requests.Timeout:
        return "", "❌ Reference URL: timed out"
    except requests.RequestException:
        return "", "❌ Reference URL: fetch failed"


def build_grounded_context(model_desc, use_case, population, optional_url=""):
    """Query every registry (+ optional URL) and assemble the Phase-1 source
    records — the half of the Phase-1 output bundle the Phase-2 critics verify
    the draft against."""
    q = build_queries(model_desc, use_case, population)
    ct_text, ct_status = search_clinicaltrials(q["ct"])
    fda_text, fda_status = search_openfda(q["fda"])
    pm_text, pm_status = search_pubmed(q["pubmed"])
    url_text, url_status = fetch_url_text(optional_url)

    sections = []
    if ct_text:
        sections.append("### ClinicalTrials.gov (study designs, endpoints, enrollment)\n" + ct_text)
    if fda_text:
        sections.append("### openFDA (device classification / 510(k) precedents)\n" + fda_text)
    if pm_text:
        sections.append("### PubMed (literature)\n" + pm_text)
    if url_text:
        sections.append("### Reference document (user-provided URL)\n" + url_text)

    statuses = [ct_status, fda_status, pm_status]
    if url_status:
        statuses.append(url_status)

    return "\n\n".join(sections)[:9000], statuses
