import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "write-explainer", "scripts")
sys.path.insert(0, SCRIPTS)

import check_style as cs  # noqa: E402

CLI = os.path.join(SCRIPTS, "check_style.py")


def kinds(doc, **kw):
    return [k for (k, _, _) in cs.check(doc, **kw)]


class StyleTest(unittest.TestCase):
    def test_long_sentence_flagged(self):
        doc = "가" * 70 + "다. 짧다."
        self.assertEqual(kinds(doc, max_len=60), ["긴 문장"])

    def test_clause_comma_flagged(self):
        doc = "간격이 짧아질 수 없어서, 시각이 늦어진다."
        self.assertIn("쉼표 이음", kinds(doc))

    def test_list_comma_not_flagged(self):
        self.assertNotIn("쉼표 이음", kinds("위치, 방향, 속도를 잰다."))

    def test_bare_identifier_flagged_code_not(self):
        self.assertEqual(kinds("간격은 base_dt로 정한다."), ["맨 식별자"])
        self.assertEqual(kinds("간격은 `base_dt`로 정한다."), [])
        self.assertEqual(kinds("간격은 $base_dt$로 정한다."), [])

    def test_section_without_visual_flagged(self):
        doc = "## 1. 공간\n\n글만 있다.\n\n## 2. 시간\n\n<image source=\"a.png\">\n캡션\n</image>\n"
        res = cs.check(doc)
        self.assertEqual([(k, d) for (k, _, d) in res if k == "시각 자료 없는 절"], [("시각 자료 없는 절", "1. 공간")])

    def test_table_is_not_a_visual(self):
        # 사용자 판단(2026-11-20): 표만 있는 절은 시각 자료가 없는 절이다
        doc = "## 1. 표\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n"
        self.assertIn("시각 자료 없는 절", kinds(doc))

    def test_page_length(self):
        doc = ("가나다라마. " * 300)
        self.assertIn("분량", kinds(doc, max_len=1000, max_page=1000))

    def test_code_fence_and_math_skipped(self):
        doc = "```\nlong_variable_name = 1, 2\n```\n$$\na_b, c\n$$\n짧다."
        self.assertEqual(kinds(doc), [])

    def test_cli_summary(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "page.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("간격은 base_dt로 정한다.\n")
        r = subprocess.run([sys.executable, CLI, "--doc", p], capture_output=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.strip().splitlines()[-1].startswith("요약: 긴 문장 0 · 쉼표 이음 0 · 맨 식별자 1"))
        r2 = subprocess.run([sys.executable, CLI, "--doc", p, "--strict"], capture_output=True, encoding="utf-8")
        self.assertEqual(r2.returncode, 1)


if __name__ == "__main__":
    unittest.main()
