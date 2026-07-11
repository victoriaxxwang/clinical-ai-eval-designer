"""CHUNK B — money-table re-check against the ACTUAL engine (not a prototype mirror).

For every golden case + a few neutral probes, run the REAL build_queries ->
normalize_mesh(..., new_bares=...) path and report which canonical MeSH heading
(and, on +hierarchy, which children) each case resolves to.

Pass criteria:
  * REGRESSIONS = NONE : the 8 cases that already grounded still resolve to a
    sensible CLINICAL heading (disease C / drug D / psych F).
  * PAYOFF            : sepsis + pneumonia (mechanism buried the disease before)
    now SURFACE the disease as a new-bare and resolve to a broad-parent WITH
    children -> +hierarchy finally has something to expand.

Hits the live NCBI E-utilities + NLM MeSH SPARQL endpoints. Regenerable.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine
from ablation_harness import CASES

# 4 neutral probes: common "-itis" conditions NOT in the golden slate, to make
# sure the category filter isn't accidentally dropping legitimate diseases.
NEUTRALS = {
    "cystitis":      ("A model that flags urinary tract infection cystitis from urine dipstick and EHR data.",
                      "Cystitis detection decision support"),
    "sinusitis":     ("A model that detects acute bacterial sinusitis from symptom and exam features.",
                      "Sinusitis triage decision support"),
    "appendicitis":  ("A model that predicts acute appendicitis from ED labs and exam findings.",
                      "Appendicitis risk decision support"),
    "cholecystitis": ("A model that flags acute cholecystitis from ultrasound and lab features.",
                      "Cholecystitis detection decision support"),
}


def resolve(model_desc, use_case, population="", setting=""):
    q = engine.build_queries(model_desc, use_case, population, setting)
    cands = q.get("mesh_candidates") or []
    new_bares = q.get("mesh_new_bares") or []
    mesh = engine.normalize_mesh(cands, with_children=True, new_bares=new_bares)
    return cands, new_bares, mesh


def show(label, model_desc, use_case, population="", setting=""):
    cands, new_bares, mesh = resolve(model_desc, use_case, population, setting)
    print(f"\n=== {label} ===")
    print(f"  candidates : {cands}")
    print(f"  new_bares  : {new_bares}")
    if mesh:
        print(f"  -> HEADING : {mesh['preferred']}  ({mesh['descriptor_id']})"
              f"  from input={mesh['input']!r}"
              f"  {'[NEW-BARE]' if mesh['input'] in new_bares else '[existing]'}")
        print(f"     synonyms: {len(mesh['synonyms'])}  children: {len(mesh['children'])}"
              f"{' -> ' + str(mesh['children'][:4]) if mesh['children'] else ''}")
    else:
        print("  -> HEADING : None (no MeSH resolution)")
    return mesh


print("#" * 70)
print("# GOLDEN SLATE (10) — REGRESSIONS = NONE expected; sepsis+pneumonia = PAYOFF")
print("#" * 70)
for name, c in CASES.items():
    show(name, c["model_desc"], c["use_case"], c.get("population", ""), c.get("setting", ""))

print("\n" + "#" * 70)
print("# NEUTRAL PROBES (4) — legitimate diseases must still resolve")
print("#" * 70)
for name, (md, uc) in NEUTRALS.items():
    show(name, md, uc)
