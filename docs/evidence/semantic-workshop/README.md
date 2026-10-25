# Semantic workshop rehearsal

The two model evaluations were completed from the branch based directly on
main: [recorded pair](../met-two-condition-eval/README.md). The general prompt
scored 10/20 and MAP + Linked Art scored 16/20.

The local contract check passed before the exercise. Removing `Wood-Furniture`
from the governed prompt produced the expected `prompt.instructions` failure,
with the missing label identified in the report. See [pass](local-pass.json)
and [intentional failure](local-fail.json).

The GitHub violation-and-repair phase is being recorded on this PR. The final
record will link both check runs and retain the repaired result. The model
runs used a managed cloud Docker environment with the existing Met database;
this is not a claim that a browser Codespace was provisioned during rehearsal.
