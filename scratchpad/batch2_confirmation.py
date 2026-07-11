"""CHUNK C — INDEPENDENT confirmation of the engine on 20 fresh Claude-Science cases.

These 20 cases (Set A = 10 pre-assigned diseases, Set B = 10 CS-chosen) never
touched the engine. Each carries a MeSH ORACLE from Claude Science:
  MESH_HEADING          — the canonical heading CS says the condition maps to
  MESH_IS_BROAD_PARENT  — yes/no : does it have narrower descriptors beneath it
  MESH_EXAMPLE_CHILDREN — example narrower terms

For each case we drive the REAL engine (build_queries -> normalize_mesh with
new_bares + with_children) and check THREE things against the oracle:
  (a) DISEASE SURFACES  — the canonical condition enters the query, as an
      existing candidate OR as a surfaced NEW-BARE (the reverted-in fix), and
      resolves to a heading (not None).
  (b) HEADING MATCHES   — engine's resolved preferred heading == CS's MESH_HEADING.
  (c) HIERARCHY BEHAVES — broad parents fetch >=1 child; leaves fetch 0.
      (This is normalize_mesh's true tree read, independent of the separate
       MESH_MAX_TERMS query-slot saturation limit, which is about the QUERY only.)

NOT precision/recall, NO citations. Read-only, no engine edits, commits nothing.
Hits live NCBI E-utilities + NLM MeSH SPARQL. Regenerable.
"""
import sys, os, re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_MD = os.path.join(ROOT, "scratchpad", "claude_science_batch2_results.md")

FIELDS = {
    "INTERVENTION_TYPE", "MODEL_DESC", "USE_CASE", "POPULATION", "SETTING",
    "CANONICAL_CONDITION", "MESH_HEADING", "MESH_IS_BROAD_PARENT",
    "MESH_EXAMPLE_CHILDREN",
}


def parse_cases(path):
    """Parse the labeled blocks. A block starts at a '--- ... ---' divider and
    ends at the next divider (or a '===' banner / 'CS closing'/'CS preamble')."""
    cases = []
    cur = None
    label = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = re.match(r"^---\s+(.*?)\s+---\s*$", line)
            if m:
                if cur is not None and "MESH_HEADING" in cur:
                    cur["_label"] = label
                    cases.append(cur)
                label = m.group(1).strip()
                cur = {}
                continue
            if line.startswith("====") or line.startswith("SET ") or \
               line.startswith("CS closing") or line.startswith("CS preamble"):
                if cur is not None and "MESH_HEADING" in cur:
                    cur["_label"] = label
                    cases.append(cur)
                cur = None
                continue
            if cur is None:
                continue
            km = re.match(r"^([A-Z_]+):\s*(.*)$", line)
            if km and km.group(1) in FIELDS:
                cur[km.group(1)] = km.group(2).strip()
            elif km and km.group(1) == "CASE":
                cur["CASE"] = km.group(2).strip()
        if cur is not None and "MESH_HEADING" in cur:
            cur["_label"] = label
            cases.append(cur)
    return cases


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower().rstrip(". "))


def resolve(c):
    q = engine.build_queries(c.get("MODEL_DESC", ""), c.get("USE_CASE", ""),
                             c.get("POPULATION", ""), c.get("SETTING", ""))
    cands = q.get("mesh_candidates") or []
    new_bares = q.get("mesh_new_bares") or []
    mesh = engine.normalize_mesh(cands, with_children=True, new_bares=new_bares)
    return cands, new_bares, mesh


def main():
    cases = parse_cases(RESULTS_MD)
    print(f"Parsed {len(cases)} cases from {os.path.basename(RESULTS_MD)}\n")
    rows = []
    for c in cases:
        label = c.get("_label", c.get("CASE", "?"))
        oracle_head = c.get("MESH_HEADING", "")
        oracle_broad = norm(c.get("MESH_IS_BROAD_PARENT", "")) == "yes"
        cands, new_bares, mesh = resolve(c)

        got_head = mesh["preferred"] if mesh else None
        got_id = mesh["descriptor_id"] if mesh else None
        n_children = len(mesh["children"]) if mesh else 0
        via = None
        if mesh:
            via = "NEW-BARE" if mesh["input"] in new_bares else "existing"

        surfaced = mesh is not None
        head_match = bool(mesh) and norm(got_head) == norm(oracle_head)
        # hierarchy behaves: broad->has children, leaf->no children
        if mesh:
            hier_ok = (n_children > 0) if oracle_broad else (n_children == 0)
        else:
            hier_ok = None

        rows.append(dict(
            label=label, oracle_head=oracle_head, oracle_broad=oracle_broad,
            got_head=got_head, got_id=got_id, n_children=n_children, via=via,
            surfaced=surfaced, head_match=head_match, hier_ok=hier_ok,
            cands=cands, new_bares=new_bares,
        ))

    # ---- detail ----
    print("=" * 88)
    print("PER-CASE DETAIL")
    print("=" * 88)
    for r in rows:
        s = "surf" if r["surfaced"] else "MISS"
        h = "head=OK " if r["head_match"] else "head=XX "
        hb = {True: "hier=OK", False: "hier=XX", None: "hier=--"}[r["hier_ok"]]
        print(f"\n{r['label']}")
        print(f"  oracle : {r['oracle_head']!r}  broad={r['oracle_broad']}")
        got = f"{r['got_head']!r} ({r['got_id']}) via {r['via']}, {r['n_children']} children" \
            if r["surfaced"] else "None (no MeSH resolution)"
        print(f"  engine : {got}")
        print(f"  verdict: [{s}] {h} {hb}")
        if not r["surfaced"] or not r["head_match"]:
            print(f"    candidates: {r['cands']}")
            print(f"    new_bares : {r['new_bares']}")

    # ---- summary ----
    n = len(rows)
    surfaced = sum(1 for r in rows if r["surfaced"])
    head_ok = sum(1 for r in rows if r["head_match"])
    hier_ok = sum(1 for r in rows if r["hier_ok"] is True)
    hier_testable = sum(1 for r in rows if r["hier_ok"] is not None)
    print("\n" + "=" * 88)
    print("SUMMARY")
    print("=" * 88)
    print(f"  cases parsed          : {n}")
    print(f"  disease surfaced      : {surfaced}/{n}")
    print(f"  heading matches CS    : {head_ok}/{n}")
    print(f"  hierarchy behaves     : {hier_ok}/{hier_testable} (of cases that resolved)")
    print("\n  MISSES / MISMATCHES (for analysis):")
    for r in rows:
        flags = []
        if not r["surfaced"]:
            flags.append("no-surface")
        if r["surfaced"] and not r["head_match"]:
            flags.append(f"head:{r['got_head']!r}!={r['oracle_head']!r}")
        if r["hier_ok"] is False:
            exp = "broad" if r["oracle_broad"] else "leaf"
            flags.append(f"hier:{r['n_children']}ch but oracle={exp}")
        if flags:
            print(f"    - {r['label']:34s} {'; '.join(flags)}")


if __name__ == "__main__":
    main()
