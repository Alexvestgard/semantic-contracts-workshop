"""Check the runnable rehearsal without starting inference or Docker."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.sql_eval import main

ROOT = Path(__file__).resolve().parents[1]


class RehearsalTests(unittest.TestCase):
    def run_launcher(self, root, fail=''):
        (root / 'scripts').mkdir()
        (root / 'eval').mkdir()
        shutil.copyfile(ROOT / 'scripts/rehearse_sql_eval.sh', root / 'scripts/rehearse_sql_eval.sh')
        shutil.copyfile(ROOT / 'eval/rehearsal-budget.json', root / 'eval/rehearsal-budget.json')
        (root / 'scripts/sql_eval.py').write_text('''import json
import os
from pathlib import Path
import sys
args = sys.argv[1:]
with Path("calls.jsonl").open("a") as log:
    log.write(json.dumps(args) + "\\n")
if args[0] == os.environ.get("FAIL_STEP"):
    sys.exit(7)
if args[0] == "score":
    out = Path(args[args.index("--artifacts") + 1]) / "reports"
    out.mkdir()
    (out / "improved.json").write_text(json.dumps({"correct": 10, "total": 20, "elapsed_seconds": 1110.9}))
''')
        return subprocess.run(['bash', str(root / 'scripts/rehearse_sql_eval.sh')],
                              env=dict(os.environ, FAIL_STEP=fail), capture_output=True, text=True)

    def test_default_runs_twenty_improved_only_with_fixed_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.run_launcher(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in (root / 'calls.jsonl').read_text().splitlines()]
            runs = [c for c in calls if c[0] == 'run']
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0][runs[0].index('--stage') + 1], 'improved')
            self.assertFalse({'pilot', 'freeze', 'compare'} & {c[0] for c in calls})
            self.assertEqual(calls[-1][0], 'stop')
            budget = json.loads(next((root / 'artifacts').glob('*/budget.json')).read_text())
            self.assertEqual(budget['max_tool_calls'], 1)
            self.assertEqual(budget['question_timeout_seconds'], 271)
            self.assertEqual(budget['request_timeout_seconds'], 271)
            self.assertEqual(budget['max_output_tokens'], 384)
            self.assertEqual(json.loads((ROOT / 'eval/question-set.json').read_text()),
                             [f'q{i:02}' for i in range(1, 21)])
            self.assertIn('10/20 correct', result.stdout)

    def test_failed_run_preserves_logs_and_does_not_score(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.run_launcher(root, fail='run')
            self.assertNotEqual(result.returncode, 0)
            calls = [json.loads(line) for line in (root / 'calls.jsonl').read_text().splitlines()]
            self.assertEqual(calls[-1][0], 'run')
            self.assertTrue(next((root / 'artifacts').glob('*/improved.log')).is_file())
            self.assertFalse(list((root / 'artifacts').glob('*/reports')))

    def test_stop_targets_only_the_model(self):
        with patch('sys.argv', ['sql_eval', 'stop']), patch('scripts.sql_eval.compose') as compose:
            main()
        compose.assert_called_once_with('stop', 'model-runner')
