from __future__ import annotations

from app.db.models import Attachment, Policy


def detect_refund_intent(message: str) -> str:
    lowered = message.lower()
    refund_keywords = [
        "คืนเงิน",
        "refund",
        "return",
        "สินค้าเสียหาย",
        "ของเสียหาย",
        "ของพัง",
    ]
    if any(keyword in lowered for keyword in refund_keywords):
        return "refund_request"
    return "refund_request"


def select_relevant_policy_titles(policies: list[Policy]) -> list[str]:
    return [policy.title for policy in policies if policy.title]


def evaluate_evidence(attachments: list[Attachment]) -> dict[str, object]:
    groups = sorted({attachment.evidence_group for attachment in attachments if attachment.evidence_group})
    has_damaged_item = "damaged_item" in groups
    sufficient = has_damaged_item or len(groups) >= 2
    return {
        "attachment_count": len(attachments),
        "evidence_groups": groups,
        "sufficient": sufficient,
    }


def calculate_refund_risk(order_total: float | None, evidence_result: dict[str, object]) -> int:
    base_score = 30
    if order_total and order_total > 2000:
        base_score += 25
    if not evidence_result.get("sufficient", False):
        base_score += 20
    if evidence_result.get("attachment_count", 0) >= 3:
        base_score -= 10
    return max(0, min(100, base_score))


def build_refund_response(order_id: str, case_id: str, has_evidence: bool) -> str:
    if has_evidence:
        return (
            f"ได้รับคำขอคืนเงินสำหรับออเดอร์ {order_id} แล้วค่ะ "
            f"ระบบตรวจพบว่าคุณแนบรูปหลักฐานสินค้าเสียหายแล้ว และได้เปิดเคส {case_id} เพื่อส่งให้เจ้าหน้าที่ตรวจสอบค่ะ"
        )
    return (
        f"ได้รับคำขอคืนเงินสำหรับออเดอร์ {order_id} แล้วค่ะ "
        f"ตอนนี้ฉันได้เปิดเคส {case_id} ไว้ให้ก่อน และแนะนำให้แนบรูปสินค้าเสียหาย รูปกล่องพัสดุ และใบปะหน้าเพื่อให้ตรวจสอบได้เร็วขึ้นค่ะ"
    )
