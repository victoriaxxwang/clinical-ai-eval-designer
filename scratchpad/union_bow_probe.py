"""CHUNK B step 2b — probe a UNION lit_bow (user's words + distinctive method).

The one-line fix (lit_bow = user's original words) is a net WASH: it wins sepsis
(+3) & fall_risk (+1) but loses AFib (-3) & depression (-1), because the OLD code
appended the distinctive MODALITY terms (ecg/photoplethysmography) that some
cases rank on. This probe tests the obvious real fix: keep BOTH.

  union_bow = new_bow (user's words)  +  method-tail (old_bow minus the heading)

No engine edit. Scores each of the 4 swing cases (sepsis, fall_risk, AFib,
depression) under old / new / union bags against that case's golden set.
Regenerable. Live EBI/OpenAlex/S2 (S2 may 429; per-provider try/except).
"""
import sys, os, json, importlib.util
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine
from ablation_harness import CASES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_bk = os.path.join(ROOT, "scratchpad", "engine_BACKUP_before_litbow_fix.py")
spec = importlib.util.spec_from_file_location("engine_old", _bk)
engine_old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine_old)

SWING = ["sepsis", "fall_risk", "AFib", "depression"]


def load_gold(name):
    g = json.load(open(os.path.join(ROOT, f"golden_expected_ids_{name}.json")))
    return set(g["required"]["pmids"]), {d.lower() for d in g["required"]["dois"]}


def resolve_once(case):
    c = CASES[case]
    args = (c["model_desc"], c["use_case"], c.get("population", ""), c.get("setting", ""))
    q0 = engine.build_queries(*args)
    mesh = engine.normalize_mesh(q0.get("mesh_candidates") or [], with_children=True,
                                 new_bares=q0.get("mesh_new_bares") or [])
    return args, mesh


def overlap(term, bool_term, gp, gd, max_results=15):
    got_p, got_d = set(), set()
    for fn, t in [(engine._europepmc_records, bool_term),
                  (engine._openalex_records, term),
                  (engine._semanticscholar_records, term)]:
        try:
            for rec in fn(t, max_results=max_results):
                if rec.get("pmid"):
                    got_p.add(rec["pmid"])
                if rec.get("doi"):
                    got_d.add(rec["doi"].lower())
        except Exception:
            pass
    return len(got_p & gp) + len(got_d & gd)


def method_tail(old_bow, preferred):
    """old_bow = heading + method; strip the heading words -> the method tail."""
    head = set((preferred or "").lower().split())
    return " ".join(w for w in old_bow.split() if w.lower() not in head)


print("=" * 78)
print("UNION lit_bow PROBE  — old (heading+method) / new (words) / union (both)")
print("=" * 78)
for case in SWING:
    args, mesh = resolve_once(case)
    old_bow = engine_old.build_queries(*args, mesh=mesh)["lit_bow"]
    qn = engine.build_queries(*args, mesh=mesh)
    new_bow, boolq = qn["lit_bow"], qn["pubmed"]
    pref = (mesh or {}).get("preferred")
    tail = method_tail(old_bow, pref) if mesh else ""
    union_bow = engine._clean((new_bow + " " + tail).strip(), 200) if tail else new_bow
    gp, gd = load_gold(case)
    n_old = overlap(old_bow, boolq, gp, gd)
    n_new = overlap(new_bow, boolq, gp, gd)
    n_uni = overlap(union_bow, boolq, gp, gd)
    print(f"\n{case:12s} mesh={pref!r}")
    print(f"  old  : {old_bow!r:55s} -> {n_old}")
    print(f"  new  : {new_bow!r:55s} -> {n_new}")
    print(f"  UNION: {union_bow!r:55s} -> {n_uni}")
