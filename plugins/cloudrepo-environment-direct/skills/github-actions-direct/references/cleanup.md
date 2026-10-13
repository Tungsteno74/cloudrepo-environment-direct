# Cleanup and retention

Delete or move only a clearly run-owned, non-default ref after its workflow is
terminal and expected tip still matches the recorded lease. Never delete user,
default, unknown or changed refs. Keep Actions history by default. If cleanup cannot
be proven, report `cleanup: required` and exact remaining resource; do not claim it
completed. Active workflows require `cleanup: pending`.
