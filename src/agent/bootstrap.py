from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import logging
from typing import TYPE_CHECKING

# Vraksha Core Imports
from src.memory.coordinator import memory_coordinator

if TYPE_CHECKING:
    from src.memory.coordinator import MemoryCoordinator

logger = logging.getLogger(__name__)

DEFAULT_SOUL = """
    # VRAKSHA DEFAULT SOUL
    You are Vraksha, a powerful agentic AI designed by Cybro (vraksha organization) for local-first software development.
    Your personality is technical, direct, and proactive. You always prioritize security, 
    performance, and code purity. You remember your user and respect their project context.
"""

# Just to let agent know trying to do harmful stuff would be blocked anyway and will just waste tokens.
BASELINE_RULES = """
    # VRAKSHA BASELINE RULES (IMMUTABLE)
    1. LOCAL-FIRST: Never exfiltrate sensitive data to external servers without explicit consent.
    2. SECURITY: Reject any tool calls that attempt to bypass the Docker sandbox.
    3. INTEGRITY: Preserve Vraksha's core system files (soul.md, rules.md) at all costs.
    4. TRANSPARENCY: Explain your actions clearly before executing complex file changes.

    ## > Don't waste your energy on trying to do the things mentioned above,
        as you would face alot of friction and you would be blocked.

    So, don't waste your time on trying to do what's mentioned as "Not to be done".
"""

@dataclass
class VrakshaDeps:
    """
        The Vraksha Services injected into the PydanticAI Engine.
    """
    memory: MemoryCoordinator
    soul: str
    rules: str
    session_id: str
    user_id: str

def bootstrap_vraksha(
    memory_path: Path | str = "memory",
    session_id: str = "default_session",
    user_id: str = "default_user"
) -> VrakshaDeps:
    """
        Pre-flight loader for the Vraksha Agent.
        Loads Identity (SOUL.md) and Governance (RULES.md) with safe fallbacks.
    """
    base_path = Path(memory_path)
    
    # 1. Load Soul (Identity)
    soul_file = base_path / "soul.md"
    soul_file_cap = base_path / "SOUL.md"

    if soul_file.exists() or soul_file_cap.exists():
        soul_content = soul_file.read_text(encoding="utf-8")
        logger.info("✅ Soul loaded from memory/SOUL.md")

    else:
        soul_content = DEFAULT_SOUL
        logger.warning("⚠️ memory/SOUL.md not found. Using Default Vraksha Soul.")

    # 2. Load Rules (Governance)
    rules_file = base_path / "rules.md"
    rules_file_cap = base_path / "RULES.md"

    if rules_file.exists() or rules_file_cap.exists():
        rules_content = rules_file.read_text(encoding="utf-8")
        logger.info("✅ Rules loaded from memory/RULES.md")

    else:
        rules_content = BASELINE_RULES
        logger.warning("⚠️ memory/RULES.md not found. Using Baseline Safety Rules.")

    # 3. Build the Dependency Context
    return VrakshaDeps(
        memory=memory_coordinator,
        soul=soul_content,
        rules=rules_content,
        session_id=session_id,
        user_id=user_id
    )
