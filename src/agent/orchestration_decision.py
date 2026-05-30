from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic_ns
from typing import Any, Literal

Decision = Literal["allow", "block"]


@dataclass(slots=True, frozen=True)
class OrchestratorDecision:
    request_id: str
    decision: Decision
    reason: str
    observed: bool = True
    created_ns: int = field(default_factory=monotonic_ns)

    @property
    def allowed(self) -> bool:
        return self.decision == "allow"

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "decision": self.decision,
            "reason": self.reason,
            "observed": self.observed,
            "created_ns": self.created_ns,
        }
