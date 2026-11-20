import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "skills", "write-explainer")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
REFS = ["spec-template.md", "claims-evidence.md", "structure.md",
        "explain-devices.md", "korean-style.md", "review-rubric.md", "numbers-format.md"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


class SkillLayoutTest(unittest.TestCase):
    def test_skill_md_under_150_lines(self):
        self.assertLessEqual(len(read(SKILL_MD).splitlines()), 150)

    def test_skill_frontmatter_has_name_and_description(self):
        fm = frontmatter(read(SKILL_MD))
        self.assertEqual(fm.get("name"), "write-explainer")
        self.assertTrue(fm.get("description"))

    def test_every_reference_file_is_linked_from_skill_md(self):
        text = read(SKILL_MD)
        for ref in REFS:
            self.assertIn(f"references/{ref}", text)
            self.assertTrue(os.path.exists(os.path.join(SKILL_DIR, "references", ref)), ref)

    def test_scripts_referenced_exist(self):
        names = set(re.findall(r"scripts/([a-z_]+\.py)", read(SKILL_MD)))
        self.assertEqual(names, {"check_numbers.py", "check_terms.py", "check_style.py",
                                 "list_questions.py", "review_state.py"})
        for n in names:
            self.assertTrue(os.path.exists(os.path.join(SKILL_DIR, "scripts", n)), n)

    def test_skill_has_handoff_and_state_rules(self):
        text = read(SKILL_MD)
        for needle in ("AGENTS.md", "review_state.py status", "미검토"):
            self.assertIn(needle, text)

    def test_claims_only_if_is_one_direction(self):
        text = read(os.path.join(SKILL_DIR, "references", "claims-evidence.md"))
        self.assertIn("B ⇒ A", text)
        self.assertNotIn("양방향을 각각 증명하거나", text)

    def test_agents_frontmatter(self):
        for name in ("cold-reader", "rubric-reviewer"):
            fm = frontmatter(read(os.path.join(ROOT, "agents", f"{name}.md")))
            self.assertEqual(fm.get("name"), name)
            self.assertTrue(fm.get("description"), name)
            self.assertEqual(fm.get("tools"), "Read, Glob, Grep", name)

    def test_manifests_parse(self):
        plugin = json.loads(read(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
        market = json.loads(read(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])


if __name__ == "__main__":
    unittest.main()
