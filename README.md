# Vraksha - Your Personal AI Assistant

<p align="center">
  <img src="https://github.com/vraksha/vraksha/blob/main/assets/Vraksha.png" alt="Vraksha Logo" style="width: 60%;">
</p>

A **personal** AI agent that remembers.

Most AI assistants forget everything the moment a session ends. **Vraksha** doesn't.
It reads from and writes to three structured files before and after every session —
so it always knows who you are, what you're building, and what was decided last time.
You never re-explain your context. It already knows.

## What It Does

- Reads your rules, memory, and project state at the start of every session
- Answers questions, helps you think, assists with your work
- Updates its own memory at the end of every session — compressed, clean, no noise
- Tracks your projects and decisions across time
- Follows rules that are hardcoded and untouchable — even by itself

- Distinguishes between AI slop vs Human written content.

## How Memory Works

Vraksha maintains three files:

- `rules.md` — your permanent rules and preferences. Vraksha can never modify this.
- `memory.yaml` — session context. Vraksha rewrites this every session with a compressed summary.
- `projects.yaml` — project state. Vraksha updates this when something meaningful changes.

Nothing is stored in the cloud. Everything lives in your own files.

> Note: It supports API keys for both Anthropic and OpenAI, but prioritizes Claude over ChatGPT if both are provided.

## Before using

- Make sure you have either ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file

## Structure

```
e:\Agent
├── .env.example
├── .env.local
├── README.md
├── draft.md
├── main.py
├── requirements.txt
├── tree_output.txt
│
├── assets
│   ├── logo.png
│   └── Vraksha.png
│
├── memory
│   ├── .gitkeep
│   ├── memory.yaml
│   ├── projects.yaml
│   └── rules.md
│
├── secret
│   ├── image.png
│   └── Vraksha..png
│
└── src
    ├── __init__.py
    │
    ├── agent
    │   ├── __init__.py
    │   ├── llm.py
    │   ├── loop.py
    │   └── prompts.py
    │
    ├── slop_detector
    │   ├── __init__.py
    │   ├── detector.py
    │   └── prompts.py
    │
    └── utils
        ├── __init__.py
        ├── api_keys.py
        ├── changes.py
        ├── client.py
        ├── fetch_commits.py
        ├── fetch_content.py
        ├── github_token.py
        ├── read_memory.py
        └── url_converter.py

```