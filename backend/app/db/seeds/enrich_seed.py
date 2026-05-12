"""
Enrich existing seed data to give all 3 portals (Customer, Admin, AI Engineer)
a realistic view with synced data.
"""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AgentTrace,
    Approval,
    Case,
    Conversation,
    Customer,
    Message,
    Order,
    OrderItem,
    ProactiveAlert,
    RefundRequest,
    Seller,
    Shipment,
    ShipmentEvent,
    ShipmentItem,
    ToolLog,
    User,
)
from app.core.security import get_password_hash


def _exists(db: Session, model: type, id_val: str) -> bool:
    return db.scalar(select(model).where(model.id == id_val)) is not None


def enrich(db: Session) -> None:
    now = datetime.utcnow()
    _pw = get_password_hash("demo1234")

    # ── Additional Customer ──────────────────────────────────────────────────
    if not _exists(db, User, "U-004"):
        db.add(User(id="U-004", name="somchai_demo", email="somchai@shopeasy.local",
                     role="customer", status="active", hashed_password=_pw,
                     created_at=now, updated_at=now))
    if not _exists(db, Customer, "CUST-002"):
        db.add(Customer(id="CUST-002", user_id="U-004", name="Somchai",
                        email="somchai@example.com", phone="0811111111",
                        tier="premium", preferred_language="th",
                        created_at=now, updated_at=now))

    # ── Additional Seller ────────────────────────────────────────────────────
    if not _exists(db, Seller, "SELL-003"):
        db.add(Seller(id="SELL-003", name="HomeDecor Plus", sla_level="standard",
                      rating=4.9, status="active", created_at=now, updated_at=now))

    # ── Additional Orders for CUST-001 ───────────────────────────────────────
    new_orders = [
        ("SP-3091", "CUST-001", "SELL-003", "processing", "paid", 3200.00,
         (now + timedelta(days=5)).date(), now - timedelta(days=1)),
        ("SP-4010", "CUST-001", "SELL-001", "completed", "paid", 890.00,
         (now - timedelta(days=3)).date(), now - timedelta(days=10)),
    ]
    for oid, cid, sid, st, ps, amt, dd, cat in new_orders:
        if not _exists(db, Order, oid):
            db.add(Order(id=oid, customer_id=cid, seller_id=sid, order_status=st,
                         payment_status=ps, total_amount=amt, currency="THB",
                         promised_delivery_date=dd, created_at=cat, updated_at=now))

    # ── Orders for CUST-002 ──────────────────────────────────────────────────
    cust2_orders = [
        ("SP-5001", "CUST-002", "SELL-002", "shipped", "paid", 4590.00,
         (now + timedelta(days=3)).date(), now - timedelta(days=5)),
        ("SP-5002", "CUST-002", "SELL-001", "completed", "paid", 1290.00,
         (now - timedelta(days=7)).date(), now - timedelta(days=14)),
    ]
    for oid, cid, sid, st, ps, amt, dd, cat in cust2_orders:
        if not _exists(db, Order, oid):
            db.add(Order(id=oid, customer_id=cid, seller_id=sid, order_status=st,
                         payment_status=ps, total_amount=amt, currency="THB",
                         promised_delivery_date=dd, created_at=cat, updated_at=now))

    # ── Order Items ──────────────────────────────────────────────────────────
    items = [
        ("ITEM-3001", "SP-3091", "โคมไฟตั้งโต๊ะ LED", "HD-LAMP-005", 1, 1450.00),
        ("ITEM-3002", "SP-3091", "หมอนอิง ลายมินิมอล", "HD-PILLOW-012", 2, 875.00),
        ("ITEM-4001", "SP-4010", "เสื้อยืด Oversize", "FHB-SHIRT-OS", 1, 890.00),
        ("ITEM-5001", "SP-5001", "แท็บเล็ต Android 11", "GDM-TAB-11", 1, 4590.00),
        ("ITEM-5002", "SP-5002", "เสื้อเชิ้ตทำงาน", "FHB-FORMAL-01", 1, 1290.00),
    ]
    for iid, oid, pn, sku, qty, price in items:
        if not _exists(db, OrderItem, iid):
            db.add(OrderItem(id=iid, order_id=oid, product_name=pn, sku=sku,
                             quantity=qty, unit_price=price, created_at=now))

    # ── Additional Shipments ─────────────────────────────────────────────────
    new_shipments = [
        ("SHP-4001", "SP-4010", "J&T Express", "TH4001", "delivered", 0,
         (now - timedelta(days=3)).date(), now - timedelta(days=3)),
        ("SHP-5001", "SP-5001", "Kerry Express", "TH5001", "in_transit", 42,
         (now + timedelta(days=3)).date(), now - timedelta(hours=6)),
        ("SHP-5002", "SP-5002", "Flash Express", "TH5002", "delivered", 0,
         (now - timedelta(days=7)).date(), now - timedelta(days=7)),
    ]
    for sid, oid, car, trk, st, risk, eta, lu in new_shipments:
        if not _exists(db, Shipment, sid):
            db.add(Shipment(id=sid, order_id=oid, carrier=car, tracking_no=trk,
                            shipment_status=st, eta=eta, last_update=lu,
                            delay_risk_score=risk, created_at=lu, updated_at=now))

    # ── Shipment Items ───────────────────────────────────────────────────────
    si_list = [
        ("SHIPITEM-010", "SHP-4001", "ITEM-4001", 1),
        ("SHIPITEM-011", "SHP-5001", "ITEM-5001", 1),
        ("SHIPITEM-012", "SHP-5002", "ITEM-5002", 1),
    ]
    for siid, shid, oiid, qty in si_list:
        if not _exists(db, ShipmentItem, siid):
            db.add(ShipmentItem(id=siid, shipment_id=shid, order_item_id=oiid,
                                quantity=qty, created_at=now))

    # ── Rich Shipment Events ─────────────────────────────────────────────────
    events = [
        # SHP-9001 (delivered)
        ("EVT-1001", "SHP-9001", "picked_up", "พัสดุถูกรับจากผู้ส่ง",
         "กรุงเทพฯ — คลังสินค้า FashionHub", now - timedelta(days=7)),
        ("EVT-1002", "SHP-9001", "sorted", "คัดแยกพัสดุที่ศูนย์กระจายสินค้า",
         "กรุงเทพฯ — ศูนย์บางนา", now - timedelta(days=6)),
        ("EVT-1003", "SHP-9001", "in_transit", "อยู่ระหว่างขนส่ง",
         "ปทุมธานี — ศูนย์คลองหลวง", now - timedelta(days=5)),
        ("EVT-1004", "SHP-9001", "out_for_delivery", "กำลังนำส่ง",
         "นนทบุรี — สาขาแจ้งวัฒนะ", now - timedelta(days=4)),
        ("EVT-1005", "SHP-9001", "delivered", "จัดส่งสำเร็จ — ผู้รับเซ็นรับพัสดุแล้ว",
         "นนทบุรี", now - timedelta(days=4)),
        # SHP-9002 (in_transit — delayed)
        ("EVT-2001", "SHP-9002", "picked_up", "พัสดุถูกรับจากผู้ส่ง",
         "กรุงเทพฯ — คลังสินค้า FashionHub", now - timedelta(days=5)),
        ("EVT-2002", "SHP-9002", "sorted", "คัดแยกพัสดุ",
         "กรุงเทพฯ — ศูนย์ลาดกระบัง", now - timedelta(days=4)),
        ("EVT-2003", "SHP-9002", "in_transit", "อยู่ระหว่างขนส่ง",
         "ชลบุรี — ศูนย์กระจายสินค้า", now - timedelta(days=3)),
        # SHP-9003 (out_for_delivery)
        ("EVT-3001", "SHP-9003", "picked_up", "พัสดุถูกรับจากผู้ส่ง",
         "กรุงเทพฯ — คลังสินค้า GadgetMall", now - timedelta(days=3)),
        ("EVT-3002", "SHP-9003", "sorted", "คัดแยกพัสดุ",
         "กรุงเทพฯ — ศูนย์บางนา", now - timedelta(days=2)),
        ("EVT-3003", "SHP-9003", "in_transit", "อยู่ระหว่างขนส่ง",
         "ปทุมธานี", now - timedelta(days=1)),
        ("EVT-3004", "SHP-9003", "out_for_delivery", "กำลังนำส่ง",
         "นนทบุรี — สาขาแจ้งวัฒนะ", now - timedelta(hours=3)),
        # SHP-4001 (delivered)
        ("EVT-4001", "SHP-4001", "picked_up", "พัสดุถูกรับจากผู้ส่ง",
         "กรุงเทพฯ — FashionHub", now - timedelta(days=6)),
        ("EVT-4002", "SHP-4001", "delivered", "จัดส่งสำเร็จ",
         "นนทบุรี", now - timedelta(days=3)),
        # SHP-5001 (in_transit)
        ("EVT-5001", "SHP-5001", "picked_up", "พัสดุถูกรับจากผู้ส่ง",
         "กรุงเทพฯ — GadgetMall", now - timedelta(days=2)),
        ("EVT-5002", "SHP-5001", "sorted", "คัดแยกพัสดุ",
         "กรุงเทพฯ — ศูนย์สุวรรณภูมิ", now - timedelta(days=1)),
        ("EVT-5003", "SHP-5001", "in_transit", "อยู่ระหว่างขนส่ง",
         "เชียงใหม่ — ศูนย์กระจายสินค้า", now - timedelta(hours=6)),
        # SHP-5002 (delivered)
        ("EVT-5010", "SHP-5002", "picked_up", "พัสดุถูกรับจากผู้ส่ง",
         "กรุงเทพฯ — FashionHub", now - timedelta(days=10)),
        ("EVT-5011", "SHP-5002", "delivered", "จัดส่งสำเร็จ",
         "เชียงใหม่", now - timedelta(days=7)),
    ]
    for eid, shid, et, msg, loc, t in events:
        if not _exists(db, ShipmentEvent, eid):
            db.add(ShipmentEvent(id=eid, shipment_id=shid, event_type=et,
                                 event_message=msg, location=loc,
                                 event_time=t, created_at=t))

    # ── Additional Conversations ─────────────────────────────────────────────
    convs = [
        ("CONV-SEED-003", "CUST-001", "track_shipment", now - timedelta(days=5)),
        ("CONV-SEED-004", "CUST-001", "general_inquiry", now - timedelta(days=3)),
        ("CONV-SEED-005", "CUST-002", "track_shipment", now - timedelta(days=2)),
        ("CONV-SEED-006", "CUST-002", "refund_request", now - timedelta(days=1)),
    ]
    for cid, cust, intent, t in convs:
        if not _exists(db, Conversation, cid):
            db.add(Conversation(id=cid, customer_id=cust, channel="web_chat",
                                status="closed", latest_intent=intent,
                                created_at=t, updated_at=t))

    msgs = [
        ("MSG-SEED-003", "CONV-SEED-003", "customer", "CUST-001", "พัสดุไปถึงไหนแล้ว"),
        ("MSG-SEED-004", "CONV-SEED-004", "customer", "CUST-001", "อยากสอบถามเรื่องนโยบายคืนเงิน"),
        ("MSG-SEED-005", "CONV-SEED-005", "customer", "CUST-002", "ออเดอร์ SP-5001 ส่งถึงเมื่อไหร่"),
        ("MSG-SEED-006", "CONV-SEED-006", "customer", "CUST-002", "สินค้าไม่ตรงรุ่น ขอคืนเงิน"),
    ]
    for mid, cid, st, sid, content in msgs:
        if not _exists(db, Message, mid):
            db.add(Message(id=mid, conversation_id=cid, sender_type=st,
                           sender_id=sid, content=content,
                           metadata_json={"language": "th"}, created_at=now))

    # ── Additional Cases ─────────────────────────────────────────────────────
    new_cases = [
        ("CS-8001", "CUST-002", "SP-5001", "shipping_inquiry", "low", "resolved",
         "ลูกค้าสอบถามสถานะจัดส่ง — AI ตอบเรียบร้อย", now - timedelta(days=2)),
        ("CS-8002", "CUST-002", "SP-5002", "refund", "medium", "open",
         "ลูกค้าร้องเรียนสินค้าไม่ตรงรุ่น — รอตรวจสอบ", now - timedelta(days=1)),
    ]
    for cid, cust, oid, ct, pri, st, summary, t in new_cases:
        if not _exists(db, Case, cid):
            db.add(Case(id=cid, customer_id=cust, order_id=oid, case_type=ct,
                        priority=pri, status=st, ai_summary=summary,
                        assigned_role="admin", created_by="ai",
                        created_at=t, updated_at=t))

    # ── Additional Refund Request ────────────────────────────────────────────
    if not _exists(db, RefundRequest, "RF-8002"):
        db.add(RefundRequest(
            id="RF-8002", order_id="SP-5002", customer_id="CUST-002",
            case_id="CS-8002", reason="สินค้าส่งผิดรุ่น ได้เสื้อสีดำแทนสีขาว",
            requested_resolution="refund", eligibility_status="under_review",
            risk_score=30, ai_recommendation="แนะนำอนุมัติ — สินค้าส่งผิดรุ่น",
            status="pending", created_at=now - timedelta(days=1), updated_at=now,
        ))

    # ── Additional Approvals ─────────────────────────────────────────────────
    if not _exists(db, Approval, "APR-8002"):
        db.add(Approval(
            id="APR-8002", case_id="CS-8002", approval_type="refund",
            requested_action="คืนเงิน ฿1,290 — ออเดอร์ SP-5002 ส่งผิดรุ่น",
            amount=1290.00, currency="THB", risk_level="low",
            status="pending",
            ai_reason="Risk score 30 — สินค้าส่งผิดรุ่น ตรงตามนโยบายคืนเงิน",
            created_at=now - timedelta(days=1),
        ))

    # ── Additional Proactive Alerts ──────────────────────────────────────────
    if not _exists(db, ProactiveAlert, "ALT-2001"):
        db.add(ProactiveAlert(
            id="ALT-2001", order_id="SP-5001", shipment_id="SHP-5001",
            alert_type="shipment_delay", risk_score=42, status="open",
            recommended_action="ติดตามสถานะกับ Kerry Express",
            message_draft="สวัสดีค่ะ คุณ Somchai พัสดุ TH5001 อาจจัดส่งล่าช้า 1-2 วัน",
            case_id=None, created_at=now - timedelta(hours=6),
        ))

    # ── Fix existing trace statuses + add more traces ────────────────────────
    # Update TRACE-001 to success
    t1 = db.scalar(select(AgentTrace).where(AgentTrace.id == "TRACE-001"))
    if t1 and t1.status != "success":
        t1.status = "success"

    # Add agent traces with proper statuses for realistic eval
    traces = [
        ("TRACE-SEED-002", "CONV-SEED-003", None, "workflow_01_track_shipment",
         "track_shipment", 0.95, "success", False, now - timedelta(days=5)),
        ("TRACE-SEED-003", "CONV-SEED-004", None, "workflow_01_track_shipment",
         "general_inquiry", 0.88, "success", False, now - timedelta(days=3)),
        ("TRACE-SEED-004", "CONV-SEED-005", "CS-8001", "workflow_01_track_shipment",
         "track_shipment", 0.97, "success", False, now - timedelta(days=2)),
        ("TRACE-SEED-005", "CONV-SEED-006", "CS-8002", "workflow_02_refund",
         "refund_request", 0.91, "success", True, now - timedelta(days=1)),
        ("TRACE-SEED-006", None, "CS-7001", "workflow_03_proactive",
         "proactive_delay_alert", 0.99, "success", True, now - timedelta(hours=12)),
        # A failed trace for eval variety
        ("TRACE-SEED-007", "CONV-002", "CS-5521", "workflow_02_refund",
         "refund_request", 0.72, "failed", True, now - timedelta(days=4)),
    ]
    for tid, cid, caseid, wf, intent, conf, st, human, t in traces:
        if not _exists(db, AgentTrace, tid):
            db.add(AgentTrace(
                id=tid, conversation_id=cid, case_id=caseid,
                workflow_name=wf, intent=intent, confidence=conf,
                status=st, requires_human_approval=human,
                final_response=f"[{wf}] processed {intent}",
                state_snapshot={"enriched": True},
                started_at=t, ended_at=t + timedelta(seconds=45),
            ))

    # Add tool logs for new traces
    tool_logs = [
        ("LOG-SEED-010", "TRACE-SEED-002", "router_node", "detect_intent", "success", 28),
        ("LOG-SEED-011", "TRACE-SEED-002", "shipping_node", "get_shipments", "success", 42),
        ("LOG-SEED-012", "TRACE-SEED-002", "respond_node", "generate_response", "success", 35200),
        ("LOG-SEED-020", "TRACE-SEED-003", "router_node", "detect_intent", "success", 31),
        ("LOG-SEED-021", "TRACE-SEED-003", "respond_node", "generate_response", "success", 42100),
        ("LOG-SEED-030", "TRACE-SEED-004", "router_node", "detect_intent", "success", 25),
        ("LOG-SEED-031", "TRACE-SEED-004", "shipping_node", "get_shipments", "success", 38),
        ("LOG-SEED-032", "TRACE-SEED-004", "respond_node", "generate_response", "success", 38700),
        ("LOG-SEED-040", "TRACE-SEED-005", "router_node", "detect_intent", "success", 29),
        ("LOG-SEED-041", "TRACE-SEED-005", "refund_node", "validate_refund", "success", 55),
        ("LOG-SEED-042", "TRACE-SEED-005", "policy_node", "search_policy", "success", 120),
        ("LOG-SEED-043", "TRACE-SEED-005", "risk_node", "assess_risk", "success", 18),
        ("LOG-SEED-044", "TRACE-SEED-005", "respond_node", "generate_response", "success", 45300),
        ("LOG-SEED-050", "TRACE-SEED-006", "event_node", "ingest_event", "success", 12),
        ("LOG-SEED-051", "TRACE-SEED-006", "risk_node", "assess_risk", "success", 15),
        ("LOG-SEED-052", "TRACE-SEED-006", "alert_node", "send_alert", "success", 25),
        ("LOG-SEED-060", "TRACE-SEED-007", "router_node", "detect_intent", "success", 33),
        ("LOG-SEED-061", "TRACE-SEED-007", "refund_node", "validate_refund", "failed", 48),
    ]
    for lid, tid, agent, tool, st, lat in tool_logs:
        if not _exists(db, ToolLog, lid):
            db.add(ToolLog(id=lid, trace_id=tid, agent_name=agent,
                           tool_name=tool, status=st, latency_ms=lat,
                           input_payload={"enriched": True},
                           output_payload={"enriched": True},
                           created_at=now))

    db.flush()
    print("[enrich_seed] Done — additional data committed.")
