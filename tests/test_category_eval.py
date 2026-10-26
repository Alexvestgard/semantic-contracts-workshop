"""Protect the two-condition comparison and the category contract."""
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts.build_category_eval import build, generate, profile, vocabulary, CONDITIONS, FIXTURES
from scripts.check_prompt_map import CONTRACT, check
from scripts.run_category_eval import compare, main
from sql_eval.common import read_json, write_json
from sql_eval.prompts import render
from tests.test_prompt_map import candidate

ROOT = Path(__file__).resolve().parents[1]
ASSET = FIXTURES + '/prompt-map-linked-art.json'


class CategoryEvalTests(unittest.TestCase):
    def test_twenty_questions_preserve_basic_and_cover_six_medium_categories(self):
        build(check=True)
        fixtures = generate()
        questions = fixtures['questions.json']
        self.assertEqual(questions[:10], read_json(ROOT / 'eval/questions.json')[:10])
        self.assertEqual(fixtures['question-set.json'], [f'q{i:02}' for i in range(1, 21)])
        self.assertEqual({q['difficulty'] for q in questions[10:]}, {'medium'})
        self.assertEqual({q['category'] for q in questions[10:]},
                         {'Sculpture', 'Painting', 'Drawing', 'Print', 'Furniture', 'Architectural objects'})

    def test_only_two_conditions_and_local_references_reach_prompt(self):
        self.assertEqual(CONDITIONS, ('prompt-only', 'prompt-map-linked-art'))
        fixtures = generate()
        base, linked = [fixtures[name + '.json'] for name in CONDITIONS]
        self.assertEqual(base, read_json(ROOT / 'eval/prompts/semantic.json'))
        self.assertEqual(base['semantics'], linked['semantics'])
        self.assertTrue(linked['instructions'].startswith(base['instructions'] + '\n'))
        for ref in profile()['linkedArtReferences'].values():
            self.assertIn(ref['uri'], render(linked))
            self.assertIn(ref['description'], render(linked))
            self.assertEqual(ref['description'], vocabulary()[ref['name']]['description'])

    def test_reference_answers_and_label_boundaries(self):
        mapping = profile()['categoryMapping']
        self.assertNotIn('Sword Furniture-Tsuba', mapping['Furniture'])
        self.assertEqual(set(mapping['Sculpture']) & set(mapping['Architectural objects']),
                         {'Sculpture-Architectural', 'Sculpture-Architectural-Stone'})
        answers = generate()['gold/answers.json']['answers']
        self.assertEqual([answers[f'q{i:02}']['expected'][0][0] for i in range(11, 17)],
                         [296, 353, 113, 55, 23, 13])
        rows = read_json(ROOT / 'data_contract_components/data_assets/db_migrations/raw_data/objects.json')
        for qid, category in [('q17', 'Sculpture'), ('q18', 'Architectural objects'),
                              ('q19', 'Painting'), ('q20', 'Furniture')]:
            ids = sorted(r['objectID'] for r in rows if r.get('classification') in mapping[category])[:5]
            self.assertEqual(answers[qid]['expected'], [[object_id] for object_id in ids])
        for ref in list(answers.values())[10:]:
            self.assertNotIn('JOIN', ref['sql'])
            self.assertNotIn('GROUP BY', ref['sql'])

    def test_category_prompt_violation_and_policy_edit_cannot_evade_base(self):
        self.assertEqual(check(ROOT, ROOT)['checked_assets'], ['eval/prompts/semantic.json', ASSET])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate(root)
            prompt = read_json(root / ASSET)
            prompt['instructions'] = prompt['instructions'].replace('"Wood-Furniture", ', '')
            write_json(root / ASSET, prompt)
            violations = check(ROOT, root)['violations']
            self.assertEqual([(v['asset'], v['rule']) for v in violations], [(ASSET, 'prompt.instructions')])
            self.assertIn('Missing mapped labels in instruction text: ["Wood-Furniture"]', violations[0]['message'])
            contract = read_json(root / CONTRACT)
            contract['metadataApplicationProfile']['additionalProfiles'][0]['approved_instructions'] = prompt['instructions']
            write_json(root / CONTRACT, contract)
            self.assertEqual({v['rule'] for v in check(ROOT, root)['violations']},
                             {'prompt.instructions', 'policy.change'})

    def test_tampered_pinned_vocabulary_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / 'vendor/linked-art/guidance'
            shutil.copytree(ROOT / 'vendor/linked-art/guidance', target)
            path = target / 'recommended-vocabulary.md'
            path.write_text(path.read_text().replace('Sculpture', 'Invented'))
            with self.assertRaisesRegex(ValueError, 'Pinned Linked Art documentation changed'):
                vocabulary(root)

    def test_two_conditions_keep_gold_private_and_controls_equal(self):
        calls, prompts, budgets = [], [], []
        questions = read_json(ROOT / FIXTURES / 'questions.json')
        ids = [q['id'] for q in questions]
        def container(service, mounts, *args):
            calls.append(service)
            paths = {dest: src for src, dest, readonly in mounts}
            self.assertEqual(read_json(paths['/app/eval/questions.json']), questions)
            self.assertEqual(read_json(paths['/app/eval/question-set.json']), ids)
            if service == 'eval-agent':
                self.assertFalse(any('gold' in str(src) or 'gold' in dest for src, dest, readonly in mounts))
                prompts.append(read_json(paths['/prompt.json']))
                budgets.append(read_json(paths['/budget.json']))
            elif '--run' in args:
                write_json(paths['/reports'] / 'report.json', {
                    'controls': {'question_ids': ids, 'questions': questions},
                    'questions': [{'id': qid, 'correct': True} for qid in ids],
                    'correct': 20, 'total': 20, 'elapsed_seconds': 1})
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'run'
            with patch('sys.argv', ['run', '--out', str(out)]), patch(
                    'scripts.run_category_eval.container_run', side_effect=container):
                main()
            result = read_json(out / 'comparison.json')
            self.assertEqual(result['order'], list(CONDITIONS))
            self.assertEqual(set(result['scores'][CONDITIONS[0]]['sections']), {'basic', 'medium'})
        self.assertEqual(calls, ['eval-scorer'] + ['eval-agent', 'eval-scorer'] * 2)
        self.assertEqual(prompts, [read_json(ROOT / FIXTURES / (name + '.json')) for name in CONDITIONS])
        self.assertEqual(budgets[0], budgets[1])

    def test_verify_gold_does_not_start_inference(self):
        with patch('sys.argv', ['run', '--verify-gold']), patch('scripts.run_category_eval.container_run') as run:
            main()
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], 'eval-scorer')
        self.assertEqual(run.call_args.args[-1], '--verify-gold')

    def test_changed_controls_or_inconsistent_totals_are_rejected(self):
        questions = read_json(ROOT / FIXTURES / 'questions.json')
        report = {'controls': {'question_ids': [q['id'] for q in questions], 'questions': questions},
                  'questions': [{'id': q['id'], 'correct': True} for q in questions],
                  'correct': 20, 'total': 20, 'elapsed_seconds': 1}
        for mutation in ('controls', 'totals'):
            reports = {name: deepcopy(report) for name in CONDITIONS}
            if mutation == 'controls':
                reports[CONDITIONS[1]]['controls']['seed'] = 2
            else:
                reports[CONDITIONS[1]]['correct'] = 19
            with self.assertRaises(ValueError):
                compare(reports)
