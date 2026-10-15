"""Groq LLM provider implementation using OpenAI-compatible SDK."""

import os
from collections.abc import AsyncIterator

from openai import OpenAI

from app.providers.base import ChatModel, UsageRecord


class GroqChatModel(ChatModel):
    """ChatModel implementation communicating with Groq's high-speed inference engine."""

    def __init__(self, model: str = "openai/gpt-oss-120b", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key,
        )
        self._last_usage = UsageRecord(
            kind="chat",
            units_in=0,
            units_out=0,
            cost_usd=0.0,
            model=self.model,
            provider="groq",
        )

    async def stream(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        prompt_tokens_est = sum(len(m.get("content", "")) for m in messages) // 4
        out_tokens_est = 0

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                out_tokens_est += len(text) // 4
                yield text

        # Rate estimate for budget model (~$0.15/M tokens)
        cost = (prompt_tokens_est + out_tokens_est) * (0.15 / 1_000_000)
        self._last_usage = UsageRecord(
            kind="chat",
            units_in=prompt_tokens_est,
            units_out=out_tokens_est,
            cost_usd=cost,
            model=self.model,
            provider="groq",
        )

    def last_usage(self) -> UsageRecord:
        return self._last_usage
