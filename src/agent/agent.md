# Agent Orchestration Guide

This package owns Vraksha's main agent runtime. In architecture terms, this
agent is the orchestrator: it has session context, memory access, governance
rules, model fallback, registry-mounted capabilities, and the authority to
approve or block expert communication.

The goal is:

```text
User -> Agent Orchestrator -> Capability / Expert Request -> Policy -> Result
```

Experts do not coordinate freely. Tools do not execute freely. The agent-owned
orchestrator controls the flow.

## Runtime Flow

`runtime.py` creates the live `vraksha_agent`:

```text
create_vraksha_agent()
    -> Agent(TestModel, deps_type=VrakshaDeps)
    -> attach_registry_tools(agent)
    -> register_governance_prompt(agent)
    -> return agent
```

Important files:

* `runtime.py` creates and exports the live agent.
* `bootstrap.py` builds `VrakshaDeps`.
* `governance.py` registers the system prompt.
* `initialize_tools/bootstrap_tools.py` discovers registry modules and mounts
  enabled tools/experts.
* `initialize_tools/tool_adapter.py` converts registry entries into PydanticAI
  tool functions.
* `bridge.py` keeps the older loop compatible with the new agent runtime.
* `engine.py` is now only a compatibility export surface.

## Dependencies And Context

`bootstrap.py` produces `VrakshaDeps`, which is injected into each agent run.

`VrakshaDeps` currently carries:

* `memory`: the memory coordinator
* `soul`: identity prompt text
* `rules`: governance prompt text
* `session_id`: session identity
* `user_id`: user identity

This is why the agent is the correct orchestrator: it has the context required
to judge whether a request is relevant, safe, useful, and permitted.

## Governance Flow

`governance.py` owns prompt assembly.

```text
RunContext[VrakshaDeps]
    -> memory.get_essential_context_async()
    -> build_system_prompt(soul, rules, essential_context)
    -> PydanticAI system prompt
```

Prompt construction stays outside `runtime.py` so agent creation remains small.

## Capability Mounting

At startup, `attach_registry_tools(agent)` performs:

```text
discover_registry_modules()
    -> decorators populate Registry
    -> ToolAdapter(agent).register_all()
    -> LLM sees safe tool names
```

Today, enabled registry entries are still directly mounted as PydanticAI tools.
The intended next step is to put the broker between the agent and the primitive
implementations so the LLM asks for capabilities rather than directly invoking
tool classes.

Current smoke capabilities should remain boring and minimal:

* `tool.universal.echo`
* `expert.architecture.smoke_check`

## Expert Communication Rule

Experts must not talk to each other directly.

All expert-to-expert communication must pass through the agent orchestrator:

```text
Expert A
    -> ExpertMessageRequest
    -> AgentOrchestrator.review_expert_message(...)
    -> ExpertMessagePolicy.decide(...)
    -> OrchestratorDecision
    -> allow/block
    -> observed log entry
```

The orchestrator observes every request before anything is allowed.

## Expert Message Files

Expert communication is split into focused files:

* `expert_messages.py`
  Defines `ExpertMessageRequest`.

* `orchestration_decision.py`
  Defines `OrchestratorDecision` and the `allow` / `block` decision shape.

* `orchestration_policy.py`
  Defines `ExpertMessagePolicy`, the fail-closed policy layer.

* `orchestration_log.py`
  Defines `ObservedExpertMessage`, the audit record pairing request and decision.

* `guardrails.py`
  Defines general orchestration guardrails for recursion, fanout, prompt
  injection markers, payload size, session/user mismatches, and bulk memory
  export attempts.

* `orchestrator.py`
  Defines `AgentOrchestrator`, which applies expert-message policy, exposes
  guardrail review, and records observations.

## Fail-Closed Policy

`ExpertMessagePolicy` blocks by default.

A request is blocked if:

* source or target is not an expert
* topic is explicitly blocked
* route is not explicitly allowed
* reason is empty

A request is allowed only when:

* it is expert-to-expert
* the topic is not blocked
* `(source.name, target.name)` is in `allowed_routes`
* a non-empty reason is supplied

This keeps expert collaboration observable and intentional.

## Stress-Test Foundation

The `AGENT OMEGA` stress scenario requires several boundaries before advanced
behavior can be trusted.

Current foundation:

* Long-term memory is injected through `VrakshaDeps.memory`.
* Session and user identity are carried through `VrakshaDeps`.
* Expert-to-expert messages are blocked unless explicitly routed.
* All expert messages are observable through `observed_messages`.
* `AgentGuardrailPolicy` blocks common unsafe request shapes.
* MCP exists only as an edge adapter and fails closed when unconfigured.
* Legacy direct tools are archived; new primitives have clean homes.

Guardrail checks currently cover:

* recursive agent/expert expansion
* excessive parallel tool/capability requests
* cross-session impersonation
* cross-user impersonation
* bulk memory export attempts
* oversized payloads
* obvious prompt-injection text in untrusted content
* empty request reasons

These checks are not the final intelligence layer. They are the foundation above
which the broker, memory policy, sandboxing, and expert implementations can be
built safely.

## Observability

`AgentOrchestrator.review_expert_message(request)` always records the request
and decision as an `ObservedExpertMessage`.

The current in-memory view is:

```python
orchestrator.observed_messages
```

This is a placeholder for durable auditing. Later, these observations should be
written through the broker or memory layer with session/request IDs.

## Legacy Bridge

`bridge.py` owns `agent_bridge(messages)`, used by the older loop.

It performs:

```text
legacy message dicts
    -> PydanticAI message history
    -> model priorities for "orchestrator"
    -> provider fallback loop
    -> vraksha_agent.run_sync(...)
    -> output or structured failure text
```

Provider failure parsing lives in `src/error_handlers/extract.py`.
Provider selection lives in `src/providers/client.py`.

## Compatibility Layer

`engine.py` intentionally remains as a tiny compatibility module:

```python
from src.agent.bridge import agent_bridge
from src.agent.runtime import create_vraksha_agent, vraksha_agent
```

Existing imports such as `from src.agent.engine import vraksha_agent` continue
to work, but new code should prefer the focused modules directly.

## Current Boundaries

Use these ownership rules:

* Agent runtime and flow control live in `src/agent`.
* Shared request/result contracts live in `src/capabilities`.
* Primitive execution homes live in `tools/`.
* Reasoning units live in `experts/`.
* MCP is an edge adapter under `tools/mcp`, not the internal fast path.

Internal expert/tool communication should remain in-process and brokered for
speed. MCP should be used for external servers and integrations.

## Next Foundation Step

The next robust step is to add the capability broker as the only LLM-facing
execution tool:

```text
Agent -> request_capability -> Broker -> Policy -> Primitive Tool / Expert
```

Once that exists, the direct registry adapter should mount the broker-facing
entry instead of every primitive implementation.
