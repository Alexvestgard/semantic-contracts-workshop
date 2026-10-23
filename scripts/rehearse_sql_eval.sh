#!/usr/bin/env bash
# Preserve a separate set of logs and results for each rehearsal.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts
run_dir=$(mktemp -d "$PWD/artifacts/sql-eval-five-XXXXXX")
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
run_step pilot pilot --stage improved
run_step freeze freeze
for stage in baseline improved regressed; do
    run_step "$stage" run --stage "$stage"
    run_step "score-$stage" score --stage "$stage"
done
run_step compare compare
run_step revert revert
run_step protect protect
echo "Finished. Read $run_dir/comparison.md and keep the full evidence directory."
