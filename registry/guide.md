# Registry System Guide

The registry system provides a centralized and validated way to register:

* Tools
* Experts (sub-agents)

Registration is performed entirely through decorators.

Users are NOT required to inherit from any base class.

---

# Quick Start

```python
from registry.register import tool, expert
```

---

# Tool Registration

```python
@tool(
    enabled=True,
    domain="web",
    tags=["read", "retrieve"]
)
class SearchTool:
    name = "search_tool"
    description = "Searches the web"

    input_schema = [
        {
            "query": "str"
        }
    ]

    output_schema = [
        {
            "result": "str"
        }
    ]

    def call(self, query: str):
        return "..."
```

---

# Expert Registration

```python
@expert(
    domain="finance",
    tags=["analysis", "markets"]
)
class FinanceExpert:
    name = "finance_expert"
    description = "Handles finance-related reasoning"

    input_schema = [
        {
            "question": "str"
        }
    ]

    output_schema = [
        {
            "answer": "str"
        }
    ]

    instruction_files = [
        "finance.md"
    ]

    def call(self, question: str):
        return "..."
```

---

# Decorator Arguments

## `enabled`

```python
enabled=True
```

Whether the object should be registered.

Default:

```python
True
```

If set to:

```python
enabled=False
```

the class is ignored by the registry.

Useful for:

* testing
* drafts
* experimental tools
* temporary disabling

---

## `domain`

```python
domain="web"
```

Logical namespace/grouping.

Examples:

* `"web"`
* `"filesystem"`
* `"finance"`
* `"database"`

Used internally for canonical registry key generation.

---

## `tags`

```python
tags=["search", "retrieve"]
```

Optional routing metadata.

Tags help:

* orchestrators
* routers
* LLMs
* planners

understand tool/expert capabilities.

---

# Canonical Registry Key

Registry keys are automatically generated.

Format:

```text
{kind}.{domain}.{name}
```

Examples:

```text
tool.web.search_tool
tool.filesystem.read_file
expert.finance.risk_analyzer
```

---

# Validation Rules

All registered objects are validated automatically during registration.

---

# Required Fields (Tools + Experts)

Every tool and expert MUST define:

```python
name
description
input_schema
output_schema
call()
```

---

# Required Fields (Experts Only)

Experts MUST additionally define:

```python
instruction_files
```

Example:

```python
instruction_files = [
    "finance.md"
]
```

Rules:

* must be a list
* must contain at least one file
* all files must end in `.md`
* all files must exist

---

# Uniqueness Rules

The following combination MUST be unique:

```text
(kind, domain, name)
```

Meaning:

## INVALID

```python
@tool(domain="web")
class ToolA:
    name = "search"
```

```python
@tool(domain="web")
class ToolB:
    name = "search"
```

Duplicate:

```text
tool.web.search
```

---

## VALID

Tool and expert MAY share the same domain/name pair.

```python
@tool(domain="web")
class SearchTool:
    name = "search"
```

```python
@expert(domain="web")
class SearchExpert:
    name = "search"
```

Generated keys:

```text
tool.web.search
expert.web.search
```

These are distinct.

---

# Internal Metadata

During registration, metadata is attached automatically:

```python
__registry_key__
__registry_kind__
__registry_domain__
__registry_tags__
```

Example:

```python
SearchTool.__registry_key__
# tool.web.search_tool
```

---

# Registry Access

The internal registry stores `RegistryEntry` objects.

Example internal structure:

```python
{
    "tool.web.search_tool": RegistryEntry(...),
    "expert.finance.risk_analyzer": RegistryEntry(...)
}
```

---

# Design Philosophy

The system intentionally uses:

* structural validation
* decorator-based registration
* runtime metadata injection

instead of inheritance-based enforcement.

This keeps plugin authoring:

* simple
* decoupled
* extensible

while preserving strong validation guarantees.

---

# Recommended Conventions

## Naming

Prefer semantic names:

```python
name = "search"
```

instead of:

```python
name = "tool_search"
```

The registry already namespaces automatically.

---

## Domains

Keep domains broad and logical.

Good:

```python
web
filesystem
finance
database
```

Avoid:

```python
web_v2_temp_final
```

---

## Tags

Tags should describe capabilities.

Good:

```python
["search", "retrieve", "internet"]
```

Bad:

```python
["tool", "misc"]
```

---

# Recommended Architecture

## Tools

Use tools for:

* deterministic execution
* APIs
* retrieval
* computation
* filesystem operations
* database operations

Tools should ideally:

* be stateless
* execute quickly
* avoid orchestration logic

---

## Experts

Use experts for:

* reasoning
* planning
* orchestration
* domain-specific cognition
* multi-step workflows

Experts may:

* use tools
* call other experts
* manage context
* perform decomposition
