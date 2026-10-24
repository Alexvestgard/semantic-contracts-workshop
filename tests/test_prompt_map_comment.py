"""Exercise the privileged reporter without GitHub access or artifact execution."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / '.github/workflows/prompt-map-comment.yml').read_text().split('          script: |\n', 1)[1]
SCRIPT = '\n'.join(line[12:] for line in SCRIPT.splitlines())


@unittest.skipUnless(shutil.which('node'), 'Node is needed for the GitHub reporter tests')
class CommentTests(unittest.TestCase):
    def run_reporter(self, **options):
        harness = r'''
const script = JSON.parse(process.argv[1]);
const options = JSON.parse(process.argv[2]);
const calls = [];
const github = {
  rest: {
    pulls: {get: async () => ({data: {state: 'open', head: {sha: options.stale ? 'new' : 'tested'}}})},
    actions: {listWorkflowRunArtifacts: 'artifacts', downloadArtifact: async () => ({data: []})},
    issues: {
      listComments: 'comments',
      updateComment: async x => calls.push(['update', x]),
      createComment: async x => calls.push(['create', x])
    }
  },
  paginate: async kind => kind === 'artifacts' ? [{id: 1, name: 'prompt-map-report', size_in_bytes: 100}] :
    options.existing ? [{id: 9, user: {login: 'github-actions[bot]'}, body: '<!-- museum-prompt-map -->old'}] : []
};
const context = {repo: {owner:'museum', repo:'workshop'}, payload: {workflow_run: {
  id: 1, head_sha: 'tested', conclusion: options.passed ? 'success' : 'failure',
  pull_requests: options.noPR ? [] : [{number: 2}], html_url: 'https://github.com/museum/workshop/actions/runs/1'
}}};
const report = {status: options.passed ? 'pass' : 'fail', violations: options.passed ? [] : [
  {rule: 'missing_text', expected: 'null_or_blank', actual: 'null_only', message: '<script>@someone</script>'}
]};
const customRequire = name => {
  if (name === 'fs') return {writeFileSync: () => {}};
  if (name === 'child_process') return {execFileSync: () => Buffer.from(JSON.stringify(report))};
  return require(name);
};
process.env.RUNNER_TEMP = '/tmp';
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
new AsyncFunction('github','context','core','require',script)(github,context,{notice: x => calls.push(['notice',x])},customRequire)
 .then(() => process.stdout.write(JSON.stringify(calls))).catch(e => {console.error(e);process.exit(1)});
'''
        result = subprocess.run(['node', '-e', harness, json.dumps(SCRIPT), json.dumps(options)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_failure_explains_violation_and_escapes_untrusted_markup(self):
        calls = self.run_reporter()
        self.assertEqual(calls[0][0], 'create')
        body = calls[0][1]['body']
        self.assertIn('missing_text', body)
        self.assertIn('null_only', body)
        self.assertIn('Prompt MAP: FAIL', body)
        self.assertNotIn('<script>', body)
        self.assertNotIn('@someone', body)

    def test_repair_updates_existing_bot_comment(self):
        calls = self.run_reporter(passed=True, existing=True)
        self.assertEqual(calls[0][0], 'update')
        self.assertEqual(calls[0][1]['comment_id'], 9)
        self.assertIn('Prompt MAP: PASS', calls[0][1]['body'])

    def test_stale_run_and_ambiguous_pr_cannot_comment(self):
        for options in ({'stale':True}, {'noPR':True}):
            with self.subTest(options=options):
                calls = self.run_reporter(**options)
                self.assertFalse(any(kind in ('create', 'update') for kind, _ in calls))
