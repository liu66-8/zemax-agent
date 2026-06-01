from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Iterator, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from zemax_agent.core.config import LLMConfig

logger = logging.getLogger(__name__)


class LLMCallResult(BaseModel):
    content: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    finish_reason: str = "stop"
    model: str = ""
    usage: dict[str, int] = Field(default_factory=dict)
    duration_ms: float = 0.0


class OpticalRequirements(BaseModel):
    system_type: str = ""
    focal_length: Optional[float] = None
    f_number: Optional[float] = None
    field_of_view: Optional[float] = None
    wavelength_range: Optional[tuple[float, float]] = None
    wavelength_primary: Optional[float] = None
    image_height: Optional[float] = None
    back_focal_length: Optional[float] = None
    total_track_limit: Optional[float] = None
    mtf_target: Optional[dict[str, float]] = None
    distortion_limit: Optional[float] = None
    telecentric: Optional[bool] = None
    special_requirements: list[str] = Field(default_factory=list)
    missing_params: list[str] = Field(default_factory=list)
    raw_description: str = ""


class LLMProvider:
    def __init__(self, config: LLMConfig):
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key or "placeholder",
            base_url=config.api_base,
            timeout=config.request_timeout,
            max_retries=config.max_retries,
        )
        self._call_count: int = 0
        self._total_tokens: int = 0
        self._total_cost: float = 0.0

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_model: Optional[type[BaseModel]] = None,
    ) -> LLMCallResult:
        start = time.perf_counter()

        msgs = self._compress_if_needed(messages)
        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "messages": msgs,
            "temperature": temperature or self._config.temperature,
            "max_tokens": max_tokens or self._config.max_tokens,
        }

        if tools:
            kwargs["tools"] = tools

        if response_model:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        duration = (time.perf_counter() - start) * 1000
        self._call_count += 1

        usage = {}
        if response.usage:
            self._total_tokens += response.usage.total_tokens
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args,
                })

        content = choice.message.content or ""
        if response_model and content:
            try:
                parsed = response_model.model_validate_json(content)
                return LLMCallResult(
                    content=content, tool_calls=tool_calls,
                    finish_reason=choice.finish_reason or "stop",
                    model=self._config.model, usage=usage, duration_ms=duration,
                )
            except Exception:
                pass

        return LLMCallResult(
            content=content, tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            model=self._config.model, usage=usage, duration_ms=duration,
        )

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        msgs = self._compress_if_needed(messages)
        stream = self._client.chat.completions.create(
            model=self._config.model,
            messages=msgs,
            temperature=temperature or self._config.temperature,
            max_tokens=max_tokens or self._config.max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def extract_structured_output(
        self,
        messages: list[dict[str, Any]],
        output_model: type[BaseModel],
    ) -> Optional[BaseModel]:
        result = self.chat(
            messages=messages,
            response_model=output_model,
            temperature=0.0,
        )
        if result.content:
            try:
                return output_model.model_validate_json(result.content)
            except Exception as e:
                logger.warning("Structured output parse failed: %s", e)
        return None

    def parse_requirements(self, user_description: str) -> OpticalRequirements:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an optical engineering assistant. Extract structured optical design requirements "
                    "from the user's natural language description. Output valid JSON matching the schema. "
                    "If a parameter is not mentioned, omit it. List parameters the user should clarify "
                    "in the 'missing_params' field. All numerical values should be in millimeters and degrees."
                ),
            },
            {"role": "user", "content": user_description},
        ]
        result = self.chat(messages=messages, temperature=0.0)
        try:
            data = json.loads(result.content)
            req = OpticalRequirements(
                raw_description=user_description,
                **{k: v for k, v in data.items() if k in OpticalRequirements.model_fields},
            )
            return req
        except (json.JSONDecodeError, Exception):
            return OpticalRequirements(raw_description=user_description)

    def _compress_if_needed(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        estimated_tokens = sum(
            len(json.dumps(m.get("content", ""), ensure_ascii=False)) // 3
            for m in messages
        )

        max_tokens = self._config.context_window_size or 128000
        if estimated_tokens < max_tokens * 0.8:
            return messages

        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        if len(non_system) <= self._config.max_context_messages:
            return system_msgs + non_system

        keep = max(4, self._config.max_context_messages)
        recent = non_system[-keep:]

        return system_msgs + recent

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
            "total_cost_usd": round(self._total_cost, 4),
        }
