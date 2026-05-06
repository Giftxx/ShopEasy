from __future__ import annotations

from datetime import datetime, timedelta

from app.db.models import Policy, Shipment


def detect_proactive_event(event_type: str) -> str:
    if event_type == "shipment_no_update_48h":
        return "proactive_delay_alert"
    return "proactive_delay_alert"


def calculate_delay_risk(shipment: Shipment) -> int:
    if shipment.delay_risk_score is not None:
        return min(100, max(0, shipment.delay_risk_score))
    return 50


def is_stale_update(last_update: datetime | None, threshold_hours: int = 48) -> bool:
    if last_update is None:
        return True
    return last_update <= datetime.utcnow() - timedelta(hours=threshold_hours)


def select_proactive_policy_titles(policies: list[Policy]) -> list[str]:
    return [policy.title for policy in policies if policy.title]


def build_proactive_message(order_id: str, shipment_id: str, risk_score: int) -> str:
    return (
        f"เราแจ้งเตือนล่วงหน้าสำหรับออเดอร์ {order_id} แล้วค่ะ "
        f"เนื่องจากพัสดุ {shipment_id} ไม่มีการอัปเดตเกิน 48 ชั่วโมง และถูกจัดเป็นความเสี่ยงระดับ {risk_score}/100"
    )
