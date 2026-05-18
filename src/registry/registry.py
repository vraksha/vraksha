from __future__ import annotations

from typing import Dict, Type

from src.registry.base import RegistryKind


class Registry:
    """
    Central registry for tools and experts.
    """

    _registry: Dict[RegistryKind, Dict[str, Type]] = {
        RegistryKind.TOOL: {},
        RegistryKind.EXPERT: {},
    }

    # ==========================================
    # Validation
    # ==========================================

    @staticmethod
    def _validate_common(cls: Type) -> None:
        required_fields = [
            "name",
            "description",
            "input_schema",
            "output_schema",
        ]

        for field in required_fields:
            if not hasattr(cls, field):
                raise TypeError(
                    f"{cls.__name__} missing required field: {field}"
                )

        if not isinstance(cls.name, str) or not cls.name:
            raise TypeError("name must be a non-empty string")

        if not isinstance(cls.description, str) or not cls.description:
            raise TypeError("description must be a non-empty string")

        if not isinstance(cls.input_schema, list):
            raise TypeError("input_schema must be List[Dict]")

        if not isinstance(cls.output_schema, list):
            raise TypeError("output_schema must be List[Dict]")

        if not callable(getattr(cls, "call", None)):
            raise TypeError("Must implement call() method")

    @staticmethod
    def _validate_tool(cls: Type) -> None:
        Registry._validate_common(cls)

    @staticmethod
    def _validate_expert(cls: Type) -> None:
        Registry._validate_common(cls)

        md_files = getattr(cls, "instruction_files", None)

        if not isinstance(md_files, list):
            raise ValueError(
                "Expert must define instruction_files: List[str]"
            )

        if len(md_files) == 0:
            raise ValueError(
                "Expert must define at least one .md file"
            )

    # ==========================================
    # Internal registration
    # ==========================================

    @staticmethod
    def _register(cls: Type, kind: RegistryKind):

        setattr(cls, "__registry_kind__", kind)

        if kind == RegistryKind.TOOL:
            Registry._validate_tool(cls)

        elif kind == RegistryKind.EXPERT:
            Registry._validate_expert(cls)

        else:
            raise ValueError(f"Unknown registry kind: {kind}")

        name = cls.name

        if name in Registry._registry[kind]:
            raise ValueError(
                f"Duplicate registration: {name}"
            )

        Registry._registry[kind][name] = cls

        return cls

    # ==========================================
    # Access helpers
    # ==========================================

    @staticmethod
    def get(kind: RegistryKind, name: str):
        return Registry._registry[kind].get(name)

    @staticmethod
    def all(kind: RegistryKind):
        return Registry._registry[kind]


def tool(*, enabled: bool = True):
    """
        Public decorator for tools.
    """

    def decorator(cls: Type):

        if not enabled:
            return cls

        return Registry._register(
            cls,
            RegistryKind.TOOL
        )

    return decorator


def expert(*, enabled: bool = True):
    """
        Public decorator for experts.
    """

    def decorator(cls: Type):

        if not enabled:
            return cls

        return Registry._register(
            cls,
            RegistryKind.EXPERT
        )

    return decorator

