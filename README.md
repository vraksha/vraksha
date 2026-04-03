## About

Your personal AI assistant

> Note: It supports API keys for both Anthropic and OpenAI, but prioritizes Claude over ChatGPT if both are provided.

## Before using

- Make sure you have either ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file

## Structure

```
e:\Agent
├── .env.local
├── draft.md
├── main.py
├── README.md
├── requirements.txt
├── memory/
│   ├── .gitkeep
│   ├── memory.yaml
│   ├── projects.yaml
│   └── rules.md
└── src/
    ├── __init__.py
    ├── agent/
    │   ├── __init__.py
    │   ├── llm.py
    │   ├── loop.py
    │   └── prompts.py           # agent prompts
    ├── slop_detector/
    │   ├── __init__.py
    │   ├── detector.py
    │   └── prompts.py           # forensic prompts
    └── utils/
        ├── __init__.py
        ├── changes.py
        ├── client.py
        ├── extract_api.py
        └── extract_content.py

```