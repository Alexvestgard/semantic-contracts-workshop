#!/usr/bin/env python3
"""Run the two frozen category conditions against the existing read-only database."""
import argparse
import hashlib
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_category_eval import build, CONDITIONS, FIXTURES
from scripts.sql_eval import container_run
from scripts.compare_map_eval import compare_pair
from sql_eval.common import read_json, write_json


def compare(reports):
    first = reports[CONDITIONS[0]]
    ids = [f'q{i:02}' for i in range(1, 21)]
    for report in reports.values():
        if report['controls'] != first['controls']:
            raise ValueError('Run controls differ between conditions.')
        if [q['id'] for q in report['questions']] != ids:
            raise ValueError('Expected the complete 20-question comparison.')
    compare_pair(reports[CONDITIONS[0]], reports[CONDITIONS[1]])
    difficulty = {q['id']: q['difficulty'] for q in first['controls']['questions']}
    result = {'order': list(CONDITIONS), 'scores': {}, 'changes': []}
    for name, report in reports.items():
        sections = {}
        for section in dict.fromkeys(difficulty[qid] for qid in ids):
            selected = [q for q in report['questions'] if difficulty[q['id']] == section]
            sections[section] = {'correct': sum(q['correct'] for q in selected), 'total': len(selected)}
        result['scores'][name] = {k: report[k] for k in ('correct', 'total', 'elapsed_seconds')}
        result['scores'][name]['sections'] = sections
    for old, new in zip(CONDITIONS, CONDITIONS[1:]):
        before = {q['id']: q['correct'] for q in reports[old]['questions']}
        result['changes'].append({'from': old, 'to': new,
            'fixed': [q['id'] for q in reports[new]['questions'] if q['correct'] and not before[q['id']]],
            'regressed': [q['id'] for q in reports[new]['questions'] if not q['correct'] and before[q['id']]]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--verify-gold', action='store_true', help='Verify reference SQL without inference.')
    args = parser.parse_args()
    build(check=True)
    if args.verify_gold:
        fixtures = ROOT / FIXTURES
        container_run('eval-scorer', [(fixtures / name, '/app/eval/' + name, True)
                      for name in ('questions.json', 'question-set.json', 'gold/answers.json')], '--verify-gold')
        return
    if args.out is None:
        parser.error('--out is required for an evaluation.')
    out = args.out.resolve()
    if out.exists():
        parser.error('Use a new output directory; preserve previous evidence.')
    out.mkdir(parents=True)
    # Freeze inputs before any inference. Gold is mounted only in the scorer.
    inputs = out / 'inputs'
    shutil.copytree(ROOT / FIXTURES, inputs)
    budget = out / 'budget.json'
    shutil.copyfile(ROOT / 'eval/rehearsal-budget.json', budget)
    frozen = [*inputs.rglob('*.json'), budget]
    hashes = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen}
    write_json(out / 'input-hashes.json', hashes)
    shared = [(inputs / name, '/app/eval/' + name, True)
              for name in ('questions.json', 'question-set.json')]
    gold = (inputs / 'gold/answers.json', '/app/eval/gold/answers.json', True)
    container_run('eval-scorer', [*shared, gold], '--verify-gold')
    reports = {}
    for name in CONDITIONS:
        print('Starting condition: ' + name, flush=True)
        run = out / name
        report_dir = out / (name + '-reports')
        run.mkdir()
        report_dir.mkdir()
        container_run('eval-agent', [*shared, (budget, '/budget.json', True),
                      (inputs / (name + '.json'), '/prompt.json', True),
                      (run, '/out', False)], '--stage', 'improved', '--prompt', '/prompt.json')
        container_run('eval-scorer', [*shared, gold, (run, '/run', True),
                      (report_dir, '/reports', False)], '--run', '/run', '--out', '/reports/report.json')
        reports[name] = read_json(report_dir / 'report.json')
    if hashes != {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen}:
        raise ValueError('Frozen inputs changed during inference.')
    result = compare(reports)
    write_json(out / 'comparison.json', result)
    print(result, flush=True)


if __name__ == '__main__':
    main()
