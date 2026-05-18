from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Base(ABC):
    """
        Internal contrat only.
    """
    name: str
    description: str

    input_schema: Optional[List[Dict]] = None
    output_schema: Optional[List[Dict]] = None

    @abstractmethod
    def call(self, *args, **kwargs):
        pass


class RegistryKind(str, Enum):
    TOOL = "tool"
    EXPERT = "expert"

