import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/architecture-advisor/SKILL.md"
SCENARIOS = ROOT / "tests/scenarios.json"
ADVERSARIAL = ROOT / "tests/adversarial_scenarios.json"


class SkillContractTests(unittest.TestCase):
    def test_skill_metadata_and_workflow(self):
        text = SKILL.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(frontmatter)
        self.assertIn("name: architecture-advisor", frontmatter[1])
        self.assertIn("MANUAL USE ONLY", frontmatter[1])
        self.assertIn('version: "2.0"', frontmatter[1])
        headings = re.findall(r"^## (\d+)\. (.+)$", text, re.M)
        self.assertEqual(headings, [
            ("1", "Frame one decision"),
            ("2", "Inspect a representative workflow"),
            ("3", "Compare feasible options"),
            ("4", "Recommend the smallest useful step"),
            ("5", "Persist only on explicit request"),
        ])
        self.assertLessEqual(len(text.split()), 1800)

    def test_explicit_policy_contracts_remain_present(self):
        text = " ".join(SKILL.read_text(encoding="utf-8").split())
        contracts = {
            "constraints": "Hard constraints are feasibility gates, not scoring signals.",
            "baseline": "including keeping the current approach",
            "evidence": "Distinguish observed facts, user-reported symptoms, and hypotheses.",
            "uncertainty": "do not force a winner",
            "consent": "Agreeing with a recommendation is not authorization to edit files.",
            "transition": "current state, proposed target, and rules effective now",
            "enforcement": "baseline passes while a representative new violation fails",
        }
        for contract, clause in contracts.items():
            with self.subTest(contract=contract):
                self.assertIn(clause, text)

    def test_local_references_exist_and_are_used(self):
        references = SKILL.parent / "references"
        mentioned = set(re.findall(
            r"`(references/[^`]+\.md)`", SKILL.read_text(encoding="utf-8")
        ))
        self.assertTrue(mentioned)
        actual = {str(path.relative_to(SKILL.parent)) for path in references.glob("*.md")}
        self.assertEqual(mentioned, actual)
        for relative in mentioned:
            with self.subTest(reference=relative):
                path = SKILL.parent / relative
                self.assertTrue(path.is_file())
                self.assertTrue(path.read_text(encoding="utf-8").startswith("# "))

    def test_readme_local_links_exist(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", text)
        self.assertTrue(links)
        for link in links:
            if "://" not in link:
                with self.subTest(link=link):
                    self.assertTrue((ROOT / link).is_file())

    def test_behavioral_scenarios_are_complete_and_safe_to_materialize(self):
        scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        scenarios += json.loads(ADVERSARIAL.read_text(encoding="utf-8"))
        ids = [case["id"] for case in scenarios]
        self.assertEqual(len(ids), len(set(ids)))
        covered = set()
        for case in scenarios:
            with self.subTest(case=case["id"]):
                self.assertEqual(set(case), {
                    "id", "covers", "files", "turns", "evidence", "pass", "fail"
                })
                for field in ("covers", "turns", "pass", "fail"):
                    self.assertIsInstance(case[field], list)
                    self.assertTrue(case[field])
                    self.assertTrue(all(isinstance(item, str) and item.strip()
                                        for item in case[field]))
                covered.update(case["covers"])
                self.assertIsInstance(case["files"], dict)
                self.assertIsInstance(case["evidence"], list)
                for name, content in case["files"].items():
                    path = Path(name)
                    self.assertFalse(path.is_absolute())
                    self.assertNotIn("..", path.parts)
                    self.assertNotIn(".git", path.parts)
                    self.assertTrue(content.strip())
                    if path.suffix == ".py":
                        compile(content, name, "exec")
                for evidence in case["evidence"]:
                    self.assertEqual(set(evidence), {"path", "contains"})
                    self.assertIn(evidence["path"], case["files"])
                    self.assertTrue(evidence["contains"])
                    self.assertIn(evidence["contains"], case["files"][evidence["path"]])
        self.assertEqual(covered, {
            "restraint", "constraints", "evidence", "transition", "consent",
            "uncertainty", "greenfield", "mechanism-independence",
            "contradictions", "write-scope", "enforcement",
        })
