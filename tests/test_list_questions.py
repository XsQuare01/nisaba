import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "write-explainer", "scripts")
sys.path.insert(0, SCRIPTS)

import list_questions as lq  # noqa: E402

CLI = os.path.join(SCRIPTS, "list_questions.py")


def sentences(doc):
    return [s for _, s in lq.list_questions(doc)]


class ListQuestionsTest(unittest.TestCase):
    def test_detects_self_raised_doubt(self):
        s = "한 쌍이 식 3개(x, y, z 성분)를 주니 2쌍이면 될 것 같지만 그렇지 않다."
        self.assertEqual(sentences("미지수는 6개다. " + s), [s])

    def test_detects_question_mark(self):
        s = "손이 움직인 길을 로봇은 어떻게 따라가나?"
        self.assertEqual(sentences(s), [s])

    def test_plain_statement_not_listed(self):
        self.assertEqual(sentences("미지수는 6개다."), [])

    def test_code_and_math_blocks_ignored(self):
        doc = "```c\nx = a ? b : c;\n```\n$$\n\\text{왜?}\n$$\n본문이다."
        self.assertEqual(sentences(doc), [])

    def test_notion_tag_lines_ignored(self):
        doc = '<image source="https://x/a.png?x=1">\n그림은 왜 이렇게 생겼을까?\n</image>'
        self.assertEqual(lq.list_questions(doc), [(2, "그림은 왜 이렇게 생겼을까?")])

    def test_question_after_leading_mention_is_found(self):
        doc = '<mention url="https://x/p/1?y=2">강체</mention>에서 본 자유도는 왜 6일까?'
        self.assertEqual(sentences(doc), ["강체에서 본 자유도는 왜 6일까?"])

    def test_cli_korean_output_cp949(self):
        d = tempfile.mkdtemp()
        doc_p = os.path.join(d, "page.md")
        with open(doc_p, "w", encoding="utf-8") as f:
            f.write("🎯 손짓은 어떻게 경로가 되나?")
        env = dict(os.environ)
        env.pop("PYTHONIOENCODING", None)
        env.pop("PYTHONUTF8", None)
        p = subprocess.run([sys.executable, CLI, "--doc", doc_p],
                           capture_output=True, encoding="utf-8", env=env)
        self.assertNotIn("UnicodeEncodeError", p.stderr)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("🎯", p.stdout)


if __name__ == "__main__":
    unittest.main()
