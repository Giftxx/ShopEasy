"""ReAct Engine — Reasoning + Acting loop for autonomous tool execution."""

from __future__ import annotations

import logging
import time
import time
from dataclasses import dataclass, field
from typing import Any

from app.agents.circuit_breaker import CircuitBreaker
from app.agents.error_recovery import ErrorRecoverySystem
from app.agents.tool_registry import ToolRegistry
from app.agents.tool_selector import ToolSelector

logger = logging.getLogger(__name__)


@dataclass
class ReActObservation:
    iteration: int
    thought: str
    action: str
    params: dict
    result: Any
    success: bool
    used_fallback: bool = False


@dataclass
class ReActState:
    intent: str
    customer_id: str
    context: dict = field(default_factory=dict)
    observations: list[ReActObservation] = field(default_factory=list)
    final_response: str = ""
    react_done: bool = False
    escalate: bool = False
    replan_count: int = 0
    total_tool_calls: int = 0


class ReActEngine:
    """
    ReAct (Reasoning + Acting) engine.
    Loop: THOUGHT → ACTION → OBSERVE → REFLECT → (loop or Finish)
    Max 8 iterations.
    """

    MAX_ITERATIONS = 4
    TIME_BUDGET_SECONDS = 30  # total time budget for the ReAct loop

    def __init__(self, db=None, session_id: str = ""):
        self.db = db
        self.session_id = session_id
        self.tool_selector = ToolSelector()
        self.recovery = ErrorRecoverySystem()

    def run(self, intent: str, customer_id: str, initial_context: dict) -> ReActState:
        """
        Synchronous ReAct loop.
        Returns ReActState with final_response or escalate flag.
        """
        state = ReActState(intent=intent, customer_id=customer_id, context=dict(initial_context))
        start_time = time.time()
        start_time = time.time()

        # Load short-term memory if available
        self._load_memory(state)

        available_tools = ToolRegistry.list_for_llm(
            tags=self._get_relevant_tags(intent)
        )

        for iteration in range(self.MAX_ITERATIONS):
            # Check time budget
            elapsed = time.time() - start_time
            if elapsed > self.TIME_BUDGET_SECONDS:
                logger.warning("ReAct time budget exceeded (%.1fs) — finishing early", elapsed)
                state.final_response = self._build_fallback_response(state)
                state.react_done = True
                break

            # Check time budget
            elapsed = time.time() - start_time
            if elapsed > self.TIME_BUDGET_SECONDS:
                logger.warning("ReAct time budget exceeded (%.1fs) — finishing early", elapsed)
                state.final_response = self._build_fallback_response(state)
                state.react_done = True
                break

            # THOUGHT — LLM decides next action
            thought_result = self.tool_selector.think(
                intent=state.intent,
                context=state.context,
                observations=state.observations,
                available_tools=available_tools,
            )

            action = thought_result.get("action", "FINISH")

            if action == "FINISH":
                state.final_response = thought_result.get("response", "")
                state.react_done = True
                break

            if action == "ESCALATE":
                state.escalate = True
                break

            # ACTION — execute tool
            tool_name = action
            params = thought_result.get("params", {})

            try:
                tool_def = ToolRegistry.get(tool_name)
            except ValueError:
                # Invalid tool name from LLM — log and continue
                obs = ReActObservation(
                    iteration=iteration,
                    thought=thought_result.get("reasoning", ""),
                    action=tool_name,
                    params=params,
                    result=f"Tool '{tool_name}' not found",
                    success=False,
                )
                state.observations.append(obs)
                continue

            # Check circuit breaker
            if not CircuitBreaker.can_execute(tool_name):
                obs = ReActObservation(
                    iteration=iteration,
                    thought=thought_result.get("reasoning", ""),
                    action=tool_name,
                    params=params,
                    result="Circuit breaker OPEN",
                    success=False,
                )
                state.observations.append(obs)
                continue

            kwargs = {"db": self.db} if tool_def.requires_db else {}

            # Execute tool (sync)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in sync context, call handler directly
                    result = self._execute_sync(tool_def.handler, params, kwargs)
                else:
                    result = loop.run_until_complete(
                        self.recovery.execute_with_recovery(
                            tool_name=tool_name,
                            params=params,
                            handler=tool_def.handler,
                            kwargs=kwargs,
                        )
                    )
            except RuntimeError:
                result = self._execute_sync(tool_def.handler, params, kwargs)

            state.total_tool_calls += 1

            # OBSERVE
            obs = ReActObservation(
                iteration=iteration,
                thought=thought_result.get("reasoning", ""),
                action=tool_name,
                params=params,
                result=result.data if hasattr(result, "success") and result.success else (result.error if hasattr(result, "error") else str(result)),
                success=result.success if hasattr(result, "success") else True,
                used_fallback=result.used_fallback if hasattr(result, "used_fallback") else False,
            )
            state.observations.append(obs)

            # Update context with results
            if hasattr(result, "success") and result.success and isinstance(result.data, dict):
                state.context.update(result.data)
            elif isinstance(result, dict):
                state.context.update(result)

            # REFLECT — check if escalation needed
            if hasattr(result, "escalate") and result.escalate:
                state.escalate = True
                break

        # Save short-term memory
        self._save_memory(state)

        return state

    def _execute_sync(self, handler, params: dict, kwargs: dict):
        """Execute a handler synchronously with error recovery wrapping."""
        import inspect
        from app.agents.error_recovery import ToolResult

        try:
            if inspect.iscoroutinefunction(handler):
                import asyncio
                result = asyncio.run(handler(**params, **kwargs))
            else:
                result = handler(**params, **kwargs)
            data = result if isinstance(result, dict) else {"result": result}
            return ToolResult(success=True, data=data)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


    def _build_fallback_response(self, state: ReActState) -> str:
        """Build a response from whatever data we collected so far."""
        ctx = state.context
        parts = []
        if ctx.get("order_status"):
            parts.append(f"Order status: {ctx['order_status']}")
        if ctx.get("shipment_status"):
            parts.append(f"Shipment status: {ctx['shipment_status']}")
        if ctx.get("tracking_no"):
            parts.append(f"Tracking: {ctx['tracking_no']}")
        if parts:
            return "Here is what I found: " + ", ".join(parts)
        return ""


    def _build_fallback_response(self, state: ReActState) -> str:
        """Build a response from whatever data we collected so far."""
        ctx = state.context
        parts = []
        if ctx.get("order_status"):
            parts.append(f"Order status: {ctx['order_status']}")
        if ctx.get("shipment_status"):
            parts.append(f"Shipment status: {ctx['shipment_status']}")
        if ctx.get("tracking_no"):
            parts.append(f"Tracking: {ctx['tracking_no']}")
        if parts:
            return "Here is what I found: " + ", ".join(parts)
        return ""

    def _get_relevant_tags(self, intent: str) -> list[str] | None:
        """Get relevant tool tags based on intent."""
        tag_map = {
            "track_shipment": ["tracking", "proactive"],
            "refund_request": ["refund", "tracking"],
            "proactive_delay_alert": ["proactive", "tracking"],
        }
        return tag_map.get(intent)

    def _load_memory(self, state: ReActState):
        """Try to load short-term memory from Redis."""
        if not self.session_id:
            return
        try:
            import redis
            from app.core.config import get_settings
            settings = get_settings()
            r = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
            import json
            cached = r.hget(f"session:{self.session_id}", "last_context")
            if cached:
                state.context.update(json.loads(cached))
        except Exception:
            pass  # Memory loading is best-effort

    def _save_memory(self, state: ReActState):
        """Save context to short-term memory in Redis."""
        if not self.session_id:
            return
        try:
            import json
            import redis
            from app.core.config import get_settings
            settings = get_settings()
            r = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
            # Only save serializable context
            safe_ctx = {}
            for k, v in state.context.items():
                try:
                    json.dumps(v)
                    safe_ctx[k] = v
                except (TypeError, ValueError):
                    pass
            r.hset(f"session:{self.session_id}", "last_context", json.dumps(safe_ctx, default=str))
            r.expire(f"session:{self.session_id}", 86400)
        except Exception:
            pass  # Memory saving is best-effort
