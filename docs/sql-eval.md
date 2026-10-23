# Museum SQL evaluation

This exercise uses the existing museum sample and Gemma 4 E2B Q4_K_M in Docker
Model Runner. It teaches a five-step sequence:

1. Run a baseline prompt on five questions.
2. Improve the prompt and run the same evaluation.
3. Make a plausible prompt change and use the evaluation to detect a regression.
4. Restore the exact improved prompt without another evaluation.
5. Protect the restored prompt with semantic contracts, without another evaluation.

The three scored stages produce 15 attempts. This branch selects q01–q05 through
`eval/question-set.json`: total artworks, populated artist names, missing artist
names, public-domain artworks, and populated image URLs. The full 20-question bank
and reference answers remain unchanged. The desired improvement and regression
are rehearsal goals, not guaranteed scores. Retain every result, including no change.
The question set is a teaching diagnostic, not a general model benchmark.

The local ARM64 rehearsal took about 49 minutes for these five questions across
all three prompts, plus nine minutes for pilots and additional setup time.
Codespaces timing is unmeasured. Reducing the question count does not fix the
observed schema loops or guarantee the intended score pattern.

For a copyable command sequence, see [the five-question Codespaces run](codespaces-five-question-eval.md).

## Setup in Codespaces

Use the configured four-core, 16 GB Codespace, Docker Engine with Compose 2.20+
and Python 3. The host commands use only Python's standard library. Dependencies
are installed inside the eval images. First startup downloads the pinned model
(about 4.09 GB); no Hugging Face account, API key, or hosted inference is needed.

Rebuild an existing devcontainer after checking out this change. Its Docker feature
installs the Compose CLI, and `SQL_EVAL_HOST_ROOT` maps workspace mounts to the Docker
host's paths. This follows the [Dev Containers guidance for host Docker access](https://github.com/devcontainers/features/tree/main/src/docker-outside-of-docker#supporting-bind-mounts-from-the-workspace-folder).
Keep artifacts inside the repository when running from the devcontainer. The runner
uses the caller's non-root UID; when the terminal runs as root, it grants UID 1000
ownership of the result directory and runs the agent as that user.

Wait for the normal workshop startup to finish loading the museum data, then run
these commands from the repository root:

```sh
python scripts/sql_eval.py build
python scripts/sql_eval.py start
python scripts/sql_eval.py verify-gold
python scripts/sql_eval.py isolation
```

The eval uses the workshop's existing `postgres` database. `start` grants the
`eval_reader` account SELECT access to its eight museum tables, connects the database
container to the internal eval network, and waits for the model's `READY` inference
probe. It does not seed data or create another database or database volume.

When exactly one workshop PostgreSQL container is running, it is selected
automatically. If several are running, set `SQL_EVAL_DB_CONTAINER` to the intended
container name before running `start`. `python scripts/sql_eval.py prepare-db`
performs only the database access setup, without starting the model.
Keep the model volume when stopping containers to retain its cache.

Docker Desktop may hide the pinned runner from Compose dependency discovery; the
known limitation and native Linux target are recorded in [model setup](model-runner.md).
The Codespaces walkthrough must be checked on native AMD64 before workshop acceptance.

## Time pilots, then freeze the limits

Three separate pilot questions establish a starting tool/time budget. They are
excluded from the five scored questions. Run the improved prompt for the pilot:

```sh
python scripts/sql_eval.py pilot --stage improved
python scripts/sql_eval.py freeze
```

Freezing requires a completed pilot run, including any failed attempts. It records
the outcome counts, sets the tool limit to the observed maximum plus three (at least
six), and sets the question timeout to 1.5 times the slowest pilot (at least 60 seconds). Inspect
the pilot traces before accepting those limits. Timeouts and invalid SQL are useful
failures; a perfect pilot is not required. Submission is not a correctness check.
Limits are identical for all three scored runs.

The initial pilot allows 12 database calls, 180 seconds per question, and a
45-second request timeout. These are provisional limits, not measured performance.
The agent gets at most the tool-call limit plus four model turns, so invalid
responses cannot create an unbounded retry loop. Each SQL statement has a two-second
database timeout. Tool output is bounded to 20 rows and recent context is bounded.
The model response uses a JSON schema that permits one schema, query, or final
action. The application validates the action again before executing a tool.

## Run the three scored stages

```sh
python scripts/sql_eval.py run --stage baseline
python scripts/sql_eval.py score --stage baseline

python scripts/sql_eval.py run --stage improved
python scripts/sql_eval.py score --stage improved

python scripts/sql_eval.py run --stage regressed
python scripts/sql_eval.py score --stage regressed

python scripts/sql_eval.py compare
```

The runner exits before the scorer starts. A host lock prevents the normal score
command from running while that stage's agent process is active. Incomplete runs
are never scored. Existing output directories are not overwritten; use
`--artifacts /path/to/new-run` on every command for another rehearsal.

Read `artifacts/sql-eval/comparison.md` for scores and changed questions. Each stage
has a manifest and one JSON trace per question: visible model response, action,
tool result/error, token usage, submitted answer rows, tool count, and elapsed time.
SQL remains in query-tool traces. No hidden reasoning is requested. Reports show
timeouts, invalid answers, and wrong results; query errors remain in the traces.

All stages use fresh question contexts and the same model configuration, question
order, decoding settings, and budget. These settings are recorded as readable values
and compared directly. Keep the eval code and workshop data unchanged through
all three runs; the eval does not fingerprint the database. The separate
`verify-gold` setup check confirms that reference queries agree with the expected
answers, but does not detect every possible data change. Scoring reads saved
answers and expected values without querying the database or calling a model.
The comparison command rejects differing
recorded controls. Temperature is zero; this does not
guarantee deterministic CPU inference. Repeat paired questions before drawing a
strong conclusion from a small score difference.

## Restore and protect without another eval

```sh
python scripts/sql_eval.py revert
python scripts/sql_eval.py protect
```

`revert` copies the improved prompt byte for byte to `active-prompt.json`. `protect`
checks its declarations against `eval/prompt-contract.json` and writes a contract
check record. Neither command starts Docker, calls Gemma, or invokes the scorer.

To demonstrate a rejected prompt edit without model inference:

```sh
python scripts/sql_eval.py protect --prompt eval/prompts/regressed.json
```

This command must fail. The contract requires blank-aware missing-text semantics,
joins/counts at the object-ID grain, an explicit public-domain flag, and the
question's requested columns/order. The regression changes only the missing-text
setting to a common SQL shortcut: treating `IS NOT NULL` as “populated.” The improved
prompt uses `NULLIF(BTRIM(column), '')` because the dataset contains blank strings.

The semantic choices are typed declarations rendered into prompt sentences. The
contract validates those declarations and compares the instructions directly with
the approved text to block an unchecked contradictory edit. It does not infer the
meaning of arbitrary rewrites or prove that Gemma obeys the rules. Review intentional
instruction changes before updating the approved text. No contract-stage accuracy gain is claimed.

## Questions and scoring

`eval/questions.json` retains ten basic and ten intermediate questions; this branch
selects the first five basic questions for every scored stage. The full bank covers
counts, missing text, public-domain flags, departments, sorting, distinct values,
and joins. Every question specifies its result shape; ambiguous requirements are
avoided in this first SQL-only exercise. Column comments remain available through
the schema tool in every stage.

The agent submits result values in a final action. For example, a count of 42 is
`{"action":"final","rows":[[42]]}`. Multiple columns occupy one row in the order the
question requests; multiple results occupy separate rows. Do not include column
headers. Use `[]` for no results and JSON `null` for SQL NULL.

The scorer compares submitted rows directly with source-derived expected rows.
This check is deterministic for the same answer files and expected values; it
executes no submitted SQL and uses no model judge. It preserves duplicates, NULLs,
and column positions, and enforces row order when requested. Numeric values such
as `1` and `1.0` compare equally; text `"1"` and boolean `true` do not equal numeric
`1`. The current cases return text and integer counts; there is no floating-point
tolerance rule. A correct query in a trace cannot compensate for an incorrect
submitted answer. Missing or malformed rows receive `invalid_answer`.

Older runs that submitted SQL must be rerun with this answer format. Preserve
those traces as historical evidence; do not convert them into model answers.

Reference SQL and expected results live in `eval/gold/answers.json`. Expected results
were calculated independently from the checked-in JSON, then checked against all
20 reference queries in PostgreSQL. Keep these answers unchanged across the three
scored stages; the eval does not record or compare hashes of the gold file.
`scripts/build_sql_eval_fixtures.py` reproduces the draft fixtures; run it only before
freezing a comparison because it rewrites questions, answers, and prompt versions.
Preserve the repository's museum attribution and source history; no images or live
Met API data are downloaded.

## Isolation and tests

The agent image copies only its runtime, public questions, prompts, and model lock.
It has no gold, scorer, repository mount, Docker socket, file tool, or shell tool.
It runs as a non-root user with a read-only root filesystem on an internal network.
The database role grants SELECT only; the SQL parser rejects writes, multiple
statements, non-museum tables, row locks, and functions outside a small allowlist.
Only the controlled schema tool queries catalog metadata.

The eval requirements are `psycopg[binary]`, already used by the workshop, and
SQLGlot 30.24.0 for SQL parsing. SQLGlot uses the
[MIT license](https://github.com/tobymao/sqlglot/blob/v30.24.0/LICENSE).

The scorer image contains gold and reads completed answers. Gold is never loaded
into the agent process or database. The isolation check scans the actual agent image
for a gold-only sentinel. This protects answers from the agent, not from a participant
who administers the Codespace and can inspect the repository or Docker images.

For local unit tests, use Python 3.12+ and an isolated environment:

```sh
python -m venv .venv
.venv/bin/pip install -r eval/requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

The database integration tests additionally require `EVAL_TEST_DSN` pointing to the
seeded workshop database with the `eval_reader` role. They check real role
permissions, server timeouts, row limits, and absence of gold tables without
changing museum data. CI uses the normal workshop startup in its own Compose
project before running these checks.

## Review and acceptance

The implementation follows Mark's ten-question interview and approved five-stage
sequence. The 10/10 difficulty split, specific questions, prompt versions, and typed
contract mechanism are implementation proposals for review. Model smoke tests are
already recorded in `model-runner.md`; full Codespaces timing and the desired score
sequence require measured rehearsal evidence. See [the validation record](sql-eval-validation.md).
