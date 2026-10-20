"""Checks for the self-contained public knowledge-card distribution.

Run from the repository root:
    python -m unittest discover -s tests -v

Only files inside this public package are read. No original course documents,
installed skills, network services, or third-party Python packages are needed.
"""

import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CARDS_PATH = ROOT / "data" / "cards.json"
SEARCH_PATH = ROOT / "scripts" / "search.py"
REGISTER_PATH = ROOT / "references" / "source-register.md"
EXPECTED_COUNTS = {
    "career": 7,
    "family": 6,
    "education": 7,
    "finance": 7,
    "comparison": 6,
    "selfworth": 6,
}
REQUIRED_CARD_FIELDS = {
    "id", "topic", "core", "conditions", "questions", "actions", "limits", "sources",
}
REQUIRED_SOURCE_FIELDS = {
    "doc_id", "title", "paragraph", "start", "end", "reason", "path",
}
PRIVATE_SOURCE_FIELDS = {
    "quote", "filename", "exact_quote_verified", "original_filename",
    "original_path", "source_file", "original_file", "raw_text",
}
COVERAGE_QUERIES = {
    "career": (
        "职业转型 可迁移能力",
        "换城市 找工作 家庭资源",
    ),
    "family": (
        "伴侣 私房钱 共同支出",
        "父母 成年子女 经济支持 边界",
    ),
    "education": (
        "孩子选专业 教育规划",
        "孩子使用AI 自主学习",
    ),
    "finance": (
        "失业 房贷 现金流压力",
        "沉没成本 家庭支出",
    ),
    "comparison": (
        "同龄人买房 我觉得失败",
        "社交圈 阶层焦虑 资源比较",
    ),
    "selfworth": (
        "别人评价 自我价值 内耗",
        "自我期待 生活意义",
    ),
}
# Test conceptual coverage, not a brittle exact ordering. A broad same-topic
# match alone is insufficient when the query names a specific card concept.
EXPECTED_QUERY_CARDS = {
    "职业转型 可迁移能力": {"CAR02"},
    "换城市 找工作 家庭资源": {"CAR04"},
    "伴侣 私房钱 共同支出": {"FAM01"},
    "父母 成年子女 经济支持 边界": {"FAM03"},
    "孩子选专业 教育规划": {"EDU01", "EDU02", "EDU06"},
    "孩子使用AI 自主学习": {"EDU07"},
    "失业 房贷 现金流压力": {"FIN01"},
    "沉没成本 家庭支出": {"FIN06"},
    "同龄人买房 我觉得失败": {"CMP01", "CMP02", "CMP04", "CMP05"},
    "社交圈 阶层焦虑 资源比较": {"CMP03", "CMP05"},
    "别人评价 自我价值 内耗": {"SELF01", "SELF02"},
    "自我期待 生活意义": {"SELF01", "SELF04", "SELF06"},
}


def public_files():
    """Exclude only local tooling state, not published subdirectories."""
    ignored = {".git", "__pycache__", ".venv"}
    return [
        path for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in ignored for part in path.relative_to(ROOT).parts)
    ]


def result_list(payload):
    if isinstance(payload, dict):
        payload = payload.get("results")
    if not isinstance(payload, list):
        raise AssertionError("Search must return a result list or an object with results.")
    return payload


def without_fences(markdown):
    """Leave real prose links while excluding fenced command examples."""
    lines = []
    fence_char = None
    fence_length = 0
    for line in markdown.splitlines():
        opening = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if opening:
            marker = opening.group(1)
            if fence_char is None:
                fence_char, fence_length = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length:
                fence_char = None
            continue
        if fence_char is None:
            lines.append(line)
    return "\n".join(lines)


def markdown_targets(markdown):
    text = without_fences(markdown)
    # Inline links and images; optional Markdown titles are not part of paths.
    inline = r"\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[\"'][^\n]*?[\"'])?\s*\)"
    targets = [match.group(1).strip("<>") for match in re.finditer(inline, text)]
    # Reference-style link definitions, including ones used by images.
    reference = r"(?m)^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|[^\s]+)"
    targets.extend(match.group(1).strip("<>") for match in re.finditer(reference, text))
    return targets


def markdown_anchors(markdown):
    text = without_fences(markdown)
    anchors = set(re.findall(r"\bid\s*=\s*[\"']([^\"']+)[\"']", text))
    duplicates = {}
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", match.group(1))
        heading = re.sub(r"<[^>]*>", "", heading)
        slug = re.sub(r"[^\w\s-]", "", heading.lower())
        slug = re.sub(r"\s", "-", slug)
        occurrence = duplicates.get(slug, 0)
        duplicates[slug] = occurrence + 1
        anchors.add(slug if occurrence == 0 else f"{slug}-{occurrence}")
    return anchors


class PublicPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (CARDS_PATH, SEARCH_PATH, REGISTER_PATH, ROOT / "SKILL.md"):
            if not path.is_file():
                raise AssertionError(f"Required public package file is missing: {path}")
        cls.cards = json.loads(CARDS_PATH.read_text(encoding="utf-8"))
        spec = importlib.util.spec_from_file_location("_public_skill_search", SEARCH_PATH)
        if spec is None or spec.loader is None:
            raise AssertionError("Cannot import the public search module.")
        cls.search_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.search_module
        spec.loader.exec_module(cls.search_module)
        if not callable(getattr(cls.search_module, "search_corpus", None)):
            raise AssertionError("The public search module must expose search_corpus.")

    def assert_card_results(self, results, topic=None):
        self.assertTrue(results, "Expected at least one matching knowledge card.")
        known_ids = {card["id"] for card in self.cards}
        for record in results:
            self.assertIsInstance(record, dict)
            self.assertEqual(record.get("record_type"), "knowledge_card")
            self.assertNotIn("quote", record)
            self.assertNotIn("raw_text", record)
            encoded = json.dumps(record, ensure_ascii=False)
            self.assertNotIn("references/corpus/", encoded)
            self.assertNotIn("data/chunks.jsonl", encoded)
            card_id = record.get("card_id", record.get("id"))
            if card_id is not None:
                self.assertIn(card_id, known_ids)
        if topic is not None:
            self.assertTrue(
                any(
                    record.get("topic") == topic or topic in record.get("topics", [])
                    for record in results
                ),
                f"No card from requested topic {topic!r} was returned.",
            )

    def run_search(self, query, *args):
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(SEARCH_PATH), query, "--json", *args],
            cwd=ROOT,
            env=environment,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=30,
            check=False,
        )

    def test_card_count_topics_and_schema(self):
        self.assertIsInstance(self.cards, list)
        self.assertEqual(len(self.cards), 39)
        self.assertEqual(len({card["id"] for card in self.cards}), 39)
        counts = {topic: 0 for topic in EXPECTED_COUNTS}
        for card in self.cards:
            with self.subTest(card=card.get("id")):
                self.assertTrue(REQUIRED_CARD_FIELDS <= card.keys())
                self.assertIsInstance(card["id"], str)
                self.assertTrue(card["id"].strip())
                self.assertIn(card["topic"], EXPECTED_COUNTS)
                counts[card["topic"]] += 1
                self.assertIsInstance(card["core"], str)
                self.assertTrue(card["core"].strip())
                for field in ("conditions", "questions", "actions", "limits"):
                    self.assertIsInstance(card[field], list)
                    self.assertTrue(card[field])
                    self.assertTrue(all(isinstance(value, str) and value.strip()
                                        for value in card[field]))
                self.assertIsInstance(card["sources"], list)
                self.assertTrue(card["sources"])
        self.assertEqual(counts, EXPECTED_COUNTS)

    def test_sources_are_metadata_without_course_text(self):
        register_anchors = markdown_anchors(REGISTER_PATH.read_text(encoding="utf-8"))
        for card in self.cards:
            for source in card["sources"]:
                with self.subTest(card=card["id"], source=source.get("doc_id")):
                    self.assertEqual(set(source), REQUIRED_SOURCE_FIELDS)
                    self.assertFalse(PRIVATE_SOURCE_FIELDS & source.keys())
                    self.assertRegex(source["doc_id"], r"^D0[1-7]$")
                    for field in ("title", "reason"):
                        self.assertIsInstance(source[field], str)
                        self.assertTrue(source[field].strip())
                    for field in ("paragraph", "start", "end"):
                        self.assertIs(type(source[field]), int)
                    self.assertGreaterEqual(source["paragraph"], 1)
                    self.assertGreaterEqual(source["start"], 0)
                    self.assertGreater(source["end"], source["start"])
                    anchor = source["doc_id"].lower()
                    self.assertEqual(
                        source["path"], f"references/source-register.md#{anchor}"
                    )
                    self.assertIn(anchor, register_anchors)

    def test_no_raw_corpus_or_original_document_payloads(self):
        self.assertFalse((ROOT / "references" / "corpus").exists())
        self.assertFalse((ROOT / "data" / "chunks.jsonl").exists())
        forbidden_directories = {"corpus", "full_sources", "raw_sources", "sources"}
        for path in public_files():
            relative = path.relative_to(ROOT)
            with self.subTest(path=str(relative)):
                self.assertFalse(
                    forbidden_directories & {part.lower() for part in relative.parts[:-1]}
                )
                self.assertNotIn(path.suffix.lower(), {".docx", ".doc", ".pdf"})
                self.assertNotEqual(path.name.lower(), "chunks.jsonl")

    def test_all_local_markdown_links_and_anchors_resolve(self):
        root = ROOT.resolve()
        for document in public_files():
            if document.suffix.lower() != ".md":
                continue
            markdown = document.read_text(encoding="utf-8")
            for target in markdown_targets(markdown):
                with self.subTest(document=str(document.relative_to(ROOT)), target=target):
                    parts = urlsplit(target)
                    if parts.scheme or parts.netloc:
                        # External references are deliberately not fetched.
                        continue
                    candidate = (
                        document.parent / unquote(parts.path)
                        if parts.path else document
                    ).resolve()
                    self.assertTrue(
                        candidate == root or root in candidate.parents,
                        f"Local link escapes the public package: {target}",
                    )
                    self.assertTrue(candidate.exists(), f"Missing local target: {target}")
                    if parts.fragment:
                        self.assertTrue(candidate.is_file())
                        self.assertEqual(candidate.suffix.lower(), ".md")
                        anchors = markdown_anchors(candidate.read_text(encoding="utf-8"))
                        self.assertIn(unquote(parts.fragment), anchors,
                                      f"Missing Markdown anchor: {target}")

    def test_search_corpus_defaults_to_knowledge_cards(self):
        results = result_list(self.search_module.search_corpus("职业转型 可迁移能力"))
        self.assert_card_results(results)

    def test_search_corpus_rejects_raw_only(self):
        with self.assertRaisesRegex(ValueError, r"公开|原文|raw|unavailable|unsupported"):
            self.search_module.search_corpus("职业转型", raw_only=True)

    def test_cli_rejects_raw_only_with_explanation(self):
        completed = self.run_search("职业转型", "--raw-only")
        self.assertEqual(completed.returncode, 2)
        explanation = completed.stderr + completed.stdout
        self.assertRegex(
            explanation.lower(),
            r"公开|不含原文|不提供原文|raw.{0,80}(not|unavailable|unsupported)|not.{0,80}raw",
        )
        self.assertNotIn("Traceback", explanation)

    def test_default_cli_returns_only_cards(self):
        completed = self.run_search("家庭共同支出 个人自主", "--top-k", "10")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assert_card_results(result_list(json.loads(completed.stdout)))

    def test_unrelated_programming_request_has_no_results(self):
        completed = self.run_search("Python里list和tuple有什么区别？给一个简单例子。")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result_list(json.loads(completed.stdout)), [])

    def test_two_queries_per_topic_have_card_coverage(self):
        for topic, queries in COVERAGE_QUERIES.items():
            for query in queries:
                with self.subTest(topic=topic, query=query):
                    completed = self.run_search(query, "--topic", topic, "--top-k", "10")
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    results = result_list(json.loads(completed.stdout))
                    self.assert_card_results(results, topic=topic)
                    actual_ids = {record.get("card_id") for record in results}
                    self.assertTrue(
                        EXPECTED_QUERY_CARDS[query] & actual_ids,
                        f"Relevant concept cards missing for {query!r}; "
                        f"expected one of {sorted(EXPECTED_QUERY_CARDS[query])}, "
                        f"received {sorted(actual_ids)}.",
                    )


if __name__ == "__main__":
    unittest.main()
