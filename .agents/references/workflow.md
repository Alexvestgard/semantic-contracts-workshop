# Work and continuity

Keep work scoped to the agreed workshop development task. Read the relevant code
and workshop plan, preserve existing changes, and implement and verify the outcome.
These development instructions do not impose tools or accounts on participants.

## Changes and review

Use an isolated Git worktree for each workstream, a focused `codex/` branch,
and a PR for Mark to review and merge. Keep the shared checkout free of task edits. Keep separate
workstreams in separate PRs; link dependencies when stacking changes. Commit and
push checked, agreed work without a separate approval round. Do not merge for Mark.

Use the verified `otmd-ai-agent` identity for GitHub work. Before committing,
check effective author and committer attribution, the agent's GitHub noreply
address, signing key/format, and signing policy. Authentication and signing are
separate checks. If required identity or signing is unavailable, leave the work
reviewable and report the blocker; never switch to Mark's credentials, export
private keys, disable signing, or weaken SSH host checks. Credentials stay in
1Password; do not store machine-specific sockets or keys in this repository.

PRs should explain the resulting behavior, verification, limitations, and related
task. Ask before other publishing or messaging unless already authorized. A
policy copied from HQ does not itself authorize sending Slack messages.

## Task continuity

For coordinated OTMD work, reuse the relevant task in the private
[OpenAI Codex Dot Asana project](https://app.asana.com/0/1219127286179178/list).
Use the verified `ai-agent@onthemarkdata.com` identity and assignee; do not create
duplicates or invent deadlines. Keep outcome, next step, acceptance checks, and
links in the description; record evidence and decisions in progress comments.
Mark's pending review is **Waiting on Mark**; complete tasks only when all their
acceptance checks pass. Access to a board does not expand the agreed task.

The [Kata skill](../skills/kata/SKILL.md) provides optional local continuity when
that is useful. Use only this workshop's wrapper and instance, and link related
records rather than maintaining duplicate task lists. Kata initialization is a
developer choice, not a prerequisite for code changes or participant exercises.
If tracking is unavailable, leave a concrete handoff in the PR or chat.

No task sync, merge monitor, or messaging automation is installed by this setup.
Verify any separately configured automation before relying on it.

## Verification and private state

Run relevant checks and `git diff --check`. Include actual evidence and remaining
work in the handoff; do not equate one merged PR with completion of a larger task.
Keep local state in `.kata/local/` and private working files in `data/private/`,
both ignored. Never put secrets in task records, snapshots, Git, or chat.
