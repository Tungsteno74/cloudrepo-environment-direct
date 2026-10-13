# Fallback recommendations

Run bounded read-only checks first: authoritative task/plugin availability, exact
source ref, correlated Actions runs/jobs, and provider-visible side effects. A
fallback recommendation needs an eligible, verified executor/readiness block after
those checks. Include the failed capability and evidence.

Never recommend fallback for code or test failure (`FAILED_CHECKS`), `PENDING`, an
actively progressing workflow, authorization denial, uncertain mutation state, or
an unverified absence. Reconcile uncertain writes first. Discovery and Bootstrap
may recommend this plugin only under the same rule; this plugin does not modify
them.
