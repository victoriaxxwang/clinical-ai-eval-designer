"""OPTION-1 DE-RISK PROBE — simulate a WIDE-NET disease scan on the 20 Chunk C
cases WITHOUT touching engine.py. Answers Victoria's question: if we stop only
reading the first 12 words and instead scan the WHOLE description (every word +
adjacent word-pair), how many of the Chunk C misses do we actually recover, and
how often would the clarifying question fire?

Three tiers per case (measured live vs the CS oracle heading):
  TIER 0  today      — the REAL engine as shipped (build_queries -> normalize_mesh).
  TIER 1  wide+strict— whole-text unigrams + bigrams, resolved with the SAME exact
                       match + disease-only category filter the engine uses. This is
                       the SAFE automatic version (no guessing). Reports: did the
                       oracle disease surface? how many DISTINCT diseases surfaced?
  TIER 2  wide+loose — ONLY for cases Tier 1 still misses. Relaxes the match to the
                       unquoted `term[MeSH Terms]` (ranked, ambiguous) and keeps the
                       disease hits. This is the "loosen + ASK the user" path: the
                       distinct-disease count = how many options the clarifying
                       question would show. Reports whether the oracle is among them.

Read-only. No engine edits. Caches every lookup so NCBI isn't hammered. Regenerable.
Hits live NCBI E-utilities. NotOpenSSLWarning is benign.
"""
import sys, os, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_MD = os.path.join(ROOT, "scratchpad", "claude_science_batch2_results.md")
FIELDS = {"INTERVENTION_TYPE", "MODEL_DESC", "USE_CASE", "POPULATION", "SETTING",
          "CANONICAL_CONDITION", "MESH_HEADING", "MESH_IS_BROAD_PARENT",
          "MESH_EXAMPLE_CHILDREN"}

SLEEP = 0.12  # be polite to NCBI's un-keyed limit


def parse_cases(path):
    cases, cur, label = [], None, None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = re.match(r"^---\s+(.*?)\s+---\s*$", line)
            if m:
                if cur is not None and "MESH_HEADING" in cur:
                    cur["_label"] = label; cases.append(cur)
                label = m.group(1).strip(); cur = {}; continue
            if line.startswith("====") or line.startswith("SET ") or \
               line.startswith("CS closing") or line.startswith("CS preamble"):
                if cur is not None and "MESH_HEADING" in cur:
                    cur["_label"] = label; cases.append(cur)
                cur = None; continue
            if cur is None:
                continue
            km = re.match(r"^([A-Z_]+):\s*(.*)$", line)
            if km and km.group(1) in FIELDS:
                cur[km.group(1)] = km.group(2).strip()
            elif km and km.group(1) == "CASE":
                cur["CASE"] = km.group(2).strip()
        if cur is not None and "MESH_HEADING" in cur:
            cur["_label"] = label; cases.append(cur)
    return cases


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower().rstrip(". "))


def toks(text):
    t = re.sub(r"[-/]", " ", (text or "").lower())
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return [w for w in t.split() if len(w) > 2 and w not in engine._STOP]


def terms_for(case):
    """Every meaningful unigram + adjacent bigram across the WHOLE case text."""
    full = " ".join(case.get(k, "") for k in
                    ("MODEL_DESC", "USE_CASE", "POPULATION", "SETTING"))
    words = toks(full)
    unis = list(dict.fromkeys(words))
    bigs = list(dict.fromkeys(f"{a} {b}" for a, b in zip(words, words[1:])))
    # bigrams first (more specific -> multi-word headings), then unigrams
    return bigs + unis


# ---- cached MeSH resolution -------------------------------------------------
_ES, _SUM = {}, {}


def _esearch(term):
    if term in _ES:
        return _ES[term]
    try:
        r = engine._eutils_mesh_get("esearch", {"db": "mesh", "retmode": "json",
                                                "term": term, "retmax": 5})
        ids = r.json().get("esearchresult", {}).get("idlist", []) or []
    except Exception:
        ids = []
    time.sleep(SLEEP)
    _ES[term] = ids
    return ids


def _summary(uid):
    if uid in _SUM:
        return _SUM[uid]
    try:
        r = engine._eutils_mesh_get("esummary", {"db": "mesh", "id": uid, "retmode": "json"})
        it = (r.json().get("result", {}) or {}).get(uid, {}) or {}
    except Exception:
        it = {}
    time.sleep(SLEEP)
    _SUM[uid] = it
    return it


def _disease_hit(uid):
    """Return preferred heading if uid is a DISEASE (C-tree) main/SCR record, else None."""
    it = _summary(uid)
    terms = [t for t in (it.get("ds_meshterms") or []) if t]
    desc = it.get("ds_meshui", "") or ""
    if not terms or desc[:1] not in ("D", "C"):
        return None
    # disease-only gate (same as engine's new-bare rule: needs a C-tree category)
    if not engine._accept_mesh_category(engine._mesh_tree_cats(desc), is_new_bare=True):
        return None
    return terms[0]


def scan(case, loose):
    """Return dict{preferred_heading: first-term-that-surfaced-it} across the case.
    loose=False -> exact  `\"t\"[MeSH Terms]`  ;  loose=True -> `t[MeSH Terms]`."""
    found = {}
    for t in terms_for(case):
        q = f'{t}[MeSH Terms]' if loose else f'"{t}"[MeSH Terms]'
        for uid in _esearch(q):
            pref = _disease_hit(uid)
            if pref and pref not in found:
                found[pref] = t
            if not loose:
                break  # exact: engine takes only the first id
    return found


def main():
    cases = parse_cases(RESULTS_MD)
    print(f"Parsed {len(cases)} cases\n")
    rows = []
    for i, c in enumerate(cases, 1):
        label = c.get("_label", c.get("CASE", "?"))
        oracle = norm(c.get("MESH_HEADING", ""))
        print(f"[{i}/{len(cases)}] {label} ...", flush=True)

        # TIER 0 — real engine as shipped
        q = engine.build_queries(c.get("MODEL_DESC", ""), c.get("USE_CASE", ""),
                                 c.get("POPULATION", ""), c.get("SETTING", ""))
        mesh = engine.normalize_mesh(q.get("mesh_candidates") or [], with_children=False,
                                     new_bares=q.get("mesh_new_bares") or [])
        t0 = bool(mesh) and norm(mesh["preferred"]) == oracle

        # TIER 1 — wide net, strict (safe/automatic)
        strict = scan(c, loose=False)
        t1_hit = any(norm(h) == oracle for h in strict)

        # TIER 2 — wide net, loose (only if T1 missed): the "ask the user" path
        loose = scan(c, loose=True) if not t1_hit else {}
        t2_hit = any(norm(h) == oracle for h in loose)

        rows.append(dict(label=label, oracle=c.get("MESH_HEADING", ""),
                         t0=t0, t1_hit=t1_hit, t1n=len(strict), strict=strict,
                         t2_hit=t2_hit, t2n=len(loose), loose=loose))

    # ---- report ----
    print("\n" + "=" * 90)
    print("PER-CASE   (T0=today  T1=wide+strict  T2=wide+loose/ask)")
    print("=" * 90)
    for r in rows:
        mark = lambda b: "OK " if b else "-- "
        print(f"\n{r['label']}   oracle={r['oracle']!r}")
        print(f"  T0 today      : {mark(r['t0'])}")
        print(f"  T1 wide+strict: {mark(r['t1_hit'])} ({r['t1n']} distinct disease(s) surfaced)")
        if not r["t1_hit"]:
            print(f"       surfaced : {list(r['strict'].keys())}")
            print(f"  T2 wide+loose : {mark(r['t2_hit'])} ({r['t2n']} disease(s) -> "
                  f"clarifying question would show these)")
            if r["t2n"]:
                print(f"       options  : {list(r['loose'].keys())[:6]}")

    n = len(rows)
    s0 = sum(r["t0"] for r in rows)
    s1 = sum(r["t1_hit"] for r in rows)
    s2 = sum(r["t1_hit"] or r["t2_hit"] for r in rows)
    ask_fires = sum(1 for r in rows if (r["t1_hit"] and r["t1n"] > 1) or
                    (not r["t1_hit"] and r["t2n"] > 1))
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"  cases                                : {n}")
    print(f"  T0  surfaced today                   : {s0}/{n}")
    print(f"  T1  surfaced by wide+strict (auto)   : {s1}/{n}")
    print(f"  T1+T2 surfaced w/ loosen+ask         : {s2}/{n}")
    print(f"  clarifying question would fire in    : {ask_fires}/{n} cases (>1 disease)")
    print(f"\n  still MISSING after everything:")
    for r in rows:
        if not (r["t1_hit"] or r["t2_hit"]):
            print(f"    - {r['label']:32s} oracle={r['oracle']!r}")


if __name__ == "__main__":
    main()
