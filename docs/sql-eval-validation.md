# SQL eval validation

The evaluation harness is implemented and locally tested. Workshop acceptance still
requires the three scored runs in a fresh four-core, 16 GB Codespace. No baseline,
improvement, or regression score is claimed in this record.

## PR #9 database simplification

The eval now uses the existing workshop PostgreSQL database through `eval_reader`.
The separate database, seed service, migration dependencies, and database
fingerprinting were removed. No museum data was reloaded for this check.
SQLGlot 30.24.0 (MIT) replaces pglast (GPL-3.0-or-later) as the SQL parser.

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

The source JSON hash is
`10eae3d1e7d8186e24dae68b4c783a7f5f841317f37ec9eb64ebf20527fd80cb`.
The original isolated-database pilot recorded this database fingerprint (the current
implementation reuses the workshop database and no longer calculates it):
`3ca6d0b4f5ddea133f598b715587e6ebdd38468b2672353b96a414a72ea627fd`.

## Pilot evidence

Pilots use separate questions and do not count toward the 60 scored attempts.
Earlier local pilots exposed malformed JSON actions, repeated schema guesses,
invalid SQL, and timeouts. The final shared setup constrains the JSON action format
and exposes table and column names through the schema tool. Model mistakes remain
in the traces; correct answers are not required to freeze a pilot budget.

The [manifest](evidence/sql-eval-local-pilot/manifest.json) records the local
setup before the PR #9 database simplification, using the improved prompt.
These are timing pilots, not baseline scores. The captured files are retained
unchanged as historical evidence.

| Pilot trace | Outcome | Database calls | Seconds |
| --- | --- | ---: | ---: |
| [Three largest object IDs](evidence/sql-eval-local-pilot/p01.json) | Timeout | 9 | 180.016 |
| [Musical Instruments count](evidence/sql-eval-local-pilot/p02.json) | Submitted SQL | 6 | 139.928 |
| [First three Asian Art artworks](evidence/sql-eval-local-pilot/p03.json) | Timeout | 10 | 180.007 |

The [derived local budget](evidence/sql-eval-local-pilot/budget.json) allows 13
database calls and 271 seconds per question. Its worst-case question time across
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
