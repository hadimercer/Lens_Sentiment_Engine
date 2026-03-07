"""OpenAI provider and response validation helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import logging
import time
from typing import Optional

from lens.config import get_settings

logger = logging.getLogger(__name__)

SENTIMENT_MAX_TOKENS = 120
THEME_MAX_TOKENS = 1200
SUMMARY_MAX_TOKENS = 900


class APIError(Exception):
    pass


class APITimeoutError(Exception):
    pass


class RateLimitError(Exception):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, *, system_prompt: str, user_message: str, max_tokens: int, context_tag: str) -> str:
        raise NotImplementedError


class OpenAIChatProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        try:
            from openai import OpenAI as OpenAIClient
        except ImportError as error:
            raise RuntimeError("The openai package is required for live mode.") from error

        self.client = OpenAIClient(api_key=api_key)
        self.model = model

    def complete(self, *, system_prompt: str, user_message: str, max_tokens: int, context_tag: str) -> str:
        try:
            from openai import APIError as OpenAIAPIError, APITimeoutError as OpenAIAPITimeoutError, RateLimitError as OpenAIRateLimitError
        except ImportError:
            OpenAIAPIError = Exception
            OpenAIAPITimeoutError = TimeoutError
            OpenAIRateLimitError = Exception

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content or "{}"
        except OpenAIRateLimitError as error:
            raise RateLimitError(str(error)) from error
        except OpenAIAPITimeoutError as error:
            raise APITimeoutError(str(error)) from error
        except OpenAIAPIError as error:
            raise APIError(str(error)) from error


class APIClient:
    def __init__(
        self,
        api_key: str,
        system_prompt: str,
        retry_count: int = 2,
        retry_delay_seconds: float = 1.5,
        provider: Optional[LLMProvider] = None,
        model: str | None = None,
    ):
        self.system_prompt = system_prompt
        self.retry_count = retry_count
        self.retry_delay_seconds = retry_delay_seconds
        self.model = model or get_settings().openai_model
        self.provider = provider or OpenAIChatProvider(api_key=api_key, model=self.model)
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def _call(self, *, user_message: str, max_tokens: int, context_tag: str) -> Optional[dict]:
        last_error: Exception | None = None
        for attempt in range(self.retry_count + 1):
            try:
                self._call_count += 1
                raw = self.provider.complete(
                    system_prompt=self.system_prompt,
                    user_message=user_message,
                    max_tokens=max_tokens,
                    context_tag=context_tag,
                )
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError("Response payload is not a JSON object.")
                return payload
            except RateLimitError as error:
                wait = self.retry_delay_seconds * (attempt + 2)
                last_error = error
                logger.warning("[%s] Rate limit hit. Waiting %.1fs", context_tag, wait)
                time.sleep(wait)
            except (APITimeoutError, json.JSONDecodeError, ValueError) as error:
                last_error = error
                logger.warning("[%s] Retrying after malformed or timed-out response: %s", context_tag, error)
                time.sleep(self.retry_delay_seconds)
            except APIError as error:
                logger.error("[%s] Non-retryable API error: %s", context_tag, error)
                return None

        logger.error("[%s] All attempts failed. Last error: %s", context_tag, last_error)
        return None

    def score_record(self, prompt: str, record_index: int) -> Optional[dict]:
        result = self._call(
            user_message=prompt,
            max_tokens=SENTIMENT_MAX_TOKENS,
            context_tag=f"record_{record_index}",
        )
        if result is None:
            return None

        required = {"sentiment_label", "confidence_score", "reasoning"}
        if not required.issubset(result.keys()):
            logger.warning("[record_%s] Response missing required keys: %s", record_index, result.keys())
            return None

        label = str(result["sentiment_label"]).strip().lower()
        if label not in {"positive", "neutral", "negative"}:
            label = "neutral"

        try:
            confidence = float(result["confidence_score"])
        except (TypeError, ValueError):
            confidence = 0.5

        return {
            "sentiment_label": label,
            "confidence_score": max(0.0, min(1.0, confidence)),
            "reasoning": str(result.get("reasoning") or "").strip() or None,
        }

    def extract_themes(self, prompt: str) -> list[dict]:
        result = self._call(
            user_message=prompt,
            max_tokens=THEME_MAX_TOKENS,
            context_tag="theme_batch",
        )
        if result is None or "themes" not in result or not isinstance(result["themes"], list):
            return []

        validated: list[dict] = []
        for theme in result["themes"]:
            if not isinstance(theme, dict):
                continue
            try:
                frequency = int(theme.get("frequency", 0))
            except (TypeError, ValueError):
                frequency = 0
            validated.append(
                {
                    "label": str(theme.get("label") or "Unknown theme"),
                    "frequency": max(0, frequency),
                    "dominant_sentiment": str(theme.get("dominant_sentiment") or "neutral").lower(),
                    "representative_quotes": [str(quote) for quote in list(theme.get("representative_quotes", []))[:2]],
                }
            )
        return validated

    def generate_summary(self, prompt: str) -> dict:
        fallback = {
            "executive_summary": "Summary unavailable - pipeline error during summary generation.",
            "key_takeaways": [],
            "priority_actions": [],
        }
        result = self._call(
            user_message=prompt,
            max_tokens=SUMMARY_MAX_TOKENS,
            context_tag="exec_summary",
        )
        if result is None:
            return fallback

        executive_summary = str(result.get("executive_summary") or fallback["executive_summary"]).strip() or fallback["executive_summary"]
        key_takeaways = _clean_list(result.get("key_takeaways"))
        priority_actions = _clean_list(result.get("priority_actions"))

        return {
            "executive_summary": executive_summary,
            "key_takeaways": key_takeaways,
            "priority_actions": priority_actions,
        }



def _clean_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item or "").strip()
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(text)
    return cleaned
