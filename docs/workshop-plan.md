# Semantic contracts workshop: review proposal

Status: documentation-only proposal, 20 October 2026. Mark owns the workshop and review decisions. The proposed work window is **21–22 October 2026, America/Los_Angeles**, not an external deadline. Helsinki is the first delivery; retain reusable curriculum for the November O'Reilly version.

## Outcome and boundaries

An advanced Python/SQL audience spends three in-person, hands-on hours applying the same loop twice: **observe a failure → specify the contract → detect/prevent violations → rerun and interpret evidence**. First use the existing database/data-contract exercise, then repeat with an AI database-reading skill and semantic contracts. Keep the museum scenario, PostgreSQL infrastructure, and data continuous. Semantic rules constrain the skill and its use of data; there is no separate semantic layer.

Participants should leave able to:

1. Run a small local CPU model inside their Codespace.
2. Inspect tool calls and trajectory logs with an open-source local tool.
3. Run a quick evaluation.
4. Interpret its score, failures, and limitations.
5. Constrain skill files with explicit semantic rules and compare outcomes.

Each participant uses a lightweight Docker-based GitHub Codespace. Require no additional service accounts, API keys, gated model access, hosted inference, or hosted telemetry. Model and trace viewer are **unselected** until measured together on the intended Codespaces size. Use the checked-in Met subset exclusively; live Met API calls and image downloads are not runtime dependencies.

The conceptual article combines Mark's Data Contracts work and Jessica Talisman's Ontology Pipeline work. Jessica collaborates on the article only: she is not a workshop developer, instructor, or endorser of these technology candidates.

## Existing evidence, before choosing the exercise

Source baseline: `889babb2e30b85c0208f9472cedbc0a78bb466b4`. Existing components include Python 3.12, PostgreSQL 17, Alembic, JSON contract definitions, catalog coverage/violation checks, and database-backed tests. Static inspection is complete; successful startup and tests have **not** yet been demonstrated.

Read-only inspection of `data_contract_components/data_assets/db_migrations/raw_data/objects.json` found:

| Observation | Count |
| --- | ---: |
| Objects / unique object IDs | 3,025 / 3,025 |
| Top-level fields | 57 |
| Objects with tags / tag occurrences | 1,690 / 4,449 |
| Objects with actual AAT URLs | 1,644 |
| Actual AAT URL occurrences / distinct URLs | 3,894 / 443 |
| Other namespaces in the field named `AAT_URL`: IA / ULAN / TGN | 454 / 30 / 15 |
| Tag occurrences without a populated URL | 56 |

Useful fields include title, department, classification, medium, culture, objectDate, and tags containing term/AAT_URL/Wikidata_URL. Department is populated for all objects; classification for 1,568, medium for 2,376, and culture for 1,392. The database already preserves tags in `object_tags` and related fields in normalized tables.

Explore subject-versus-material interpretation, missing evidence, namespace validation, and identifier/label ambiguity before locking the questions. The sample maps “Leopards” and “Panthers” to the same stored AAT URL, but this is evidence to investigate, not an automatic synonym exercise or a verified equivalence claim. Do not cherry-pick an example just because it makes the constrained agent look better.

## Proposed 180-minute delivery

Start Codespaces immediately so setup overlaps the introduction. Private access and download preparation must be rehearsed before the event.

| Minutes | Activity | Participant evidence |
| --- | --- | --- |
| 0–15 | Launch environment; museum scenario and common loop | Health check and dataset identity |
| 15–35 | Existing architecture and guided SQL exploration | Read the existing contract and inspect related tables |
| 35–65 | Loop 1: introduce the existing data-contract violation, inspect detection, repair and rerun | Failing then passing contract checks; explain why |
| 65–75 | Debrief and short break | Connect structural guarantees to remaining semantic ambiguity |
| 75–95 | Local model, database-reading skill, tool boundaries; first query | One end-to-end trajectory |
| 95–120 | Loop 2 baseline: run fixed questions and inspect traces | Baseline scores and concrete failure categories |
| 120–150 | Add controlled-vocabulary semantic constraints to skill files | Reviewable rules grounded in museum data |
| 150–165 | Rerun identical evaluation and compare | Paired score/latency differences, including regressions |
| 165–180 | Interpret limitations, recap five takeaways, Q&A | Explain what improved, what did not, and next experiments |

The older hour-by-hour outline is superseded by this two-loop proposal. Benchmark gates below must show the evaluation fits these slots; otherwise reduce agent step/token budgets or simplify scope before rehearsal, not by changing questions mid-comparison. Recorded traces may support recovery from an environment failure but must be labeled as recordings, not a participant's live result.

## Evaluation and hidden-gold boundary

Freeze approximately ten data-specific questions after exploration and Mark's review. Include clear answerable cases, ambiguity/missingness, and appropriate abstention; define expected answers with reference SQL and human review. Use separate development examples while drafting constraints.

Baseline and constrained conditions must share model/quantization, data snapshot, questions/order, decoding settings/seeds, tool permissions, step/token budgets, scoring rubric, and runtime. Change only the versioned skill constraints and their declared vocabulary context. Record hashes and configuration. Fix seeds where supported and repeat a small paired sample to expose nondeterminism; do not claim seeds guarantee deterministic CPU inference.

Proposed separation: the agent runner gets only question text, an allowlisted read-only SQL tool with time/row limits, and the approved skill/vocabulary files. Give it no arbitrary shell, filesystem, Docker socket, host network, or scorer endpoint. Mount gold only in a separate offline scorer container/process with no agent-visible volume or database table; the scorer consumes completed answer files after the agent exits. Return scores to the participant-facing viewer, never into an ongoing agent context. Gold, reference SQL, expected outputs, and scorer traces must be excluded from agent images, repository mounts, prompts, tool results, and logs. A prompt saying “do not read gold” is insufficient.

This protects gold from the model, not from a participant with administrative control of their Codespace; make that limitation explicit. Test isolation with sentinel content and attempted tool/file access before accepting the harness. Keep broad workspace mounts and the existing Docker socket away from the agent runtime.

Use a predeclared deterministic rubric where possible: normalized answer sets/counts and IDs, explicit null/abstention rules, and evidence requirements. Have Mark adjudicate ambiguous cases before freeze. Report per-question outcomes, total correct out of N, regressions, timeouts/tool errors, tool-call counts, and latency alongside the paired difference. Ten items are a teaching diagnostic, not a general capability benchmark. Zero improvement or negative improvement is a valid result; never weaken the baseline, leak gold, or change scoring to manufacture uplift.

## Prioritized work for the proposed two-day window

Timeboxes are estimates, not promises. Assistant prepares focused draft PRs and evidence; Mark reviews pedagogy and accepts tradeoffs. No automatic merges or public distribution.

| Priority / proposed slot | Task and dependency | Acceptance gate / owner |
| --- | --- | --- |
| P0 · Oct 21 · 60–90 min | Reproduce original baseline before adding AI | Assistant records fresh startup, migrations, 3,025 seeded IDs, existing checks, intentional failure/recovery, repeatable reset. Mark confirms loop matches the workshop. If blocked, fix baseline first. |
| P0 · Oct 21 · 60–90 min | Explore sample and draft question categories; follows baseline | Assistant profiles joins, missingness, tags and namespace ambiguity. Mark selects learning failures and approves ~10 questions/rubric; do not freeze synonyms in advance. |
| P0 · Oct 21 · 90–120 min | Benchmark a small shortlist of ungated, commercially usable CPU models and open-source local trace viewers; follows baseline | Record exact model/quantization/license, download size, cold/warm startup, peak RAM, per-query p50/p95, and whole-eval wall time with DB/viewer running. Proposed targets: fresh setup ≤15 min, warm setup ≤5 min, ten-question run ≤10 min, peak RAM ≤75% of selected machine. Mark accepts measured fit or revises scope. No account/key required. |
| P0 · Oct 21 · 30–45 min | Review private participant access, Codespaces machine/cost, source permissions and vocabulary provenance | Mark owns access/budget/rights decisions; assistant supplies options. Confirm distribution path and cost cap before invitations, paid settings, or broader sharing. These are not enabled by this plan. |
| P1 · Oct 22 · 90–120 min | Design/build isolated evaluation and minimal trace capture; depends on model, questions and access design | Assistant demonstrates gold isolation, read-only bounded SQL, frozen manifests, score validity and offline trace viewing. Log question/run ID, skill version, tool inputs/results, final answer, duration/errors; do not promise hidden model reasoning. Mark reviews one complete run. |
| P1 · Oct 22 · 60–90 min | Add minimal licensed vocabulary subset and semantic skill constraints; depends on data exploration and provenance gate | Assistant versions source/retrieval date/hash, attribution/notices and explicit rules. Run unchanged baseline/constrained comparison and report all outcomes. Mark approves instructional value, not a required score increase. |
| P1 · Oct 22 · 60–90 min | End-to-end rehearsal and reusable instructor/participant notes; depends on all gates | Mark rehearses transitions and timing; assistant records timings, recovery steps and known failures. Both loops and five takeaways fit three hours. Keep November reuse in mind without expanding scope now. |

If a timebox expires, deliver findings and a smaller next PR. The critical path is baseline → model/runtime fit and dataset exploration → valid isolated evaluation → semantic intervention → rehearsal. Trace UI must remain lightweight; reject candidates that need cloud sign-in, heavyweight services, or overwhelm memory. Pin dependencies and dataset/model artifacts once chosen; startup currently installs unpinned Python dependencies and must be measured rather than assumed reproducible.

## Vocabulary and rights candidates, not selections

- [Getty vocabulary data services](https://www.getty.edu/research-conservation/tools-databases/vocabularies/data-services/) identifies ODC-By 1.0 as its data license. [The license](https://opendatacommons.org/licenses/by/1-0/) permits use/adaptation subject to its conditions, including attribution and notices. A small frozen AAT subset is a candidate for commercial workshop use; retain source URIs, provenance, license link/text and applicable notices. Do not infer that every stored `AAT_URL` is AAT or import a vocabulary in this planning PR.
- [CIDOC CRM 7.1.3](https://cidoc-crm.org/sites/default/files/Documents/cidoc_crm_version_7.1.3.html), whose definition identifies CC BY 4.0, is an optional source for a tiny conceptual model. [Linked Art](https://linked.art/model/index.html) is an optional modeling profile. Neither is selected, required infrastructure, nor Jessica-endorsed.
- [Met Open Access documentation](https://metmuseum.github.io/) describes selected metadata under CC0. Image rights are separate; this exercise uses local metadata and must not assume every linked image is reusable.
- The original repository contains no explicit LICENSE/COPYING/NOTICE in the inspected tree. Preserve its README, attribution and history; Mark reviews permission before broader redistribution. Do not invent a source license or infer one from public availability.

## Review decisions and current status

Mark's review should confirm the two-loop agenda, proposed time budgets and benchmark targets, and prioritize the first baseline-validation PR. Model, telemetry UI, vocabulary subset, exact questions, distribution permissions and budget remain open decisions.

This PR changes documentation only. The repository remains private, Actions disabled, and Pages disabled. No runtime, vocabulary import, participant invitations, spending changes, or workshop delivery claims are made here.
