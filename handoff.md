# Capability Architecture Handoff

This handoff is for a fresh Codex session working on Vraksha's tool/expert and
capability architecture.

## Current Goal

Move Vraksha from direct tool exposure toward a robust capability architecture:

```text
Agent -> Capability Request -> Broker -> Tool/Expert -> Sandbox/Implementation -> Result
```

The registry and discovery layer now works end-to-end. The broker layer is not
implemented yet.

## Project Context

Workspace:

```text
/mnt/win_c/active_projects/Vraksha
```

Python environment used during this work:

```bash
.venv/bin/python -m pytest
```

There is also an older `venv/`, but `.venv/` is the one with pytest and project
dependencies installed.

Current pytest result:

```text
9 passed
```

## Important Files

Architecture guides:

```text
guides/capability_system.md
guides/tools_and_experts.md
guides/capability_broker.md
guides/guide.md
registry/guide.md
```

Registry and discovery:

```text
registry/register.py
registry/base.py
registry/validate.py
registry/discovery.py
src/agent/initialize_tools/bootstrap_tools.py
src/agent/initialize_tools/tool_adapter.py
```

Current tools:

```text
src/agent/search_memory.py
tools/file_system/create_file.py
tools/file_system/get_tree.py
tools/file_system/read_file.py
tools/file_system/remove_file.py
tools/file_system/write_file.py
tools/system/command_tool.py
```

Current expert:

```text
experts/slop_detector/skill.py
experts/slop_detector/SKILL.md
```

LLM visibility/debug:

```text
tests/test_llm_view.py
llm_view_snapshot.json
```

Registry tests:

```text
tests/test_registry_discovery.py
```

## What Was Implemented

### Pytest Setup

Added:

```text
pyproject.toml
```

Current config:

```toml
[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]
python_files = ["*.py"]
python_functions = ["test_*"]
```

`tests/test_wiki.py` was made non-interactive. It used to call `input()` at
import time, which broke pytest collection.

### Memory Test Fixes

The memory layer had async wrappers using `asyncio.to_thread()`. In this
environment that completed work but left the process alive, causing pytest to
hang. The async wrappers in `src/memory/local_index.py` now call sync
implementations directly.

Also added:

```python
async def remember(self, record: MemoryRecord) -> None
```

Raw journal trust was lowered from `0.45` to `0.20` so raw journal contents do
not leak expired/low-trust poisoned memories back into search results.

`src/memory/wiki.py` had a stale import for `atomic_append`; it now imports it
from:

```python
src.memory.utils.async_journal_writer
```

### Registry Discovery

Added:

```text
registry/discovery.py
```

Discovery imports only modules that:

* import `registry.register`
* contain `@tool` or `@expert`
* are not under ignored dirs like `tests/`, `.venv/`, `venv/`, `.git/`, caches,
  assets, or memory

This avoids importing unrelated broken modules.

Current discovery result:

```text
entries 8
errors 0
```

Registered entries currently include:

```text
expert.forensics.slop_detector
tool.system.search_memory
tool.filesystem.create_file
tool.filesystem.get_tree_structure
tool.filesystem.read_file
tool.filesystem.remove_file
tool.system.write_file
tool.system.run_command
```

### Agent Tool Mounting

`src/agent/initialize_tools/bootstrap_tools.py` now calls:

```python
discover_registry_modules()
```

before:

```python
ToolAdapter(agent).register_all()
```

### Tool Adapter

`src/agent/initialize_tools/tool_adapter.py` wraps registry entries as
PydanticAI tools.

Important details:

* registry key dots become underscores:

```text
tool.system.run_command -> tool_system_run_command
expert.forensics.slop_detector -> expert_forensics_slop_detector
```

* wrapper signatures are generated from `input_schema`
* wrapper `__annotations__` are required for PydanticAI schema generation
* JSON schema `enum` becomes `typing.Literal[...]` so the LLM sees enum values

Tool calls currently invoke:

```python
tool_instance.call(kwargs)
```

The call contract is:

```python
def call(self, tool_input: dict) -> dict:
    ...
```

Expected return shape:

```python
{"success": True, "data": {...}, "error": None}
```

### Search Memory Tool

`src/agent/search_memory.py` used to be an async function decorated with
`@tool`, but the validator expects class-style registry objects. It is now:

```python
@tool(enabled=True, domain="system", tags=["core", "memory"])
class SearchMemoryTool:
    name = "search_memory"
    ...
```

It calls `memory_coordinator.memory.search_sync(...)` and returns structured
output.

### Slop Detector Expert

`experts/slop_detector/skill.py` was legacy and imported stale modules:

```python
skills.base
skills.slop_detector.llm
```

It was converted into:

```python
@expert(enabled=True, domain="forensics", tags=[...])
class SlopDetectorExpert:
    name = "slop_detector"
    instruction_files = ["experts/slop_detector/SKILL.md"]
```

It currently returns a structured placeholder:

```text
status: queued_for_analysis
```

It does not yet perform real forensic analysis. This expert needs the next real
rewrite.

## What the LLM Currently Sees

Run:

```bash
.venv/bin/python -m pytest tests/test_llm_view.py -q
```

Then inspect:

```text
llm_view_snapshot.json
```

Current callable entries visible to the LLM:

```text
expert_forensics_slop_detector
tool_system_search_memory
tool_filesystem_create_file
tool_filesystem_get_tree_structure
tool_filesystem_read_file
tool_filesystem_remove_file
tool_system_write_file
tool_system_run_command
```

`tests/test_llm_view.py` uses async `vraksha_agent.run(...)`, not
`run_sync(...)`, because `run_sync()` caused a Python 3.12 event loop
deprecation warning.

The `null` fields in `llm_view_snapshot.json` are optional PydanticAI metadata
from `TestModel`; they are not bugs.

## Key Design Decision

Do not rewrite the registry. It is a good foundation.

Do not blindly rewrite all tools.

Do move toward:

```text
small primitive tools + many reasoning experts + broker policy boundary
```

The guides now document this direction.

## Current Architecture Gap

The guides describe a brokered capability architecture, but runtime currently
mounts tools and experts directly on the agent through `ToolAdapter`.

Current:

```text
Agent -> PydanticAI tool -> ToolAdapter -> tool/expert.call()
```

Target:

```text
Agent -> request_capability -> CapabilityBroker -> policy -> implementation
```

The next major architecture task is to build the broker layer.

## Recommended Next Steps

### 1. Add Capability Broker

Create something like:

```text
src/capabilities/broker.py
src/capabilities/policy.py
src/capabilities/request.py
src/capabilities/result.py
```

Expose one agent-facing tool:

```text
tool.capability.request_capability
```

Potential input schema:

```json
{
  "capability": "execute_command",
  "arguments": {},
  "reason": "why the agent needs this"
}
```

The broker should route to registry entries internally.

### 2. Decide Capability Names

Map current tools to capabilities:

```text
file_read -> tool.filesystem.read_file
file_write -> tool.system.write_file
file_create -> tool.filesystem.create_file
file_delete -> tool.filesystem.remove_file
file_tree -> tool.filesystem.get_tree_structure
execute_command -> tool.system.run_command
memory_search -> tool.system.search_memory
invoke_expert.slop_detector -> expert.forensics.slop_detector
```

Long term, consolidate file tools into a smaller filesystem primitive.

### 3. Implement Policy Checks

Start simple:

* allow read/tree/search always inside project
* allow write/create/delete only inside project and not immutable
* require stricter checks for shell
* cap timeouts
* cap output size
* log every request

Then expand toward the guide's full model.

### 4. Refactor Tools Into Primitives

Current filesystem tools are split. That is okay for now, but the guide points
toward a primitive filesystem capability.

Potential future:

```text
tool.filesystem.operate
```

with:

```json
{
  "operation": "read|write|append|list|delete|exists|stat|search",
  "path": "...",
  "content": "...",
  "max_depth": 3
}
```

Do this after the broker exists, not before.

### 5. Rewrite Slop Detector Expert

Current `experts/slop_detector/services/*` contains stale imports like:

```python
src.skills...
skills...
```

The real rewrite should:

* use `experts.slop_detector...` imports
* fetch GitHub content safely
* analyze commit/content signals
* return YAML-ish structured verdict per `SKILL.md`
* avoid importing broken service modules during discovery
* use tools or brokered capabilities for network/content access when broker
  exists

## Gotchas

### Discovery Is Import-Side-Effect Based

Decorators run only when modules are imported. Do not hide decorated classes
inside functions.

### Disabled Capabilities

`enabled=False` means the decorator returns the class without registering it.
It will not be mounted.

### Validator Requires Dict Schemas

`input_schema` and `output_schema` must be JSON-schema dictionaries, not lists.

### Experts Need Existing Markdown Files

`instruction_files` must be a non-empty list of `.md` paths that exist relative
to the project root/current working directory.

### ToolAdapter Currently Treats Experts Like Tools

This is intentional for now: experts appear as callable PydanticAI tools.
The broker should eventually distinguish routing/policy.

### `tests/tool_use.py`

Pytest currently collects all `.py` files in `tests/`, but only functions named
`test_*`. `tests/tool_use.py` has a simple import test and passes.

### `requirements-dev.txt`

A `requirements-dev.txt` file was created with:

```text
-r requirements.txt
pytest
```

But local `.git/info/exclude` ignores `*.txt`, so it may not show in `git
status`.

## Commands To Verify

Run focused tests:

```bash
.venv/bin/python -m pytest tests/test_registry_discovery.py tests/test_llm_view.py -q
```

Run all tests:

```bash
.venv/bin/python -m pytest
```

Inspect LLM surface:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
snapshot = json.loads(Path("llm_view_snapshot.json").read_text(encoding="utf-8"))
for tool in snapshot["tools"]:
    print(tool["name"])
PY
```

## Current Working Tree Awareness

There are several modified/untracked files from prior work. Do not revert user
changes casually. The important files changed during this architecture work
include:

```text
registry/discovery.py
src/agent/initialize_tools/bootstrap_tools.py
src/agent/initialize_tools/tool_adapter.py
src/agent/search_memory.py
experts/slop_detector/skill.py
tests/test_llm_view.py
tests/test_registry_discovery.py
guides/*.md
registry/guide.md
handoff.md
```

## One-Sentence State

Vraksha currently has working decorator discovery and direct agent mounting for
tools/experts; the next robust/security-first step is to insert a
CapabilityBroker between the agent and registered implementations.
