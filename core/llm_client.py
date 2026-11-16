"""OpenAI-compatible LLM client. No retries, per-call max_tokens."""
from __future__ import annotations

from openai import OpenAI

from .config import LLMConfig


class LLMClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg
        self.client = OpenAI(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            timeout=cfg.timeout,
            max_retries=0,
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.cfg.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.cfg.temperature,
            max_tokens=max_tokens or self.cfg.max_tokens,
        )
        return response.choices[0].message.content or ""

    def chat_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
        on_token=None,
    ) -> str:
        """Stream tokens; call on_token(delta) for each chunk."""
        stream = self.client.chat.completions.create(
            model=self.cfg.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.cfg.temperature,
            max_tokens=max_tokens or self.cfg.max_tokens,
            stream=True,
        )
        parts = []
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content or ""
            if delta:
                parts.append(delta)
                if on_token:
                    on_token(delta)
        return "".join(parts)