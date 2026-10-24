#!/usr/bin/env bash
# Run the 20-question improved prompt with the measured local limits.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts
run_dir=$(mktemp -d "$PWD/artifacts/sql-eval-twenty-XXXXXX")
cp eval/rehearsal-budget.json "$run_dir/budget.json"
echo "Rehearsal evidence: $run_dir"

run_step() {
    local label=$1
    shift
    python3 scripts/sql_eval.py "$@" --artifacts "$run_dir" 2>&1 | tee "$run_dir/$label.log"
}

run_step build build
run_step start start
run_step verify-gold verify-gold
run_step isolation isolation
run_step improved run --stage improved
run_step score-improved score --stage improved
run_step revert revert
run_step protect protect
run_step stop-model stop
python3 - "$run_dir/reports/improved.json" <<'PYSUMMARY'
import json
import sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text())
print(f"Result: {report['correct']}/{report['total']} correct in {report['elapsed_seconds']:.1f} seconds.")
PYSUMMARY
echo "Finished. Keep the logs, traces, and scores in $run_dir."
