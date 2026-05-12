"""Supervisor Agent — meta-agent that monitors quality and decides escalation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.agents.llm import call_llm

logger = logging.getLogger(__name__)

QUALITY_PROMPT = """\
ประเมินคุณภาพของ response นี้สำหรับลูกค้า ShopEasy

Intent: {intent}
คำถามลูกค้า: {customer_message}
คำตอบ AI: {response}
Tools ที่ใช้: {tools_used}

ประเมินเป็น JSON เท่านั้น (ไม่ต้อง markdown):
{{"quality_score": 0.0-1.0, "issues": ["ปัญหาที่พบ"], "requires_human": true/false, "reason": "เหตุผล"}}

เกณฑ์:
- คำตอบตรงกับ intent หรือไม่ (0.3)
- ใช้ tools ที่เหมาะสมหรือไม่ (0.2)
- ข้อมูลครบถ้วนหรือไม่ (0.3)
- ภาษาถูกต้อง สุภาพหรือไม่ (0.2)
"""


@dataclass
class SupervisionResult:
    approved: bool
    quality_score: float
    requires_human: bool
    issues: list[str] = field(default_factory=list)
    reason: str = ""


class SupervisorAgent:
    """
    Full Supervisor Agent — monitors quality and decides escalation.
    Uses rule-based checks first (saves LLM tokens), then LLM quality check.
    """

    QUALITY_THRESHOLD = 0.6
    HIGH_RISK_SCORE = 70

    def supervise(
        self,
        intent: str,
        customer_message: str,
        response: str,
        risk_score: int = 0,
        replan_count: int = 0,
        tools_used: list[str] | None = None,
    ) -> SupervisionResult:
        """
        Evaluate response quality and decide if human review is needed.
        Rule-based checks run FIRST to save LLM tokens.
        """
        tools_used = tools_used or []

        # ── Rule-based checks (no LLM needed) ─────────────────────────────────
        if risk_score >= self.HIGH_RISK_SCORE:
            return SupervisionResult(
                approved=False,
                quality_score=0.5,
                requires_human=True,
                issues=["High risk score"],
                reason=f"Risk score {risk_score} ≥ {self.HIGH_RISK_SCORE}",
            )

        if replan_count >= 2:
            return SupervisionResult(
                approved=False,
                quality_score=0.4,
                requires_human=True,
                issues=["Too many replans"],
                reason=f"Replanned {replan_count} ครั้ง — ส่ง human",
            )

        if not response or len(response.strip()) < 10:
            return SupervisionResult(
                approved=False,
                quality_score=0.2,
                requires_human=True,
                issues=["Empty or too short response"],
                reason="Response ว่างหรือสั้นเกินไป",
            )

        # ── LLM quality check ─────────────────────────────────────────────────
        prompt = QUALITY_PROMPT.format(
            intent=intent,
            customer_message=customer_message,
            response=response,
            tools_used=", ".join(tools_used) or "ไม่มี",
        )

        system = "คุณคือ QA Agent ของ ShopEasy ตอบเป็น JSON เท่านั้น"
        result_text = call_llm(system, "", prompt)

        if result_text is None:
            # LLM unavailable — approve by default (rule-based passed)
            return SupervisionResult(
                approved=True,
                quality_score=0.7,
                requires_human=False,
                reason="LLM QA unavailable — rule-based checks passed",
            )

        try:
            text = result_text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
        except json.JSONDecodeError:
            # Can't parse LLM response — approve by default
            return SupervisionResult(
                approved=True,
                quality_score=0.6,
                requires_human=False,
                reason="QA parse error — rule-based checks passed",
            )

        score = float(data.get("quality_score", 0.5))
        requires_human = data.get("requires_human", False)

        return SupervisionResult(
            approved=score >= self.QUALITY_THRESHOLD and not requires_human,
            quality_score=score,
            requires_human=requires_human,
            issues=data.get("issues", []),
            reason=data.get("reason", ""),
        )
