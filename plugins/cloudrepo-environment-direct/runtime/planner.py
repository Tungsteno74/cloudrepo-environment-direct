"""Offline repository CI planner; it never calls a provider or changes files."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence


class Provider(str, Enum):
    GITHUB_ACTIONS = "github_actions"
    AZURE_DEVOPS = "azure_devops"


class Decision(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    FAILED_CHECKS = "FAILED_CHECKS"
    PENDING = "PENDING"
    FALLBACK_RECOMMENDED = "FALLBACK_RECOMMENDED"


@dataclass(frozen=True)
class ProviderCapabilities:
    provider: Provider
    read_refs: bool = False
    read_actions: bool = False
    publish_ci_ref: bool = False
    delete_ref: bool = False
    workflow_dispatch: bool = False


@dataclass(frozen=True)
class Strategy:
    runner: str
    command: str
    reason: str
    workflow: Optional[str]
    source_sha: Optional[str]
    requires_write: bool = False


@dataclass(frozen=True)
class Status:
    decision: Decision
    reason: str
    fallback_eligible: bool
    next_action: str


def classify_status(event: str, *, authoritative_reads_complete: bool = False) -> Status:
    """Classify terminal state without converting uncertainty into fallback."""
    states: Dict[str, Status] = {
        "checks_failed": Status(Decision.FAILED_CHECKS, "Native CI checks failed.", False, "report checks"),
        "pending": Status(Decision.PENDING, "Workflow remains active or observation is incomplete.", False, "observe"),
        "auth_denied": Status(Decision.BLOCKED, "Provider authorization was denied.", False, "request authorization"),
        "unknown_mutation": Status(Decision.BLOCKED, "Mutation outcome is unknown; reconcile first.", False, "reconcile"),
        "progressing": Status(Decision.PENDING, "A correlated workflow is still progressing.", False, "observe"),
        "ready": Status(Decision.READY, "Planning is ready; this is not a CI pass.", False, "Root chooses executor"),
    }
    if event == "executor_unavailable" and authoritative_reads_complete:
        return Status(Decision.FALLBACK_RECOMMENDED, "Verified executor or plugin readiness block after bounded reads.", True, "return to Root")
    return states.get(event, Status(Decision.BLOCKED, "Unknown or unverified state.", False, "verify state"))


_KNOWN_RUNNERS = {"ubuntu-latest", "windows-latest", "macos-latest"}
_DYNAMIC_COMMAND = re.compile(
    r"\$\{|\$\(|`|\b(?:eval|exec)\b|\b(?:sh|bash|pwsh|powershell)\s+-(?:c|command)\b",
    re.IGNORECASE,
)


def _indented_lines(text: str) -> Sequence[tuple[int, str]]:
    """Return non-comment YAML-like lines for the deliberately bounded reader."""
    lines: List[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#") or "\t" in raw_line:
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, raw_line.strip()))
    return lines


def _has_push_trigger(lines: Sequence[tuple[int, str]]) -> bool:
    for index, (indent, line) in enumerate(lines):
        if indent == 0 and (line == "on: push" or line == "on: [push]"):
            return True
        if line != "on:" or indent != 0:
            continue
        for child_indent, child_line in lines[index + 1:]:
            if child_indent <= indent:
                break
            if child_indent == 2 and (child_line == "push:" or child_line.startswith("push:")):
                return True
    return False


def _workflow_strategy(path: Path, source_sha: Optional[str]) -> Optional[Strategy]:
    """Recognize one safe, intentionally narrow GitHub Actions workflow shape.

    This is not a YAML parser. Unsupported YAML, multiple jobs, expressions in a
    command, and anything other than the bounded profile return ``None``.
    """
    try:
        lines = _indented_lines(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return None
    if not _has_push_trigger(lines):
        return None

    jobs = [(index, indent) for index, (indent, line) in enumerate(lines) if line == "jobs:"]
    if len(jobs) != 1:
        return None
    start, jobs_indent = jobs[0]
    job_names: List[tuple[int, int]] = []
    for index, (indent, line) in enumerate(lines[start + 1:], start + 1):
        if indent <= jobs_indent:
            break
        if indent == jobs_indent + 2 and re.fullmatch(r"[A-Za-z0-9_-]+:", line):
            job_names.append((index, indent))
    if len(job_names) != 1:
        return None
    job_start, job_indent = job_names[0]
    job_end = next((index for index, (indent, _) in enumerate(lines[job_start + 1:], job_start + 1)
                    if indent <= jobs_indent), len(lines))
    job_lines = lines[job_start:job_end]

    runner_values = [line.split(":", 1)[1].strip() for indent, line in job_lines
                     if indent == job_indent + 2 and line.startswith("runs-on:")]
    if len(runner_values) != 1:
        return None
    runner = runner_values[0].strip("'\"")
    matrix_values: List[str] = []
    if runner == "${{ matrix.os }}":
        matrix_values = [line.split(":", 1)[1].strip() for indent, line in job_lines
                         if line.startswith("os:") and indent > job_indent]
        if len(matrix_values) != 1:
            return None
        match = re.fullmatch(r"\[\s*([A-Za-z-]+(?:\s*,\s*[A-Za-z-]+)*)\s*\]", matrix_values[0])
        if not match:
            return None
        runners = [value.strip() for value in match.group(1).split(",")]
        if not runners or any(value not in _KNOWN_RUNNERS for value in runners):
            return None
        runner = ", ".join(runners)
    elif runner not in _KNOWN_RUNNERS:
        return None

    commands = [line.split(":", 1)[1].strip().strip("'\"") for indent, line in job_lines
                if line.startswith("- run:") and indent > job_indent]
    concrete_steps = [line for _, line in job_lines if line.startswith("- uses:") or line.startswith("- run:")]
    if len(commands) != 1 or len(concrete_steps) < 2:
        return None
    command = commands[0]
    if not command or command in {"|", ">", "|-", ">-"} or _DYNAMIC_COMMAND.search(command) or "\n" in command:
        return None
    return Strategy(runner, command, "Reuse a safe, observed existing GitHub Actions workflow; this is a plan, not a passed run.",
                    str(path), source_sha)


def _commands(root: Path) -> List[tuple[str, str]]:
    commands: List[tuple[str, str]] = []
    package = root / "package.json"
    if package.is_file():
        try:
            scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
        except (OSError, UnicodeError, json.JSONDecodeError):
            scripts = {}
        test_script = scripts.get("test") if isinstance(scripts, dict) else None
        if (isinstance(test_script, str) and test_script.strip()
                and "no test specified" not in test_script.lower()):
            commands.append(("ubuntu-latest", "npm test"))
    pytest_evidence = (root / "pytest.ini").is_file()
    unittest_evidence = (root / "unittest.cfg").is_file()
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            pyproject_text = pyproject.read_text(encoding="utf-8")
            pytest_evidence = pytest_evidence or "[tool.pytest" in pyproject_text
            unittest_evidence = unittest_evidence or "unittest" in pyproject_text.lower()
        except (OSError, UnicodeError):
            pass
    setup = root / "setup.cfg"
    if setup.is_file():
        try:
            setup_text = setup.read_text(encoding="utf-8").lower()
            pytest_evidence = pytest_evidence or "[tool:pytest]" in setup_text
            unittest_evidence = unittest_evidence or "unittest" in setup_text
        except (OSError, UnicodeError):
            pass
    if pytest_evidence:
        commands.append(("ubuntu-latest", "pytest"))
    elif unittest_evidence:
        commands.append(("ubuntu-latest", "python -m unittest discover"))
    if (root / "Cargo.toml").is_file():
        commands.append(("ubuntu-latest", "cargo test"))
    if list(root.glob("*.sln")):
        commands.append(("windows-latest", "dotnet test"))
    return commands


def choose_strategy(root: Path, source_sha: Optional[str], runner_override: Optional[str] = None,
                    command_override: Optional[str] = None) -> Strategy:
    """Prefer an existing workflow; otherwise return conservative inferred checks."""
    if source_sha is not None and not re.fullmatch(r"[0-9a-fA-F]{40}", source_sha):
        raise ValueError("source_sha must be a complete 40-character Git SHA.")
    workflows = sorted((root / ".github" / "workflows").glob("*.y*ml")) if (root / ".github" / "workflows").is_dir() else []
    if runner_override and command_override:
        return Strategy(runner_override, command_override, "Explicit Root override.", str(workflows[0]) if workflows else None, source_sha)
    workflow_candidates = [plan for path in workflows if (plan := _workflow_strategy(path, source_sha))]
    if len(workflow_candidates) == 1:
        return workflow_candidates[0]
    if len(workflow_candidates) > 1:
        return Strategy("", "", "Multiple safe existing workflows conflict; Root must choose checks.", None, source_sha)
    if workflows:
        return Strategy("", "", "Existing workflow is unsupported or ambiguous; Root must choose checks.",
                        str(workflows[0]), source_sha)
    candidates = _commands(root)
    if len(candidates) != 1:
        return Strategy("", "", "Ambiguous framework or no recognized manifest; Root must choose checks.", str(workflows[0]) if workflows else None, source_sha)
    runner, command = candidates[0]
    reason = "Reuse the observed existing workflow before any write." if workflows else "Inferred from a single local manifest; requires Root review."
    return Strategy(runner, command, reason, str(workflows[0]) if workflows else None, source_sha, not bool(workflows))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source-sha")
    parser.add_argument("--runner")
    parser.add_argument("--command")
    parser.add_argument("--manifest", type=Path, help="Optional local JSON override manifest.")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    manifest: Dict[str, object] = {}
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must contain a JSON object.")
    source_sha = args.source_sha or manifest.get("source_sha")
    runner = args.runner or manifest.get("runner")
    command = args.command or manifest.get("command")
    if not all(value is None or isinstance(value, str) for value in (source_sha, runner, command)):
        raise ValueError("manifest source_sha, runner and command must be strings.")
    plan = choose_strategy(args.repo.resolve(), source_sha, runner, command)
    print(json.dumps(asdict(plan), indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
