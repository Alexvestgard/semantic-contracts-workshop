#!/usr/bin/env python3
"""Compare two completed runs; never turn a desired improvement into a claimed one."""
import argparse
import json
from pathlib import Path


def compare_pair(current, semantic):
    if current['controls'] != semantic['controls']:
        raise ValueError('Run controls differ; only the prompt may change.')
    for report in (current, semantic):
        ids = report['controls']['question_ids']
        if ([q['id'] for q in report['questions']] != ids or report['total'] != len(ids)
                or report['correct'] != sum(q['correct'] for q in report['questions'])):
            raise ValueError('Report totals or question order are inconsistent.')
    before = {q['id']: q['correct'] for q in current['questions']}
    delta = semantic['correct'] - current['correct']
    return {'current': {k: current[k] for k in ('correct', 'total', 'elapsed_seconds')},
            'semantic': {k: semantic[k] for k in ('correct', 'total', 'elapsed_seconds')},
            'delta': delta, 'improvement_observed': delta > 0,
            'fixed': [q['id'] for q in semantic['questions'] if q['correct'] and not before[q['id']]],
            'regressed': [q['id'] for q in semantic['questions'] if not q['correct'] and before[q['id']]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('current', type=Path)
    parser.add_argument('semantic', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = compare_pair(json.loads(args.current.read_text()), json.loads(args.semantic.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    print('One paired run is a teaching diagnostic, not a general model benchmark.')


if __name__ == '__main__':
    main()
