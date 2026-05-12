"""Planning Layer — creates execution plans before running tools."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.agents.llm import call_llm

logger = logging.getLogger(__name__)

PLAN_PROMPT = """\
สร้าง execution plan สำหรับจัดการคำขอนี้

## Intent: {intent}
## Customer Context: {context_json}
## Tools ที่ใช้ได้:
{tools_json}

สร้าง plan เป็น JSON เท่านั้น (ไม่ต้อง markdown):
{{"plan_id": "PLAN-XXXXXXXX", "reasoning": "เหตุผลที่เลือก steps เหล่านี้", "steps": [{{"step": 1, "tool": "tool_name", "description": "อธิบาย", "params": {{"key": "{{{{context.field}}}}"}}, "output_mapping": {{"output_field": "next.input_field"}}, "depends_on": [], "fallback_tool": null}}], "requires_human_approval": false, "risk_level": "low", "estimated_steps": 3}}
"""

REPLAN_PROMPT = """\
Plan เดิมล้มเหลวที่ step {failed_step}
เหตุผล: {failure_reason}

Steps ที่ทำสำเร็จแล้ว: {completed_steps}
Context ที่มีอยู่: {context_json}
Tools ที่ใช้ได้: {tools_json}

สร้าง plan ใหม่สำหรับ steps ที่เหลือ (JSON เท่านั้น):
{{"plan_id": "PLAN-XXXXXXXX", "reasoning": "...", "steps": [...], "requires_human_approval": false, "risk_level": "low", "estimated_steps": 2}}
"""


@dataclass
class PlanStep:
    step: int
    tool: str
    description: str
    params: dict = field(default_factory=dict)
    output_mapping: dict = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)
    fallback_tool: str | None = None
    status: str = "pending"  # pending | running | done | failed
    error: str | None = None


@dataclass
class ExecutionPlan:
    plan_id: str
    intent: str
    steps: list[PlanStep]
    reasoning: str = ""
    requires_human_approval: bool = False
    risk_level: str = "low"
    created_at: datetime = field(default_factory=datetime.utcnow)
    replan_count: int = 0

    def completed_steps(self) -> list[int]:
        return [s.step for s in self.steps if s.status == "done"]

    def next_step(self) -> PlanStep | None:
        return next((s for s in self.steps if s.status == "pending"), None)

    def to_chain_plan(self) -> list[dict]:
        """Convert to format expected by ToolChainExecutor."""
        return [
            {
                "step": s.step,
                "tool": s.tool,
                "params": s.params,
                "output_mapping": s.output_mapping,
            }
            for s in self.steps
            if s.status == "pending"
        ]

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "intent": self.intent,
            "reasoning": self.reasoning,
            "steps": [
                {
                    "step": s.step,
                    "tool": s.tool,
                    "description": s.description,
                    "status": s.status,
                    "error": s.error,
                }
                for s in self.steps
            ],
            "requires_human_approval": self.requires_human_approval,
            "risk_level": self.risk_level,
            "replan_count": self.replan_count,
        }


class Planner:
    """Creates and manages execution plans using LLM."""

    def create_plan(self, intent: str, context: dict, available_tools: list) -> ExecutionPlan:
        """Create an execution plan using LLM."""
        # Serialize context safely
        safe_context = {}
        for k, v in context.items():
            try:
                json.dumps(v)
                safe_context[k] = v
            except (TypeError, ValueError):
                safe_context[k] = str(v)

        prompt = PLAN_PROMPT.format(
            intent=intent,
            context_json=json.dumps(safe_context, ensure_ascii=False, default=str),
            tools_json=json.dumps(available_tools, ensure_ascii=False, indent=2),
        )

        system = "คุณคือ AI Planner ของ ShopEasy ตอบเป็น JSON เท่านั้น"
        response = call_llm(system, "", prompt)

        if response is None:
            # Fallback: create a simple default plan based on intent
            return self._default_plan(intent, context)

        try:
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Planner: invalid JSON from LLM, using default plan")
            return self._default_plan(intent, context)

        steps = []
        for s in data.get("steps", []):
            steps.append(PlanStep(
                step=s.get("step", len(steps) + 1),
                tool=s.get("tool", ""),
                description=s.get("description", ""),
                params=s.get("params", {}),
                output_mapping=s.get("output_mapping", {}),
                depends_on=s.get("depends_on", []),
                fallback_tool=s.get("fallback_tool"),
            ))

        plan_id = data.get("plan_id", f"PLAN-{uuid.uuid4().hex[:8].upper()}")

        return ExecutionPlan(
            plan_id=plan_id,
            intent=intent,
            steps=steps,
            reasoning=data.get("reasoning", ""),
            requires_human_approval=data.get("requires_human_approval", False),
            risk_level=data.get("risk_level", "low"),
        )

    def replan(self, plan: ExecutionPlan, failed_step: PlanStep, context: dict, available_tools: list) -> ExecutionPlan:
        """Replan after a step failure."""
        safe_context = {}
        for k, v in context.items():
            try:
                json.dumps(v)
                safe_context[k] = v
            except (TypeError, ValueError):
                safe_context[k] = str(v)

        prompt = REPLAN_PROMPT.format(
            failed_step=failed_step.step,
            failure_reason=failed_step.error or "unknown",
            completed_steps=plan.completed_steps(),
            context_json=json.dumps(safe_context, ensure_ascii=False, default=str),
            tools_json=json.dumps(available_tools, ensure_ascii=False, indent=2),
        )

        system = "คุณคือ AI Planner ของ ShopEasy ตอบเป็น JSON เท่านั้น"
        response = call_llm(system, "", prompt)

        if response is None:
            plan.replan_count += 1
            return plan

        try:
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
        except json.JSONDecodeError:
            plan.replan_count += 1
            return plan

        new_steps = []
        for s in data.get("steps", []):
            new_steps.append(PlanStep(
                step=s.get("step", len(new_steps) + 1),
                tool=s.get("tool", ""),
                description=s.get("description", ""),
                params=s.get("params", {}),
                output_mapping=s.get("output_mapping", {}),
                depends_on=s.get("depends_on", []),
                fallback_tool=s.get("fallback_tool"),
            ))

        plan.steps = [s for s in plan.steps if s.status == "done"] + new_steps
        plan.replan_count += 1
        return plan

    def _default_plan(self, intent: str, context: dict) -> ExecutionPlan:
        """Create a default plan based on intent when LLM fails."""
        plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
        customer_id = context.get("customer_id", "")

        if intent == "track_shipment":
            steps = [
                PlanStep(step=1, tool="get_shipment_status", description="ดึงข้อมูล shipment",
                         params={"customer_id": customer_id}),
                PlanStep(step=2, tool="build_tracking_response", description="สร้างข้อความตอบ",
                         params={"customer_name": context.get("customer_name", ""), "shipments": "{{step_1.shipments}}"}),
            ]
        elif intent == "refund_request":
            steps = [
                PlanStep(step=1, tool="get_order_detail", description="ดึงข้อมูล order",
                         params={"customer_id": customer_id, "order_id": context.get("order_id")}),
                PlanStep(step=2, tool="search_policy", description="ค้นหา policy",
                         params={"query": "refund return policy"}),
                PlanStep(step=3, tool="calculate_refund_risk", description="คำนวณ risk",
                         params={"order_total": "{{step_1.order_total}}", "evidence_result": {}}),
            ]
        else:
            steps = [
                PlanStep(step=1, tool="get_order_detail", description="ดึงข้อมูลทั่วไป",
                         params={"customer_id": customer_id}),
            ]

        return ExecutionPlan(
            plan_id=plan_id,
            intent=intent,
            steps=steps,
            reasoning="Default plan (LLM unavailable)",
        )
