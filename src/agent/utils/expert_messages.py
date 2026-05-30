from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic_ns
from typing import Any
from uuid import uuid4

from src.capabilities.contracts import Actor


@dataclass(slots=True, frozen=True)
class ExpertMessageRequest:
    source: Actor
    target: Actor
    topic: str
    payload: dict[str, Any]
    reason: str
    request_id: str = field(default_factory=lambda: uuid4().hex)
    parent_id: str | None = None
    created_ns: int = field(default_factory=monotonic_ns)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "parent_id": self.parent_id,
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "topic": self.topic,
            "payload": self.payload,
            "reason": self.reason,
            "created_ns": self.created_ns,
        }
