# Shell Primitive

Purpose: execute commands in a sandbox for git, tests, build tools, and local
project automation.

Planned capability names:

* `shell_run`

This primitive should never expose unrestricted host execution. Timeouts,
working-directory checks, command policy, and output caps belong at the
broker/policy boundary.
