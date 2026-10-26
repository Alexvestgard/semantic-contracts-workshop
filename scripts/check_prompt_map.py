#!/usr/bin/env python3
"""Check a prompt data asset against a separately approved MAP (stdlib only)."""
import argparse
import ast
import json
from pathlib import Path
import sys

CONTRACT = 'data_contract_components/contract_definition/object_images_contract_spec.json'
MARKER = '<!-- museum-prompt-map -->'


def read_json(path):
    return json.loads(path.read_text())


def within(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Contract paths must stay within the checkout.')
    return path


def check_profile(candidate_root, ref, prompt_path=None):
    violations = []
    def reject(rule, expected, actual, message):
        violations.append(dict(rule=rule, expected=expected, actual=actual, message=message))
    profile = ref
    if (not isinstance(profile.get('id'), str) or not profile['id']
            or not isinstance(profile.get('version'), str) or not profile['version']):
        raise ValueError('The MAP requires an identifier and version.')
    asset = prompt_path or ref['promptAssetResourceName']
    prompt = read_json(within(candidate_root, asset))
    if not isinstance(prompt, dict):
        raise ValueError('Prompt must be a JSON object.')
    if set(prompt) != {'instructions', 'semantics'}:
        reject('prompt.fields', ['instructions', 'semantics'], sorted(prompt), 'Only approved prompt fields are allowed.')
    if prompt.get('instructions') != ref['approved_instructions']:
        message = 'Free-text instructions differ from the approved data contract.'
        actual = prompt.get('instructions')
        if isinstance(actual, str):
            missing = sorted({label for labels in ref.get('categoryMapping', {}).values()
                              for label in labels if json.dumps(label, ensure_ascii=False) not in actual})
            if missing:
                message += ' Missing mapped labels in instruction text: ' + json.dumps(missing)
        reject('prompt.instructions', ref['approved_instructions'], actual, message)
    semantics = prompt.get('semantics')
    if not isinstance(semantics, dict):
        raise ValueError('Prompt semantics must be a JSON object.')
    elements = profile['elements']
    keys = [element['id'] for element in elements]
    if len(set(keys)) != len(keys) or not keys:
        raise ValueError('MAP elements must have distinct, nonempty identifiers.')
    for element in elements:
        key = element['id']
        if (element['prompt_path'] != 'semantics.' + key or element['required'] is not True
                or element['max_occurs'] != 1 or element['value_type'] != 'string'
                or not isinstance(element['required_value'], str)
                or not isinstance(element['definition'], str)):
            raise ValueError('Unsupported MAP element constraint: ' + key)
        if semantics.get(key) != element['required_value']:
            reject(key, element['required_value'], semantics.get(key), element['definition'])
    for key in sorted(set(semantics) - set(keys)):
        reject(key, 'no additional semantic setting', semantics[key], 'This setting is not in the approved MAP.')
    # Read the literal rule table without importing or executing candidate code.
    tree = ast.parse((candidate_root / 'sql_eval/prompts.py').read_text())
    tables = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'RULES' for target in node.targets)]
    if len(tables) != 1:
        raise ValueError('Expected one literal RULES table.')
    for element in elements:
        actual = tables[0].get(element['id'], {}).get(element['required_value'])
        if actual != element['definition']:
            reject('render.' + element['id'], element['definition'], actual, 'Rendered rule text differs from the approved MAP.')
    return dict(status='fail' if violations else 'pass', asset=asset,
                map_id=profile['id'], map_version=profile['version'], violations=violations)


def check(policy_root, candidate_root, prompt_path=None):
    ref = read_json(policy_root / CONTRACT)['metadataApplicationProfile']
    profiles = [ref] if prompt_path else [ref, *ref.get('additionalProfiles', [])]
    if (len({p['id'] for p in profiles}) != len(profiles)
            or len({p['promptAssetResourceName'] for p in profiles}) != len(profiles)):
        raise ValueError('MAP profiles must have distinct identifiers and prompt assets.')
    reports = [check_profile(candidate_root, p, prompt_path) for p in profiles]
    violations = [dict(v, asset=r['asset']) for r in reports for v in r['violations']]
    def reject(rule, expected, actual, message):
        violations.append(dict(rule=rule, expected=expected, actual=actual, message=message))
    # In PRs the base branch owns policy; changing prompt and policy together cannot evade it.
    if policy_root.resolve() != candidate_root.resolve():
        candidate_contract = read_json(within(candidate_root, CONTRACT))
        if candidate_contract.get('metadataApplicationProfile') != ref:
            reject('policy.change', 'approved MAP section', 'metadataApplicationProfile changed',
                   'The MAP section requires separate maintainer review.')
        for relative in ('scripts/check_prompt_map.py', 'sql_eval/prompts.py'):
            if within(policy_root, relative).read_bytes() != within(candidate_root, relative).read_bytes():
                reject('policy.change', 'approved base-branch policy', relative,
                       'Policy or validator changes require separate maintainer review; this PR is checked against the base policy.')
    return dict(status='fail' if violations else 'pass', asset=reports[0]['asset'],
                map_id=ref['id'], map_version=ref['version'],
                checked_assets=[r['asset'] for r in reports], violations=violations)


def markdown(report):
    lines = [MARKER, '## Prompt MAP: ' + report['status'].upper(), '',
             'The **Prompt MAP contract** check validates the prompt contract. '
             'It blocks merging only when required by the target branch rules.', '']
    for item in report['violations']:
        # The workflow reporter escapes these values before posting them in a pre block.
        lines += [f"Rule: {item['rule']}", f"Expected: {json.dumps(item['expected'], ensure_ascii=False)}",
                  f"Actual: {json.dumps(item['actual'], ensure_ascii=False)}", item['message'], '']
    if not report['violations']:
        lines.append('The prompt satisfies the approved MAP. This does not establish model accuracy.')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy-root', type=Path, default=Path('.'))
    parser.add_argument('--candidate-root', type=Path, default=Path('.'))
    parser.add_argument('--prompt')
    parser.add_argument('--report', type=Path, default=Path('artifacts/prompt-map/report.json'))
    parser.add_argument('--markdown', type=Path, default=Path('artifacts/prompt-map/report.md'))
    args = parser.parse_args()
    try:
        report = check(args.policy_root, args.candidate_root, args.prompt)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
        report = dict(status='fail', violations=[dict(rule='input.invalid', expected='valid prompt, MAP and contract',
                                                     actual=str(error), message='The check failed closed.')])
    for path, contents in ((args.report, json.dumps(report, indent=2) + '\n'), (args.markdown, markdown(report))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    print(markdown(report))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
