---
name: cloudrepo-environment-direct
description: >-
  Plan deterministic direct CI for one exact repository revision. Use as the
  Root-facing skill when GitHub Actions may be primary, or when Discovery or
  Bootstrap has verified an eligible executor block. It does not create Cloud
  resources, publish refs, push, open PRs, merge, fork, or choose Root's executor.
---

# CloudRepo Environment Direct

ChatGPT Chat is Root: present evidence and a recommendation, but Root makes the
final executor decision. Treat one full, observed source SHA as one validation
request. Dirty or unpublished changes are excluded. First inspect repository files,
manifests, test configurations, existing workflows and the exact full source SHA.
Use the optional local planner only as a read-only suggestion.

Choose `ubuntu-latest`, `windows-latest`, `macos-latest`, or a verified existing
matrix only with a stated reason. Prefer matching existing CI before any write.
If manifests are ambiguous, return the alternatives and request a Root override;
never guess a command. Load [runner and test selection](references/runner-selection.md)
for that stage and [status schema](references/status-schema.md) for every result.

Use `$github-actions-direct` only once GitHub Actions is selected. It is the
implemented provider. Azure DevOps appears solely in
[provider contracts](references/provider-contracts.md), not as an executor.

Fallback is narrow. It may be recommended only after bounded, read-only checks of
the authoritative task, exact refs, Actions state and possible side effects verify
that the executor/plugin cannot be readied. `PENDING`, active workflows, denied
authorization, unknown mutation results, and `FAILED_CHECKS` are never fallbacks.
Read [fallback recommendations](references/fallback-recommendations.md) before
making one. A task marked READY is a planning state, not a passing check.
