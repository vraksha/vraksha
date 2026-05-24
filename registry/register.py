# registry.py

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Type

from registry.base import RegistryKind, RegistryEntry
from registry.validate import Validator

# =========================================================
# Registry
# =========================================================

class Registry:
    """
    Central plugin registry for:
        - tools
        - experts

    Architecture
    ------------
    Registry keys are globally unique.

    Example:
        tool.web.search
        expert.finance.risk_analyzer

    Internal Structure
    ------------------
    Registry stores flat mappings:

        {
            "tool.web.search": RegistryEntry(...)
        }

    This avoids:
        - nested traversal
        - namespace collisions
        - lookup complexity

    Public API
    ----------
    Use:
        @tool(...)
        @expert(...)

    Users NEVER interact with Registry directly.
    """

    # str: Our unique key (eg: tool.web.search)
    _registry: Dict[str, RegistryEntry] = {}

    
    # =====================================================
    # Registration
    # =====================================================

    @staticmethod
    def _register(
        *,
        cls: Type,
        kind: RegistryKind,
        enabled: bool,
        domain: str,
        tags: Optional[List[str]] = None,
    ) -> Type:
        """
        Internal registration pipeline.

        Steps
        -----
        1. Validate metadata.
        2. Generate unique key.
        3. Validate class structure.
        4. Create registry entry.
        5. Store entry.
        """

        # -------------------------------------------------
        # Domain validation
        # -------------------------------------------------

        if not isinstance(domain, str):
            raise TypeError("domain must be str")

        if not domain.strip():
            raise ValueError("domain cannot be empty")

        # normalize
        domain = domain.strip().lower()

        # -------------------------------------------------
        # Tags normalization
        # -------------------------------------------------

        tags = tags or []

        if not isinstance(tags, list):
            raise TypeError("tags must be List[str]")

        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError(
                    "all tags must be str"
                )

        # -------------------------------------------------
        # Validate by kind
        # -------------------------------------------------

        if kind == RegistryKind.TOOL:
            Validator.validate_tool(cls)

        elif kind == RegistryKind.EXPERT:
            Validator.validate_expert(cls)

        else:
            raise ValueError(
                f"Unknown registry kind: {kind}"
            )

        # -------------------------------------------------
        # Generate canonical key
        # -------------------------------------------------

        # Creates a key like tool.web.search
        key = f"{kind.value}.{domain}.{cls.name}"

        # -------------------------------------------------
        # Prevent duplicates
        # -------------------------------------------------

        if key in Registry._registry:
            raise ValueError(
                f"Duplicate registry key detected: {key}"
            )

        # -------------------------------------------------
        # Attach runtime metadata
        # -------------------------------------------------

        setattr(cls, "__registry_key__", key)
        setattr(cls, "__registry_kind__", kind)
        setattr(cls, "__registry_domain__", domain)
        setattr(cls, "__registry_tags__", tags)

        # -------------------------------------------------
        # Create entry
        # -------------------------------------------------

        entry = RegistryEntry(
            name=cls.name,
            domain=domain,
            key=key,
            kind=kind,
            cls=cls,
            enabled=enabled,
            tags=tags,
        )

        # -------------------------------------------------
        # Store
        # -------------------------------------------------

        Registry._registry[key] = entry

        return cls

    # =====================================================
    # Access Helpers
    # =====================================================

    @staticmethod
    def get(key: str) -> Optional[RegistryEntry]:
        """
            Retrieve registry entry by canonical key.
        """

        return Registry._registry.get(key)

    @staticmethod
    def all() -> Dict[str, RegistryEntry]:
        """
            Return all registered entries.
        """

        return Registry._registry

    @staticmethod
    def tools() -> Dict[str, RegistryEntry]:
        """
            Return all registered tools.
        """

        return {
            k: v
            for k, v in Registry._registry.items()
            if v.kind == RegistryKind.TOOL
        }

    @staticmethod
    def experts() -> Dict[str, RegistryEntry]:
        """
            Return all registered experts.
        """

        return {
            k: v
            for k, v in Registry._registry.items()
            if v.kind == RegistryKind.EXPERT
        }


# =========================================================
# Public Decorators
# =========================================================

def tool(
    *,
    enabled: bool = True,
    domain: str,
    tags: Optional[List[str]] = None,
) -> Callable:
    """
    Public decorator for TOOL registration.

    Example
    -------
    @tool(
        domain="web",
        tags=["search", "retrieval"]
    )
    class WebSearch:
        ...
    """

    def decorator(cls: Type):
        if not enabled:
            return cls

        return Registry._register(
            cls=cls,
            kind=RegistryKind.TOOL,
            enabled=enabled,
            domain=domain,
            tags=tags,
        )

    return decorator


def expert(
    *,
    enabled: bool = True,
    domain: str,
    tags: Optional[List[str]] = None,
) -> Callable:
    """
    Public decorator for EXPERT registration.

    Example
    -------
    @expert(
        domain="finance",
        tags=["risk", "markets"]
    )
    class FinanceExpert:
        ...
    """

    def decorator(cls: Type):

        if not enabled:
            return cls

        return Registry._register(
            cls=cls,
            kind=RegistryKind.EXPERT,
            enabled=enabled,
            domain=domain,
            tags=tags,
        )

    return decorator

