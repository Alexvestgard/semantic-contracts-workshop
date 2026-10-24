# SQL eval validation

> Update, 23 October: the improved-only 20-question Codespaces rehearsal completed
> with 13/20 correct in 516.5 seconds. See [the current result record](codespaces-eval-results.md).
> The sections below preserve earlier validation history; their pending-rehearsal
> statements predate this run. Three-stage and resource acceptance remain open.

The evaluation harness is implemented and locally tested. Workshop acceptance still
requires the three scored runs in a fresh four-core, 16 GB Codespace. No baseline,
improvement, or regression score is claimed in this record.

## Result-value submissions

The questions and expected values are unchanged. The agent now submits answer
rows, and scoring compares those values directly without database or model calls.
Reference-query validation remains a separate setup check. The pilot traces below
predate this answer format and are retained unchanged; new model runs are required
to evaluate it.

Validation: 30 unit checks and five database integration checks passed. All 20
reference queries still match the unchanged expected values. The rebuilt scorer
ran twice with networking disabled and no database configuration; its reports
were byte-identical. Controlled fixtures scored 20/20, then 18/20 after one wrong
value and one malformed answer. These are harness checks, not Gemma scores.
The rebuilt agent image also passed the gold-isolation check.

## PR #9 database simplification

The eval now uses the existing workshop PostgreSQL database through `eval_reader`.
The separate database, seed service, migration dependencies, and database
fingerprinting were removed. No museum data was reloaded for this check.
SQLGlot 30.24.0 (MIT) replaces pglast (GPL-3.0-or-later) as the SQL parser.
The eval records settings and prompt text directly. SHA fields and hash checks
were removed from run metadata, reports, budgets, and prompt protection.

Validation on ARM64 Docker Desktop: 28 unit checks passed, all five database
integration checks passed against the running workshop database, and all 20
reference queries matched the source-derived answers. The rebuilt agent image
passed the gold-isolation check. Compose setup and the repository configuration
check passed. Native Codespaces rehearsal remains open.

## Local checks on 22 October 2026

The host was ARM64 Docker Desktop. The pinned runner used four CPU cores and a
6 GiB memory limit. This is not a native AMD64 Codespaces performance measurement.

| Check | Result |
| --- | --- |
| Unit checks | 26 passed; five database checks skipped in this invocation |
| Database integration checks | All five passed separately in PostgreSQL 17 |
| Reference answers | All 20 reference queries matched independently calculated source answers |
| Scorer failure detection | Controlled fixtures scored 20/20, then 18/20 after one wrong result and one forbidden query; these are test fixtures, not Gemma scores |
| Image isolation | Agent image excludes gold sentinel, scorer, repository mount, and Docker socket |
| Agent permissions | Image defaults to UID 1000; read-only database role blocks writes independently of the SQL parser |
| Prompt restore | Restored improved prompt byte for byte, without model or scorer calls |
| Prompt protection | Restored prompt passed; regressed missing-text setting and unapproved free-text edits failed |
| Fixture reproduction | Regenerated JSON files were byte-identical |
| Configuration | Compose validation and repository development checks passed |
| GitHub CI on implementation commit `d2932af` | SQL eval checks and both existing Docker Image CI jobs passed |

## Pilot evidence

Pilots use separate questions and do not count toward the 60 scored attempts.
Earlier local pilots exposed malformed JSON actions, repeated schema guesses,
invalid SQL, and timeouts. The final shared setup constrains the JSON action format
and exposes table and column names through the schema tool. Model mistakes remain
in the traces; correct answers are not required to freeze a pilot budget.

The traces below record the local setup before the PR #9 simplification, using
the improved prompt. These are timing pilots, not baseline scores. The three
traces are retained unchanged; metadata files from the old format are excluded.

| Pilot trace | Outcome | Database calls | Seconds |
| --- | --- | ---: | ---: |
| [Three largest object IDs](evidence/sql-eval-local-pilot/p01.json) | Timeout | 9 | 180.016 |
| [Musical Instruments count](evidence/sql-eval-local-pilot/p02.json) | Submitted SQL | 6 | 139.928 |
| [First three Asian Art artworks](evidence/sql-eval-local-pilot/p03.json) | Timeout | 10 | 180.007 |

The budget derived from those pilots allowed 13 database calls and 271 seconds
per question. Its worst-case question time across
60 attempts is 4 hours 31 minutes, so it does not establish that the exercise fits
the three-hour workshop. Repeat these pilots
in Codespaces before selecting its limits. A local timing budget is not a workshop
timing claim.

## Remaining acceptance checks

1. Rebuild the devcontainer in a fresh four-core, 16 GB Codespace. Check Docker
   Compose, workspace mounts, non-root result writes, cold startup, and warm startup.
2. Run the separate pilots, inspect their traces, and freeze a shared budget.
3. Run all 20 questions for each of the three prompt versions, preserving failures.
   Compare scores and changed questions. If the intended pattern is absent, record
   that outcome and revise the teaching proposal without altering the scores.
4. Restore and protect the improved prompt without another eval. Check that the
   full exercise fits the workshop time budget and has adequate memory headroom.

The AI Agent's GitHub credentials lack Codespaces access, so native rehearsal could
not be performed from this session. Mark's earlier Codespaces smoke test confirms
basic Gemma inference; it does not validate the new agent workload. The typed prompt
contract protects declared requirements and approved instructions. It does not
prove that the model follows them.
