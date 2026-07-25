from dataclasses import dataclass
from typing import Any, Literal, Protocol

import httpx


class AIProviderError(RuntimeError):
    """Raised when the configured AI service cannot return a valid answer."""


@dataclass(frozen=True)
class AICompletion:
    text: str
    provider: str
    model: str


class AIProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    def complete(
        self,
        *,
        instructions: str,
        input_text: str,
        safety_identifier: str,
    ) -> AICompletion: ...


class OpenAICompatibleProvider:
    """Small HTTP client for OpenAI and OpenAI-compatible local services."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        api_mode: Literal["responses", "chat_completions"] = "responses",
        reasoning_effort: str = "medium",
        max_output_tokens: int = 1200,
        timeout_seconds: float = 60,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_mode = api_mode
        self._reasoning_effort = reasoning_effort
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    @property
    def provider_name(self) -> str:
        return "openai-compatible"

    @property
    def model_name(self) -> str:
        return self._model

    def complete(
        self,
        *,
        instructions: str,
        input_text: str,
        safety_identifier: str,
    ) -> AICompletion:
        if self._api_mode == "chat_completions":
            endpoint = "/chat/completions"
            payload = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": input_text},
                ],
                "max_completion_tokens": self._max_output_tokens,
                "safety_identifier": safety_identifier,
            }
            parser = self._parse_chat_completion
        else:
            endpoint = "/responses"
            payload = {
                "model": self._model,
                "instructions": instructions,
                "input": [
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": input_text}],
                    }
                ],
                "max_output_tokens": self._max_output_tokens,
                "reasoning": {"effort": self._reasoning_effort},
                "text": {"verbosity": "medium"},
                "safety_identifier": safety_identifier,
            }
            parser = self._parse_response

        try:
            with httpx.Client(
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = client.post(
                    f"{self._base_url}{endpoint}",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as error:
            raise AIProviderError(
                f"AI 服务返回 HTTP {error.response.status_code}"
            ) from error
        except (httpx.HTTPError, ValueError) as error:
            raise AIProviderError("无法连接 AI 服务或响应格式无效") from error

        text = parser(data).strip()
        if not text:
            raise AIProviderError("AI 服务返回了空内容")
        return AICompletion(
            text=text,
            provider=self.provider_name,
            model=self._model,
        )

    @staticmethod
    def _parse_response(data: dict[str, Any]) -> str:
        direct_text = data.get("output_text")
        if isinstance(direct_text, str):
            return direct_text

        chunks: list[str] = []
        output = data.get("output", [])
        if not isinstance(output, list):
            return ""
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for part in content:
                if (
                    isinstance(part, dict)
                    and part.get("type") == "output_text"
                    and isinstance(part.get("text"), str)
                ):
                    chunks.append(part["text"])
        return "\n".join(chunks)

    @staticmethod
    def _parse_chat_completion(data: dict[str, Any]) -> str:
        choices = data.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return ""
        choice = choices[0]
        if not isinstance(choice, dict):
            return ""
        message = choice.get("message", {})
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        return content if isinstance(content, str) else ""
