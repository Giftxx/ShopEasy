"""Tool Registry — central registry of all tools the AI agent can select from."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Type

from pydantic import BaseModel


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    handler: Callable
    tags: list[str] = field(default_factory=list)
    requires_db: bool = False
    max_retries: int = 3
    timeout_seconds: int = 10


class ToolRegistry:
    """Central registry of all available tools for autonomous selection."""

    _tools: dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool: ToolDefinition):
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> ToolDefinition:
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        return cls._tools[name]

    @classmethod
    def list_for_llm(cls, tags: list[str] | None = None) -> list[dict]:
        """Return tool descriptions formatted for LLM prompt."""
        tools = list(cls._tools.values())
        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_fields": list(t.input_schema.model_fields.keys()),
                "output_fields": list(t.output_schema.model_fields.keys()),
                "tags": t.tags,
            }
            for t in tools
        ]

    @classmethod
    def list_names(cls) -> list[str]:
        return list(cls._tools.keys())

    @classmethod
    def reset(cls):
        """Reset registry (for testing)."""
        cls._tools = {}
