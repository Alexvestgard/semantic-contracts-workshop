# From eval scores to a MAP merge gate

This exercise connects prompt semantics to the existing museum data contract:

1. Evaluate the current prompt unchanged.
2. Evaluate a semantics-focused prompt against the same 20 questions.
3. Compare the actual scores and failures.
4. Protect the second prompt with the MAP section in the original data contract.
5. Change the prompt to violate that MAP and open a pull request.
6. Read the failed check and its explanation, then restore the rule.

The failed required check blocks merging. A pull-request comment explains the
violation but cannot block merging on its own. No deployment is involved.

## Files and responsibilities

| File | Role |
| --- | --- |
| `eval/prompts/current.json` | Exact copy of the existing improved prompt at `e60e0d0`; the first evaluation uses this, not the older minimal baseline |
| `eval/prompts/semantic.json` | Second prompt and the editable prompt asset protected by the contract |
| `data_contract_components/contract_definition/object_images_contract_spec.json` | Original database contract, extended with `metadataApplicationProfile` |
| `scripts/check_prompt_map.py` | Checks the prompt and its rendered rules against the approved MAP |
| `eval/prompts/map-violation.json` | Teaching fixture that changes only missing-text semantics |

The original contract's database asset and schema remain intact. Its new
`metadataApplicationProfile` section names the prompt asset, contains the versioned MAP
definitions, field applicability, required values, multiplicity, source references,
and approved free-text instructions.
The existing database detector continues to validate the schema section. The
new checker validates the MAP section. Both checks are needed.

This is a local metadata application profile for the SQL exercise. Linked Art
informs the distinction between an object record, a conceptual work, an image,
and an artwork classification. The profile does not assert that the dataset
conforms to Linked Art or that every collection item is independently classified
as an artwork. For the unchanged questions, it explicitly defines “artwork” as
one object record. No vocabulary download, ontology service, or Cromulent
installation is required. The MAP definitions are local rules; the linked
sources provide context, not machine-verified mappings.

## Run the two evaluations

Start the normal workshop database and wait for seeding to finish. From the
repository root:

```sh
bash scripts/rehearse_map_eval.sh
```

In this managed cloud environment, first source the prepared environment:

```sh
source /workspace/cloud-setup/activate.sh
```

The launcher builds the eval images, initializes the model, verifies reference
answers and isolation, and runs `current` followed by `semantic`. Both use the
same model, schema, questions, order, read-only SQL tool, decoding settings,
frozen time limits, and answer scorer. Only the selected prompt changes.
Both internal manifests use the existing `improved` stage name; their separate
`current/` and `semantic/` directories and saved prompt contents identify the
conditions. Gold answers remain isolated in the scorer.

The comparison reports the score difference, fixed questions, regressions, and
elapsed time. A tie or decline is reported as such. Do not change questions,
expected answers, scoring, budgets, or the first prompt to manufacture an
improvement. The new semantic instructions clarify field meanings, missingness,
object-counting grain, aggregation, and faithful submission of query results;
they contain no expected answers or reference queries.

Evidence is retained in a new `artifacts/map-eval-*` directory. The launcher
then checks the approved prompt, verifies that the intentional violation fails
specifically on `missing_text`, and stops the model. No third inference run is
needed to demonstrate contract enforcement. On an earlier failure, logs remain;
stop only the model with `python3 scripts/sql_eval.py stop` when finished diagnosing.

The first local paired run measured **12/20 → 15/20**, with six fixes and three
regressions. See [the evidence](evidence/prompt-map/README.md) for both reports
and limitations. Participants should report their own observed scores.

## Add the MAP, then demonstrate a violation

The implementation PR introduces the new contract section and the passing
prompt together. A stacked PR can target that implementation branch before it
is merged. Validation runs on every branch push and for every PR target, using that target's MAP as the
approved policy. Branches in the same repository call the comment workflow
directly after validation, so their comments work before installation on `main`.
For fork PRs, the separate `workflow_run` reporter must first reach the default
branch; fork workflows never receive a comment-writing token.

In a participant branch, change the governed prompt:

```sh
cp eval/prompts/map-violation.json eval/prompts/semantic.json
python3 scripts/check_prompt_map.py
```

The command exits 1 and reports:

```text
Rule: missing_text
Expected: "null_or_blank"
Actual: "null_only"
Treat NULL and empty or whitespace-only text as missing. For populated text, use NULLIF(BTRIM(column), '') IS NOT NULL.
```

Commit that prompt change and open a PR. Keep the MAP and contract unchanged.
GitHub's **Prompt MAP contract** check fails and the comment job posts the
explanation. Pushing a repair reruns the check and updates
the existing bot comment instead of adding another one.

To repair the example, restore `semantics.missing_text` to `null_or_blank` in
`eval/prompts/semantic.json`, rerun the checker, and push the corrected prompt.
Passing the MAP check does not replace the original database tests or establish
model accuracy.

## Configure the GitHub merge gate

A repository administrator must configure the target branch after the workflow
has produced its first check:

1. Ensure GitHub Actions is enabled for the repository and the workflows are
   permitted. Fork runs may require maintainer approval.
2. In the target branch ruleset or branch protection, require pull requests and
   the **Prompt MAP contract** status check. Keep the existing database checks
   required too; do not replace other protections.
3. Require review for changes to the contract's MAP section,
   validator, prompt renderer, and workflow files. Restrict bypass authority
   to maintainers who can intentionally approve policy changes.

This PR provides workflow files; their presence does not prove Actions is
active or branch protection is configured. Repository settings and a live
failing PR must be verified before presenting the gate as active.
For a stacked demonstration, target the parent PR branch with a separate ruleset
requiring **Prompt MAP contract** from GitHub Actions. A rule covering only
`main` does not protect a PR targeting another branch. Keep the demo rule scoped
to that exact branch and preserve existing repository protections.

For an established installation, validation uses the base branch's checker,
MAP, and contract section against the proposed prompt. A PR cannot change the
expected value alongside the prompt and silently pass. Changes to approved
MAP policy, validator, or renderer intentionally require a separate maintainer
review and policy rollout. The first installation has no base-branch MAP, so
it validates the candidate and visibly reports bootstrap mode.

The validation job runs with read-only permissions and publishes a bounded JSON
report. A separate comment job has only Actions read and pull-request write
permissions. It performs no checkout, checks that the PR still points to the
evaluated commit, reads report data without executing files from the validation
runner, escapes markup and mentions, and updates only its own marked bot comment.
Same-repository contributors can edit workflow code, so those changes still need
maintainer review. Fork reports run the trusted default-branch workflow; that
workflow skips internal PRs to avoid duplicate comments.
If GitHub supplies no unambiguous PR association, the details remain in the check
summary. Comment failure cannot turn the failed validation check into a pass.

## What this contract proves

The gate checks explicit prompt declarations, the approved instruction text,
and the rule text associated with each declaration. It catches missing rules,
extra settings, free-text instruction changes, and the deliberate missing-text
regression. It is not a natural-language contradiction detector, a proof of
model obedience, or a full Linked Art validator. The two evaluations measure
answer behavior; the merge gate preserves the approved input agreement.

Sources: [Linked Art introduction](https://linked.art/model/intro/),
[required vocabulary](https://linked.art/model/vocab/required/), and the
checked-in museum schema referenced by the original contract's MAP section.
