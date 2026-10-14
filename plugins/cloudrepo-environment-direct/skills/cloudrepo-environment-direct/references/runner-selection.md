# Runner and test selection

Inspect, in this order: a matching existing workflow and its matrix, test config,
project manifests, lockfiles and explicit Root constraints. Reuse an existing
workflow only when its trigger, jobs and source revision can be correlated to the
request. A matrix is eligible only when its concrete OS values are observed.

Conservative local signals are a non-empty `package.json` `scripts.test` -> `npm test`,
pytest configuration -> `pytest`, explicit unittest evidence -> `python -m unittest discover`, `Cargo.toml` -> `cargo test`, and a verified
`.sln` -> `dotnet test` on `windows-latest`. They are planning hints, not execution
proof. Multiple frameworks, platform-specific files, unrecognized manifests or a
missing command are `ambiguous`; return candidate evidence and ask Root.

Prefer `ubuntu-latest` for portable checks, `windows-latest` for Windows-native
requirements, and `macos-latest` only for a verified Apple-specific requirement.
State why the selected runner and command cover the requested check.
