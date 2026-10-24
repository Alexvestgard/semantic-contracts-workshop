#!/usr/bin/env bash
# Two scored runs, then deterministic prompt protection. No regression inference.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts
run_dir=$(mktemp -d "$PWD/artifacts/map-eval-XXXXXX")
echo "Evidence: $run_dir"
run_step() {
  local label=$1
  shift
  "$@" 2>&1 | tee "$run_dir/$label.log"
}
run_step build python3 scripts/sql_eval.py build
run_step start python3 scripts/sql_eval.py start
run_step verify-gold python3 scripts/sql_eval.py verify-gold
run_step isolation python3 scripts/sql_eval.py isolation
for stage in current semantic; do
  mkdir "$run_dir/$stage"
  cp eval/rehearsal-budget.json "$run_dir/$stage/budget.json"
  run_step "$stage-run" python3 scripts/sql_eval.py run --stage improved \
    --prompt "eval/prompts/$stage.json" --artifacts "$run_dir/$stage"
  run_step "$stage-score" python3 scripts/sql_eval.py score --stage improved --artifacts "$run_dir/$stage"
done
run_step compare python3 scripts/compare_map_eval.py \
  "$run_dir/current/reports/improved.json" "$run_dir/semantic/reports/improved.json" \
  --out "$run_dir/comparison.json"
run_step protect python3 scripts/check_prompt_map.py \
  --report "$run_dir/map-pass.json" --markdown "$run_dir/map-pass.md"
if python3 scripts/check_prompt_map.py --prompt eval/prompts/map-violation.json \
  --report "$run_dir/map-violation.json" --markdown "$run_dir/map-violation.md"; then
  echo 'The intentionally regressed prompt unexpectedly passed.' >&2
  exit 1
fi
python3 - "$run_dir/map-violation.json" <<'PY'
import json, sys
report=json.load(open(sys.argv[1]))
assert [v['rule'] for v in report['violations']] == ['missing_text'], report
PY
run_step stop python3 scripts/sql_eval.py stop
echo "Keep all evidence in $run_dir. See docs/prompt-map-workflow.md for the GitHub PR exercise."
