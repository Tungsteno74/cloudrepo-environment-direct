# Project memory

## Decisions

- GitHub Actions is the only implemented execution provider in 0.1.1.
- Agent Plugins 1.0 package lives at `plugins/cloudrepo-environment-direct`.
- The local Python planner is pure, offline and read-only; skills own execution.
- ChatGPT Chat is Root and makes the final executor decision.
- No Codex Cloud task, marketplace, remote, account publication, push, PR, merge,
  fork or default-branch write belongs to this repository.

## Verified

- The GitHub connector identifier supplied for optional binding is
  `connector_76869538009648d5b282a4bb21c3d157`.
- That identifier alone does not prove `workflow_dispatch`, ref deletion, write
  authority, or any specific GitHub API operation.
- The package and archive validation are offline and reproducible from source.
- GitHub Actions run 38574222069 passed this repository's `validate.yml` on
  Ubuntu and Windows; this verifies package CI, not full agent selection or
  external-executor authorization.

## Inferred

- Existing repository workflows are normally safer than temporary workflow
  publication because their policy and ownership can be observed first.
- A bounded static existing GitHub workflow can provide a conservative initial
  CI plan; unsupported, dynamic, multi-job, or conflicting shapes require Root.

## Unresolved

- No live GitHub connector capabilities were exercised by this repository.
- Azure DevOps support is a future provider contract, not an implementation.
- No marketplace or account publication has been authorized.
