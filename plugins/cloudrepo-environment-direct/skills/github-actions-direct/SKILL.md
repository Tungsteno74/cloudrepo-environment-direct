---
name: github-actions-direct
description: >-
 Plan and, only with independently confirmed authorization and capabilities,
 execute deterministic GitHub Actions CI for an exact source SHA. Reuse matching
 existing CI first. Do not use this skill for PRs, merges, forks, default-branch
 writes, credential creation, or unsupported GitHub connector operations.
---

# GitHub Actions direct CI

Use the optional GitHub connector only for operations it actually exposes. Its
presence does **not** establish `workflow_dispatch`, `delete_ref`, mutation rights,
or login identity. Independently authorized `gh` through RDC may be used only when
available; never invent credentials or use a connector identifier as a token.

Read [authorization](references/authorization.md) and
[GitHub execution](references/github-actions-execution.md) before external actions.
Verify the complete source SHA, repository identity, existing workflow trigger,
observed run/jobs and exact checked-out SHA. Existing matching CI is preferred.

Only if the Root explicitly authorizes publication and all capabilities are proven,
publish a unique non-default CI ref for an `on.push` workflow. Require a
workflow-only diff, trusted actions pinned to full SHAs, `permissions: contents:
read`, `persist-credentials: false`, checkout of exact source SHA plus native SHA
verification, finite timeout, explicit native checks, and observed job completion.
Never silently replace application tests or report pass from task readiness.

Before retrying after any ambiguous write, use
[idempotent reconciliation](references/idempotent-reconciliation.md). A pending or
active correlated run blocks duplicate publication and cleanup. Perform only safe,
owned cleanup with an expected-SHA lease; use
[cleanup](references/cleanup.md). Report with the shared status schema.
