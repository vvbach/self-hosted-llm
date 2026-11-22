
import asyncio
import logging
from pathlib import Path 

import httpx
from pydantic import ValidationError

from app.config import settings
from app.schema import (
    CLASSIFICATION_SCHEMA,
    ClassificationResponse,
)

logger = logging.getLogger(__name__)


PROMPT_PATH = Path(__file__).resolve().parent / "system_prompt.txt"

SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()


class LLMError(Exception):
    pass


class LLMTimeout(LLMError):
    pass


class LLMUnavailable(LLMError):
    pass


class InvalidLLMResponse(LLMError):
    pass


class Classifier:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.semaphore = asyncio.Semaphore(
            settings.MAX_CONCURRENT
        )

    async def classify(
        self,
        error: str,
    ) -> ClassificationResponse:

        payload = {
            "model": settings.MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": error,
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "error_classification",
                    "strict": True,
                    "schema": CLASSIFICATION_SCHEMA,
                },
            },
            "temperature": 0,
            "max_tokens": settings.MAX_TOKENS,
        }

        try:
            async with self.semaphore:
                response = await self.client.post(
                    settings.LLM_URL,
                    json=payload,
                    timeout=settings.LLM_TIMEOUT,
                )
                response.raise_for_status()

        except httpx.TimeoutException as exc:
            logger.warning("LLM request timed out")
            raise LLMTimeout(
                "LLM request timed out"
            ) from exc

        except httpx.HTTPError as exc:
            logger.exception("LLM HTTP request failed")
            raise LLMUnavailable(
                "LLM service unavailable"
            ) from exc

        try:
            data = response.json()
            choice = data["choices"][0]

            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")

            logger.info(
                "LLM finish_reason=%s usage=%s",
                finish_reason,
                data.get("usage"),
            )

            if finish_reason != "stop":
                logger.warning(
                    "Incomplete LLM generation: %r",
                    content,
                )
                raise InvalidLLMResponse(
                    f"Incomplete generation: {finish_reason}"
                )

            result = ClassificationResponse.model_validate_json(
                content
            )

            logger.info(
                "Classification completed: category=%s severity=%s",
                result.category,
                result.severity,
            )

            return result

        except InvalidLLMResponse:
            raise

        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            ValidationError,
        ) as exc:
            logger.exception(
                "Invalid LLM response: %s",
                response.text[:2000],
            )
            raise InvalidLLMResponse(
                "Invalid classification response"
            ) from exc
