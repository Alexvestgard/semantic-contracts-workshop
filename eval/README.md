# Gemma analytics exercise

Use Gemma in Docker to answer 20 questions about the checked-in museum data.
The agent inspects the existing workshop database, runs read-only SQL queries,
and submits result values. A separate scorer compares those values with fixed
expected answers. Scoring is deterministic; model responses can vary between runs.

## Exercise sequence

1. Run the baseline prompt and score its answers.
2. Improve the prompt and score the same questions.
3. Change the prompt and check for a regression.
4. Restore the improved prompt without another eval.
5. Protect the restored prompt with semantic contracts, without another eval.

Keep the questions, data, model, and run limits fixed during the three scored
stages. Preserve errors and wrong answers. Improvement and regression are teaching
goals, not guaranteed outcomes.

## Start here

Use the configured four-core, 16 GB GitHub Codespace and wait for the workshop
database to finish loading. Gemma runs in Docker Model Runner; no hosted inference
account or API key is required. Run exercise commands from the repository root.

- [Setup and exercise commands](../docs/sql-eval.md): build the containers, time
  the pilots, freeze shared limits, run and score each stage, then restore and protect.
- [The 20 questions](../docs/sql-eval-questions.md): ten basic and ten intermediate
  analytics questions.
- [Model setup](../docs/model-runner.md): the pinned model, resource requirements,
  and Docker details.
- [Validation and remaining checks](../docs/sql-eval-validation.md): local evidence
  and the Codespaces rehearsal still needed before workshop acceptance.

## Read the results

Each question produces a trace containing model responses, database actions,
observations, errors, and the submitted answer rows. The comparison report shows
scores and which answers changed between prompt stages. A correct SQL query in a
trace does not earn credit if the submitted values are wrong.

Expected answers are excluded from the agent image. Scoring runs after the agent
exits and makes no database queries or model calls. Reference SQL is used only by
the separate setup check that validates expected answers against the workshop data.

For the original database/data-contract exercise and museum source attribution,
see the [repository README](../README.md).
