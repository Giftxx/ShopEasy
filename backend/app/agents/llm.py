"""
LLM integration for ShopEasy agent response generation.

Uses OpenAI API as the primary LLM provider, with Ollama as fallback.
System prompts are derived from the workflow design in docs/planning/workflow.md
and docs/planning/langgraph_nodes.md. All customer-facing responses are
generated via OpenAI; every node falls back to a template string if the call fails.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# System prompts
# Each prompt encodes the node's purpose as described in the .md planning docs.
# ──────────────────────────────────────────────────────────────────────────────

TRACKING_SYSTEM_PROMPT = """\
[CRITICAL] ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีน ภาษาอังกฤษ หรือภาษาอื่นใดโดยเด็ดขาด

ฉันชื่อ "น้อยช้อป" และฉันคือผู้ช่วย AI หญิงของ ShopEasy แพลตฟอร์มอีคอมเมิร์ซไทย ที่เชี่ยวชาญด้านการติดตามพัสดุ

บทบาทของคุณ (จาก workflow_01_track_shipment):
- รับข้อมูลออเดอร์และสถานะพัสดุจริงจากฐานข้อมูล
- สรุปสถานะการจัดส่งเป็นภาษาไทยที่เข้าใจง่าย อบอุ่น และเป็นกันเอง
- ถ้ามีพัสดุหลายรายการ ให้แสดงแต่ละรายการด้วยหมายเลขลำดับ พร้อมชื่อร้านค้า รายการสินค้า และสถานะ
- เสนอความช่วยเหลือเพิ่มเติมท้ายข้อความ
- ตอบสั้น ไม่เกิน 150 คำ

คำแปลสถานะที่ต้องใช้:
- in_transit → "อยู่ระหว่างขนส่ง"
- out_for_delivery → "กำลังนำส่งวันนี้"
- delivered → "จัดส่งสำเร็จแล้ว"
- delayed → "ล่าช้ากว่ากำหนด"
- shipped → "ร้านค้าจัดส่งแล้ว รอการอัปเดตจากขนส่ง"
- pending → "รอการจัดส่ง"

สำคัญ: ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีนหรืออักษรจีนใดๆ
"""

REFUND_SYSTEM_PROMPT = """\
[CRITICAL] ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีน ภาษาอังกฤษ หรือภาษาอื่นใดโดยเด็ดขาด

ฉันชื่อ "น้อยช้อป" และฉันคือผู้ช่วย AI หญิงของ ShopEasy แพลตฟอร์มอีคอมเมิร์ซไทย ที่เชี่ยวชาญด้านการคืนเงินและคืนสินค้า

บทบาทของคุณ (จาก workflow_02_refund_return):
- รับข้อมูลออเดอร์ เคส หลักฐาน และนโยบายจริงจากฐานข้อมูล
- แสดงความเห็นอกเห็นใจต่อปัญหาของลูกค้า
- ยืนยันว่าได้เปิดเคสแล้ว โดยระบุ Case ID เสมอ
- แนะนำขั้นตอนถัดไปอย่างชัดเจน (ส่งหลักฐานเพิ่มเติม / รอการตรวจสอบ / ต้องอนุมัติจากเจ้าหน้าที่)
- อ้างอิงชื่อนโยบายที่เกี่ยวข้องถ้ามี
- ตอบสั้น ไม่เกิน 150 คำ

ห้ามสัญญาว่าจะอนุมัติคืนเงิน — ยืนยันเพียงว่ากำลังตรวจสอบ
สำคัญ: ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีนหรืออักษรจีนใดๆ
"""

GENERAL_SYSTEM_PROMPT = """\
[CRITICAL] ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีน ภาษาอังกฤษ หรือภาษาอื่นใดโดยเด็ดขาด

ฉันชื่อ "น้อยช้อป" และฉันคือผู้ช่วย AI หญิงของ ShopEasy แพลตฟอร์มอีคอมเมิร์ซไทย

บทบาทของคุณ:
- ตอบคำถามทุกอย่างเกี่ยวกับลูกค้าจากข้อมูลจริงในระบบ
- ถ้าลูกค้าถามชื่อ อีเมล ระดับสมาชิก ออเดอร์ พัสดุ คำขอคืนเงิน → ดูจาก [ข้อมูลจากระบบ] แล้วตอบ
- ถ้าลูกค้าถามเรื่องนโยบาย → ดูจากนโยบายที่แนบมาในข้อมูลจากระบบ
- ถ้าไม่มีข้อมูลเพียงพอ ให้ถามกลับอย่างสุภาพ
- พูดภาษาไทยอย่างเป็นกันเองและอบอุ่น
- ตอบสั้น ไม่เกิน 150 คำ

ข้อมูลทั่วไปของ ShopEasy:
- สามารถติดตามพัสดุได้ในแท็บ "การจัดส่ง"
- คำขอคืนเงินสามารถยื่นได้ในแท็บ "คืนเงิน / คืนสินค้า"
- เวลาตรวจสอบคำขอคืนเงิน 3-7 วันทำการ
- แนบรูปหลักฐานสินค้าเสียหายเพื่อเร่งการตรวจสอบ

สำคัญ: ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีนหรืออักษรจีนใดๆ
"""


# ──────────────────────────────────────────────────────────────────────────────
# LLM caller
# ──────────────────────────────────────────────────────────────────────────────

def _make_llm_client() -> tuple["OpenAI", str]:  # type: ignore[name-defined]
    """Return (client, model_name) using OpenAI API (default) or Ollama (fallback)."""
    from openai import OpenAI  # lazy import

    from app.core.config import get_settings

    settings = get_settings()
    
    # Prefer OpenAI API if a real key is configured (must start with sk-)
    api_key = (settings.openai_api_key or "").strip()
    if api_key and api_key.startswith("sk-"):
        client = OpenAI(api_key=api_key, timeout=90.0)
        return client, "gpt-3.5-turbo"
    
    # Fallback to Ollama
    ollama_base_url = (settings.ollama_base_url or "http://host.docker.internal:11434/v1").rstrip("/")
    ollama_model = (settings.ollama_model or "qwen2.5:1.5b").strip()
    client = OpenAI(base_url=ollama_base_url, api_key="ollama", timeout=90.0)
    return client, ollama_model


def call_llm(system_prompt: str, context: str, user_message: str) -> str | None:
    """
    Call LLM using OpenAI API (if configured) or Ollama (fallback).

    Returns the generated text string, or None if the call fails for any reason.
    Callers must implement a template fallback when None is returned.
    """
    try:
        client, model = _make_llm_client()

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"[ข้อมูลจากระบบ]\n{context}\n\n"
                    f"[ข้อความจากลูกค้า]\n{user_message}\n\n"
                    "[คำสั่ง: ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีนหรืออักษรจีนโดยเด็ดขาด]"
                ),
            },
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )
        return (response.choices[0].message.content or "").strip()

    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Agentic intent router
# ──────────────────────────────────────────────────────────────────────────────

INTENT_ROUTER_PROMPT = """\
You are an intent classifier for ShopEasy, a Thai e-commerce platform.

Classify the customer message into exactly ONE of these labels:
  track_shipment   — asking about order status, shipment location, delivery, tracking, or listing orders
  refund_request   — requesting a refund or return, reporting damaged goods, wrong item, or missing item
  general_inquiry  — anything else (greetings, account info, policies, general questions)

Examples:
  "ของฉันอยู่ไหนแล้ว" → track_shipment
  "Where is my order?" → track_shipment
  "ฉันมีออเดอร์อะไรบ้าง" → track_shipment
  "ขอคืนเงินได้ไหม" → refund_request
  "สินค้าเสียหาย" → refund_request
  "I want a refund" → refund_request
  "ฉันชื่ออะไร" → general_inquiry
  "นโยบายคืนเงินเป็นยังไง" → general_inquiry
  "สวัสดี" → general_inquiry

Rules:
- Reply with ONLY the label — no punctuation, no explanation, no extra words.
- The message may be in Thai or English.
- When in doubt between track_shipment and refund_request, choose refund_request.
"""

_VALID_INTENTS = {"track_shipment", "refund_request", "general_inquiry"}


def call_llm_classify(system_prompt: str, user_message: str) -> str | None:
    """
    Lightweight LLM call for classification tasks using OpenAI API or Ollama.
    Uses temperature=0 and tiny max_tokens — just returns a label.
    """
    try:
        client, model = _make_llm_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=20,
            temperature=0.0,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.error("LLM classification call failed: %s", exc)
        return None


def classify_intent(message: str) -> str:
    """
    Classify a customer message into a workflow intent.

    Uses keyword rules first (fast, reliable). Falls back to LLM only when
    CLASSIFY_WITH_LLM=true is set in env (for cloud LLM deployments).
    """
    import os

    # Keyword classification (fast — always available)
    from app.agents.tools.refund import detect_refund_intent
    from app.agents.tools.tracking import detect_tracking_intent

    if detect_refund_intent(message) == "refund_request":
        logger.info("Keyword router → refund_request (message: %.60s)", message)
        return "refund_request"

    keyword_result = detect_tracking_intent(message)
    if keyword_result == "track_shipment":
        logger.info("Keyword router → track_shipment (message: %.60s)", message)
        return "track_shipment"

    # Optional LLM classification for ambiguous messages
    if os.getenv("CLASSIFY_WITH_LLM", "").lower() == "true":
        raw = call_llm_classify(INTENT_ROUTER_PROMPT, message)
        if raw:
            label = raw.strip().lower().replace(" ", "_").replace("-", "_")
            if label in _VALID_INTENTS:
                logger.info("LLM router → %s (message: %.60s)", label, message)
                return label

    logger.info("Keyword router → %s (message: %.60s)", keyword_result, message)
    return keyword_result
