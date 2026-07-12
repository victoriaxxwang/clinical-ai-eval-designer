# Hackathon Submission — Clinical AI Eval Designer

Built with Claude: Life Sciences · Build track · Deadline 2026-07-13

> Draft answers to the five required submission fields. Refine wording before
> submitting; the video talk-track (Q3) will be written last, once the app is
> finalized.

---

## 1. Project description — what you built, what you found, why it matters

**What I built.** Clinical AI Eval Designer — a tool that takes what a clinical
AI model does and its clinical context (AI model, clinical use case, patient
population, healthcare setting) and outputs a structured, citable **validation
specification**: study design, sensor/input validation, performance benchmarks,
ground-truth strategy, sample size, subgroup requirements, regulatory pathway,
and post-deployment monitoring — eight fields, each flagged by confidence
(HIGH/MEDIUM/LOW) and by the kind of expert review it still needs.

Critically, it grounds every citation in **live registry data** — it queries
ClinicalTrials.gov, openFDA, and PubMed programmatically *before* the model
writes anything, then uses Claude Fable 5 as a constrained synthesis layer that
maps real records into the structure. It is constrained by design: no invented
thresholds, every quantitative claim carries a real citation or is explicitly
flagged as team-set.

**What I found.** The weeks-long, expert-only process of figuring out *what a
clinical AI model must prove before anyone will adopt it* can be compressed into
a grounded, citable first draft in minutes — and, more importantly, doing it
*safely* is not a retrieval problem, it's a **constraint problem**. An
unconstrained model produces confident, fabricated benchmarks. The value is the
constraint layer that forces honesty (cite-or-flag, confidence tiers,
"certifies / does not certify"), plus grounding that makes citations verifiable
by construction.

**Why it matters.** Clinical AI teams routinely build models that work
technically but stall clinically because they lack the right validation
evidence, and the answer changes by indication, population, and intended claim.
A tool that gives them a rigorous, grounded starting point — while being honest
about what still needs a human — turns weeks of manual literature work into an
expert-review conversation. And it's a template for trustworthy AI in a
high-stakes domain: the safety is enforced at the model-behavior level, not just
the UI.

### Key design decisions (the reasoning behind the build)
- **The moat is the constraint layer, not the retrieval.** Retrieval is table stakes — anyone can call PubMed. What's defensible is the encoded expert structure (the 8 fields, sensor-validation-as-a-precondition, physics/physiology subgroup threats) plus behavioral constraints (no invented numbers, cite-or-flag, confidence tiers) enforced at the model level. That's a trustworthy-AI story only Claude can tell credibly.
- **Grounded before the model reads anything → verifiable by construction.** The app pulls real records from public registries *first*, then hands them to Fable. Every citation is a re-resolvable identifier (PMID, NCT number, FDA K-number/product code), not model memory — so a reviewer can check each one against the issuing database.
- **"Reproducible + verifiable," not "bit-identical."** We deliberately do *not* over-claim determinism. Live registries update, so we guarantee pinned queries, an explicit sort key + hard cap, and a timestamped snapshot of the raw records in the output bundle — and treat a re-resolvable ID as the verifiability guarantee, not a frozen ranking. The honesty is the point.
- **Core First, Agents Later.** A bounded, deterministic engine ships and is tested first (verified disease-agnostic across 12 unrelated indications). Agentic critics — a clinical-integrity checker and a self-correction loop — are Phase 2, layered on top and inheriting the same constraints, never replacing the deterministic core.
- **Claude Science is the discovery engine, not a runtime dependency.** It proved the concept; it has no programmatic endpoint, so the product replicates its *pattern* — grounded retrieval → constrained reasoning — with direct public-registry APIs. In one respect that's *more* verifiable than routing through any model: there is no model in the retrieval path.

### How I validated the grounding — a 10-case ablation eval
Retrieval that *looks* reasonable isn't evidence. So I built a hand-verified answer
key for **10 diverse clinical AI cases** — spanning devices, drugs, biologics, and
hybrids; regulatory-approved, regulatory-null, and mixed situations — and scored the
live pipeline against them on **precision and recall**, never raw counts (counts
always reward the widest, noisiest net). Every one of the ~470 scored identifiers
re-resolves against its live registry today. Then I ran an **ablation study**: hold
the shipped pipeline as a baseline and change exactly one dial at a time, across all
10 cases, to see which parts actually earn their place.

- **What earns its place:** the multi-database literature layer does — adding
  OpenAlex recovers a genuinely load-bearing landmark paper in **3 of the 10** cases
  (DR / warfarin / AFib), wherever the golden literature is retrievable by ranking at
  all. Crossref DOI-verification is a correctness guard that costs nothing on clean
  data. Both stay.
- **The honest negatives — measured and reported, not hidden.** (1) I shipped a
  fix that surfaces the disease name and makes broad conditions resolve — and then
  measured that it only helps when the disease is *named early*: on realistic
  *mechanism-first* write-ups (disease buried in ML jargon) it surfaces the condition
  in just 3 of 20 independent cases. That's a first-principle bound of the keyword-only
  approach. The wide-net fix that recovers it (2→17) I built and measured: it surfaces the
  buried disease, and a ranking + clarifying-question tiebreaker resolves the multi-disease
  fork it opens — 10/10 on the test slate (every previously-working case unchanged;
  buried-disease cases either resolve correctly or raise the clarifying question, never a
  silent wrong pick). It is now **wired into the shipped app and on by default**, with the
  frozen keyword engine one toggle away for a live side-by-side (see OPTION1_WIDENET.md) —
  a measured, default capability, not a promise. Its one documented cost is next: (2) a
  side-effect of that same fix costs sepsis its one golden
  paper (literature 2→0, because making its MeSH resolve rebuilds the query); the
  compensating patch was net-negative across the slate (−1 golden) so I reverted it and
  document the tradeoff. (3) The MeSH `+hierarchy` vocabulary-expansion axis is still
  score-inert — now for a measured reason (a 5-term query cap fills with synonyms
  before any child term is reached), not the unlaunched fix of the earlier draft. I'm
  reporting all three openly rather than claiming a clean win.
- **The headline finding — and the fix I then built.** The dials we can turn barely
  move recall. What actually determines whether the right FDA records surface is **how
  the question is aimed** — records named by *function* ("Prioritization Software") or by
  a *specific device name* don't rank on a *disease* query, in 6 of 10 cases. So the fix
  isn't a knob: it aims the FDA search at the recovered disease on **two axes** — the
  device *classification codes* that name the disease, and the 510(k) *device names*
  themselves (kept only when they sit under a real AI / CAD / triage code or a recent
  diagnostic clearance). I built it as a standalone module (`fda_bridge.py`, frozen engine
  untouched) and validated it live on all 10 cases: **3 now cite their real cleared AI
  devices** (retinopathy, stroke, NSCLC), TB grounds to its correct bacteriological
  reference, and the other 6 **degrade safely** — off-target records are *named and
  rejected, never cited* — for **zero fabricated predicates across the slate**. Diagnosing
  the problem with a repeatable harness *and* shipping the validated fix is the
  deliverable.

This is the trust story in miniature: the tool is measurably honest about what it
grounds well, what it doesn't, and why. (Full method + per-case detail:
`eval_results/ablation_findings.md`.)

## 2. Link to your work
- **GitHub:** https://github.com/victoriaxxwang/clinical-ai-eval-designer
  *(ensure the repo is public before submission)*

## 3. Demo video (max 3 minutes)
- **Link:** _TBD — https://youtube.com/watch?v=..._
- **Script:** to be written after the app is finalized. Working blueprint in
  `DEMO_PLAN.md` (Problem/Hook → live 8-field generation showing confidence flags
  and real citations → moat + roadmap). Final talk-track goes here.

## 4. How did you use Claude? Which products? Where did they matter most?

Three distinct roles:

- **Claude Science — the discovery engine.** Where I *proved the concept*: I ran
  the full literature synthesis for HRV-based stress detection on consumer
  wearables (500-participant decentralized design, per-device sensor validation,
  Fitzpatrick skin-tone subgroup analysis, regulatory landscape) grounded in 48
  papers, and it worked. That proof-of-concept is what convinced me the
  structured starting point could be generated automatically.

- **Claude Code — the builder.** Wrote the Streamlit app, the constraint-layer
  system prompt, and the live-registry retrieval pipeline; extracted the
  deterministic retrieval into a testable module and verified it stays
  disease-agnostic across 12 unrelated indications (20 automated tests, including
  a regression guard on the registry field paths). Handled git/repo setup. This
  is where the manual insight became working, tested software.

- **Anthropic API (Claude Fable 5 → Opus 4.8) — the runtime engine.** Each
  generation calls Fable 5 as the constrained synthesis layer over records
  retrieved live from the public registries. In practice Fable's safety classifier
  frequently declines benign life-sciences requests, so I ship Anthropic's
  server-side refusal fallback by default: Opus 4.8 transparently re-serves the
  response inside the same call, with no user-visible failure and no safeguard
  weakened. Verified end-to-end (2026-07-08): a real HRV-wearable case retrieved
  6 trials / 10 FDA records / 8 papers and produced a fully-grounded 8-field spec
  in ~90s — Fable declined, the Opus 4.8 fallback served it, and the constraint
  layer is identical on either model. The honest read is that clinical inputs
  often run on Opus 4.8 today; the value (constraint layer + grounding) is
  model-independent.

- **Anthropic API (Claude Fable 5 → Opus 4.8) — the review panel.** A second,
  optional call puts the finished spec in front of three Claude-played personas —
  an FDA/regulatory reviewer, a biostatistician, and a clinical scientist — that each
  return one strength plus flagged (🔴 blocking / 🟡 minor) critiques, in one
  structured JSON call. It is explicitly **advisory, not an authoritative verdict**,
  and held to the same discipline as the generator: cite-or-flag (name a specific
  study or record only if it's in the retrieved evidence, otherwise reason generally,
  never invent). A deterministic **warn-only grounding audit** then cross-checks every
  identifier the panel named against the retrieved evidence. This is where I leaned on
  Claude hardest for judgment, and where I watched fabrication risk closely — an
  end-to-end live run on 3 fresh device/imaging cases (2026-07-11), each spec generated
  *from* the retrieved evidence, came back **fully grounded with zero fabrication**;
  when I turned web search on, the panel correctly **caught and flagged** the
  model's web-sourced (unverifiable) citations, which is why that toggle now defaults
  off. The panel touches nothing in the deterministic engine.

**Where it mattered most:** Claude Science proved the workflow was possible;
Claude Code turned that into a product whose defensibility is the constraint
layer, not the retrieval. The honest framing is that the app is an *automated,
programmatic mirror* of the Claude Science discovery workflow — Claude Science
has no runtime API to call, so I replicated its pattern (grounded retrieval →
constrained reasoning) with direct registry APIs.

## 5. Thoughts / feedback on building with Claude Science

- **What worked well:** Fast, high-quality synthesis across dozens of papers into
  a structured, decision-ready output — exactly the discovery step that normally
  takes an expert weeks. It made the whole product idea credible.
- **Friction / wishlist:** There's no programmatic way to invoke a
  Claude-Science-style deep-research workflow from an application — I had to
  rebuild the retrieval pattern against public registry APIs to productize it. A
  callable "deep research" primitive (retrieve + verify against named sources +
  return real identifiers) would let builders ship the Claude Science experience
  instead of approximating it. Also: surfacing verifiable identifiers (PMIDs,
  NCT numbers, clearance numbers) as first-class, checkable outputs would make
  grounded citation the default rather than something builders have to engineer.
- **A design insight the workbench sharpened:** the honest framing of determinism
  — *reproducible + verifiable, not bit-identical* — and treating a re-resolvable
  identifier as the unit of trust (a citation is trustworthy iff its ID
  re-resolves against the issuing database). That reframe is more defensible than
  claiming frozen, repeatable searches, and it came directly from working the
  retrieval problem in the Science environment.
