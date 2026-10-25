# From category evals to a MAP check in GitHub

The current workshop runs exactly two conditions on ten basic and ten medium
Met questions: the existing general prompt, then the prompt with the category
MAP and six local Linked Art definitions. Follow the manual
[Part 2 walkthrough](../README.md#-part-2-implementing-semantic-contracts-with-metadata-application-profiles).

| File | Role |
| --- | --- |
| `eval/category-comparison/questions.json` | Current 20-question set |
| `eval/category-comparison/prompt-only.json` | General prompt, with no category mapping |
| `eval/category-comparison/prompt-map-linked-art.json` | Governed category prompt |
| `data_contract_components/contract_definition/object_images_contract_spec.json` | Original contract; `museum-met-categories-map-linked-art` is in `metadataApplicationProfile.additionalProfiles` |
| `vendor/linked-art/guidance/` | Pinned source definitions, provenance, and license |
| `scripts/build_category_eval.py` | Generate/check fixtures and restore the approved prompt |
| `scripts/run_category_eval.py` | Run the two conditions with frozen inputs and separate scoring |
| `scripts/check_prompt_map.py` | Check the original and category prompt profiles |

Use the existing prepared database. The runner's `--verify-gold` mode checks
reference SQL without inference. A normal run needs a new `--out` directory:

```bash
python3 scripts/build_category_eval.py --check
python3 scripts/run_category_eval.py --verify-gold
python3 scripts/run_category_eval.py --out artifacts/new-category-pair
```

The full walkthrough covers building images, starting the local CPU model,
checking isolation, stopping the model, and reviewing the two score reports.
[Recorded results](evidence/met-two-condition-eval/README.md) show 10/20 for the
general prompt and 16/20 for MAP + Linked Art. This is a single teaching run;
record all regressions as well as improvements.

For the contract exercise, remove only the quoted `Wood-Furniture` label from
the category prompt's instructions. Keep the MAP unchanged. The check fails on
`prompt.instructions` and identifies the missing mapped label. Push the edit to
a PR whose base already contains the approved category MAP. After inspecting
the failed check and bot comment, run `python3 scripts/build_category_eval.py`,
verify the restored prompt, and push the repair. No third evaluation is needed.

The base branch owns policy. Editing the contract and prompt together triggers
policy review rather than silently approving a changed meaning. A failing check
blocks merging only where branch rules require it. The comment explains the
result; it does not itself block merging. Branch-protection configuration is
outside this walkthrough.

The [end-to-end rehearsal record](evidence/semantic-workshop/README.md) links the
failed and repaired GitHub runs. The earlier missing-text workflow and its
reports remain historical material; its scripts are not the current workshop
entry point. The original database exercise remains unchanged.
