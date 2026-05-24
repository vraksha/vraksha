# Beware to always returna structured json like this at any cost, never return string!!!

## Use the data types shown below

```json
        "success": {"type": "boolean"},
        "data": {"type": ["object", "null"]},
        "error": {"type": ["string", "null"]}
```

```json
    "success": {"type": "boolean"},
    "data": {
        "type": "object",
        "properties": {
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "exit_code": {"type": "integer"}
        }
    },
    "error": {"type": ["string", "null"]}
```
