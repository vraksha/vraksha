## About

Your personal AI assistant

> Note: It supports API keys for both Anthropic and OpenAI, but prioritizes Claude over ChatGPT if both are provided.

## Structure

```
e:\Agent
├── .env.local
├── main.py
├── requirements.txt
├── memory/
│   ├── memory.yaml
│   ├── projects.yaml
│   └── rules.md
└── src/
    ├── __init__.py          
    ├── agent/
    │   ├── __init__.py      
    │   ├── llm.py
    │   └── prompts.py      # agent prompts
    ├── slop_detector/
    │   ├── __init__.py      
    │   ├── detector.py      
    │   └── prompts.py       # forensic prompts 
    └── utils/
        ├── __init__.py     
        ├── changes.py
        ├── extract_api.py
        └── extract_content.py
```