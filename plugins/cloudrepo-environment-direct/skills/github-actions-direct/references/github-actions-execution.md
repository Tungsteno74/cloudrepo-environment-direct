# GitHub Actions execution

First correlate existing CI to exact full source SHA and requested checks. Observe
the intended runner/job and terminal conclusion. If it fails, return
`FAILED_CHECKS`; do not fallback.

For an authorized temporary workflow, use a unique run-owned non-default branch and
an `on.push.branches` trigger matching only it. The diff may contain the workflow
only. It must use GitHub-hosted selected runner, finite timeout, `permissions:
contents: read`, full-SHA-pinned trusted actions, checkout exact source SHA with
`persist-credentials: false`, verify `git rev-parse HEAD`, and run explicit native
commands. No caches, uploads, secrets, OIDC or broad permissions.

Observe the correlated run and jobs boundedly. No completion means `PENDING`, not
another write. Connector support for `workflow_dispatch` or `delete_ref` must be
observed, never assumed.
