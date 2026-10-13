# Project memory

## Decisions

- GitHub Actions is the only implemented execution provider in 0.1.0.
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

## Inferred

- Existing repository workflows are normally safer than temporary workflow
  publication because their policy and ownership can be observed first.
- Python project manifests can provide a conservative initial test selection.

## Unresolved

- No live GitHub connector capabilities were exercised by this repository.
- Azure DevOps support is a future provider contract, not an implementation.
- No marketplace or account publication has been authorized.
