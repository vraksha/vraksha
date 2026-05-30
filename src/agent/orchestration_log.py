from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agent.expert_messages import ExpertMessageRequest
from src.agent.orchestration_decision import OrchestratorDecision


@dataclass(slots=True, frozen=True)
class ObservedExpertMessage:
    request: ExpertMessageRequest
    decision: OrchestratorDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "decision": self.decision.to_dict(),
        }
