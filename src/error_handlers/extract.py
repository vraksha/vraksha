def extract_error_info(err, model_inst):
    import re
    import logging
    
    logger = logging.getLogger(__name__)
    logger.error("Caught exception during model execution", exc_info=err)

    status_code = getattr(err, "status_code", "unknown")

    model_name = getattr(model_inst, "model_name", None)
    if not model_name:
        model_name = str(model_inst)

    body = getattr(err, "body", None)

    if body is None:
        response = getattr(err, "response", None)

        try:
            if response and hasattr(response, "json"):
                body = response.json()
            else:
                body = str(err)
        except Exception:
            body = str(err)

    message = "Unknown error"

    if isinstance(body, dict):
        # Nested error format (Anthropic / Google)
        if "error" in body and isinstance(body["error"], dict):
            message = body["error"].get("message", message)

        # Flat error format (OpenAI)
        elif "message" in body:
            message = body.get("message", message)
    else:
        message = str(body)

    message = message.split("\n")[0]

    urls = re.findall(r"https?://[^\s,]+", str(body))
    help_url = urls[0] if urls else None

    return {
        "status_code": status_code,
        "model_name": model_name,
        "message": message,
        "help_url": help_url,
    }


