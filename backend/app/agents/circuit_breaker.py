"""Circuit Breaker pattern for tool execution resilience."""

from __future__ import annotations

import time
from collections import defaultdict


class CircuitBreaker:
    """
    CLOSED → (threshold fails) → OPEN → (timeout) → HALF_OPEN → (success) → CLOSED

    Class-level state shared across all requests.
    """

    THRESHOLD = 5
    TIMEOUT = 60  # seconds before HALF_OPEN

    _state: dict[str, str] = defaultdict(lambda: "CLOSED")
    _fail_count: dict[str, int] = defaultdict(int)
    _open_time: dict[str, float] = {}

    @classmethod
    def can_execute(cls, tool_name: str) -> bool:
        state = cls._state[tool_name]
        if state == "CLOSED":
            return True
        if state == "OPEN":
            if time.time() - cls._open_time.get(tool_name, 0) > cls.TIMEOUT:
                cls._state[tool_name] = "HALF_OPEN"
                return True
            return False
        # HALF_OPEN — allow one request through to test recovery
        return True

    @classmethod
    def record_success(cls, tool_name: str):
        cls._fail_count[tool_name] = 0
        cls._state[tool_name] = "CLOSED"

    @classmethod
    def record_failure(cls, tool_name: str):
        cls._fail_count[tool_name] += 1
        if cls._fail_count[tool_name] >= cls.THRESHOLD:
            cls._state[tool_name] = "OPEN"
            cls._open_time[tool_name] = time.time()

    @classmethod
    def reset(cls):
        """Reset all state (useful for testing)."""
        cls._state = defaultdict(lambda: "CLOSED")
        cls._fail_count = defaultdict(int)
        cls._open_time = {}
