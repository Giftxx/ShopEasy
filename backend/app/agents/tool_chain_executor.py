"""Tool Chain Executor — executes a plan of tools with automatic output→input mapping."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any

from app.agents.error_recovery import ErrorRecoverySystem
from app.agents.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolChainExecutor:
    """Execute tool chain according to a plan, mapping outputs to inputs automatically."""

    def __init__(self, db=None):
        self.db = db
        self.recovery = ErrorRecoverySystem()
        self.step_results: dict[int, Any] = {}

    async def execute(self, plan: list[dict], context: dict) -> dict:
        """
        Execute a tool chain plan.

        Args:
            plan: [{"step": 1, "tool": "...", "params": {...}, "output_mapping": {...}}, ...]
            context: initial context dict

        Returns:
            {"results": {...}, "context": {...}, "success": True} or error dict
        """
        accumulated_context = dict(context)

        for step_def in plan:
            step_num = step_def["step"]
            tool_name = step_def["tool"]
            raw_params = step_def.get("params", {})
            output_mapping = step_def.get("output_mapping", {})

            # Resolve params
            resolved_params = self._resolve_params(raw_params, accumulated_context)

            # Get tool definition
            try:
                tool_def = ToolRegistry.get(tool_name)
            except ValueError as e:
                logger.error("Step %d: %s", step_num, e)
                continue

            kwargs = {}
            if tool_def.requires_db:
                kwargs["db"] = self.db

            # Execute with error recovery
            result = await self.recovery.execute_with_recovery(
                tool_name=tool_name,
                params=resolved_params,
                handler=tool_def.handler,
                kwargs=kwargs,
            )

            if not result.success:
                if result.escalate:
                    return {
                        "error": f"Tool {tool_name} failed at step {step_num}",
                        "escalate": True,
                        "step": step_num,
                        "results": self.step_results,
                    }
                continue

            # Store step result
            self.step_results[step_num] = result.data

            # Apply output mapping
            self._apply_output_mapping(result.data, output_mapping, accumulated_context, step_num)

        return {"results": self.step_results, "context": accumulated_context, "success": True}

    def execute_sync(self, plan: list[dict], context: dict) -> dict:
        """Synchronous version of execute."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in an async context, run in a new loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.execute(plan, context))
                    return future.result()
            return loop.run_until_complete(self.execute(plan, context))
        except RuntimeError:
            return asyncio.run(self.execute(plan, context))

    def _resolve_params(self, params: dict, context: dict) -> dict:
        """Replace {{context.field}} and {{step_N.field}} with actual values."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                path = value[2:-2].strip()
                resolved[key] = self._resolve_path(path, context)
            else:
                resolved[key] = value
        return resolved

    def _resolve_path(self, path: str, context: dict) -> Any:
        """Resolve 'step_1.order_total' or 'context.customer_id'."""
        parts = path.split(".", 1)
        root = parts[0]
        remainder = parts[1] if len(parts) > 1 else None

        if root.startswith("step_"):
            step_num = int(root.replace("step_", ""))
            base = self.step_results.get(step_num, {})
        elif root == "context":
            base = context
        else:
            # Try direct lookup in context
            base = context.get(root, context)

        if remainder and isinstance(base, dict):
            return base.get(remainder)
        if remainder is None:
            return base
        return None

    def _apply_output_mapping(self, output: Any, mapping: dict, context: dict, step_num: int):
        """Copy output fields into accumulated context according to mapping."""
        if not mapping or not isinstance(output, dict):
            # If no explicit mapping, merge all output into context
            if isinstance(output, dict):
                for k, v in output.items():
                    context[f"step_{step_num}.{k}"] = v
            return

        for output_field, target_key in mapping.items():
            value = output.get(output_field)
            if value is not None:
                clean_key = target_key.replace("next.", "").replace("context.", "")
                context[clean_key] = value
                context[f"step_{step_num}.{output_field}"] = value
