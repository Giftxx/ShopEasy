"""Error Recovery System with retry, fallback, and escalation."""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from app.agents.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str = ""
    used_fallback: bool = False
    escalate: bool = False


FALLBACK_MAP: dict[str, str] = {
    "get_shipment_status": "get_shipment_from_db_direct",
    "search_policy": "get_all_policies_fallback",
    "calculate_refund_risk": "use_default_risk_medium",
    "get_order_detail": "get_order_from_db_direct",
    "evaluate_evidence": "use_default_evidence_insufficient",
}


class ErrorRecoverySystem:
    """
    3-level error recovery:
    Level 1: Retry with exponential backoff (3 attempts)
    Level 2: Fallback to alternative tool
    Level 3: Escalate to human
    """

    async def execute_with_recovery(
        self,
        tool_name: str,
        params: dict,
        handler: Callable,
        kwargs: dict | None = None,
    ) -> ToolResult:
        kwargs = kwargs or {}
        last_error = ""

        if not CircuitBreaker.can_execute(tool_name):
            return ToolResult(
                success=False,
                error=f"Circuit breaker OPEN for {tool_name}",
                escalate=True,
            )

        # Level 1: Retry with exponential backoff
        for attempt in range(1, 4):
            try:
                if inspect.iscoroutinefunction(handler):
                    result = await handler(**params, **kwargs)
                else:
                    result = handler(**params, **kwargs)
                CircuitBreaker.record_success(tool_name)
                data = result if isinstance(result, dict) else {"result": result}
                return ToolResult(success=True, data=data)
            except Exception as exc:
                last_error = str(exc)
                CircuitBreaker.record_failure(tool_name)
                logger.warning(
                    "Tool %s attempt %d failed: %s", tool_name, attempt, last_error
                )
                if attempt < 3:
                    await asyncio.sleep(2**attempt)

        # Level 2: Fallback
        fallback_name = FALLBACK_MAP.get(tool_name)
        if fallback_name:
            try:
                from app.agents.tool_registry import ToolRegistry

                fallback_def = ToolRegistry.get(fallback_name)
                fb_kwargs = dict(kwargs)
                if fallback_def.requires_db and "db" not in fb_kwargs:
                    pass  # caller must provide db in kwargs if needed

                if inspect.iscoroutinefunction(fallback_def.handler):
                    result = await fallback_def.handler(**params, **fb_kwargs)
                else:
                    result = fallback_def.handler(**params, **fb_kwargs)
                data = result if isinstance(result, dict) else {"result": result}
                logger.info("Tool %s recovered via fallback %s", tool_name, fallback_name)
                return ToolResult(success=True, data=data, used_fallback=True)
            except Exception as fb_exc:
                logger.error("Fallback %s also failed: %s", fallback_name, fb_exc)

        # Level 3: Escalate
        logger.error("Tool %s failed all recovery — escalating", tool_name)
        return ToolResult(success=False, error=last_error, escalate=True)
