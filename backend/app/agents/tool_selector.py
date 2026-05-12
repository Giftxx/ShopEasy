"""Tool Selector — LLM-based autonomous tool selection."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.llm import call_llm

logger = logging.getLogger(__name__)

THINK_PROMPT = """\
คุณคือ AI Agent ของ ShopEasy ที่กำลังจัดการคำขอของลูกค้า

## สถานการณ์ปัจจุบัน
- Intent: {intent}
- Context ที่มีอยู่: {context_summary}
- สิ่งที่ทำไปแล้ว: {observations_summary}

## Tools ที่ใช้ได้
{tools_json}

## ตัดสินใจ (เลือก 1 อย่าง)
1. เรียก tool → ระบุ tool name + params (ใช้ field ที่มีจาก context)
2. FINISH → ถ้ามีข้อมูลพอที่จะตอบลูกค้าแล้ว ให้สร้าง response ภาษาไทย
3. ESCALATE → ถ้าไม่สามารถจัดการได้หรือ risk สูงมาก

ตอบเป็น JSON เท่านั้น (ไม่ต้องมี markdown หรือ backtick):
{{"reasoning": "...", "action": "tool_name หรือ FINISH หรือ ESCALATE", "params": {{}}, "response": "ข้อความตอบลูกค้า (ถ้า action = FINISH)"}}
"""


class ToolSelector:
    """Uses LLM to decide which tool to call next in the ReAct loop."""

    def think(self, intent: str, context: dict, observations: list, available_tools: list) -> dict:
        """
        Synchronous think method.
        Returns dict with: reasoning, action, params, response
        """
        obs_summary = "\n".join(
            f"- ใช้ {getattr(o, 'action', o.get('action', '?')) if isinstance(o, dict) else o.action}: "
            f"{'สำเร็จ' if (getattr(o, 'success', True) if not isinstance(o, dict) else o.get('success', True)) else 'ล้มเหลว'}"
            for o in (observations[-3:] if observations else [])
        )

        # Summarize context — only show key fields
        ctx_items = []
        for k, v in list(context.items())[:10]:
            if isinstance(v, (str, int, float, bool)):
                ctx_items.append(f"{k}={v}")
            elif isinstance(v, list):
                ctx_items.append(f"{k}=[{len(v)} items]")
            elif isinstance(v, dict):
                ctx_items.append(f"{k}={{...}}")
        context_summary = ", ".join(ctx_items) or "ไม่มี context"

        prompt = THINK_PROMPT.format(
            intent=intent,
            context_summary=context_summary,
            observations_summary=obs_summary or "ยังไม่ได้ทำอะไร",
            tools_json=json.dumps(available_tools, ensure_ascii=False, indent=2),
        )

        # Use existing call_llm with a system prompt for tool selection
        system = "คุณคือ AI ที่เลือก tool สำหรับ ShopEasy ตอบเป็น JSON เท่านั้น"
        response = call_llm(system, "", prompt)

        if response is None:
            logger.warning("ToolSelector: LLM returned None — escalating")
            return {"action": "ESCALATE", "reasoning": "LLM unavailable", "params": {}, "response": ""}

        # Parse JSON from response
        try:
            # Try to extract JSON from response (may have markdown wrapping)
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("ToolSelector: invalid JSON from LLM: %.200s", response)
            # Try to be smart about it — if it mentions FINISH, use that
            if "FINISH" in response:
                return {"action": "FINISH", "reasoning": "LLM format issue", "params": {}, "response": response}
            return {"action": "ESCALATE", "reasoning": "LLM returned invalid JSON", "params": {}, "response": ""}

    async def think_async(self, intent: str, context: dict, observations: list, available_tools: list) -> dict:
        """Async wrapper — currently delegates to sync think."""
        return self.think(intent, context, observations, available_tools)
