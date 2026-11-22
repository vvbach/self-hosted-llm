
import os

class Settings:
    LLM_URL = os.getenv(
        "LLM_URL",
        "http://llm:8080/v1/chat/completions",
    )

    LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
    MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "1"))

    MODEL_NAME = os.getenv("MODEL_NAME", "local")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "256"))


settings = Settings()
