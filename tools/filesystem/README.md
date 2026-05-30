# Filesystem Primitive

Purpose: read, write, list, and search workspace files through broker policy.

Planned capability names:

* `file_read`
* `file_write`
* `file_list`
* `file_search`

Keep this layer deterministic. Path validation, workspace boundaries, immutable
file checks, and output limits belong at the broker/policy boundary before this
primitive executes.
