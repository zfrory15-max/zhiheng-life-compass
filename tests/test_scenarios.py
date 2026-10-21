"""Observable v2 coverage, source boundaries and portable action retrieval."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import consult


class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shards = consult.load_shards()
        cls.actions = [a for s in cls.shards for a in s['actions']]
        cls.queries = json.loads((ROOT / 'tests/scenario_queries.json').read_text(encoding='utf-8'))

    def test_catalog_counts_and_source_scopes(self):
        self.assertEqual(len(self.shards), 34)
        self.assertEqual(len(self.actions), 699)
        self.assertEqual(len({a['id'] for a in self.actions}), 699)
        source_fields = {'section_id', 'doc_id', 'title', 'paragraph', 'support', 'path'}
        for shard in self.shards:
            with self.subTest(topic=shard['topic']['id']):
                self.assertEqual(len(shard['analysis']['mechanisms']), 3)
                self.assertEqual(len(shard['actions']), shard['topic']['count'])
                self.assertTrue(shard['analysis']['when_to_use'])
                self.assertTrue(shard['analysis']['limits'])
                for item in [*shard['actions'], *shard['analysis']['mechanisms']]:
                    self.assertTrue(item['sources'])
                    for source in item['sources']:
                        self.assertEqual(set(source), source_fields)
                        self.assertTrue(source['support'])
                        self.assertTrue(source['path'].startswith('references/evidence-map.md#'))
                        self.assertNotIn('references/corpus/', json.dumps(source))
        for action in self.actions:
            with self.subTest(action=action['id']):
                self.assertEqual(len(action['steps']), 3)
                self.assertTrue(action['template'])
                self.assertTrue(action['deliverable'])
                self.assertTrue(action['review'])
                self.assertTrue(action['exercise_type'])

    def test_two_realistic_queries_per_topic(self):
        counts = {}
        for case in self.queries:
            counts[case['topic']] = counts.get(case['topic'], 0) + 1
            with self.subTest(query=case['query']):
                payload = consult.retrieve(case['query'], topic=case['topic'], top_k=5)
                actual = {a['id'] for a in payload['results']}
                self.assertTrue(set(case['expected_ids']) & actual, str(actual))
                self.assertTrue(all(a['topic'] == case['topic'] for a in payload['results']))
                self.assertTrue(payload['topic_context'][0]['limits'])
                self.assertTrue(payload['topic_context'][0]['mechanisms'])
        self.assertEqual(len(counts), 34)
        self.assertTrue(all(n == 2 for n in counts.values()))

    def test_unfiltered_queries_find_specific_actions(self):
        for case in self.queries[::4]:
            with self.subTest(query=case['query']):
                actual = {a['id'] for a in consult.retrieve(case['query'], top_k=8)['results']}
                self.assertTrue(set(case['expected_ids']) & actual, str(actual))

    def test_direct_read_keeps_steps_and_conditions(self):
        payload = consult.retrieve(action_id='M141')
        self.assertEqual(payload['results'][0]['id'], 'M141')
        self.assertTrue(payload['results'][0]['review'])
        self.assertTrue(payload['topic_context'][0]['questions'])
        self.assertEqual(payload['topic_context'][0]['id'], 'money-care')

    def test_short_paraphrase_and_cross_topic_facts(self):
        short = consult.retrieve('读研', topic='family-routes')['results']
        self.assertIn('K141', {a['id'] for a in short})
        payday = consult.retrieve('奖金迟发，房贷月底扣款')['results']
        self.assertEqual(payday[0]['id'], 'M001')
        self.assertNotIn('R036', {a['id'] for a in payday})  # Metaphorical bonus is a different context.
        mixed = consult.retrieve('42岁，奖金延迟两月，房贷月底扣，家里资产主要是两套房，想辞职加盟朋友的店。')['results']
        ids = {a['id'] for a in mixed}
        self.assertIn('FIN01', ids)
        self.assertIn('M183', ids)
        self.assertNotIn('K003', ids)  # The question did not mention childcare.

    def test_unrelated_and_empty_have_no_results(self):
        for query in ('Python里list和tuple有什么区别？给一个简单例子。', '', '火星地貌的光谱分类'):
            with self.subTest(query=query):
                self.assertEqual(consult.retrieve(query)['results'], [])

    def test_invalid_topic_cannot_escape_package(self):
        for topic in ('../private', 'unknown-theme'):
            with self.assertRaises(ValueError):
                consult.retrieve('照护', topic=topic)
        with self.assertRaises(ValueError):
            consult.retrieve(action_id='no-such-action')
        with self.assertRaises(ValueError):
            consult.retrieve('照护', top_k=100)

    def test_cli_from_other_directory_and_raw_refusal(self):
        command = [sys.executable, '-B', str(ROOT / 'scripts/consult.py')]
        good = subprocess.run([*command, '--id', 'K003', '--json'], cwd=ROOT.parent,
                              capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)['results'][0]['id'], 'K003')
        bad = subprocess.run([*command, '家庭', '--raw-only', '--json'], cwd=ROOT.parent,
                             capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(bad.returncode, 2)
        self.assertIn('不含课程原文', json.loads(bad.stdout)['notice'])


if __name__ == '__main__':
    unittest.main()
