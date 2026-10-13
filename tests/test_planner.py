from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "cloudrepo-environment-direct"))
from runtime.planner import Decision, choose_strategy, classify_status  # noqa: E402


class PlannerTests(unittest.TestCase):
    def test_python_project_prefers_existing_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
            workflow = root / ".github" / "workflows"
            workflow.mkdir(parents=True)
            (workflow / "ci.yml").write_text("name: CI\n", encoding="utf-8")
            plan = choose_strategy(root, "a" * 40)
            self.assertEqual(plan.runner, "ubuntu-latest")
            self.assertFalse(plan.requires_write)
            self.assertIn("Reuse", plan.reason)

    def test_ambiguous_manifests_need_root_choice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "Cargo.toml").write_text("[package]", encoding="utf-8")
            plan = choose_strategy(root, None)
            self.assertEqual(plan.command, "")
            self.assertIn("Ambiguous", plan.reason)

    def test_explicit_override_wins(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan = choose_strategy(Path(temporary), "b" * 40, "windows-latest", "dotnet test")
            self.assertEqual((plan.runner, plan.command), ("windows-latest", "dotnet test"))

    def test_abbreviated_sha_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                choose_strategy(Path(temporary), "abc1234")

    def test_non_fallback_states_stay_non_fallback(self) -> None:
        for event, decision in (("pending", Decision.PENDING), ("auth_denied", Decision.BLOCKED),
                                ("unknown_mutation", Decision.BLOCKED), ("progressing", Decision.PENDING),
                                ("checks_failed", Decision.FAILED_CHECKS)):
            result = classify_status(event, authoritative_reads_complete=True)
            self.assertEqual(result.decision, decision)
            self.assertFalse(result.fallback_eligible)

    def test_verified_executor_block_is_only_fallback_case(self) -> None:
        self.assertFalse(classify_status("executor_unavailable").fallback_eligible)
        self.assertTrue(classify_status("executor_unavailable", authoritative_reads_complete=True).fallback_eligible)
