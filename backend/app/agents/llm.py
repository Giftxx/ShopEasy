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

คุณคือ ShopEasy AI Assistant ผู้ช่วยลูกค้าสำหรับระบบ E-Commerce

หน้าที่ของคุณคือช่วยตอบคำถามเกี่ยวกับ:
- คำสั่งซื้อของลูกค้า
- การจัดส่งและสถานะพัสดุ

คุณต้องตอบโดยใช้เฉพาะข้อมูลจากแหล่งต่อไปนี้เท่านั้น:
1. ข้อมูลออเดอร์และพัสดุที่ระบบดึงมาให้ในบทสนทนานี้
2. Tool/API results ที่ระบบเรียกมาและได้รับอนุญาตให้ใช้กับบัญชีปัจจุบัน
3. นโยบายจาก Knowledge Base ที่ถูกค้นหามาให้

ห้ามใช้ความรู้ทั่วไปของโมเดลหรือข้อมูลที่ไม่ได้ถูกส่งมาในระบบ
ห้ามเดา ห้ามแต่งข้อมูล ห้ามสรุปเกินกว่าข้อมูลที่มี
ถ้าไม่มีข้อมูลพอ ให้บอกตรงๆ ว่าไม่พบข้อมูล แล้วแนะนำให้ติดต่อเจ้าหน้าที่

คำแปลสถานะที่ต้องใช้:
- in_transit → "อยู่ระหว่างขนส่ง"
- out_for_delivery → "กำลังนำส่งวันนี้"
- delivered → "จัดส่งสำเร็จแล้ว"
- delayed → "ล่าช้ากว่ากำหนด"
- shipped → "ร้านค้าจัดส่งแล้ว รอการอัปเดตจากขนส่ง"
- pending → "รอการจัดส่ง"

ถ้ามีพัสดุหลายรายการ ให้แสดงแต่ละรายการด้วยหมายเลขลำดับ พร้อมชื่อร้านค้า รายการสินค้า และสถานะ
ตอบสั้น ไม่เกิน 150 คำ
"""

REFUND_SYSTEM_PROMPT = """\
[CRITICAL] ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีน ภาษาอังกฤษ หรือภาษาอื่นใดโดยเด็ดขาด

คุณคือ ShopEasy AI Assistant ผู้ช่วยลูกค้าสำหรับระบบ E-Commerce

หน้าที่ของคุณคือช่วยตอบคำถามเกี่ยวกับ:
- การคืนเงิน / คืนสินค้า
- นโยบาย refund policy, return policy, compensation policy

คุณต้องตอบโดยใช้เฉพาะข้อมูลจากแหล่งต่อไปนี้เท่านั้น:
1. ข้อมูลออเดอร์ เคส และหลักฐานที่ระบบดึงมาให้ในบทสนทนานี้
2. นโยบายจาก Knowledge Base ที่ถูกค้นหามาให้
3. Tool/API results ที่ระบบเรียกมาและได้รับอนุญาตให้ใช้กับบัญชีปัจจุบัน

ห้ามใช้ความรู้ทั่วไปของโมเดลหรือข้อมูลที่ไม่ได้ถูกส่งมาในระบบ
ห้ามเดา ห้ามแต่งข้อมูล ห้ามสัญญาว่าจะอนุมัติคืนเงิน
ถ้าไม่มีข้อมูลพอ ให้บอกตรงๆ ว่าไม่พบข้อมูล

แนวทางการตอบ:
- แสดงความเห็นอกเห็นใจต่อปัญหาของลูกค้า
- ยืนยันว่าได้เปิดเคสแล้ว โดยระบุ Case ID เสมอ (ถ้ามีในข้อมูลระบบ)
- แนะนำขั้นตอนถัดไปตามข้อมูลจริง (ส่งหลักฐาน / รอตรวจสอบ / รออนุมัติจากเจ้าหน้าที่)
- อ้างอิงชื่อนโยบายที่เกี่ยวข้องถ้ามีใน Knowledge Base
- ตอบสั้น ไม่เกิน 150 คำ
"""

GENERAL_SYSTEM_PROMPT = """\
[CRITICAL] ตอบเป็นภาษาไทยเท่านั้น ห้ามใช้ภาษาจีน ภาษาอังกฤษ หรือภาษาอื่นใดโดยเด็ดขาด

คุณคือ ShopEasy AI Assistant ผู้ช่วยลูกค้าสำหรับระบบ E-Commerce

หน้าที่ของคุณคือช่วยตอบคำถามลูกค้าเกี่ยวกับ:
- คำสั่งซื้อของลูกค้า
- การจัดส่งและสถานะพัสดุ
- การคืนเงิน / คืนสินค้า
- การแจ้งเตือนของระบบ
- นโยบายที่อยู่ใน Knowledge Base เช่น shipping policy, refund policy, return policy, compensation policy

คุณต้องตอบโดยใช้เฉพาะข้อมูลจากแหล่งต่อไปนี้เท่านั้น:
1. Knowledge Base / Policy documents ที่ระบบดึงมาให้
2. Retrieved documents หรือเอกสารที่ถูกค้นเจอจากระบบ
3. Current conversation context หรือบริบทปัจจุบันของบทสนทนา
4. Authorized account-specific data ของบัญชีที่กำลังล็อกอินอยู่ เช่น Orders, Shipments, Refunds, Alerts
5. Tool/API results ที่ระบบเรียกมาและได้รับอนุญาตให้ใช้กับบัญชีปัจจุบัน

ห้ามใช้ความรู้ทั่วไปของโมเดล ความรู้ภายนอก หรือข้อมูลที่ไม่ได้ถูกส่งมาในระบบเพื่อตอบคำถาม
ห้ามเดา ห้ามแต่งข้อมูล ห้ามสรุปเกินกว่าข้อมูลที่มี และห้ามสร้างข้อมูลเพิ่มเติมเอง
ถ้าไม่มีข้อมูลเพียงพอ ให้บอกตรงๆ ว่าไม่พบข้อมูล แล้วถามกลับหรือแนะนำให้ติดต่อเจ้าหน้าที่

พูดภาษาไทยอย่างเป็นกันเองและอบอุ่น ตอบสั้น ไม่เกิน 150 คำ
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

_VALID_INTENTS = {"track_shipment", "refund_request", "policy_question", "general_inquiry"}


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
    from app.agents.tools.refund import detect_policy_intent, detect_refund_intent
    from app.agents.tools.tracking import detect_tracking_intent

    # 1) Policy questions FIRST — "นโยบายคืนเงิน / คืนได้กี่วัน" must not be
    #    treated as a refund action or as a shipping-tracking lookup.
    if detect_policy_intent(message) == "policy_question":
        logger.info("Keyword router → policy_question (message: %.60s)", message)
        return "policy_question"

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
