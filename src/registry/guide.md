# Users can just do only do:

```python
from src.registry.registry import tool, expert

# Then:

@tool(enabled=True)
class SearchTool:
    name = "search_tool"

    description = "Searches the web"

    input_schema = []
    output_schema = []

    def call(self):
        # Do the task here
        pass

# and:

@expert()
class FinanceExpert:
    name = "finance_expert"

    description = "Handles finance"

    input_schema = []
    output_schema = []

    instruction_files = [
        "finance.md"
    ]

    def call(self):
        # Do the task here
        pass
```

