"""Offline repository CI planner; it never calls a provider or changes files."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


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


def _commands(root: Path) -> List[tuple[str, str]]:
    commands: List[tuple[str, str]] = []
    if (root / "package.json").is_file():
        commands.append(("ubuntu-latest", "npm test"))
    if (root / "pyproject.toml").is_file() or (root / "pytest.ini").is_file() or (root / "setup.cfg").is_file():
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
    candidates = _commands(root)
    if runner_override and command_override:
        return Strategy(runner_override, command_override, "Explicit Root override.", str(workflows[0]) if workflows else None, source_sha)
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
