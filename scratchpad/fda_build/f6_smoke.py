"""F6 free smoke test: confirm the wired wide-net engine now produces
disease-aware FDA predicates (fda_bridge) in its openFDA device section, with
no crash, and that the frozen engine.py still imports/runs. FREE — registry
calls only, no Claude. Prints just the openFDA device section for 2 cases.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "experimental"))
import engine_widenet as w  # noqa: E402
import engine as frozen  # noqa: E402

CASES = json.load(open(os.path.join(REPO, "scratchpad/f5_batch_cases.json")))["cases"]
PICK = {"diabetic_retinopathy_fundus", "melanoma_dermoscopy_transformer"}


def fda_section(ctx):
    """Pull just the openFDA device-classification section from the bundle."""
    marker = "### openFDA (device classification / 510(k) precedents)"
    if marker not in ctx:
        return "(no openFDA device section emitted)"
    tail = ctx.split(marker, 1)[1]
    # cut at the next top-level section header
    nxt = tail.find("\n### ")
    return (marker + (tail if nxt < 0 else tail[:nxt])).strip()


def main():
    print("wide-net _HAVE_FDA_BRIDGE =", w._HAVE_FDA_BRIDGE)
    for c in CASES:
        if c["id"] not in PICK:
            continue
        print("\n" + "=" * 78)
        print("CASE:", c["id"], "| oracle disease:", c["mesh_heading_oracle"])
        print("=" * 78)
        ctx, statuses, ts = w.build_grounded_context(
            c["model_desc"], c["use_case"], c.get("population", ""),
            c.get("optional_url", ""), c.get("setting", ""),
            c.get("intervention_type", "device"))
        print(fda_section(ctx))
    # confirm the frozen OFF-path still builds a bundle (unchanged behavior)
    print("\n" + "=" * 78)
    print("FROZEN engine.py (toggle OFF) — sanity: does it still run?")
    print("=" * 78)
    dr = [c for c in CASES if c["id"] == "diabetic_retinopathy_fundus"][0]
    fctx, fst, fts = frozen.build_grounded_context(
        dr["model_desc"], dr["use_case"], dr.get("population", ""),
        dr.get("optional_url", ""), dr.get("setting", ""),
        dr.get("intervention_type", "device"))
    print("frozen bundle length:", len(fctx), "| statuses:", len(fst), "| OK")


if __name__ == "__main__":
    main()
