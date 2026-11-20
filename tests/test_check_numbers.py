import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "write-explainer", "scripts")
sys.path.insert(0, SCRIPTS)

import check_numbers as cn  # noqa: E402

CLI = os.path.join(SCRIPTS, "check_numbers.py")


def calc(**kw):
    item = {"id": "n1", "kind": "계산"}
    item.update(kw)
    return item


def clean_env():
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    return env


class CheckTest(unittest.TestCase):
    def one(self, doc, item, **kw):
        res = cn.check(doc, [item], base_dir=ROOT, **kw)
        self.assertEqual(len(res), 1)
        return res[0]

    def test_expr_pass(self):
        r = self.one("1°가 틀리면 약 9 mm가 어긋난다.",
                     calc(shown="약 9 mm", value=8.73, tol=0.5, expr="500*sin(radians(1))"))
        self.assertEqual(r[1], "PASS")

    def test_value_mismatch_fails(self):
        # 표기(7)와 value(7)는 맞지만 다시 계산하면 8.73이다
        r = self.one("1°가 틀리면 약 7 mm가 어긋난다.",
                     calc(shown="약 7 mm", value=7.0, tol=0.5, expr="500*sin(radians(1))"))
        self.assertEqual(r[1], "FAIL")
        self.assertIn("계산값 8.73", r[2])

    def test_shown_missing_fails(self):
        r = self.one("오차는 1.10 mm다.", calc(shown="1.1 mm", value=1.1, tol=0.01, expr="1.1"))
        self.assertEqual(r[1], "FAIL")
        self.assertIn("본문에 없음", r[2])

    def test_shown_digit_boundary(self):
        r = self.one("오차는 11 mm다.", calc(shown="1 mm", value=1, tol=0.1, expr="1"))
        self.assertEqual(r[1], "FAIL")
        self.assertIn("본문에 없음", r[2])

    def test_cmd_pass(self):
        r = self.one("평균 0.35 mm다.",
                     calc(shown="0.35 mm", value=0.35, tol=0.001, cmd=[sys.executable, "-c", "print(0.35)"]))
        self.assertEqual(r[1], "PASS")

    def test_cmd_bad_output_fails(self):
        r = self.one("평균 0.35 mm다.",
                     calc(shown="0.35 mm", value=0.35, tol=0.001, cmd=[sys.executable, "-c", "print('hello')"]))
        self.assertEqual(r[1], "FAIL")
        self.assertIn("계산 못 함", r[2])

    def test_cmd_timeout_fails(self):
        r = self.one("평균 0.35 mm다.",
                     calc(shown="0.35 mm", value=0.35, tol=0.001,
                          cmd=[sys.executable, "-c", "import time; time.sleep(5)"]),
                     timeout_s=1)
        self.assertEqual(r[1], "FAIL")
        self.assertIn("계산 못 함", r[2])

    def test_expr_rejects_unsafe(self):
        r = self.one("값은 0이다.", calc(shown="0", value=0, tol=0, expr="__import__('os')"))
        self.assertEqual(r[1], "FAIL")
        self.assertIn("계산 못 함", r[2])

    def test_shown_number_must_match_value(self):
        r = self.one("1°가 틀리면 약 7 mm가 어긋난다.",
                     calc(shown="약 7 mm", value=8.73, tol=0.5, expr="500*sin(radians(1))"))
        self.assertEqual(r[1], "FAIL")
        self.assertIn("표기 숫자", r[2])

    def test_anchor_item_skips_shown_value_check(self):
        r = self.one("측정이 60 Hz로 오면 50 ms다.",
                     calc(shown="60 Hz", value=50, tol=0.01, expr="3*1000/60", anchor=True))
        self.assertEqual(r[1], "PASS")

    def test_shown_with_several_numbers_matches_any(self):
        r = self.one("오프셋은 (10, −80, 175) mm다.",
                     calc(shown="(10, −80, 175) mm", value=-80, tol=0.01, expr="-80"))
        self.assertEqual(r[1], "PASS")

    def test_shown_sign_boundary(self):
        r = self.one("오차는 −0.4 mm다.", calc(shown="0.4 mm", value=0.4, tol=0.01, expr="0.4"))
        self.assertEqual(r[1], "FAIL")
        self.assertIn("본문에 없음", r[2])

    def test_shown_range_dash_allowed(self):
        r = self.one("간격은 10-20 ms다.", calc(shown="20 ms", value=20, tol=0, expr="20"))
        self.assertEqual(r[1], "PASS")

    def test_shown_thousands_boundary(self):
        r = self.one("모두 1,000,000개다.", calc(shown="1,000", value=1000, tol=0, expr="1000"))
        self.assertEqual(r[1], "FAIL")

    def test_shown_unit_extension_boundary(self):
        for doc in ("길이는 5 mm다.", "속도는 5 m/s다."):
            r = self.one(doc, calc(shown="5 m", value=5, tol=0, expr="5"))
            self.assertEqual(r[1], "FAIL", doc)
        r = self.one("길이는 5 m가 된다.", calc(shown="5 m", value=5, tol=0, expr="5"))
        self.assertEqual(r[1], "PASS")

    def test_source_only_not_pass(self):
        r = self.one("테스트는 171 passed였다.",
                     {"id": "t1", "kind": "측정", "shown": "171 passed", "source": "pytest @19e85ad1"})
        self.assertEqual(r[1], "SOURCE")
        self.assertIn("pytest @19e85ad1", r[2])


class LoadTest(unittest.TestCase):
    def load(self, data):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        self.addCleanup(os.remove, path)
        return cn.load_numbers(path)

    def test_both_expr_and_cmd_is_input_error(self):
        with self.assertRaises(ValueError):
            self.load({"items": [calc(shown="1", value=1, tol=0, expr="1", cmd=["x"])]})

    def test_measure_without_source_is_input_error(self):
        with self.assertRaises(ValueError):
            self.load({"items": [{"id": "m", "kind": "측정", "shown": "5.9 s"}]})

    def test_calc_without_expr_is_input_error(self):
        with self.assertRaises(ValueError):
            self.load({"items": [calc(shown="1")]})


class UnregisteredTest(unittest.TestCase):
    def tokens(self, doc, items=(), ignore=()):
        return [t for (_, t, _) in cn.find_unregistered(doc, list(items), list(ignore))]

    def test_unregistered_number_listed(self):
        items = [calc(shown="0.4 mm", value=0.4, tol=0, expr="0.4")]
        self.assertEqual(self.tokens("점 8쌍에 0.4 mm 잡음을 섞었다.", items), ["8"])

    def test_tags_links_dates_ignored(self):
        doc = "\n".join([
            '<mention url="https://app.notion.com/p/0000aaaa">좌표 변환</mention>에서 봤다.',
            "[링크](https://x.org/12)를 본다. 2026-11-10에 3절을 썼다.",
            "```py",
            "x = 42",
            "```",
            "$$",
            "a = 2",
            "$$",
        ])
        self.assertEqual(self.tokens(doc), [])

    def test_shown_with_unit_at_line_end_is_registered(self):
        items = [{"id": "d", "kind": "가정값", "shown": "50 ms"}]
        self.assertEqual(self.tokens("### 재생은 점마다 50 ms", items), [])

    def test_shown_at_line_start_is_registered(self):
        items = [{"id": "d", "kind": "가정값", "shown": "50 ms"}]
        self.assertEqual(self.tokens("50 ms가 지나면 저장한다.", items), [])

    def test_number_after_leading_mention_is_scanned(self):
        doc = '<mention url="https://app.notion.com/p/123">강체</mention>에서 본 자유도 6이다.'
        self.assertEqual(self.tokens(doc), ["6"])


class CliTest(unittest.TestCase):
    def write(self, name, text):
        d = tempfile.mkdtemp()
        path = os.path.join(d, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def run_cli(self, doc, numbers, *extra):
        doc_p = self.write("page.md", doc)
        num_p = self.write("numbers.json", json.dumps(numbers, ensure_ascii=False))
        return subprocess.run([sys.executable, CLI, "--doc", doc_p, "--numbers", num_p, *extra],
                              capture_output=True, encoding="utf-8", env=clean_env())

    def test_summary_line_and_strict(self):
        numbers = {"items": [calc(shown="0.4 mm", value=0.4, tol=0, expr="0.4")]}
        p = self.run_cli("점 8쌍에 0.4 mm 잡음.", numbers)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip().splitlines()[-1],
                         "요약: 재계산 통과 1 · 실패 0 · 출처만 0 · 미등록 숫자 1")
        p2 = self.run_cli("점 8쌍에 0.4 mm 잡음.", numbers, "--strict")
        self.assertEqual(p2.returncode, 1)

    def test_cli_korean_output_cp949(self):
        numbers = {"items": [{"id": "🎯 장면 길이", "kind": "계산", "shown": "3.09 m",
                              "value": 3.09, "tol": 0.01, "expr": "3.09"}]}
        p = self.run_cli("경로 길이는 3.09 m다.", numbers)
        self.assertNotIn("UnicodeEncodeError", p.stderr)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("🎯 장면 길이", p.stdout)


if __name__ == "__main__":
    unittest.main()
