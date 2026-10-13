# Idempotent reconciliation

After timeout, cancellation, approval transition or generic mutation error, retain
run identity and perform bounded read-only inspection of exact refs/tips, workflow
content, correlated runs/jobs and known owned resources. Classify the result as
`confirmed_absent`, `confirmed_present`, `in_progress`, `terminal`, or
`inconclusive`.

Only `confirmed_absent` permits one identical authorized retry. Present/in-progress
state resumes observation or cleanup. Inconclusive state stops: it is neither no-op
nor a fallback condition.
