# Codespaces rehearsal result — 23 October 2026

Mark supplied the terminal output from running `bash scripts/rehearse_sql_eval.sh`
on `codex/five-question-codespaces` in a new Codespace. The transcript records a
completed improved-prompt run of all 20 questions, followed by scoring, prompt
restoration, contract validation, and model shutdown.

| Run | Correct | Eval time | SQL errors | Incorrect submitted answers |
| --- | ---: | ---: | ---: | ---: |
| Local ARM64 Docker Desktop CPU | 10/20 | 1,110.9 seconds | 7 | 3 |
| Mark's Codespaces CPU run | 13/20 | 516.5 seconds | 5 | 2 |

Times exclude image builds, model startup, preflight checks, and scoring. These are
individual observations, not evidence of a reliable accuracy difference between
machines. Both runs used the schema-first, one-query/one-final-answer procedure.

The Codespaces transcript shows:

- All 20 reference queries matched the independent expected values.
- Agent isolation passed: no gold answers, scorer, repository mount, or Docker socket.
- Every question used one SQL attempt; no retries or timeouts were reported.
- q03, q08, q17, q19, and q20 ended with `query_error`.
- The scorer returned 13/20 correct. Of the 15 submitted answers, two were incorrect;
  the terminal summary does not identify those two questions.
- Prompt restoration was byte-exact, the contract check passed, and the model stopped.

The terminal ended with:

```text
improved: 13/20
Restored improved prompt exactly. No model or scorer was invoked.
Prompt contract passed. No model or scorer was invoked.
Result: 13/20 correct in 516.5 seconds.
```

The full scores and traces remain in Mark's Codespace at
`/workspaces/semantic-contracts-workshop/artifacts/sql-eval-twenty-tH5MgV`.
This record summarizes his supplied transcript; those artifacts have not been
independently fetched. The transcript does not include machine allocation or
memory/OOM counters, so it does not verify the 16 GB resource acceptance checks.
The baseline/improved/regressed teaching sequence also remains unverified.

Local validation before publication: 43 tests passed, including six PostgreSQL
integration checks and launcher success/failure coverage. Shell syntax and
`git diff --check` passed. The local run recorded no OOM events.
