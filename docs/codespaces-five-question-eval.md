# Run five questions in Codespaces

Create a four-core, 16 GB Codespace from `codex/five-question-codespaces`. This
branch includes the evaluation stack from PR #7. If you switch an existing
Codespace to this branch, rebuild its devcontainer before running the evaluation.
Wait for the normal workshop startup and museum data loading to finish.

From the repository root, run:

```sh
bash scripts/rehearse_sql_eval.sh
```

The script builds the isolated images, starts the model, checks all 20 reference
queries and agent isolation, runs three separate pilots, freezes limits, and runs
q01–q05 for each prompt: baseline, improved, and regressed. It then compares the
15 scored attempts, restores the improved prompt, and checks its contract.

Each invocation creates a new `artifacts/sql-eval-five-*` directory and prints its
path. Logs and partial results are retained if a step fails; later steps stop.
Do not change the question selection, prompts, model, data, or limits during a run.
The script leaves the model available for inspection after success or failure.

For the final rejection demonstration, substitute the printed directory below:

```sh
python3 scripts/sql_eval.py protect --prompt eval/prompts/regressed.json --artifacts artifacts/sql-eval-five-XXXXXX
```

Expect exit 1 with `Prompt contract failed: missing_text`. This is a declared
semantic-rule check; it does not demonstrate model accuracy.

When finished, stop the model and keep its downloaded cache:

```sh
docker compose -p workshop-sql-eval -f compose.models.yaml -f compose.eval.yaml stop model-runner
```

The first model download is about 4.09 GB. In the completed local ARM64 run, these
five questions took about 49 minutes across all three prompts, plus nine minutes
for pilots and additional setup time. Codespaces performance has not been measured.
The local full run did not show the intended improvement/regression pattern;
retain whatever scores this run produces.

If `start` fails, keep `start.log` and the printed evidence directory. The local
Docker Desktop run encountered a Compose dependency-discovery error; native
Codespaces startup remains an acceptance check. With multiple workshop databases,
set `SQL_EVAL_DB_CONTAINER` to the intended existing container before starting.
See [the evaluation guide](sql-eval.md) for individual commands and constraints.
