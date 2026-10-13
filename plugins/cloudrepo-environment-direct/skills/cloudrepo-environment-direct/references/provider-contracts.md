# Provider contracts and capabilities

Provider-neutral planning uses capability names: `read_refs`, `read_runs`,
`read_jobs`, `publish_ci_ref`, `delete_owned_ref`, `observe_completion`, and
`verify_exact_sha`. Capabilities are evidence-backed per execution; a provider name
or connector binding grants none.

GitHub Actions is implemented through skill instructions only. Azure DevOps is a
future contract placeholder: no Azure client, connector, credentials, endpoint,
pipeline invocation, or claimed support exists in 0.1.0.
