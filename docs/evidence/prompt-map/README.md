# Paired prompt evaluation

Executed in the managed Linux cloud environment on October 23, 2026
(America/Los_Angeles), starting from workshop commit `e60e0d0`.

| Prompt | Correct | Accuracy | Eval time |
| --- | ---: | ---: | ---: |
| Current, unchanged | 12/20 | 60% | 283.324 seconds |
| Semantic revision | 15/20 | 75% | 351.284 seconds |

The observed change is **+3 correct answers, or +15 percentage points**, with
67.960 additional seconds of evaluation time. Times exclude image builds,
model initialization, reference checks, and scoring.

- Fixed: q03, q08, q09, q15, q19, q20.
- Regressed: q07, q14, q18.
- q16 and q17 remained incorrect.

This is one paired teaching diagnostic, not a reliable performance estimate
across repeated runs or machines. The new prompt was fixed before its run.
No questions, expected answers, scoring rules, model settings, budgets, or
museum data were changed between the two conditions. The comparator checked
that the recorded controls matched exactly. Both runs used the same pinned
Gemma model on CPU, temperature zero, one SQL attempt per question, and the
same frozen rehearsal limits. No OOM events or kills were recorded.

The first condition used the original `improved` prompt from the starting
commit, now copied byte-for-byte into `eval/prompts/current.json`. The second
used `eval/prompts/semantic.json`. Both report manifests retain the internal
stage label `improved`; their filenames and embedded prompt contents identify
the conditions.

Files in this directory:

- `current-report.json` and `semantic-report.json`: scorer outputs with prompt,
  shared controls, per-question outcomes, and elapsed times.
- `comparison.json`: score delta, fixed questions, and regressions.
- `map-violation.json`: fresh checker output rejecting only the intentional
  `missing_text` change from `null_or_blank` to `null_only`.

Full answer and query traces remain in the local ignored directory
`artifacts/map-prompt-comparison/`. They are not included in these score reports.
All 20 reference queries and the rebuilt agent's gold-isolation check passed.
The original database contract tests passed with the inline MAP section added.

Local tests also verified the proposed GitHub comment's failure explanation,
repair/update behavior, markup escaping, and stale-commit handling. These are
simulated GitHub calls. No live Actions run, PR comment, or merge-protection
setting has been verified in this environment.
