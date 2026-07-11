"""CHUNK B — DECISIVE PROBE for the sepsis literature regression (4 -> 0).

Question Victoria asked: is the regression a NICHE sepsis-only quirk, or a
FIRST-PRINCIPLE weakness in how the engine builds the literature query? And
does the cheap fix (stop hard-ANDing generic method verbs) actually recover the
golden papers?

Method: drive the REAL engine to get the exact queries, then count how many
golden sepsis IDs each variant's MERGED three-provider retrieval actually finds.
This mirrors search_literature (Europe PMC gets the boolean; OpenAlex + Semantic
Scholar get the plain bag) but returns structured records so we can score
golden overlap directly. NO engine edits — pure diagnostic.

Three variants:
  (c) PRE-FIX      : build_queries with NO mesh -> the old loose keyword bag.
  (a) NEW / current: mesh resolves -> (OR-group) AND verb1 AND verb2  [the fix, as shipped]
  (b) PROPOSED fix : same OR-group, but DROP the hard-AND method verbs.

Hits the live NCBI/EBI/OpenAlex/S2 endpoints. Regenerable.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine
from ablation_harness import CASES

GOLD = json.load(open(os.path.join(os.path.dirname(__file__), "..", "golden_expected_ids_sepsis.json")))
G_PMIDS = set(GOLD["required"]["pmids"])
G_DOIS = {d.lower() for d in GOLD["required"]["dois"]}
N_GOLD = len(G_PMIDS) + len(G_DOIS)

c = CASES["sepsis"]
MD, UC = c["model_desc"], c["use_case"]
POP, SET = c.get("population", ""), c.get("setting", "")


def merged_overlap(term, bool_term, max_results=15):
    """Replicate search_literature's provider split; return golden IDs found."""
    got_pmids, got_dois = set(), set()
    providers = [
        ("EuropePMC", engine._europepmc_records, bool_term),
        ("OpenAlex", engine._openalex_records, term),
        ("SemScholar", engine._semanticscholar_records, term),
    ]
    per_provider = {}
    for name, fn, t in providers:
        p_pmids, p_dois = set(), set()
        try:
            for rec in fn(t, max_results=max_results):
                if rec.get("pmid"):
                    p_pmids.add(rec["pmid"])
                if rec.get("doi"):
                    p_dois.add(rec["doi"].lower())
        except Exception as e:  # noqa
            per_provider[name] = f"FAILED: {e}"
            continue
        hit = (p_pmids & G_PMIDS) | {("doi:" + d) for d in (p_dois & G_DOIS)}
        per_provider[name] = f"{len(hit)} golden (of {len(p_pmids)+len(p_dois)} returned)"
        got_pmids |= p_pmids
        got_dois |= p_dois
    gp = got_pmids & G_PMIDS
    gd = got_dois & G_DOIS
    return gp, gd, per_provider


# --- Build the three variants from the real engine ---------------------------
q_old = engine.build_queries(MD, UC, POP, SET)                       # no mesh
cands = q_old.get("mesh_candidates") or []
new_bares = q_old.get("mesh_new_bares") or []
mesh = engine.normalize_mesh(cands, with_children=True, new_bares=new_bares)
q_new = engine.build_queries(MD, UC, POP, SET, mesh=mesh)            # mesh resolves

# variant (b): strip the hard-AND method verbs from the boolean; bag = heading only
bool_a = q_new["pubmed"]
bool_b = bool_a.split(" AND ", 1)[0]        # keep just the (OR-group)
term_b = (mesh or {}).get("preferred", "sepsis")

variants = [
    ("(c) PRE-FIX loose bag",         q_old["lit_bow"], q_old["pubmed"]),
    ("(a) NEW current fix",           q_new["lit_bow"], bool_a),
    ("(b) PROPOSED drop hard-AND",    term_b,           bool_b),
    # (d) keep the ORIGINAL descriptive bag for the relevance rankers, use the
    #     MeSH OR-group as the Europe PMC boolean. Tests "augment, don't replace".
    ("(d) keep old bag + OR-group",   q_old["lit_bow"], bool_b),
]

print("=" * 78)
print(f"SEPSIS DECISIVE PROBE  |  golden set = {len(G_PMIDS)} PMIDs + {len(G_DOIS)} DOIs")
print("=" * 78)
for label, term, bool_term in variants:
    print(f"\n### {label}")
    print(f"  bag  (OpenAlex/S2) : {term!r}")
    print(f"  bool (EuropePMC)   : {bool_term!r}")
    gp, gd, per = merged_overlap(term, bool_term)
    for name, msg in per.items():
        print(f"    - {name:11s}: {msg}")
    print(f"  >>> MERGED golden overlap: {len(gp)} PMIDs + {len(gd)} DOIs "
          f"= {len(gp)+len(gd)} of {N_GOLD}")
    if gp:
        print(f"      pmids: {sorted(gp)}")
    if gd:
        print(f"      dois : {sorted(gd)}")
