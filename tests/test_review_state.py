import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "write-explainer", "scripts")
sys.path.insert(0, SCRIPTS)

import review_state as rs  # noqa: E402

CLI = os.path.join(SCRIPTS, "review_state.py")


class ReviewStateTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.page = os.path.join(self.d, "page.md")
        self.figs = os.path.join(self.d, "figs")
        os.mkdir(self.figs)
        self.fig = os.path.join(self.figs, "a.png")
        self.state = os.path.join(self.d, "reviews", "state.json")
        self.write(self.page, "본문 1")
        with open(self.fig, "wb") as f:
            f.write(b"\x89PNG-1")

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_record_then_status_fresh(self):
        rs.record(self.state, "check_numbers", "통과", "실패 0", [self.page])
        self.assertIn("check_numbers", rs.status(self.state)["통과"])

    def test_edit_makes_stale(self):
        rs.record(self.state, "check_numbers", "통과", "실패 0", [self.page])
        self.write(self.page, "본문 2")
        res = rs.status(self.state)
        self.assertIn("check_numbers", res["미검토"])
        self.assertNotIn("check_numbers", res["통과"])

    def test_figure_change_makes_stale(self):
        rs.record(self.state, "cold-reader", "통과", "막힘 없음", [self.page, self.figs])
        with open(self.fig, "wb") as f:
            f.write(b"\x89PNG-2")
        self.assertIn("cold-reader", rs.status(self.state)["미검토"])

    def test_required_missing_is_unreviewed(self):
        rs.record(self.state, "check_numbers", "통과", "실패 0", [self.page])
        res = rs.status(self.state, require=["cold-reader"])
        self.assertIn("cold-reader", res["미검토"])

    def test_latest_record_wins(self):
        rs.record(self.state, "rubric-reviewer", "미해결", "🟡 2", [self.page])
        rs.record(self.state, "rubric-reviewer", "통과", "후속 처리 완료", [self.page])
        res = rs.status(self.state)
        self.assertIn("rubric-reviewer", res["통과"])
        self.assertNotIn("rubric-reviewer", res["미해결"])

    def test_unresolved_listed(self):
        rs.record(self.state, "cold-reader", "미해결", "막힘 1", [self.page])
        self.assertIn("cold-reader", rs.status(self.state)["미해결"])

    def test_record_missing_path_is_error(self):
        with self.assertRaises(ValueError):
            rs.record(self.state, "cold-reader", "통과", "막힘 없음", [self.page, os.path.join(self.d, "fig")])

    def test_cli_korean_output_cp949(self):
        env = dict(os.environ)
        env.pop("PYTHONIOENCODING", None)
        env.pop("PYTHONUTF8", None)
        p1 = subprocess.run([sys.executable, CLI, "record", "--state", self.state, "--check", "cold-reader",
                             "--outcome", "통과", "--result", "🎯 막힘 없음", "--files", self.page, self.figs],
                            capture_output=True, encoding="utf-8", env=env)
        self.assertEqual(p1.returncode, 0, p1.stderr)
        p2 = subprocess.run([sys.executable, CLI, "status", "--state", self.state, "--require", "cold-reader"],
                            capture_output=True, encoding="utf-8", env=env)
        self.assertNotIn("UnicodeEncodeError", p2.stderr)
        self.assertEqual(p2.returncode, 0, p2.stderr)
        self.assertIn("🎯 막힘 없음", p2.stdout)


if __name__ == "__main__":
    unittest.main()
