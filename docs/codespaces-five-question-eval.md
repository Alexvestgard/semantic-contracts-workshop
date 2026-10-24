# Run the 20-question eval in Codespaces

Use branch `codex/five-question-codespaces`. The branch name is unchanged, but its
default now runs all 20 questions with the improved prompt, matching the latest
local rehearsal. Use a four-core, 16 GB Codespace and wait for workshop startup
and museum data loading to finish. Rebuild an existing devcontainer if it predates
the Docker setup changes on this branch.

From the repository root, run:

```sh
bash scripts/rehearse_sql_eval.sh
```

The script builds the eval images, starts the CPU model, validates all 20 reference
queries and agent isolation, runs q01–q20 once with the improved prompt, and scores
the answers. It then restores and protects the improved prompt and stops only the
model. The existing database and downloaded model cache are retained.

Each question receives the schema and SQL rules up front. It gets one SQL attempt
and, if the query succeeds, one final-answer response. There are no retries.
There are no pilot questions or baseline/regressed stages in this command.

The script copies `eval/rehearsal-budget.json` into a new
`artifacts/sql-eval-twenty-*` directory. It uses the same execution limits as the
completed local run: one SQL call, 271 seconds per question and per request,
384 output tokens, and 20 result rows. The pinned model uses a 4,096-token context
and four CPU threads. Historical pilot outcomes are not copied into this budget.

The terminal prints progress, the final score, elapsed eval time, and the evidence
path. That directory retains `improved/` answers and traces, `reports/improved.json`,
the budget, and a log for each step. A failure stops later steps and preserves
partial evidence. Do not change the model, prompts, question selection, data, or
limits during a run.

If a step fails after model startup, stop the model when finished inspecting it:

```sh
python3 scripts/sql_eval.py stop
```

The first model download is about 4.09 GB. The completed local ARM64 Docker Desktop
CPU run scored 10/20 in 18 minutes 31 seconds: seven SQL errors and three wrong
answers. About 70% of inference time was prompt processing. These are local
measurements. Mark's subsequent Codespaces run scored 13/20 in 516.5 seconds. See
[the result record](codespaces-eval-results.md) for evidence and remaining resource
acceptance checks.

If startup fails, keep `start.log` and the printed evidence directory. Local
Docker Desktop encountered a Compose dependency-discovery error. With multiple
workshop databases, set `SQL_EVAL_DB_CONTAINER` to the intended existing container.
See [the evaluation guide](sql-eval.md) for individual commands and the separate
three-stage teaching sequence.
