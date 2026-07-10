"""
ablation_harness.py — Door B: the eval ablation harness.

WHAT IT DOES
------------
Scores the pilot-3 golden cases (HRV, DR, warfarin) against the LIVE retrieval
pipeline (`engine.build_grounded_context`) under a set of ONE-AXIS-AT-A-TIME
configs, reporting PRECISION and RECALL against the hand-verified goldens —
never raw counts alone (raw counts always crown the widest net and reward the
noise these layers exist to prevent; see COMPARISON.md Lesson 2 + INDEX.md
"Scoring rule").

It does DOUBLE DUTY (INDEX "Harness design = ABLATION STUDY, not a mega-grid"):
  (i)  validate that each Tier-B retrieval layer earns its place across diverse
       cases, and
  (ii) compare the MeSH-expansion options.
We fix a BASELINE = the shipped config, then vary ONE axis at a time. NOT a full
factorial (interaction effects are meaningless at n=3 and untenable live).

WHAT IT DOES NOT DO
-------------------
No API key needed and no Fable/Opus call: we score what the engine RETRIEVES (the
deterministic half), because that is exactly what the goldens are answer keys for.
The synthesis layer is out of scope here.

SCORING (per case × config × scored category)
---------------------------------------------
Each golden scores ONLY the categories present in its own `required` block
(HRV: no ncts/nda; DR: has ncts; warfarin: has ncts + nda) — categories are
optional-per-case. `related_context_not_scored` and `regulatory_null_evidence`
are never in `required`, so iterating `required` excludes them automatically.

  - DETERMINISTIC categories (fda_product_codes / fda_k_numbers /
    fda_den_numbers / fda_nda_numbers / ncts) → EXACT identifier match.
        recall    = |golden ∩ retrieved| / |golden|
        precision = |golden ∩ retrieved| / |retrieved in that category|
    Precision here is a LOWER BOUND: the pipeline legitimately pulls
    adjacent-correct records that aren't in the golden (e.g. warfarin's
    null-evidence PMAs are "a precision bonus, not a recall requirement"), which
    deflates golden-overlap precision. Read it as "of what we pulled, how much
    was known-golden," and use it comparatively across configs, not as an
    absolute purity score.

  - LITERATURE categories (pmids / dois) → a ranked search is NOT a curated set
    (Lesson 2), so exact golden-overlap is LOW by design. We report both the
    overlap AND the resolvable-ID floor (raw retrieved count) so the meaningful
    signal is comparative: does an added layer raise golden-overlap, or just
    inflate the count at flat overlap (= noise)?

USAGE
-----
    source .venv/bin/activate
    python ablation_harness.py                    # all cases × all configs (uses cache)
    python ablation_harness.py --refresh          # ignore cache, re-hit registries
    python ablation_harness.py --case warfarin    # one case (repeatable: HRV|DR|warfarin)
    python ablation_harness.py --config baseline   # one config
    python ablation_harness.py --list             # show cases/configs and exit

Retrieval snapshots are cached to eval_results/contexts/<case>__<config>.json so
re-scoring is instant and offline; --refresh re-pulls. Results are written to
eval_results/ as ablation_results.json (machine) + ablation_results.md (human).
"""
import argparse
import datetime
import json
import os
import re
import sys

PROJECT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT)
import engine  # noqa: E402

RESULTS_DIR = os.path.join(PROJECT, "eval_results")
CACHE_DIR = os.path.join(RESULTS_DIR, "contexts")


# ---------------------------------------------------------------------------
# CASE REGISTRY — the pilot-3 slate. model_desc/use_case/population/setting mirror
# each golden's reference_case so the queries the engine builds match the case the
# answer key was written for. intervention_type is FIXED per case (what the
# device/drug IS) and is deliberately NOT a swept axis (INDEX line 68).
# ---------------------------------------------------------------------------
CASES = {
    "HRV": {
        "golden": "golden_expected_ids.json",
        "intervention_type": "device",
        "model_desc": ("Algorithm that infers psychological stress from heart-rate "
                       "variability (HRV) derived from the optical photoplethysmography "
                       "(PPG) sensor on a consumer wrist-worn wearable."),
        "use_case": "Continuous, passive stress detection in daily life",
        "population": "General adult consumers across a range of skin tones and activity levels",
        "setting": "Consumer wellness mobile app (non-diagnostic, direct-to-consumer)",
    },
    "DR": {
        "golden": "golden_expected_ids_DR.json",
        "intervention_type": "device",
        "model_desc": ("AI algorithm that analyzes color retinal fundus photographs to "
                       "detect more-than-mild diabetic retinopathy in adults with diabetes, "
                       "with an image-quality gradeability gate."),
        "use_case": "Autonomous point-of-care diabetic retinopathy screening in primary care",
        "population": "Adults with type 1 or type 2 diabetes across skin tones and camera models",
        "setting": "Primary-care / non-ophthalmology point-of-care screening",
    },
    "warfarin": {
        # "both": the golden spans the DEVICE path (genotyping-assay 510(k)s +
        # product codes) AND the DRUG path (Coumadin NDA009218) — needs both.
        "golden": "golden_expected_ids_warfarin.json",
        "intervention_type": "both",
        "model_desc": ("Algorithm that recommends an initial warfarin dose and early dose "
                       "adjustment using clinical variables and CYP2C9/VKORC1 pharmacogenomic "
                       "genotype to reach and maintain target INR."),
        "use_case": "Warfarin initial dosing decision support to reach and maintain stable INR",
        "population": "Adults starting warfarin across genotypes and ancestries",
        "setting": "Inpatient initiation and outpatient anticoagulation-clinic management",
    },
    "sepsis": {
        # First BROAD-PARENT condition ("Sepsis" MeSH D018805 has narrower
        # descriptors) → the case the MeSH "+hierarchy" axis is expected to
        # finally DIVERGE on (inert on the leaf-term pilot 3). EHR-only software
        # SaMD, regulatory-positive (product code SAK) → intervention_type="device".
        "golden": "golden_expected_ids_sepsis.json",
        "intervention_type": "device",
        # NB: model_desc is CONDITION-FORWARD ("Sepsis early-warning algorithm that…").
        # A mechanism-first phrasing ("Algorithm that continuously analyzes routinely-
        # collected EHR time-series … to predict … sepsis") buries "sepsis" PAST
        # model_desc's top-12 keyword cap (build_queries line ~212), so the condition
        # never enters mesh_candidates/fda_terms/the query and retrieval collapses to 0.
        # That brittleness is a real engine finding (logged in ablation_findings.md +
        # INDEX "engine to-do"); here we phrase the case as a coached user would so the
        # sepsis ablation actually tests sepsis retrieval.
        "model_desc": ("Sepsis early-warning algorithm that continuously analyzes routinely-"
                       "collected structured EHR time-series (vital signs, labs, nursing "
                       "assessments) to predict onset of sepsis and septic shock in "
                       "hospitalized adults before clinical recognition."),
        "use_case": ("Inpatient sepsis early-warning clinical decision support alerting "
                     "clinicians to initiate sepsis workup and treatment"),
        "population": "Hospitalized adults on medical and surgical wards and in the ICU",
        "setting": "Inpatient hospital early-warning / clinical decision support",
    },
    "AFib": {
        # Case 5. LEAF condition ("Atrial Fibrillation" MeSH D001281 has no narrower
        # children) so "+hierarchy" correctly NO-OPS here (== canonical+synonyms) —
        # expected/benign, NOT the broad-parent hierarchy test (that's sepsis/pneumonia).
        # Regulatory-POSITIVE device case (QDA/QDB Class II 510(k)/De Novo) with a
        # null twist (no autonomous-diagnosis authorization; no PMA). intervention_type
        # ="device". model_desc is CONDITION-FORWARD ("Atrial fibrillation … algorithm")
        # so "AFib"/"atrial fibrillation" reaches build_queries before the top-12 keyword
        # cap (Case-4 Finding A); a mechanism-first phrasing would bury the condition.
        "golden": "golden_expected_ids_AFib.json",
        "intervention_type": "device",
        "model_desc": ("Atrial fibrillation (AFib) screening and notification algorithm that "
                       "analyzes a single-lead ECG waveform and a photoplethysmography (PPG) "
                       "irregular-rhythm signal recorded on a consumer wrist-worn wearable to "
                       "flag possible atrial fibrillation and notify the wearer for clinical "
                       "confirmation."),
        "use_case": ("Direct-to-consumer wearable atrial fibrillation screening and "
                     "irregular-rhythm notification prompting clinical confirmation"),
        "population": "Adults without prior AFib diagnosis across ages, skin tones, wrist sizes, and activity states",
        "setting": "Over-the-counter / direct-to-consumer, ambulatory unsupervised (non-diagnostic)",
    },
    "melanoma": {
        # Case 6. Regulatory-POSITIVE device case with a MODALITY-NULL twist:
        # three adjunctive Class II codes exist (QZS De Novo DEN230008; OYD PMA
        # P090012; ONV PMA P150046) but each uses a DIFFERENT physical signal —
        # none is a photograph-input image-AI classifier (the system under eval).
        # Slate's FIRST case with fda_pma_numbers; no K-numbers, no NDA.
        # "Melanoma" (MeSH D008545) sits under broader "Skin Neoplasms" (D012878),
        # so this is a 2nd broad-parent point for the "+hierarchy" axis (after
        # sepsis) — whether it diverges is read empirically from the sweep.
        # model_desc is CONDITION-FORWARD ("Skin-lesion malignancy / melanoma …")
        # so the condition reaches build_queries before the top-12 keyword cap
        # (Case-4 Finding A); a mechanism-first phrasing would bury it.
        "golden": "golden_expected_ids_melanoma.json",
        "intervention_type": "device",
        "model_desc": ("Skin-lesion malignancy / melanoma risk-assessment algorithm that "
                       "analyzes dermoscopic or clinical photographs of a skin lesion to "
                       "estimate malignancy risk and provide an adjunctive biopsy/refer "
                       "recommendation to a physician who is not a skin-cancer specialist."),
        "use_case": ("Adjunctive image-based skin-lesion malignancy / biopsy-referral "
                     "decision support for melanoma and other skin cancers"),
        "population": "Adults presenting with suspicious skin lesions across skin tones and lesion types",
        "setting": "Primary-care / non-dermatology point-of-care skin-cancer triage (adjunctive, non-standalone)",
    },
}


# ---------------------------------------------------------------------------
# CONFIG REGISTRY — BASELINE = shipped defaults, then ONE axis varied per config.
# baseline already IS {mesh=canonical+synonyms, providers=all-3, verify=on}, so the
# "all-3 providers", "canonical+synonyms" and "verify on" points are baseline (no
# duplicate configs). 6 configs = baseline + 2 MeSH levels + 2 provider subsets +
# verify-off, each isolating one axis (INDEX "Harness design").
# ---------------------------------------------------------------------------
CONFIGS = {
    "baseline": dict(mesh_expansion="canonical+synonyms", providers=None, verify_literature=True),
    # MeSH axis:
    "mesh_canonical": dict(mesh_expansion="canonical", providers=None, verify_literature=True),
    "mesh_hierarchy": dict(mesh_expansion="+hierarchy", providers=None, verify_literature=True),
    # Literature-providers axis (baseline = all 3):
    "lit_epmc_only": dict(mesh_expansion="canonical+synonyms",
                          providers=["europepmc"], verify_literature=True),
    "lit_epmc_openalex": dict(mesh_expansion="canonical+synonyms",
                              providers=["europepmc", "openalex"], verify_literature=True),
    # Crossref-verify axis (baseline = on):
    "verify_off": dict(mesh_expansion="canonical+synonyms", providers=None, verify_literature=False),
}

# Which axis each config probes (for the human report).
CONFIG_AXIS = {
    "baseline": "— (shipped defaults)",
    "mesh_canonical": "MeSH: canonical only (drop synonyms)",
    "mesh_hierarchy": "MeSH: + hierarchy (add child descriptors)",
    "lit_epmc_only": "Providers: Europe PMC only",
    "lit_epmc_openalex": "Providers: Europe PMC + OpenAlex",
    "verify_off": "Crossref verify: OFF",
}


# ---------------------------------------------------------------------------
# IDENTIFIER EXTRACTION — regexes matched to how engine renders each token
# (verified against engine.py formatters):
#   literature : "- PMID 12345 | DOI 10.x/y ✓Crossref | title …"
#   510(k)     : "| k_number=K073014 …"   De Novo: "| k_number=DEN180001 …"
#   class.     : "| product_code=ODW …"
#   PMA        : "| pma_number=P990037 …"
#   Drugs@FDA  : "| application=NDA009218 …"
#   CT.gov     : "- NCT02963441 | title …"
# DOIs are lowercased on both sides (engine normalizes to lowercase on merge;
# goldens carry mixed case e.g. NEJMoa) so matching is case-insensitive.
# ---------------------------------------------------------------------------
EXTRACTORS = {
    "pmids": lambda c: set(re.findall(r"PMID (\d+)", c)),
    "dois": lambda c: {d.lower() for d in re.findall(r"DOI (10\.[^\s|]+)", c)},
    "fda_product_codes": lambda c: set(re.findall(r"product_code=([A-Z0-9]{3})", c)),
    "fda_k_numbers": lambda c: set(re.findall(r"k_number=(K\d+)", c)),
    "fda_den_numbers": lambda c: set(re.findall(r"k_number=(DEN\d+)", c)),
    "fda_pma_numbers": lambda c: set(re.findall(r"pma_number=(P\d+)", c)),
    "fda_nda_numbers": lambda c: set(re.findall(r"application=([A-Z]+\d+)", c)),
    "ncts": lambda c: set(re.findall(r"(NCT\d{8})", c)),
}
LITERATURE_CATEGORIES = {"pmids", "dois"}


def normalize_golden_ids(category, ids):
    """DOIs are compared case-insensitively; other identifiers as-is (uppercase)."""
    if category == "dois":
        return {str(x).lower() for x in ids}
    return {str(x) for x in ids}


# ---------------------------------------------------------------------------
# Retrieval (cached) + scoring
# ---------------------------------------------------------------------------
def retrieve(case_name, config_name, refresh=False):
    """Return the grounded-context text for (case, config), from cache or live.
    Caches {context, statuses, timestamp, config, case} to eval_results/contexts/."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{case_name}__{config_name}.json")
    if not refresh and os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f), "cache"
    case = CASES[case_name]
    cfg = CONFIGS[config_name]
    ctx, statuses, ts = engine.build_grounded_context(
        case["model_desc"], case["use_case"], case["population"],
        optional_url="", setting=case["setting"],
        intervention_type=case["intervention_type"], **cfg)
    payload = {"case": case_name, "config": config_name, "context": ctx,
               "statuses": statuses, "retrieval_timestamp": ts}
    with open(cache_path, "w") as f:
        json.dump(payload, f, indent=2)
    return payload, "live"


def score(case_name, context):
    """Score one retrieved context against its golden. Returns a per-category dict."""
    with open(os.path.join(PROJECT, CASES[case_name]["golden"])) as f:
        required = json.load(f)["required"]
    out = {}
    for category, golden_ids in required.items():
        if category not in EXTRACTORS:
            # A scored category with no extractor would silently under-report —
            # surface it loudly instead of scoring a false zero.
            out[category] = {"error": f"no extractor for scored category {category!r}"}
            continue
        golden = normalize_golden_ids(category, golden_ids)
        retrieved = EXTRACTORS[category](context)
        hits = golden & retrieved
        recall = len(hits) / len(golden) if golden else None
        precision = len(hits) / len(retrieved) if retrieved else None
        out[category] = {
            "kind": "literature" if category in LITERATURE_CATEGORIES else "deterministic",
            "golden_n": len(golden),
            "retrieved_n": len(retrieved),
            "hits_n": len(hits),
            "recall": recall,
            "precision": precision,
            "hits": sorted(hits),
            "missed": sorted(golden - retrieved),
        }
    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def _fmt_pct(x):
    return "  —  " if x is None else f"{100 * x:4.0f}%"


def build_report(results):
    """results: {case: {config: {category: metrics}}} → (markdown, flat_rows)."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    md = [f"# Ablation results — pilot-3 golden slate\n",
          f"_Generated {now}. Recall/precision vs the hand-verified goldens; "
          f"deterministic categories are EXACT identifier matches, literature is "
          f"overlap + resolvable-ID floor (Lesson 2). Precision on deterministic "
          f"categories is a lower bound (adjacent-correct records deflate it)._\n"]
    for case_name in results:
        md.append(f"\n## {case_name}\n")
        # Determine the scored categories for this case (stable order).
        cats = list(next(iter(results[case_name].values())).keys())
        header = "| config | axis | " + " | ".join(
            f"{c} R/P (hits/n)" for c in cats) + " |"
        sep = "|" + "---|" * (2 + len(cats))
        md.append(header)
        md.append(sep)
        for config_name in CONFIGS:
            if config_name not in results[case_name]:
                continue
            cells = []
            for c in cats:
                m = results[case_name][config_name][c]
                if "error" in m:
                    cells.append("ERR")
                    continue
                cells.append(f"{_fmt_pct(m['recall'])}/{_fmt_pct(m['precision'])} "
                             f"({m['hits_n']}/{m['retrieved_n']})")
            md.append(f"| {config_name} | {CONFIG_AXIS[config_name]} | "
                      + " | ".join(cells) + " |")
    return "\n".join(md)


def run(cases, configs, refresh=False):
    results = {}
    for case_name in cases:
        results[case_name] = {}
        for config_name in configs:
            payload, origin = retrieve(case_name, config_name, refresh=refresh)
            metrics = score(case_name, payload["context"])
            results[case_name][config_name] = metrics
            # Live progress line so a long sweep is legible as it runs.
            det = {k: v for k, v in metrics.items()
                   if isinstance(v, dict) and v.get("kind") == "deterministic"}
            det_hits = sum(v["hits_n"] for v in det.values())
            det_need = sum(v["golden_n"] for v in det.values())
            lit = {k: v for k, v in metrics.items()
                   if isinstance(v, dict) and v.get("kind") == "literature"}
            lit_hits = sum(v["hits_n"] for v in lit.values())
            lit_n = sum(v["retrieved_n"] for v in lit.values())
            print(f"  [{origin:>5}] {case_name:>8} / {config_name:<18} "
                  f"deterministic {det_hits}/{det_need}  |  literature {lit_hits} golden "
                  f"of {lit_n} retrieved")
    return results


def main():
    ap = argparse.ArgumentParser(description="Door B ablation harness (pilot-3 goldens).")
    ap.add_argument("--case", choices=list(CASES), help="run one case (default: all)")
    ap.add_argument("--config", choices=list(CONFIGS), help="run one config (default: all)")
    ap.add_argument("--refresh", action="store_true", help="ignore cache; re-hit registries")
    ap.add_argument("--list", action="store_true", help="list cases/configs and exit")
    args = ap.parse_args()

    if args.list:
        print("CASES:  ", ", ".join(CASES))
        print("CONFIGS:", ", ".join(CONFIGS))
        for c, axis in CONFIG_AXIS.items():
            print(f"  {c:<20} {axis}")
        return

    cases = [args.case] if args.case else list(CASES)
    configs = [args.config] if args.config else list(CONFIGS)
    print(f"Running {len(cases)} case(s) × {len(configs)} config(s) "
          f"({'LIVE refresh' if args.refresh else 'cache if available'})...\n")
    results = run(cases, configs, refresh=args.refresh)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "ablation_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    md = build_report(results)
    with open(os.path.join(RESULTS_DIR, "ablation_results.md"), "w") as f:
        f.write(md + "\n")
    print("\n" + md)
    print(f"\nWrote eval_results/ablation_results.json + .md")


if __name__ == "__main__":
    main()
