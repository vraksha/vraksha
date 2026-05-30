from __future__ import annotations

from src.agent.guardrails import (
    AgentGuardrailContext,
    AgentGuardrailDecision,
    AgentGuardrailPolicy,
)
from src.agent.orchestration_policy import ExpertMessagePolicy
from src.agent.utils import (
    ExpertMessageRequest,
    ObservedExpertMessage,
    OrchestratorDecision,
)


class AgentOrchestrator:
    """Agent-owned boundary for expert communication and flow control."""

    def __init__(
        self,
        policy: ExpertMessagePolicy | None = None,
        guardrails: AgentGuardrailPolicy | None = None,
    ) -> None:
        self.policy = policy or ExpertMessagePolicy()
        self.guardrails = guardrails or AgentGuardrailPolicy()
        self._observed: list[ObservedExpertMessage] = []

    @property
    def observed_messages(self) -> tuple[ObservedExpertMessage, ...]:
        return tuple(self._observed)

    def review_expert_message(
        self,
        request: ExpertMessageRequest,
    ) -> OrchestratorDecision:
        decision = self.policy.decide(request)
        self._observed.append(
            ObservedExpertMessage(request=request, decision=decision)
        )
        return decision

    def review_guardrails(
        self,
        context: AgentGuardrailContext,
    ) -> AgentGuardrailDecision:
        return self.guardrails.decide(context)


Orchestrator = AgentOrchestrator
