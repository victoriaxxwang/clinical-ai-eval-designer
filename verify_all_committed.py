#!/usr/bin/env python3
"""
Independent verification sweep across the committed golden keys.

Two orthogonal checks per case, for every SCORED id in the `required` block:

  PART 1 - LIVE RE-RESOLUTION (does this id still exist in its issuing registry?)
    pmids             -> NCBI E-utils esummary
    dois              -> Crossref works
    ncts              -> ClinicalTrials.gov API v2
    fda_product_codes -> openFDA device/classification
    fda_k_numbers     -> openFDA device/510k  (k_number field)
    fda_den_numbers   -> openFDA device/510k  (k_number field; DEN resolves here)
    fda_nda_numbers   -> openFDA drug/drugsfda (application_number field)

  PART 2 - INTERNAL CONSISTENCY (is the key self-coherent, independent of any API?)
    - format-validate every id against its category regex
    - field_grounding ids are a SUBSET of required (no orphan grounding ids)
    - no duplicate ids within a category
    - no cross-case LITERATURE collisions (a pmid/doi/nct shared across cases
        is suspicious -> FAIL). Two narrow exceptions are shared vocabulary,
        not copy-paste errors, and are reported EXPECTED rather than failing:
          (a) FDA regulatory ids (product codes, K/DEN/PMA/NDA) are a shared
              taxonomy and legitimately recur when two cases share a device class.
          (b) discipline-wide reporting-STANDARD papers (DECIDE-AI, TRIPOD+AI,
              and the like) are methodology anchors that any clinical-AI spec
              cites for Field 1; they are enumerated in METHODOLOGY_SHARED so a
              genuinely disease-specific duplicate still FAILS.
    - every required id textually appears in the case's source spec .md
        (skipped only for a case with no spec file on disk)

Exit code 0 iff every case PASSES both parts. Any failure -> non-zero.

Run from repo root with the venv active:
    source .venv/bin/activate && python verify_all_committed.py
Flags:
    --no-live        skip Part 1 (offline consistency check only)
    --case NAME      restrict per-case checks + live re-resolution to one case
                     (the cross-case collision pre-pass still spans all goldens)
"""
import json
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from collections import defaultdict

# case_name -> (golden_key_file, source_spec_md_or_None)
CASES = {
    "HRV":      ("golden_expected_ids.json",           "golden_validation_spec_HRV.md"),
    "DR":       ("golden_expected_ids_DR.json",        "golden_validation_spec_DR.md"),
    "warfarin": ("golden_expected_ids_warfarin.json",  "golden_validation_spec_warfarin.md"),
    "sepsis":   ("golden_expected_ids_sepsis.json",    "golden_validation_spec_sepsis.md"),
    "AFib":     ("golden_expected_ids_AFib.json",      "golden_validation_spec_AFib.md"),
    "melanoma": ("golden_expected_ids_melanoma.json",  "golden_validation_spec_melanoma.md"),
}

FORMAT = {
    "pmids":             re.compile(r"^\d+$"),
    "dois":              re.compile(r"^10\."),
    "ncts":              re.compile(r"^NCT\d{8}$"),
    "fda_product_codes": re.compile(r"^[A-Z]{3}$"),
    "fda_k_numbers":     re.compile(r"^K\d+$"),
    "fda_den_numbers":   re.compile(r"^DEN\d+$"),
    "fda_pma_numbers":   re.compile(r"^P\d+$"),
    "fda_nda_numbers":   re.compile(r"^(NDA|BLA|ANDA)\d+$"),
}

# Discipline-wide reporting-STANDARD citations that legitimately recur across
# cases (methodology anchors for Field 1, not disease-specific findings). A
# cross-case overlap on one of these is EXPECTED shared vocabulary; any OTHER
# shared pmid/doi/nct is still treated as a suspicious collision -> FAIL.
# Each entry is the standard's PMID and DOI, kept together for provenance.
METHODOLOGY_SHARED = {
    ("pmids", "35585198"),                       # DECIDE-AI  (Nat Med 2022)
    ("dois",  "10.1038/s41591-022-01772-9"),     # DECIDE-AI
    ("pmids", "38626948"),                        # TRIPOD+AI  (BMJ 2024)
    ("dois",  "10.1136/bmj-2023-078378"),        # TRIPOD+AI
}

UA = {"User-Agent": "clinical-eval-verify/1.0 (mailto:wang.victoriax@gmail.com)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


# ---- per-category live resolvers: return True iff the id is found live ----

def resolve_pmid(pid):
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
           "?db=pubmed&retmode=json&id=" + pid)
    s, d = _get(url)
    if s != 200 or not isinstance(d, dict):
        return False
    res = d.get("result", {})
    rec = res.get(pid)
    return bool(rec) and "error" not in rec and str(rec.get("uid", "")) == pid


def resolve_doi(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    s, d = _get(url)
    return s == 200 and isinstance(d, dict) and d.get("status") == "ok"


def resolve_nct(nct):
    url = "https://clinicaltrials.gov/api/v2/studies/" + nct
    s, d = _get(url)
    if s != 200 or not isinstance(d, dict):
        return False
    got = d.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
    return got == nct


def _openfda_total(url):
    s, d = _get(url)
    if s != 200 or not isinstance(d, dict):
        return 0
    return d.get("meta", {}).get("results", {}).get("total", 0)


def resolve_product_code(code):
    url = ("https://api.fda.gov/device/classification.json"
           "?search=product_code:%s&limit=1" % code)
    return _openfda_total(url) > 0


def resolve_k(k):
    url = "https://api.fda.gov/device/510k.json?search=k_number:%s&limit=1" % k
    return _openfda_total(url) > 0


def resolve_nda(app):
    url = ("https://api.fda.gov/drug/drugsfda.json"
           "?search=application_number:%s&limit=1" % app)
    return _openfda_total(url) > 0


def resolve_pma(p):
    url = "https://api.fda.gov/device/pma.json?search=pma_number:%s&limit=1" % p
    return _openfda_total(url) > 0


RESOLVER = {
    "pmids": resolve_pmid,
    "dois": resolve_doi,
    "ncts": resolve_nct,
    "fda_product_codes": resolve_product_code,
    "fda_k_numbers": resolve_k,
    "fda_den_numbers": resolve_k,   # DEN resolves via the 510k k_number field
    "fda_pma_numbers": resolve_pma,
    "fda_nda_numbers": resolve_nda,
}


def collect_grounding_ids(fg):
    """Flatten field_grounding into {category: set(ids)}, ignoring note/prose keys."""
    out = defaultdict(set)
    if not isinstance(fg, dict):
        return out
    for _field, block in fg.items():
        if not isinstance(block, dict):
            continue
        for cat, val in block.items():
            if cat in FORMAT and isinstance(val, list):
                out[cat].update(val)
    return out


def main():
    keys = {}
    for case, (kf, _md) in CASES.items():
        with open(kf) as f:
            keys[case] = json.load(f)

    skip_live = "--no-live" in sys.argv

    # Optional per-case filter: `--case NAME` restricts the per-case checks (and
    # the live re-resolution) to one case, while the cross-case collision
    # pre-pass below still loads ALL goldens (collisions are inherently global).
    only = None
    if "--case" in sys.argv:
        i = sys.argv.index("--case")
        if i + 1 < len(sys.argv):
            only = sys.argv[i + 1]
            if only not in CASES:
                sys.exit("unknown --case %r; choose from %s" % (only, ", ".join(CASES)))

    # ---- cross-case collision pre-pass (part 2) ----
    # Literature/trial ids are expected unique across cases; a shared one is
    # suspicious. FDA regulatory ids are shared taxonomy -> overlap is expected.
    LIT_CATS = {"pmids", "dois", "ncts"}
    id_owner = defaultdict(set)   # (category, id) -> set(cases)
    for case, d in keys.items():
        for cat, ids in d.get("required", {}).items():
            for i in ids:
                id_owner[(cat, i)].add(case)
    shared = {k: sorted(v) for k, v in id_owner.items() if len(v) > 1}
    fda_overlaps = {k: v for k, v in shared.items() if k[0] not in LIT_CATS}
    lit_shared = {k: v for k, v in shared.items() if k[0] in LIT_CATS}
    # split literature overlaps: named reporting standards are expected shared
    # vocabulary; anything else is a suspicious collision -> FAIL.
    method_overlaps = {k: v for k, v in lit_shared.items() if k in METHODOLOGY_SHARED}
    lit_collisions = {k: v for k, v in lit_shared.items() if k not in METHODOLOGY_SHARED}

    overall_ok = True
    summary_rows = []

    for case, (kf, md) in CASES.items():
        if only and case != only:
            continue
        d = keys[case]
        required = d.get("required", {})
        print("\n" + "=" * 72)
        print("CASE: %s   (%s)" % (case, kf))
        print("=" * 72)

        case_ok = True

        # ---------- PART 2a: format validation ----------
        fmt_fail = []
        for cat, ids in required.items():
            rx = FORMAT.get(cat)
            if rx is None:
                fmt_fail.append("  UNKNOWN category '%s' (no format rule)" % cat)
                continue
            for i in ids:
                if not rx.match(i):
                    fmt_fail.append("  %s: '%s' fails %s" % (cat, i, rx.pattern))
        if fmt_fail:
            case_ok = False
            print("[FORMAT]   FAIL")
            for line in fmt_fail:
                print(line)
        else:
            n = sum(len(v) for v in required.values())
            print("[FORMAT]   PASS (%d ids across %d categories)" % (n, len(required)))

        # ---------- PART 2b: duplicates within a category ----------
        dup_fail = []
        for cat, ids in required.items():
            seen = set()
            for i in ids:
                if i in seen:
                    dup_fail.append("  %s: duplicate '%s'" % (cat, i))
                seen.add(i)
        if dup_fail:
            case_ok = False
            print("[DUPES]    FAIL")
            for line in dup_fail:
                print(line)
        else:
            print("[DUPES]    PASS")

        # ---------- PART 2c: field_grounding subset of required ----------
        req_sets = {c: set(v) for c, v in required.items()}
        g = collect_grounding_ids(d.get("field_grounding", {}))
        orphan = []
        for cat, ids in g.items():
            extra = ids - req_sets.get(cat, set())
            for i in sorted(extra):
                orphan.append("  %s: grounding id '%s' not in required" % (cat, i))
        if orphan:
            case_ok = False
            print("[GROUND]   FAIL")
            for line in orphan:
                print(line)
        else:
            ng = sum(len(v) for v in g.values())
            print("[GROUND]   PASS (%d grounding ids all subset of required)" % ng)

        # ---------- PART 2d: spec .md cross-check ----------
        import os
        if md and os.path.exists(md):
            with open(md) as f:
                spec_txt = f.read()
            missing = []
            for cat, ids in required.items():
                for i in ids:
                    if i not in spec_txt:
                        missing.append("  %s: '%s' absent from %s" % (cat, i, md))
            if missing:
                case_ok = False
                print("[SPEC]     FAIL (%s)" % md)
                for line in missing:
                    print(line)
            else:
                print("[SPEC]     PASS (all required ids appear in %s)" % md)
        else:
            print("[SPEC]     SKIP (no spec file on disk)")

        # ---------- PART 1: live re-resolution ----------
        if skip_live:
            print("[LIVE]     SKIP (--no-live)")
            summary_rows.append((case, case_ok))
            overall_ok = overall_ok and case_ok
            continue
        print("[LIVE]     resolving %d scored ids..." % sum(len(v) for v in required.values()))
        live_fail = []
        for cat, ids in required.items():
            fn = RESOLVER.get(cat)
            if fn is None:
                live_fail.append("  %s: NO RESOLVER" % cat)
                continue
            for i in ids:
                ok = fn(i)
                if not ok:
                    live_fail.append("  %s: '%s' DID NOT RESOLVE" % (cat, i))
                time.sleep(0.34)   # be polite to the public APIs
        if live_fail:
            case_ok = False
            print("[LIVE]     FAIL")
            for line in live_fail:
                print(line)
        else:
            print("[LIVE]     PASS (all scored ids re-resolved live)")

        summary_rows.append((case, case_ok))
        overall_ok = overall_ok and case_ok

    # ---------- cross-case collisions (global) ----------
    print("\n" + "=" * 72)
    print("CROSS-CASE ID OVERLAPS")
    print("=" * 72)
    if lit_collisions:
        overall_ok = False
        print("  LITERATURE collisions (FAIL - a shared pmid/doi/nct is suspicious):")
        for (cat, i), cs in sorted(lit_collisions.items()):
            print("    COLLISION  %s '%s' in cases: %s" % (cat, i, ", ".join(cs)))
    else:
        print("  LITERATURE: PASS (no suspicious pmid/doi/nct shared across cases)")
    if method_overlaps:
        print("  Reporting-standard overlaps (EXPECTED - shared methodology vocabulary):")
        for (cat, i), cs in sorted(method_overlaps.items()):
            print("    expected   %s '%s' in cases: %s" % (cat, i, ", ".join(cs)))
    if fda_overlaps:
        print("  FDA regulatory overlaps (EXPECTED - shared device-class taxonomy):")
        for (cat, i), cs in sorted(fda_overlaps.items()):
            print("    expected   %s '%s' in cases: %s" % (cat, i, ", ".join(cs)))
    else:
        print("  FDA regulatory: no cross-case overlaps")

    # ---------- final table ----------
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    for case, ok in summary_rows:
        print("  %-10s %s" % (case, "PASS" if ok else "FAIL"))
    print("  %-10s %s" % ("lit-collide", "PASS" if not lit_collisions else "FAIL"))
    print("-" * 72)
    print("  OVERALL    %s" % ("PASS" if overall_ok else "FAIL"))

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
