"""CHUNK B step 2 — RE-CHECK the 8 working goldens after the lit-bow fix.

The lit-bow fix changes `lit_bow` (the bag sent to the relevance rankers
OpenAlex + Semantic Scholar) ONLY for cases where MeSH resolves: pre-fix it was
rebuilt as (heading + method verbs); post-fix it stays = the user's original
descriptive words. The boolean `lit_query`/pubmed (Europe PMC) is UNCHANGED.

So the only cases that can regress are those where MeSH resolves. For each
working golden we:
  1. get OLD lit_bow from the BACKUP engine (pre-fix, heading+method)
  2. get NEW lit_bow from the CURRENT engine (post-fix, user's words)
  3. if they are identical -> UNCHANGED, no live call needed
  4. if they differ -> live-score BOTH bags' merged golden overlap and compare

PASS = NEW golden overlap >= OLD for every case (no regression). Uses the
CURRENT engine's provider functions for both (identical code in both engines).
Regenerable. Hits live EBI/OpenAlex/S2 (S2 may 429; per-provider try/except).
"""
import sys, os, json, importlib.util
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine                      # CURRENT (post-fix)
from ablation_harness import CASES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# load the pre-fix backup as a separate module
_bk = os.path.join(ROOT, "scratchpad", "engine_BACKUP_before_litbow_fix.py")
spec = importlib.util.spec_from_file_location("engine_old", _bk)
engine_old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine_old)

# 8 working goldens (exclude sepsis = already done; HRV = no golden file)
CASE_TO_GOLD = {
    "DR": "DR", "warfarin": "warfarin", "AFib": "AFib", "depression": "depression",
    "melanoma": "melanoma", "pembrolizumab": "pembrolizumab",
    "pneumonia": "pneumonia",          # payoff case, re-score too
    "fall_risk": "fall_risk",
}


def load_gold(name):
    g = json.load(open(os.path.join(ROOT, f"golden_expected_ids_{name}.json")))
    return set(g["required"]["pmids"]), {d.lower() for d in g["required"]["dois"]}


def resolve_once(case):
    """Resolve MeSH ONE time (current engine) so old/new bags share the exact
    same resolution -> the only difference is the lit_bow code, not live noise."""
    c = CASES[case]
    md, uc = c["model_desc"], c["use_case"]
    pop, setg = c.get("population", ""), c.get("setting", "")
    q0 = engine.build_queries(md, uc, pop, setg)
    cands = q0.get("mesh_candidates") or []
    nb = q0.get("mesh_new_bares") or []
    mesh = engine.normalize_mesh(cands, with_children=True, new_bares=nb)
    return (md, uc, pop, setg), mesh


def bow_from(mod, args, mesh):
    """Pure (no network): build the lit query from a FIXED mesh object."""
    q = mod.build_queries(*args, mesh=mesh)
    return q["lit_bow"], q["pubmed"], (mesh or {}).get("preferred")


def overlap(term, bool_term, gp, gd, max_results=15):
    got_p, got_d = set(), set()
    for name, fn, t in [("EuropePMC", engine._europepmc_records, bool_term),
                        ("OpenAlex", engine._openalex_records, term),
                        ("SemScholar", engine._semanticscholar_records, term)]:
        try:
            for rec in fn(t, max_results=max_results):
                if rec.get("pmid"):
                    got_p.add(rec["pmid"])
                if rec.get("doi"):
                    got_d.add(rec["doi"].lower())
        except Exception:
            pass
    return len(got_p & gp) + len(got_d & gd)


print("=" * 78)
print("WORKING-GOLDEN RE-CHECK  (lit-bow fix)  — PASS = new >= old on every case")
print("=" * 78)
regressions = []
for case, gname in CASE_TO_GOLD.items():
    args, mesh = resolve_once(case)                 # ONE live resolution, shared
    old_bow, _, mh = bow_from(engine_old, args, mesh)
    new_bow, boolq, _ = bow_from(engine, args, mesh)
    if old_bow == new_bow:
        print(f"\n{case:14s} UNCHANGED (mesh={mh!r}) bow={new_bow!r}")
        continue
    gp, gd = load_gold(gname)
    n_old = overlap(old_bow, boolq, gp, gd)
    n_new = overlap(new_bow, boolq, gp, gd)
    flag = "  <-- REGRESSION" if n_new < n_old else ("  (+improved)" if n_new > n_old else "")
    if n_new < n_old:
        regressions.append(case)
    print(f"\n{case:14s} mesh={mh!r}")
    print(f"  OLD bow: {old_bow!r}  -> {n_old} golden")
    print(f"  NEW bow: {new_bow!r}  -> {n_new} golden{flag}")

print("\n" + "=" * 78)
print(f"REGRESSIONS: {regressions if regressions else 'NONE'}")
print("=" * 78)
