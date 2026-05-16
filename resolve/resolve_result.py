from dataclasses import dataclass
from typing import Any

@dataclass
class ResolveResult:
    success: bool
    error: str | dict[str, Any] | None = None
    result: str | dict[str, Any] | None = None

    def __bool__(self):
        return self.success

        