# Option 1 — the wide-net + disambiguation prototype

*A standalone writeup of the disease-aware grounding path. It was built entirely in an
isolated copy (`experimental/engine_widenet.py`) that was **never allowed to touch** the
frozen `engine.py` (identical md5 throughout) — and it is now **wired into the shipped
app and on by default**, with the frozen keyword engine one toggle away for a live
side-by-side. The same disease-awareness was later extended to the FDA layer and
validated live on all 10 demo cases (see "The FDA net learns the disease too", below).*

---

## The one-paragraph version

The shipped engine finds a study's disease only when the write-up **names the
disease early**. On realistic *mechanism-first* descriptions — where the disease is
buried under machine-learning jargon — it misses the condition and the whole citation
search goes off-target. This experiment asked: can a **wide net** (read the entire
case text, not just the first few keywords) recover that miss, and can we then **pick
the right disease** when the wider net inevitably surfaces more than one? The answer to
both is yes, measured: the net recovers the buried disease (**oracle match 2/6 → 4/6**,
all gains on the hard mechanism-first cases, zero regression on the easy ones), and a
three-rule tiebreaker plus a clarifying-question pop-up resolves the multi-disease fork
or asks the user — scoring **10/10** on a combined test slate, and **never making a
silent wrong pick.** A follow-on step carried the same disease-awareness into the **FDA
device-precedent search** and validated it live across all 10 demo cases with **zero
fabricated predicates** (last section).

---

## The problem it addresses

The engine grounds every citation by first identifying the clinical condition, then
querying public registries for that condition. The shipped ("Option 2") approach reads
roughly the first dozen keywords of the model description to surface the disease name.

That works when a human or Claude Science writes the case **condition-forward** ("A
model for **heart failure** that ingests..."). But real users — and Claude Science
itself, left to its own phrasing — often write **mechanism-first**: "A gradient-boosted
ensemble ingesting longitudinal structured EHR signals to flag decompensation..." — and
the disease ("heart failure") shows up only in the last sentence, past the keyword
window. An independent 20-case check measured this bound honestly: the shipped surfacing
lands the disease on only **3 of 20** mechanism-first cases. It's a *first-principle*
limit of reading only the opening keywords, not a bug.

---

## The idea: cast a wider net

Instead of the first ~12 keywords of one field, scan the **whole case text**
(model description + use case + population + setting) as single words **and** adjacent
two-word phrases, and run each through the **same** disease-only safety filter the
engine already uses. Two-word phrases matter because many real MeSH headings are
multi-word ("Heart Failure", "Pulmonary Embolism") and a lone word can't match them.

A read-only probe of this idea (no engine edits) recovered disease surfacing from
**2/20 → 17/20** with no loosening of the matching rules. Encouraging enough to build
it properly — in isolation.

---

## How it was built, safely

Everything below lives in `experimental/engine_widenet.py`, a copy. The frozen
`engine.py` was **never opened for edit**. A guardrail (an md5 fingerprint of the frozen
engine, `2e6d49cdaa3106b6c29ee66b5df37e58`) was re-checked at the start and end of every
work session; if it had ever changed, work would have stopped. It never changed.

The work went in four measured steps (F1–F4).

### F1 — the wide net

Built the whole-text unigram-and-bigram scan in the isolated copy. Offline sanity check:
on all three mechanism-first test phrasings the buried disease now surfaces as a
two-word phrase ("heart failure", "kidney disease", "pulmonary embolism") — impossible
for the frozen keyword-only path. On condition-forward phrasings nothing regressed.

### F2 — does the net actually find the disease? (Yes)

Ran the frozen engine and the wide-net engine side by side on 3 fresh clinical topics,
each written **twice** — once condition-forward (the control) and once mechanism-first —
against a live medical-vocabulary lookup, no API key.

| | Frozen (shipped) | Wide-net |
|---|---|---|
| Oracle-heading match, total | **2 / 6** | **4 / 6** |
| Condition-forward controls | identical | identical (**zero regression**) |
| Mechanism-first (heart failure, pulmonary embolism) | disease **absent** from the query | resolves to the **exact** heading |

Every gain came from the mechanism-first cases; the controls were byte-for-byte
unchanged. (The third topic, chronic kidney disease, resolves to an adjacent heading on
*both* engines — a separate vocabulary-map quirk, not a wide-net failure.) **Verdict:
the net earns its keep.**

### F3 probe — the catch: the net finds *too much*

A wider net surfaces more than one disease. A stress test on two comorbidity topics
(heart-failure-in-diabetes; atrial-fibrillation-with-stroke), each written twice,
confirmed the risk cleanly: **more than one disease resolved in all 4 cases.** When the
use case *named* the target disease, the naive "first one that resolves wins" logic
picked correctly. When it named *neither* (mechanism-first), it **silently mispicked**
the distractor — diabetes instead of heart failure, embolic stroke instead of atrial
fibrillation. A silent wrong pick is the worst outcome, so this fork had to be resolved.

### F3 build — three tiebreakers + a clarifying question (10/10)

The fix is a thin wrapper (`resolve_condition`) over the **unchanged** vocabulary
resolver. It applies three rules, in order:

1. **A disease named in the use case wins** outright.
2. **A full two-word heading beats a lone word** that happened to resolve.
3. **Over-generic headings are demoted** ("Disease", "Chronic Disease", etc.).

When those rules still leave a genuine tie — a mechanism-first case where the use case
names *neither* disease and a second real, specific disease also resolves — the engine
raises a **clarifying-question pop-up** offering both diseases, rather than guessing.
Otherwise the pop-up stays silent. (The extra output is purely additive, so any code
reading only the original fields is unaffected.)

Measured live on a combined slate — **10/10**:

- **No-regression (6 single-disease cases): 6/6.** Every previously-working case still
  resolves correctly, and the pop-up **never fires** — the tiebreaker does not
  over-trigger when there's only one disease.
- **Comorbidity (4 two-disease cases): 4/4.** Controls resolve cleanly and silently. The
  two mechanism-first cases that *previously mispicked* now raise the clarifying question
  with **both** diseases on offer.

The result: the buried disease gets found (F2), and the fork it opens is either resolved
by the rules or handed back to the user as a question (F3) — **never a silent wrong
pick.**

---

## The FDA net learns the disease too

The wide net recovers the *disease*. But the FDA layer had a matching blind spot: it
searched openFDA by **device / machine-learning keywords**, so even when the disease was
known, the FDA search never used it — a melanoma case came back with surgical lasers, an
NSCLC case with a bladder-cancer lab test. The fix is a standalone module
(`experimental/fda_bridge.py`; it imports only `re` and `requests`, and the frozen engine
is untouched) that aims the FDA search at the **recovered disease**, on two axes:

1. **Code axis** — disease → FDA device *classification* codes whose name or definition
   contains the disease → the 510(k) clearances filed under those codes.
2. **Device-name axis** — search the 510(k) *device names* directly for the disease and
   its anatomy, then keep a device only if it sits under a known AI / CAD / triage code
   **or** carries a diagnostic signal in its name and was cleared in 2015 or later.

The second axis is the important one: most cleared clinical-AI devices sit under
**generically-named** codes ("Computer-Assisted Detection", "Radiological
Computer-Assisted Triage") that a disease-name query would never rank — exactly the
"records named by function don't surface" gap the ablation study measured. When a disease
is recovered, this disease-aware result **replaces** the old keyword FDA section; when no
disease is recovered, or the search comes back empty, the old keyword search stands
untouched (a safe fallback).

**Validated live, end-to-end, on all 10 demo cases** (real Fable-5 generations plus the
three-persona critic panel, 2026-07-11; frozen-engine fingerprint unchanged the whole
time):

| Outcome | Cases | What the generated spec did |
|---|---|---|
| **Real device-AI predicate cited** | Diabetic retinopathy, ischemic stroke, NSCLC | Cited the actual cleared AI devices — EyeArt / IDx-DR / AEYE-DS; Brainomix / Methinks / Rapid stroke-triage; syngo.CT Lung CAD / Lung Vision |
| **Correct reference grounded** | Tuberculosis | Cited Xpert MTB/RIF as the bacteriological ground-truth reference — the right record, used correctly |
| **Safe degradation** | Melanoma, T2DM, COPD, AKI, Crohn's, MDD | Off-target and keyword-noise records were **either absent from the spec or explicitly named and rejected** ("not valid predicates") — never cited as analogous |

**Zero fabricated predicates across all 10 cases.** Every critic panel returned a clean
grounding audit; the blockers the panels raised were legitimate methodology items
(intended-use claim, sample size, subgroup power), never a wrong FDA citation. In several
degradation cases the spec did better than staying silent — it *named* the false-positive
keyword matches ("the 'transformer' hits are electrical hardware… irrelevant") and told
the team to run a deeper predicate search. **Verdict: the FDA net earns its keep too, and
fails safe when there's nothing real to catch.**

---

## Where it sits

This is **wired into the shipped app and on by default.** The sidebar's *Disease-aware
grounding (wide-net)* toggle starts ON, so a visitor gets the disease-recovery path — now
including the disease-aware FDA search — out of the box; turning it OFF drops back to the
frozen keyword engine for a live side-by-side. The frozen `engine.py` itself was **never
edited** (identical md5 throughout), so the baseline is always one toggle away, and its
honest bound (surfacing helps most when the disease is named early) stays documented in
`SUBMISSION.md` and `eval_results/ablation_findings.md`. What began as a measured recovery
experiment is now a validated, default-on capability — recovery on the wide-net side, and
disease-aware FDA precedents with zero fabrication on the grounding side.

**Source of record:** the measurement scripts and results are in `scratchpad/`
(`f2_run.py`, `f3_probe.py`, `f3_build_run.py`, and their `.json`/`.log` outputs); the
code is in `experimental/engine_widenet.py`; the blow-by-blow log is in `INDEX.md`.
