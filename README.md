# CloudRepo Environment Direct

Independent, skills-first direct CI planning for repositories that need a
deterministic GitHub Actions check. The plugin is primary when direct CI is
authorized; CloudCodeX Discovery or Bootstrap may recommend it only for a
verified eligible block. ChatGPT Chat remains the Root decision-maker.

`github-actions-direct` first reuses a matching existing workflow for the exact
full source SHA. A temporary `on.push` workflow is only a carefully gated option:
it needs explicit authorization, supported capabilities, a workflow-only diff,
SHA-pinned trusted actions, read-only permissions, a bounded timeout, observed
native checks and safe leased cleanup. It never writes a default branch, opens a
PR, merges, forks, publishes, invents credentials, or treats a READY task as pass.

The optional local planner is pure and read-only. It can recognize one bounded,
static existing GitHub Actions `push` workflow with a known runner or concrete OS
matrix and one non-dynamic command; it only produces a plan, never a passing-run
claim. Unsupported or conflicting workflow shapes require a Root override:

```powershell
python plugins/cloudrepo-environment-direct/runtime/planner.py --repo . --pretty
python -X utf8 tools/validate.py
python -X utf8 tools/build_release.py
```

The resulting standalone archive is placed in `dist/`, outside the plugin source
directory. This repository intentionally has no marketplace manifest, remote,
release publisher, or Azure DevOps provider implementation.

See [project memory](docs/PROJECT_MEMORY.md) and package
[README](plugins/cloudrepo-environment-direct/README.md).
