# Two-condition Met category evaluation

This is one fresh run of each condition on the same 20 questions: ten unchanged basic questions and ten medium category questions. The database and runtime were unchanged. No prompt or question was revised after inference began.

| Condition | Basic | Medium | Total | Seconds |
| --- | ---: | ---: | ---: | ---: |
| prompt-only | 9/10 | 1/10 | 10/20 | 132.018 |
| prompt-map-linked-art | 7/10 | 9/10 | 16/20 | 285.865 |

The second condition adds the local MAP and six pinned Linked Art definitions together. This measures their combined effect; it does not isolate the contribution of Linked Art from the MAP. Extra context does not guarantee improvement.

## Per-question results

| Question | Group | Prompt only | + MAP + Linked Art |
| --- | --- | --- | --- |
| q01 | Basic | pass | query_error |
| q02 | Basic | pass | pass |
| q03 | Basic | pass | pass |
| q04 | Basic | pass | pass |
| q05 | Basic | pass | pass |
| q06 | Basic | pass | pass |
| q07 | Basic | query_error | query_error |
| q08 | Basic | pass | query_error |
| q09 | Basic | pass | pass |
| q10 | Basic | pass | pass |
| q11 | Sculpture | wrong answer | pass |
| q12 | Painting | query_error | pass |
| q13 | Drawing | wrong answer | pass |
| q14 | Print | query_error | query_error |
| q15 | Furniture | query_error | pass |
| q16 | Architectural objects | wrong answer | pass |
| q17 | Sculpture | wrong answer | pass |
| q18 | Architectural objects | wrong answer | pass |
| q19 | Painting | pass | pass |
| q20 | Furniture | wrong answer | pass |

## Changes between conditions

- **prompt-only → prompt-map-linked-art**: fixed q11, q12, q13, q15, q16, q17, q18, q20; regressed q01, q08.

## Evidence and limits

- [Machine-readable comparison](comparison.json), [input hashes](input-hashes.json), and [source/runtime provenance](provenance.json).
- [Prompt-only report](prompt-only-report.json), [MAP report](prompt-map-report.json), and [Linked Art report](prompt-map-linked-art-report.json) retain the complete controls and prompts.
- [Question details](question-details.json) include generated SQL, database observations, submitted answers, reference answers, errors, token usage, and elapsed time. This evidence is produced after inference and is never mounted into the agent.
- All 20 reference queries agreed with answers independently computed from the checked-in source JSON. Gold remained in the separate scorer.
- All recorded controls match across conditions. The fixed order was prompt only, then MAP plus Linked Art. Startup and prompt-cache effects can influence elapsed time.
- Condition names come from report filenames. The existing harness records `stage: improved` for both because each run supplies an explicit prompt file.
- One run per condition, with temperature zero, is a teaching diagnostic. It does not establish a statistically reliable gain or guarantee deterministic inference.
- Compare these two runs with each other; totals from different question sets are not directly comparable. No collection-interoperability or full Linked Art conformance claim is made.
- Full raw response traces remain in the ignored local `artifacts/two-condition-eval/` directory. The published question details preserve the SQL and answer evidence needed to inspect the outcomes.

Run: `python3 scripts/run_category_eval.py --out artifacts/new-two-condition-run` after preparing the existing workshop environment.
