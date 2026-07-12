"""F6c/F6d — PAID downstream check of the WIRED wide-net engine.

Unlike f5_batch_live.py (which reads pre-committed context from disk), this
retrieves context LIVE through the F6-wired engine_widenet.build_grounded_context
so the NEW disease-aware FDA section (fda_bridge) is actually exercised, then:
  1. generates the full 8-field spec via app.py's byte-faithful generate_spec,
  2. runs critic_panel.run_panel on it,
  3. records whether the recovered FDA predicates SURVIVE into the spec text.

Wide-net arm only (the frozen arm has no bridge; its behavior is already banked).
Pass case ids on argv (default = batch 1). Writes per-case spec/panel/context to
scratchpad/fda_build/f6_batch/ and a compact roll-up summary. Key read from
.streamlit/secrets.toml, NEVER printed. Run in background under caffeinate.
Tripwire asserted start + end.
"""
import hashlib
import json
import os
import re
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))          # scratchpad/fda_build
REPO = os.path.dirname(os.path.dirname(HERE))              # repo root
OUT = os.path.join(HERE, "f6_batch")

FROZEN_MD5 = "2e6d49cdaa3106b6c29ee66b5df37e58"
with open(os.path.join(REPO, "engine.py"), "rb") as fh:
    _a = hashlib.md5(fh.read()).hexdigest()
assert _a == FROZEN_MD5, f"TRIPWIRE FAIL: engine.py md5 {_a} != {FROZEN_MD5}"
print(f"[tripwire] engine.py md5 OK ({_a})", flush=True)

BATCH1 = ["diabetic_retinopathy_fundus", "ischemic_stroke_ct_ensemble", "nsclc_lung_ct_cnn"]

with open(os.path.join(REPO, "scratchpad", "f5_batch_cases.json")) as fh:
    _raw = json.load(fh)
    ALL = {c["id"]: c for c in (_raw["cases"] if isinstance(_raw, dict) else _raw)}


def _install_streamlit_stub():
    class _Stub:
        def __call__(self, *a, **k): return _Stub()
        def __getattr__(self, _): return _Stub()
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def __bool__(self): return False
        def __iter__(self): return iter([_Stub(), _Stub(), _Stub(), _Stub()])
        def __getitem__(self, _): return _Stub()
        def __setitem__(self, k, v): pass
        def __contains__(self, _): return False
    st = types.ModuleType("streamlit")
    st.__getattr__ = lambda name: _Stub()  # type: ignore[attr-defined]
    st.session_state = {}
    st.secrets = _Stub()
    st.columns = lambda spec, **k: [_Stub() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.tabs = lambda labels, **k: [_Stub() for _ in labels]
    sys.modules["streamlit"] = st
    return st


def _read_key():
    path = os.path.join(REPO, ".streamlit", "secrets.toml")
    with open(path) as fh:
        for line in fh:
            m = re.match(r'\s*ANTHROPIC_API_KEY\s*=\s*"([^"]+)"', line)
            if m:
                return m.group(1)
    raise RuntimeError("ANTHROPIC_API_KEY not found")


def _fda_section(ctx):
    marker = "### openFDA (device classification / 510(k) precedents)"
    if marker not in ctx:
        return "(no openFDA device section)"
    tail = ctx.split(marker, 1)[1]
    nxt = tail.find("\n### ")
    return (marker + (tail if nxt < 0 else tail[:nxt])).strip()


def _device_names(ctx):
    """Device/product names the bridge put in the FDA section (for survival check)."""
    names = set()
    for line in _fda_section(ctx).splitlines():
        m = re.search(r"predicate \S+ \| ([^|]+?) \|", line)
        if m:
            names.add(m.group(1).strip())
    return names


def main(effort="medium", ids=None):
    import anthropic  # noqa
    _install_streamlit_stub()
    sys.path.insert(0, REPO)
    sys.path.insert(0, os.path.join(REPO, "experimental"))
    import engine_widenet as w
    import app
    import critic_panel

    ids = ids or BATCH1
    client = anthropic.Anthropic(api_key=_read_key())
    summary = {"batch": "F6", "effort": effort, "wired_engine": True,
               "have_bridge": w._HAVE_FDA_BRIDGE, "cases": {}}

    for cid in ids:
        case = ALL[cid]
        print(f"\n########### {cid} (oracle: {case['mesh_heading_oracle']}) ###########", flush=True)
        ctx, statuses, ts = w.build_grounded_context(
            case["model_desc"], case["use_case"], case.get("population", ""),
            case.get("optional_url", ""), case.get("setting", ""),
            case.get("intervention_type", "device"))
        with open(os.path.join(OUT, f"{cid}_context.txt"), "w") as fh:
            fh.write(ctx)
        fda = _fda_section(ctx)
        dev_names = _device_names(ctx)
        print(f"    FDA device names surfaced: {sorted(dev_names)}", flush=True)

        user_message = app.wrap_with_context(
            app.build_user_message(case["model_desc"], case["use_case"],
                                   case.get("population", ""), case.get("setting", ""),
                                   case.get("claim", "")),
            ctx)
        print(f"--- {cid}: generating spec (effort={effort}) ---", flush=True)
        spec, final = app.generate_spec(client, user_message, effort, use_web_search=False)
        refusal = (final is not None and getattr(final, "stop_reason", None) == "refusal")
        with open(os.path.join(OUT, f"{cid}_spec.md"), "w") as fh:
            fh.write(spec or "")

        # do the FDA device names the bridge surfaced actually appear in the spec?
        survived = sorted(n for n in dev_names if spec and n.split(" (")[0][:18].lower() in spec.lower())
        print(f"    spec chars: {len(spec or '')} refusal={refusal} | FDA names in spec: {survived}", flush=True)

        print(f"--- {cid}: convening critic panel ---", flush=True)
        parsed, pfinal, praw = critic_panel.run_panel(client, ctx, spec or "", effort=effort)
        with open(os.path.join(OUT, f"{cid}_panel.json"), "w") as fh:
            json.dump(parsed, fh, indent=2)
        blockers = parsed.get("fix_before_submission") if isinstance(parsed, dict) else []
        audit = parsed.get("grounding_audit") if isinstance(parsed, dict) else None

        summary["cases"][cid] = {
            "oracle": case["mesh_heading_oracle"],
            "fda_device_names": sorted(dev_names),
            "fda_names_survived_into_spec": survived,
            "fda_section": fda,
            "spec_chars": len(spec or ""),
            "spec_refusal": refusal,
            "panel_blockers": len(blockers or []),
            "grounding_audit_flags": (len(audit) if isinstance(audit, list) else None),
        }
        print(f"    panel blockers: {len(blockers or [])}", flush=True)

    with open(os.path.join(OUT, "f6_batch_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\n================ F6 batch DONE ================", flush=True)


if __name__ == "__main__":
    argv_ids = sys.argv[1:] or None
    main(ids=argv_ids)
    with open(os.path.join(REPO, "engine.py"), "rb") as fh:
        end = hashlib.md5(fh.read()).hexdigest()
    assert end == FROZEN_MD5, f"TRIPWIRE FAIL AT END: {end}"
    print(f"[tripwire] engine.py md5 still OK ({end})", flush=True)
