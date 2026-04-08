# Vraksha: The Agent That Never Forgets

<p align="center">
  <img src="https://github.com/vraksha/vraksha/blob/main/assets/agent.png" alt="Vraksha Logo" style="width: 50%;">
</p>

> **"Vraksha remembers, so you can focus on creating."**

Most AI assistants are ephemeral; they forget everything the moment a session ends. **Vraksha** is built on a local-first, persistent memory architecture. It reads and writes to structured files before and after every session, ensuring your context, project state, and hardcoded rules are never lost.

No re-explaining. No context drift. Just deep work.

---

## Core Capabilities

- **Persistent Context:** Automatically synchronizes session summaries, project milestones, and user preferences.
- **Local-First Architecture:** Your intelligence lives in your files (`.yaml`, `.md`). No cloud silos.
- **Slop Detection:** Integrated forensic logic to distinguish between human-authored code and AI-generated content.
- **Immutable Governance:** Follows a `rules.md` file that is hardcoded and untouchable—even by the agent itself.
- **Explainable Logic:** Prioritizes high-fidelity reasoning over generic chat responses.

## The Three-Tier Memory System

Vraksha maintains state across three specialized files in the `/memory` directory:

1.  **`rules.md`** — Permanent governance and persona constraints. (Read-only for the agent).
2.  **`memory.yaml`** — Compressed session context and long-term user facts.
3.  **`projects.yaml`** — Active project tracking, architectural decisions, and technical debt.

---

## Quick Start

### 1. Environment Setup
Populate `.env.local` with your provider keys. Vraksha is optimized for **Claude (Anthropic)** but supports OpenAI as a secondary fallback.

```bash
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here # Required for Slop Detector
```

### 2. Configure Persona

- Define your engineering standards and personal preferences in `memory/rules.md`.

### 3. Initialize

```bash
pip install -r requirements.txt
python main.py
```

-----

## Repository Structure

```text
.
├── main.py                # Agent Entry Point
├── memory/                # Persistent State (Rules, Memory, Projects)
├── src/
│   ├── agent/             # Core LLM Orchestration & Prompt Engineering
│   ├── slop_detector/     # Forensic Code Analysis Module
│   └── utils/             # Memory I/O and GitHub Integration
└── assets/                # Brand Identity & Documentation Assets
```

-----

<!-- **Official Site:** [agentvraksha.com](https://www.google.com/search?q=https://agentvraksha.com)   -->

<!-- ``` -->
