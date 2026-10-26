# Semantic workshop rehearsal

The two model evaluations were completed from the new branch based directly on
main. [The recorded pair](../met-two-condition-eval/README.md) scored 10/20 for
the general prompt and 16/20 for prompt + MAP + Linked Art. All 20 reference
queries matched the checked-in source data, and the agent isolation check passed.

## Violation and repair

1. The [local check passed](local-pass.json) on the approved category prompt.
2. Removing only `Wood-Furniture` produced the [expected local failure](local-fail.json).
3. Commit [`34982dd`](https://github.com/onthemarkdata/semantic-contracts-workshop/commit/34982ddadc34774460c7fa6af8750c98f71be482)
   produced a [failed GitHub MAP run](https://github.com/onthemarkdata/semantic-contracts-workshop/actions/runs/40156602633)
   and a bot comment on PR #28. The rule was `prompt.instructions`; the report
   identified `Wood-Furniture` as the missing mapped label. The
   [SQL fixture run also failed](https://github.com/onthemarkdata/semantic-contracts-workshop/actions/runs/40156602471).
4. The builder restored the prompt from the unchanged contract and pinned source.
   The restored prompt matches the approved base byte-for-byte, and the
   [local repaired check passes](local-repaired.json).
5. Repair commit [`484e3a5`](https://github.com/onthemarkdata/semantic-contracts-workshop/commit/484e3a57d0981d588f219b6c83c890a665ee4bc8)
   passed the [GitHub MAP run](https://github.com/onthemarkdata/semantic-contracts-workshop/actions/runs/40156764660).
   The bot updated its comment to **Prompt MAP: PASS**. The
   [captured repaired comment](github-repaired-comment.json) and
   [repaired-run record](github-repaired-run.json) preserve that result.

The [captured failed bot comment](github-fail-comment.json) and
[failed-run record](github-fail-run.json) preserve the failure. The live
[PR comment](https://github.com/onthemarkdata/semantic-contracts-workshop/pull/28#issuecomment-6392729573)
updates when the repaired commit is checked; it is not a permanent failed-state snapshot.

The [source-derived membership comparison](membership-impact.json) shows why this
is a semantic violation: the shortened mapping selects 22 furniture objects
instead of 23, excluding object 314034, *Lupona (royal seat)*. These are deterministic
source counts, not additional model evaluations. The database was unchanged.

## Rehearsal environment

The model and local checks ran in managed cloud Docker against the already
prepared Met database. No new browser Codespace was provisioned. GitHub Actions
runs the real PR checks, while the appended README explains the corresponding
manual Codespaces setup and workflow.

The original README is preserved byte-for-byte as a prefix. The workshop PR
restores the prompt, so its final changes relative to the evaluation PR are
only documentation and recorded evidence. The failure commit and repair remain
in GitHub history. A failed check blocks merging only where branch rules require it.
