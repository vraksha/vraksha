"""
Memory Consolidation Sub-Agent for Vraksha.

This module is responsible for the 'Sleep Cycle' of the agent. It periodically
processes raw conversation transcripts to extract durable, high-signal 
memories (Rules, Facts, Preferences) and commits them to long-term storage.

The extraction is performed by a specialized LLM call that filters out 
ephemeral noise (greetings, debug logs) and focuses on state changes.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any

from src.memory.local_index import MemoryRecord
from src.memory.coordinator import memory_coordinator
from src.utils.call_llm import call_llm

logger = logging.getLogger(__name__)

CONSOLIDATION_PROMPT = """
You are the Memory Consolidation Agent for Vraksha.
Analyze the provided transcript and extract only DURABLE, HIGH-SIGNAL information.

Categories:
1. Rules: Absolute constraints or instructions explicitly mandated by the user.
2. Preferences: Subtle but stable user likes/dislikes (e.g., coding style, tool choice).
3. Facts: Verified project details, architectural decisions, or state changes.
4. Events: Significant session milestones worth historical recall.

Filtering Strategy:
- Ignore greetings, social filler, or temporary debug logs.
- Collapse redundant items into a single clear statement.
- Ensure all facts are grounded in the transcript.

Return STRICT JSON:
{
  "rules": [], "preferences": [], "facts": [], "events": []
}
"""


def _message_text(message: dict[str, Any]) -> str:
    """Safely extracts text content from various message formats (strings, lists, blocks)."""
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Handle multi-part content (e.g., Anthropic/OpenAI list format)
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        return " ".join(parts)
    return json.dumps(content, ensure_ascii=False, default=str)


def build_transcript(messages: list[dict[str, Any]], *, max_messages: int = 30, max_chars: int = 15_000) -> str:
    """Constructs a clean, timestamped transcript for consolidation analysis."""
    lines = []
    for m in messages[-max_messages:]:
        role = str(m.get("role", "unknown")).upper()
        text = _message_text(m)
        if text.strip():
            lines.append(f"{role}: {text}")
    return "\n".join(lines)[-max_chars:]


def _extract_json(content: str) -> dict[str, Any]:
    """
    Robust JSON extraction from LLM responses. Handles markdown blocks, 
    inline comments, and trailing chatter.
    """
    # 1. Try to find a JSON code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        content = match.group(1)
    
    # 2. If no block, find the first '{' and last '}'
    else:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start : end + 1]

    try:
        # Sanitize common LLM "sloppy" JSON quirks
        clean = re.sub(r"//.*", "", content)  # Remove single-line comments
        return json.loads(clean.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Consolidation parser failed to decode LLM output: {e}\nRaw: {content}")
        return {"rules": [], "preferences": [], "facts": [], "events": []}


async def consolidate_session(messages: list[dict[str, Any]]) -> None:
    """
    Core consolidation routine. Extracts memories from the recent conversation
    and saves them as a batched transaction in the memory layer.
    """
    if not messages:
        return

    transcript = build_transcript(messages)
    if not transcript.strip():
        return

    try:
        # Offload the LLM call to a thread to avoid blocking the event loop
        response = await asyncio.to_thread(
            call_llm,
            model_part="orchestrator",
            system=CONSOLIDATION_PROMPT,
            messages=[{"role": "user", "content": f"Transcript:\n{transcript}"}],
            max_tokens=1000,
            raw=False,
        )
        
        # Handle different LLM response object formats
        content = response if isinstance(response, str) else "".join(
            getattr(block, "text", "") for block in getattr(response, "content", [])
        )
        if not content.strip():
            return

        data = _extract_json(content)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_id = f"consolidation:{ts}"
        
        records = []
        mapping = {
            "rules": ("rule", 0.95),
            "preferences": ("preference", 0.80),
            "facts": ("fact", 0.75),
            "events": ("episode", 0.60),
        }

        for key, (kind, trust) in mapping.items():
            for item in data.get(key, []):
                if isinstance(item, str) and item.strip():
                    records.append(MemoryRecord(
                        source_id=source_id,
                        kind=kind,
                        title=f"consolidated {kind}",
                        content=item.strip(),
                        trust=trust,
                        pinned=(kind == "rule"),
                    ))

        if records:
            await memory_coordinator.memory.remember_many(records)
            logger.info(f"Successfully consolidated {len(records)} memories (batch: {source_id})")

    except Exception:
        logger.exception("Background memory consolidation failed")


def run_consolidation(messages: list[dict[str, Any]]) -> None:
    """
    Public entry point for consolidation. Ensures the process runs 
    asynchronously without halting the main interaction loop.
    """
    try:
        loop = asyncio.get_running_loop()
        # Fire-and-forget task in the background
        loop.create_task(consolidate_session(messages))
    except RuntimeError:
        # Fallback for environments without a running loop
        asyncio.run(consolidate_session(messages))
