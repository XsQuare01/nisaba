import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "write-explainer", "scripts")
sys.path.insert(0, SCRIPTS)

import check_terms as ct  # noqa: E402

CLI = os.path.join(SCRIPTS, "check_terms.py")


class FindAvoidedTest(unittest.TestCase):
    def test_flags_avoided_term_with_line(self):
        terms = [{"use": "좌표 변환", "avoid": ["좌표계 변환"]}]
        hits = ct.find_avoided("첫 줄이다.\n여기서 좌표계 변환을 한다.", terms)
        self.assertEqual([(h[0], h[1], h[2]) for h in hits], [(2, "좌표계 변환", "좌표 변환")])

    def test_avoid_inside_use_not_flagged(self):
        terms = [{"use": "좌표계 변환", "avoid": ["변환"]}]
        self.assertEqual(ct.find_avoided("좌표계 변환만 쓴다.", terms), [])

    def test_fenced_code_ignored(self):
        terms = [{"use": "좌표 변환", "avoid": ["좌표계 변환"]}]
        doc = "```py\n# 좌표계 변환\n```\n본문"
        self.assertEqual(ct.find_avoided(doc, terms), [])


    def test_inline_code_ignored(self):
        terms = [{"use": "트래커", "avoid": ["tracker"]}]
        doc = "경로는 `src/tracker/tasks.py`이고 tracker라고 쓰지 않는다."
        hits = ct.find_avoided(doc, terms)
        self.assertEqual([(h[0], h[1]) for h in hits], [(1, "tracker")])
        self.assertIn("라고", hits[0][3])


class CliTest(unittest.TestCase):
    def test_cli_korean_output_cp949(self):
        d = tempfile.mkdtemp()
        doc_p, terms_p = os.path.join(d, "page.md"), os.path.join(d, "terms.json")
        with open(doc_p, "w", encoding="utf-8") as f:
            f.write("🎯 좌표계 변환을 한다.")
        with open(terms_p, "w", encoding="utf-8") as f:
            json.dump({"terms": [{"use": "좌표 변환", "avoid": ["좌표계 변환"]}]}, f, ensure_ascii=False)
        env = dict(os.environ)
        env.pop("PYTHONIOENCODING", None)
        env.pop("PYTHONUTF8", None)
        p = subprocess.run([sys.executable, CLI, "--doc", doc_p, "--terms", terms_p],
                           capture_output=True, encoding="utf-8", env=env)
        self.assertNotIn("UnicodeEncodeError", p.stderr)
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertIn("🎯", p.stdout)


if __name__ == "__main__":
    unittest.main()
