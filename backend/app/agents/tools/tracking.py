from __future__ import annotations

from typing import Any

from app.schemas.chat import ShipmentSummary


def _get_attr(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def detect_tracking_intent(message: str) -> str:
    lowered = message.lower()
    tracking_keywords = [
        "อยู่ไหน",
        "พัสดุ",
        "tracking",
        "track",
        "shipment",
        "order status",
        "ส่งแล้ว",
        "จัดส่ง",
        "ออเดอร์",
        "สถานะ",
        "delivery",
        "deliver",
    ]
    if any(keyword in lowered for keyword in tracking_keywords):
        return "track_shipment"
    return "general_inquiry"


def build_memory_summary(context: Any) -> str:
    customer_name = _get_attr(_get_attr(context, "customer", {}), "name", "customer")
    active_orders = _get_attr(context, "active_orders", [])
    active_shipments = _get_attr(context, "active_shipments", [])
    return (
        f"Customer {customer_name} has "
        f"{len(active_orders)} active orders and "
        f"{len(active_shipments)} active shipments."
    )


def build_status_note(status: str) -> str:
    notes = {
        "in_transit": "อยู่ระหว่างขนส่ง และยังไม่มีอัปเดตล่าสุด",
        "out_for_delivery": "กำลังนำส่งวันนี้",
        "shipped": "ร้านค้าจัดส่งแล้วและอยู่ระหว่างอัปเดตจากขนส่ง",
        "packing": "คำสั่งซื้อกำลังเตรียมจัดส่ง",
        "pending": "ระบบรับคำสั่งซื้อแล้วและกำลังรอการจัดส่ง",
        "delivered": "จัดส่งสำเร็จแล้ว",
    }
    return notes.get(status, "สถานะกำลังอัปเดต")


def build_shipment_summaries(context: Any) -> list[ShipmentSummary]:
    shipments = _get_attr(context, "active_shipments", [])
    summaries: list[ShipmentSummary] = []

    for shipment in shipments:
        order_id = _get_attr(shipment, "order_id", "UNKNOWN")
        seller_name = _get_attr(shipment, "seller_name", None)
        if seller_name is None:
            order = _get_attr(shipment, "order", None)
            seller = _get_attr(order, "seller", None) if order is not None else None
            seller_name = _get_attr(seller, "name", "Unknown seller")

        item_names = _get_attr(shipment, "item_names", None)
        if item_names is None:
            shipment_items = _get_attr(shipment, "shipment_items", []) or _get_attr(shipment, "items", [])
            derived_names: list[str] = []
            for shipment_item in shipment_items:
                order_item = _get_attr(shipment_item, "order_item", None)
                product_name = _get_attr(order_item, "product_name", None)
                if product_name:
                    derived_names.append(product_name)
            item_names = derived_names or ["สินค้า"]

        shipment_status = _get_attr(shipment, "shipment_status", "unknown")
        summaries.append(
            ShipmentSummary(
                order_id=order_id,
                seller_name=seller_name,
                item_names=item_names,
                shipment_status=shipment_status,
                note=build_status_note(shipment_status),
            )
        )

    return summaries


def build_tracking_response(shipments: list[Any]) -> str:
    if not shipments:
        return "ตอนนี้ยังไม่พบพัสดุที่กำลังจัดส่งค่ะ หากต้องการ ฉันช่วยเช็กออเดอร์ที่ส่งสำเร็จแล้วให้ต่อได้ค่ะ"

    lines: list[str] = [f"ตอนนี้คุณมี {len(shipments)} พัสดุที่ยังไม่ถึงค่ะ", ""]
    for index, shipment in enumerate(shipments, start=1):
        order_id = _get_attr(shipment, "order_id", "UNKNOWN")
        item_names = _get_attr(shipment, "item_names", ["สินค้า"])
        seller_name = _get_attr(shipment, "seller_name", "Unknown seller")
        note = _get_attr(shipment, "note", "สถานะกำลังอัปเดต")
        lines.append(f"{index}. ออเดอร์ {order_id}: {', '.join(item_names)} จากร้าน {seller_name}")
        lines.append(f"สถานะ: {note}")
        lines.append("")
    lines.append("ต้องการให้ฉันติดตามรายการไหนเป็นพิเศษไหมคะ?")
    return "\n".join(lines)
