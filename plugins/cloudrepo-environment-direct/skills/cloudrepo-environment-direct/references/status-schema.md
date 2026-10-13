# Status schema

Return a structured result with: `status`, `source_repository`, `source_revision`
(full SHA or `not_observed`), `provider`, `strategy`, `runner`, `command`,
`workflow`, `actions_run`, `checks`, `evidence`, `authorization`, `side_effects`,
`reconciliation`, `cleanup`, `fallback_eligible`, and `next_action`.

Allowed terminal statuses: `READY` (plan only), `PASSED`, `FAILED_CHECKS`,
`PENDING`, `BLOCKED`, `AUTHORIZATION_REQUIRED`, and `FALLBACK_RECOMMENDED`.
`READY` never means `PASSED`. Include `default_branch_written: false` unless an
actual observed result proves otherwise; this plugin must never cause it.
