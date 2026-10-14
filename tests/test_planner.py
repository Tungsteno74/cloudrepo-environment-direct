from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "cloudrepo-environment-direct"))
from runtime.planner import Decision, choose_strategy, classify_status  # noqa: E402


class PlannerTests(unittest.TestCase):
    def test_real_repository_workflow_matrix_is_reused(self) -> None:
        plan = choose_strategy(ROOT, "442abe5ffaa0476955c2440d9756e5812e87b9f4")
        self.assertEqual(plan.runner, "ubuntu-latest, windows-latest")
        self.assertEqual(plan.command, "python -X utf8 tools/validate.py")
        self.assertFalse(plan.requires_write)
        self.assertIn("Reuse", plan.reason)

    def test_dynamic_or_malformed_workflow_needs_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workflow = root / ".github" / "workflows"
            workflow.mkdir(parents=True)
            (workflow / "ci.yml").write_text(
                "on:\n  push:\njobs:\n  validate:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@abc\n      - run: ${{ github.event.inputs.command }}\n", encoding="utf-8")
            plan = choose_strategy(root, "a" * 40)
            self.assertEqual(plan.command, "")
            self.assertIn("Root must choose", plan.reason)

    def test_malformed_workflow_needs_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workflow = root / ".github" / "workflows"
            workflow.mkdir(parents=True)
            (workflow / "ci.yml").write_text(
                "on:\n  push:\njobs:\n  validate:\n    runs-on: ubuntu-latest\n    steps: [not-a-step\n",
                encoding="utf-8")
            plan = choose_strategy(root, "a" * 40)
            self.assertEqual(plan.command, "")

    def test_arbitrary_pyproject_is_not_unittest_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
            plan = choose_strategy(root, None)
            self.assertEqual(plan.command, "")

    def test_unrecognized_workflow_blocks_manifest_inference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Cargo.toml").write_text("[package]", encoding="utf-8")
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "ci.yml").write_text("on:\n  workflow_dispatch:\n", encoding="utf-8")
            plan = choose_strategy(root, None)
            self.assertEqual(plan.command, "")
            self.assertIn("unsupported", plan.reason)

    def test_conflicting_safe_workflows_need_root_choice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            for name, command in (("one.yml", "python -m unittest"), ("two.yml", "pytest")):
                (workflows / name).write_text(
                    "on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@abc\n      - run: " + command + "\n", encoding="utf-8")
            plan = choose_strategy(root, "a" * 40)
            self.assertEqual(plan.command, "")
            self.assertIn("conflict", plan.reason)

    def test_ambiguous_manifests_need_root_choice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "package.json").write_text('{"scripts": {"test": "node test.js"}}', encoding="utf-8")
            (root / "Cargo.toml").write_text("[package]", encoding="utf-8")
            plan = choose_strategy(root, None)
            self.assertEqual(plan.command, "")
            self.assertIn("Ambiguous", plan.reason)

    def test_package_without_test_script_is_not_a_test_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "package.json").write_text('{"name": "x"}', encoding="utf-8")
            plan = choose_strategy(root, None)
            self.assertEqual(plan.command, "")

    def test_npm_default_placeholder_is_not_executable_test_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "package.json").write_text(
                '{"scripts":{"test":"echo \\"Error: no test specified\\" && exit 1"}}',
                encoding="utf-8",
            )
            self.assertEqual(choose_strategy(root, None).command, "")

    def test_nested_on_not_misrecognized_as_push_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / ".github" / "workflows"
            directory.mkdir(parents=True)
            (directory / "ci.yml").write_text(
                "metadata:\n  on: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
                "    steps:\n      - uses: actions/checkout@abc\n      - run: pytest\n",
                encoding="utf-8",
            )
            self.assertEqual(choose_strategy(root, None).command, "")

    def test_pytest_evidence_prefers_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
            plan = choose_strategy(root, None)
            self.assertEqual(plan.command, "pytest")

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
