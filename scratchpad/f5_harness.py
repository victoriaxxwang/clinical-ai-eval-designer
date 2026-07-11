"""Option-1 F5 — live BEFORE/AFTER capstone: frozen engine vs wide-net engine,
end-to-end, on ONE mechanism-first single-disease case (heart failure).

WHY: the shipped ("Option 2") engine only surfaces a disease when it is NAMED
EARLY. On a mechanism-first write-up (disease buried under ML jargon) it misses
the condition, so the whole citation search goes off-target. The wide-net
prototype (experimental/engine_widenet.py) reads the whole case text and surfaces
the buried disease. This harness makes that tangible: it runs the SAME case
through both engines and diffs (a) the evidence each retrieves and (b) the full
8-field spec + critic panel each produces.

The two "engines" are fully separate self-contained modules (the wide-net copy
imports nothing from the frozen engine), so the frozen engine is never touched.

TWO MODES:
  * default (F5a, no key)  -> retrieval only: build BOTH grounded contexts live
    from the public registries (free, no Anthropic call), save them, and diff the
    MeSH-normalization + query lines. This is the CHEAP GO/NO-GO GATE: it must show
    the frozen arm MISSING the disease and the wide-net arm SURFACING it before we
    spend the API key.
  * --live (F5b)           -> also generate the two full specs via app.py's real
    generate_spec (byte-faithful SYSTEM_PROMPT) and run critic_panel.run_panel on
    each, saving specs + panels. Reads the key from .streamlit/secrets.toml; the
    key is never printed. Meant to run in the background under caffeinate.

Outputs (all in scratchpad/):
  f5_frozen_context.txt / f5_widenet_context.txt   (retrieval, both modes)
  f5a_diff.json                                     (retrieval diff summary)
  f5_frozen_spec.md / f5_widenet_spec.md            (--live only)
  f5_frozen_panel.json / f5_widenet_panel.json      (--live only)
  f5b_summary.json                                  (--live only)
"""

import hashlib
import json
import os
import re
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# --- Tripwire: the frozen engine must be byte-for-byte unchanged. ------------
FROZEN_MD5 = "2e6d49cdaa3106b6c29ee66b5df37e58"
with open(os.path.join(REPO, "engine.py"), "rb") as fh:
    actual = hashlib.md5(fh.read()).hexdigest()
assert actual == FROZEN_MD5, f"TRIPWIRE FAIL: engine.py md5 {actual} != {FROZEN_MD5}"
print(f"[tripwire] engine.py md5 OK ({actual})")

# frozen engine (repo root) first, then the experimental copy on a separate name.
sys.path.insert(0, REPO)
import engine  # frozen  # noqa: E402
sys.path.insert(0, os.path.join(REPO, "experimental"))
import engine_widenet  # wide-net  # noqa: E402

ARMS = [("frozen", engine), ("widenet", engine_widenet)]

with open(os.path.join(HERE, "f5_demo_case.json")) as fh:
    CASE = json.load(fh)


def _meta_line(context, label):
    """Pull one '- {label}: ...' line out of the Retrieval Metadata block."""
    for line in context.splitlines():
        s = line.strip()
        if s.startswith(f"- {label}:"):
            return s[len(f"- {label}:"):].strip()
    return None


def _section_names(context):
    return [ln[4:].strip() for ln in context.splitlines() if ln.startswith("### ")]


def build_context(eng):
    ctx, statuses, ts = eng.build_grounded_context(
        CASE["model_desc"], CASE["use_case"], CASE["population"],
        CASE.get("optional_url", ""), CASE.get("setting", ""),
        CASE.get("intervention_type", "device"),
    )
    return ctx, statuses, ts


# ---------------------------------------------------------------------------
# F5a — retrieval-only diff (the cheap go/no-go gate)
# ---------------------------------------------------------------------------
def run_retrieval():
    print("\n================ F5a — retrieval diff (no API key) ================")
    print(f"case: {CASE['id']}  |  oracle disease: {CASE['mesh_heading_oracle']}")
    diff = {"case": CASE["id"], "oracle": CASE["mesh_heading_oracle"], "arms": {}}
    contexts = {}
    for name, eng in ARMS:
        ctx, statuses, ts = build_context(eng)
        contexts[name] = ctx
        path = os.path.join(HERE, f"f5_{name}_context.txt")
        with open(path, "w") as fh:
            fh.write(ctx)
        mesh = _meta_line(ctx, "MeSH normalization")
        query = _meta_line(ctx, "Literature/trials query")
        surfaced = bool(mesh) and CASE["mesh_heading_oracle"].lower() in (mesh or "").lower()
        n_ok = sum(1 for s in statuses if s.startswith("✅"))
        diff["arms"][name] = {
            "mesh_normalization": mesh,
            "query": query,
            "surfaced_oracle_disease": surfaced,
            "sections": _section_names(ctx),
            "context_chars": len(ctx),
            "registry_hits_ok": n_ok,
            "context_file": os.path.basename(path),
        }
        print(f"\n--- {name.upper()} ---")
        print(f"  MeSH normalization : {mesh}")
        print(f"  query              : {query}")
        print(f"  surfaced '{CASE['mesh_heading_oracle']}'? -> {surfaced}")
        print(f"  sections           : {diff['arms'][name]['sections']}")
        print(f"  context chars      : {len(ctx)}   registry ✅ statuses: {n_ok}")

    gate = (not diff["arms"]["frozen"]["surfaced_oracle_disease"]
            and diff["arms"]["widenet"]["surfaced_oracle_disease"])
    diff["gate_pass"] = gate
    with open(os.path.join(HERE, "f5a_diff.json"), "w") as fh:
        json.dump(diff, fh, indent=2)
    print("\n================ GATE ================")
    print(f"frozen MISSES disease + widenet SURFACES it? -> {gate}")
    print("  -> GO for F5b (live spec generation)" if gate
          else "  -> NO-GO: retrieval did not diverge as expected; rethink before spending key.")
    return contexts, diff


# ---------------------------------------------------------------------------
# F5b — live spec generation + critic panel (needs the key; run under caffeinate)
# ---------------------------------------------------------------------------
def _install_streamlit_stub():
    """Let app.py import with all Streamlit UI calls as no-ops, so we can reuse
    its real SYSTEM_PROMPT / generate_spec / build_user_message byte-for-byte."""
    class _Stub:
        def __call__(self, *a, **k):
            return _Stub()

        def __getattr__(self, _):
            return _Stub()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def __bool__(self):
            return False

        def __iter__(self):
            return iter([_Stub(), _Stub(), _Stub(), _Stub()])

        def __getitem__(self, _):
            return _Stub()

        def __setitem__(self, k, v):
            pass

        def __contains__(self, _):
            return False

    st = types.ModuleType("streamlit")
    # every attribute access on the module returns a fresh no-op stub (PEP 562)
    st.__getattr__ = lambda name: _Stub()  # type: ignore[attr-defined]
    st.session_state = {}
    st.secrets = _Stub()
    # layout helpers must return EXACTLY the requested count so `c1, c2 = st.columns(2)` unpacks
    st.columns = lambda spec, **k: [_Stub() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.tabs = lambda labels, **k: [_Stub() for _ in labels]
    sys.modules["streamlit"] = st
    return st


def _read_key():
    """Read ANTHROPIC_API_KEY from .streamlit/secrets.toml. Never printed."""
    path = os.path.join(REPO, ".streamlit", "secrets.toml")
    with open(path) as fh:
        for line in fh:
            m = re.match(r'\s*ANTHROPIC_API_KEY\s*=\s*"([^"]+)"', line)
            if m:
                return m.group(1)
    raise RuntimeError("ANTHROPIC_API_KEY not found in .streamlit/secrets.toml")


def run_live(contexts, effort="medium"):
    print("\n================ F5b — live spec generation + critic panel ================")
    import anthropic  # noqa: F401
    _install_streamlit_stub()
    sys.path.insert(0, REPO)
    import app          # reuses real SYSTEM_PROMPT / generate_spec / build_user_message
    import critic_panel

    client = anthropic.Anthropic(api_key=_read_key())
    summary = {"case": CASE["id"], "effort": effort, "arms": {}}

    for name, _eng in ARMS:
        ctx = contexts[name]
        user_message = app.wrap_with_context(
            app.build_user_message(CASE["model_desc"], CASE["use_case"],
                                   CASE["population"], CASE["setting"], CASE.get("claim", "")),
            ctx,
        )
        print(f"\n--- {name.upper()} : generating spec (effort={effort}) ---")
        spec, final = app.generate_spec(client, user_message, effort, use_web_search=False)
        refusal = (final is not None and getattr(final, "stop_reason", None) == "refusal")
        spec_path = os.path.join(HERE, f"f5_{name}_spec.md")
        with open(spec_path, "w") as fh:
            fh.write(spec or "")
        print(f"    spec chars: {len(spec or '')}  refusal={refusal}")

        print(f"--- {name.upper()} : convening critic panel ---")
        parsed, pfinal, praw = critic_panel.run_panel(client, ctx, spec or "", effort=effort)
        panel_path = os.path.join(HERE, f"f5_{name}_panel.json")
        with open(panel_path, "w") as fh:
            json.dump(parsed, fh, indent=2)
        blockers = []
        if isinstance(parsed, dict):
            blockers = parsed.get("fix_before_submission") or []
        summary["arms"][name] = {
            "spec_chars": len(spec or ""),
            "spec_refusal": refusal,
            "spec_file": os.path.basename(spec_path),
            "panel_blockers": len(blockers),
            "panel_file": os.path.basename(panel_path),
        }
        print(f"    panel blockers (fix_before_submission): {len(blockers)}")

    with open(os.path.join(HERE, "f5b_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\n================ F5b DONE ================")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    live = "--live" in sys.argv
    contexts, diff = run_retrieval()
    if live:
        if not diff["gate_pass"]:
            print("\n[abort] gate did not pass — not spending the API key.")
            sys.exit(1)
        run_live(contexts)
    # re-check tripwire at the end
    with open(os.path.join(REPO, "engine.py"), "rb") as fh:
        end = hashlib.md5(fh.read()).hexdigest()
    assert end == FROZEN_MD5, f"TRIPWIRE FAIL AT END: {end}"
    print(f"\n[tripwire] engine.py md5 still OK ({end})")
