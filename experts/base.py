###################################################################
# DEPRECATED
#
# Kept just for backup
###############################################################


'''

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel

class BaseSubAgent(ABC):
    """
    Pure structure. Inheriting from this does NOT trigger registration, 
    allowing for testing, mixins, or draft agents.
    """
    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    @abstractmethod
    def call(self):
        pass
'''