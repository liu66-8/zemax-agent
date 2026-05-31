from __future__ import annotations

import inspect
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, get_type_hints

from pydantic import BaseModel, ConfigDict, Field, create_model

logger = logging.getLogger(__name__)


class ToolInput(BaseModel):
    pass


class ToolOutput(BaseModel):
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class ToolDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    namespace: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    func: Any = Field(default=None, exclude=True)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._namespaces: dict[str, list[str]] = {}
        self._call_logger: Optional[Callable] = None

    def set_call_logger(self, logger_func: Callable) -> None:
        self._call_logger = logger_func

    def register(
        self,
        name: str,
        func: Callable,
        namespace: str = "default",
        description: str = "",
        input_model: Optional[type[BaseModel]] = None,
    ) -> ToolDefinition:
        if namespace not in self._namespaces:
            self._namespaces[namespace] = []

        input_schema = self._build_input_schema(func, input_model)
        output_schema = self._build_output_schema(func)

        tool_def = ToolDefinition(
            name=name,
            namespace=namespace,
            description=description or inspect.getdoc(func) or "",
            input_schema=input_schema,
            output_schema=output_schema,
            func=func,
        )

        self._tools[f"{namespace}.{name}"] = tool_def
        self._namespaces[namespace].append(name)
        return tool_def

    def _build_input_schema(self, func: Callable, input_model: Optional[type[BaseModel]] = None) -> dict[str, Any]:
        if input_model is not None:
            return input_model.model_json_schema()

        hints = get_type_hints(func)
        params = inspect.signature(func).parameters
        fields: dict[str, Any] = {}
        for name, param in params.items():
            if name in ("self", "cls", "conn", "dispatcher"):
                continue
            annotation = hints.get(name, Any)
            if param.default is not inspect.Parameter.empty:
                fields[name] = (annotation, param.default)
            else:
                fields[name] = (annotation, ...)

        if fields:
            model = create_model(f"{func.__name__}_Input", **fields)
            return model.model_json_schema()
        return {"type": "object", "properties": {}}

    def _build_output_schema(self, func: Callable) -> dict[str, Any]:
        hints = get_type_hints(func)
        return_type = hints.get("return", Any)
        if return_type is not inspect.Signature.empty and return_type is not Any:
            try:
                if issubclass(return_type, BaseModel):
                    return return_type.model_json_schema()
            except TypeError:
                pass
        return ToolOutput.model_json_schema()

    def invoke(
        self,
        tool_name: str,
        params: dict[str, Any],
        caller: str = "user",
        session_id: Optional[str] = None,
        **extra_kwargs: Any,
    ) -> ToolOutput:
        full_name = tool_name if "." in tool_name else f"default.{tool_name}"
        tool_def = self._tools.get(full_name)

        if tool_def is None:
            return ToolOutput(success=False, error=f"Tool not found: {full_name}")

        start = time.perf_counter()
        try:
            result = tool_def.func(**params, **extra_kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            output = ToolOutput(success=True, data=result, duration_ms=duration_ms)
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error("Tool %s failed: %s", full_name, e)
            output = ToolOutput(success=False, error=str(e), duration_ms=duration_ms)

        if self._call_logger:
            try:
                self._call_logger(
                    tool_name=full_name,
                    caller=caller,
                    params=params,
                    success=output.success,
                    duration_ms=duration_ms,
                    error=output.error,
                    session_id=session_id,
                )
            except Exception:
                pass

        return output

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name if "." in name else f"default.{name}")

    def list_tools(self, namespace: Optional[str] = None) -> list[ToolDefinition]:
        if namespace:
            names = self._namespaces.get(namespace, [])
            return [self._tools[f"{namespace}.{n}"] for n in names if f"{namespace}.{n}" in self._tools]
        return list(self._tools.values())

    def list_namespaces(self) -> list[str]:
        return list(self._namespaces.keys())

    def get_tools_for_llm(self, namespace: Optional[str] = None) -> list[dict[str, Any]]:
        tools = self.list_tools(namespace=namespace)
        return [
            {
                "type": "function",
                "function": {
                    "name": f"{t.namespace}.{t.name}",
                    "description": t.description,
                    "parameters": t.input_schema,
                },
            }
            for t in tools
        ]


def tool(
    registry: Optional[ToolRegistry] = None,
    namespace: str = "default",
    description: str = "",
):
    def decorator(func: Callable):
        tool_name = func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            return func(*args, **kwargs)

        wrapper._tool_name = tool_name
        wrapper._tool_namespace = namespace
        wrapper._tool_description = description
        wrapper._tool_registry = registry

        if registry is not None:
            registry.register(
                name=tool_name,
                func=func,
                namespace=namespace,
                description=description or inspect.getdoc(func) or "",
            )

        return wrapper

    return decorator
