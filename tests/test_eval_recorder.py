import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import eval_recorder as recorder


class ScenarioPolicyTests(unittest.TestCase):
    def test_all_fixtures_can_be_prepared_without_exposing_rubrics_in_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, case in recorder.load_cases().items():
                with self.subTest(case=name):
                    workspace = recorder.prepare(name, Path(directory) / name, "test", "test")
                    files = {name for name, item in recorder.snapshot(workspace).items()
                             if item["kind"] == "file"}
                    self.assertEqual(files, set(case["files"]))

    def test_every_turn_has_an_explicit_write_scope(self):
        cases = recorder.load_cases()
        policies = recorder.read_json(recorder.ROOT / "tests/write_scopes.json")
        self.assertEqual(set(cases), set(policies))
        for name, case in cases.items():
            with self.subTest(case=name):
                self.assertEqual(len(case["turns"]), len(policies[name]))
                for scope in policies[name]:
                    self.assertIsInstance(scope, list)
                    self.assertEqual(len(scope), len(set(scope)))
                    for path in scope:
                        recorder.safe_path(path)

    def test_enforcement_fixture_really_fails_the_legacy_baseline(self):
        case = recorder.load_cases()["existing-gate-fails-legacy-baseline"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in case["files"].items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            def run_check():
                return subprocess.run([sys.executable, "-B", "check_boundary.py"],
                                      cwd=root, capture_output=True, text=True, timeout=5)
            baseline = run_check()
            self.assertEqual(baseline.returncode, 1, baseline.stderr)
            self.assertIn("billing.py", baseline.stdout)
            (root / "billing.py").unlink()
            clean = run_check()
            self.assertEqual(clean.returncode, 0, clean.stderr)
            (root / "new_reach_in.py").write_text("from shipping_internal import status\n")
            mutation = run_check()
            self.assertEqual(mutation.returncode, 1, mutation.stderr)
            self.assertIn("new_reach_in.py", mutation.stdout)


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"

    def prepare(self, case="agreement-is-not-write-consent"):
        return recorder.prepare(case, self.run, "test-double-not-an-agent", "unit-test")

    def capture(self):
        recorder.capture(self.run, "Synthetic unit-test transcript, not an agent run.",
                         "Synthetic unit-test tool log; no agent tools executed.")

    def test_read_only_snapshots_are_accepted_but_not_semantically_passed(self):
        self.prepare()
        self.assertFalse(recorder.check(self.run)["observed_scope_ok"])
        self.capture()
        self.assertFalse(recorder.check(self.run)["recording_complete"])
        self.capture()
        result = recorder.check(self.run)
        self.assertTrue(result["observed_scope_ok"])
        self.assertEqual(result["behavioral_verdict"], "NOT_EVALUATED")
        self.assertEqual(result["provenance"], "externally-supplied-unverified")
        with self.assertRaises(ValueError):
            self.capture()

    def test_agreement_does_not_expand_the_allowed_scope(self):
        workspace = self.prepare()
        self.capture()
        (workspace / "ADR.md").write_text("Unauthorized decision")
        self.capture()
        result = recorder.check(self.run)
        self.assertFalse(result["observed_scope_ok"])
        self.assertEqual(result["turns"][1]["out_of_scope"], ["ADR.md"])

    def test_restoring_final_state_does_not_erase_an_earlier_violation(self):
        workspace = self.prepare()
        source = workspace / "pricing.py"
        original = source.read_bytes()
        source.write_text("Unauthorized implementation")
        self.capture()
        source.write_bytes(original)
        self.capture()
        result = recorder.check(self.run)
        self.assertFalse(result["observed_scope_ok"])
        self.assertIn("pricing.py", result["turns"][0]["out_of_scope"])

    def test_specific_later_consent_allows_only_the_adr(self):
        workspace = self.prepare("consent-narrows-after-agreement")
        self.capture()
        self.capture()
        (workspace / "docs/decisions/004-pricing.md").write_text("Accepted decision")
        self.capture()
        self.assertTrue(recorder.check(self.run)["observed_scope_ok"])

    def test_authorized_adr_does_not_allow_sibling_or_parent_changes(self):
        workspace = self.prepare("record-unresolved-decision-in-place")
        (workspace / "docs/decisions/007-report.md").write_text("Proposed decision")
        (workspace / "docs/decisions/template.md").write_text("Unauthorized template change")
        (workspace / "report.py").unlink()
        (workspace / "docs").chmod(0o700)
        self.capture()
        result = recorder.check(self.run)
        self.assertEqual(result["turns"][0]["out_of_scope"],
                         ["docs", "docs/decisions/template.md", "report.py"])

    def test_binary_mode_symlink_and_empty_directory_mutations_are_detected(self):
        workspace = self.prepare("greenfield-first-workflow")
        (workspace / "binary").write_bytes(b"\xff\x00")
        (workspace / "empty").mkdir()
        (workspace / "link").symlink_to(self.root, target_is_directory=True)
        self.capture()
        result = recorder.check(self.run)
        self.assertEqual(result["turns"][0]["out_of_scope"], ["binary", "empty", "link"])
        saved = recorder.read_json(self.run / "run.json")["turns"][0]["snapshot"]
        self.assertEqual(saved["binary"]["hex"], "ff00")
        self.assertEqual(saved["link"]["kind"], "symlink")
        self.assertNotIn("link/run", saved)
        before = recorder.snapshot(workspace)
        (workspace / "binary").chmod(0o755)
        self.assertEqual(recorder.scope_violations(before, recorder.snapshot(workspace), []),
                         ["binary"])

    def test_new_parent_directories_are_allowed_only_for_the_requested_path(self):
        before = {}
        after = {"docs": {"kind": "directory"},
                 "docs/ADR.md": {"kind": "file", "text": "decision"}}
        self.assertEqual(recorder.scope_violations(before, after, ["docs/ADR.md"]), [])
        after["docs/extra"] = {"kind": "directory"}
        self.assertEqual(recorder.scope_violations(before, after, ["docs/ADR.md"]),
                         ["docs/extra"])

    def test_prepare_does_not_overwrite_or_write_into_checkout(self):
        workspace = self.prepare()
        initial = recorder.snapshot(workspace)
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(recorder.snapshot(workspace), initial)
        with self.assertRaises(ValueError):
            recorder.prepare("greenfield-first-workflow", recorder.ROOT / "never-created",
                             "test", "test")
        manifest = recorder.read_json(self.run / "run.json")
        self.assertIn("skills/architecture-advisor/SKILL.md", manifest["skill"])
        self.assertEqual(set(initial), set(recorder.load_cases()["agreement-is-not-write-consent"]["files"]))

    def test_paths_reject_traversal_and_ambiguous_normalization(self):
        for name in ["", ".", "/tmp/escape", "../escape", "a/../../escape",
                     ".git/config", "a/.git/config", "a//b", "a/./b", "a/", "a\\b", "a\x00b"]:
            with self.subTest(path=name), self.assertRaises(ValueError):
                recorder.safe_path(name)

    def test_unsafe_or_conflicting_fixtures_are_rejected_before_creating_a_run(self):
        for files in [{"../escape": "bad"}, {"a": "file", "a/b": "conflict"}]:
            with self.subTest(files=files):
                with patch.object(recorder, "load_cases", return_value={"bad": {"files": files}}):
                    with self.assertRaises(ValueError):
                        recorder.prepare("bad", self.run, "test", "test")
                self.assertFalse(self.run.exists())

    def test_missing_evidence_or_workspace_is_not_a_clean_run(self):
        workspace = self.prepare("greenfield-first-workflow")
        for transcript, log in [("", "tools"), ("reply", " ")]:
            with self.assertRaises(ValueError):
                recorder.capture(self.run, transcript, log)
        workspace.rmdir()
        with self.assertRaises(ValueError):
            self.capture()

    def test_cli_never_labels_a_complete_recording_as_agent_success(self):
        self.prepare("greenfield-first-workflow")
        self.capture()
        process = subprocess.run([sys.executable, "-B", str(recorder.ROOT / "tests/eval_recorder.py"),
                                  "check", str(self.run)], capture_output=True, text=True, timeout=5)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["behavioral_verdict"], "NOT_EVALUATED")

    def test_cli_exits_nonzero_for_incomplete_or_violating_recordings(self):
        workspace = self.prepare("greenfield-first-workflow")
        command = [sys.executable, "-B", str(recorder.ROOT / "tests/eval_recorder.py"),
                   "check", str(self.run)]
        incomplete = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(incomplete.returncode, 1, incomplete.stderr)
        (workspace / "unauthorized.txt").write_text("mutation")
        self.capture()
        violation = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(violation.returncode, 1, violation.stderr)
        self.assertEqual(json.loads(violation.stdout)["turns"][0]["out_of_scope"],
                         ["unauthorized.txt"])
