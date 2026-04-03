def get_api_key(provider, file_path=".env.local") -> str:
    import os
    from dotenv import load_dotenv

    load_dotenv(file_path)

    if provider.lower() == "anthropic":
        return  os.getenv("ANTHROPIC_API_KEY")
    elif provider.lower() == "openai":
        return os.getenv("OPENAI_API_KEY")
    else:
        raise ValueError("Invalid provider")
