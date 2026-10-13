# Authorization boundary

Read-only inspection needs only the actually available read channel. Any CI-ref
publication, workflow addition, ref move or deletion needs explicit Root/task
authorization for the exact repository, full source SHA, operation and retention
plan, plus confirmed provider capability. Technical ability is not consent.

Do not create a new remote, push, PR, merge, fork, account publication, credentials
or Cloud task. Do not infer authorization from a connector, repository ownership,
READY state, previous run, or silence. `gh` is allowed only if independently
authorized through RDC and authenticated by the existing environment.
