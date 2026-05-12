"""
bulk_demo_seed.py — เพิ่มข้อมูลจำนวนมากและหลากหลายเคสสำหรับ demo ทั้ง 3 Portal
"""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
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


def _exists(db: Session, model: type, id_val: str) -> bool:
    return db.scalar(select(model).where(model.id == id_val)) is not None


def bulk_seed(db: Session) -> None:
    now = datetime.utcnow()
    pw = get_password_hash("demo1234")

    # ══════════════════════════════════════════════════════════════
    # 1. CUSTOMERS (3 เพิ่มใหม่)
    # ══════════════════════════════════════════════════════════════
    new_users = [
        ("U-005", "manas_demo",   "manas@shopeasy.local",   "customer",    "active"),
        ("U-006", "porntip_demo", "porntip@shopeasy.local", "customer",    "active"),
        ("U-007", "thanakorn_demo","thanakorn@shopeasy.local","customer",   "active"),
    ]
    for uid, name, email, role, status in new_users:
        if not _exists(db, User, uid):
            db.add(User(id=uid, name=name, email=email, role=role, status=status,
                        hashed_password=pw, created_at=now, updated_at=now))

    new_customers = [
        ("CUST-003", "U-005", "มนัส ทองดี",    "manas@example.com",    "090-333-3333", "silver"),
        ("CUST-004", "U-006", "พรทิพย์ ศิริพร","porntip@example.com",  "085-444-4444", "platinum"),
        ("CUST-005", "U-007", "ธนกร วงษ์สุวรรณ","thanakorn@example.com","092-555-5555", "gold"),
    ]
    for cid, uid, name, email, phone, tier in new_customers:
        if not _exists(db, Customer, cid):
            db.add(Customer(id=cid, user_id=uid, name=name, email=email,
                            phone=phone, tier=tier, preferred_language="th",
                            created_at=now, updated_at=now))

    # ══════════════════════════════════════════════════════════════
    # 2. SELLERS (3 เพิ่มใหม่)
    # ══════════════════════════════════════════════════════════════
    new_sellers = [
        ("SELL-004", "ElecHub",      4.7, "standard"),
        ("SELL-005", "SportZone",    4.5, "standard"),
        ("SELL-006", "BeautyMart",   4.8, "premium"),
    ]
    for sid, name, rating, sla in new_sellers:
        if not _exists(db, Seller, sid):
            db.add(Seller(id=sid, name=name, sla_level=sla, rating=rating,
                          status="active", created_at=now, updated_at=now))

    db.flush()

    # ══════════════════════════════════════════════════════════════
    # 3. ORDERS — 18 รายการ หลากหลายสถานะ
    # ══════════════════════════════════════════════════════════════
    # fmt: (id, cust_id, seller_id, order_status, payment_status, amount, days_ago, dd_offset)
    orders = [
        # CUST-003 มนัส
        ("SP-3001","CUST-003","SELL-004","shipped",   "paid",   5990.00, 3,  5),
        ("SP-3002","CUST-003","SELL-006","processing","paid",   890.00,  1,  4),
        ("SP-3003","CUST-003","SELL-005","cancelled", "refunded",1290.00,14,-1),
        ("SP-3004","CUST-003","SELL-001","completed", "paid",   450.00,  21,-10),
        # CUST-004 พรทิพย์ (platinum)
        ("SP-4001","CUST-004","SELL-006","shipped",   "paid",  12500.00, 2,  4),
        ("SP-4002","CUST-004","SELL-002","shipped",   "paid",   3600.00, 5,  3),
        ("SP-4003","CUST-004","SELL-004","completed", "paid",   7200.00, 30,-15),
        ("SP-4004","CUST-004","SELL-001","processing","paid",   2100.00, 0,   6),
        ("SP-4005","CUST-004","SELL-003","cancelled", "refunded",680.00,  7, -3),
        # CUST-005 ธนกร
        ("SP-5003","CUST-005","SELL-005","shipped",   "paid",   4200.00, 4,  4),
        ("SP-5004","CUST-005","SELL-002","completed", "paid",   9800.00, 20,-5),
        ("SP-5005","CUST-005","SELL-004","processing","paid",   1500.00, 1,   7),
        ("SP-5006","CUST-005","SELL-006","shipped",   "paid",   3300.00, 3,  3),
        ("SP-5007","CUST-005","SELL-001","cancelled", "refunded",2200.00,10, -2),
        # เพิ่มให้ CUST-001 นริศรา
        ("SP-1025","CUST-001","SELL-005","shipped",   "paid",   1800.00, 6,  4),
        ("SP-1026","CUST-001","SELL-004","completed", "paid",   3400.00, 25,-10),
        # เพิ่มให้ CUST-002 สมชาย
        ("SP-5008","CUST-002","SELL-005","processing","paid",   6500.00, 0,   8),
        ("SP-5009","CUST-002","SELL-006","completed", "paid",   980.00,  18,-7),
    ]
    for oid, cid, sid, os, ps, amt, dago, dd_off in orders:
        if not _exists(db, Order, oid):
            cat = now - timedelta(days=dago)
            dd  = (now + timedelta(days=dd_off)).date() if dd_off >= 0 else (now - timedelta(days=-dd_off)).date()
            db.add(Order(id=oid, customer_id=cid, seller_id=sid, order_status=os,
                         payment_status=ps, total_amount=amt, currency="THB",
                         promised_delivery_date=dd, created_at=cat, updated_at=now))

    # ── Order Items ─────────────────────────────────────────────
    items = [
        ("ITM-B001","SP-3001","สมาร์ทโฟน Galaxy A55",   "ELEC-GA55",  1, 5990.00),
        ("ITM-B002","SP-3002","ลิปสติก Matte Collection","BMT-LIP-012",2,  445.00),
        ("ITM-B003","SP-3003","รองเท้าวิ่ง Nike",        "SPZ-SHOE-NK", 1, 1290.00),
        ("ITM-B004","SP-3004","เสื้อยืด Plain",          "FHB-PT-001",  1,  450.00),
        ("ITM-B005","SP-4001","ครีมบำรุงผิว Set 5 ชิ้น", "BMT-CREAM-5", 1,12500.00),
        ("ITM-B006","SP-4002","หูฟัง TWS Pro",           "ELEC-TWS",    1, 3600.00),
        ("ITM-B007","SP-4003","แล็ปท็อป Lenovo IdeaPad", "ELEC-LNV",    1, 7200.00),
        ("ITM-B008","SP-4004","เสื้อโปโล Slim Fit",      "FHB-POLO-02", 3,  700.00),
        ("ITM-B009","SP-4005","หมวกแก๊ป Sport",          "SPZ-CAP-01",  1,  680.00),
        ("ITM-B010","SP-5003","ลู่วิ่งไฟฟ้า Mini",        "SPZ-TRML-01", 1, 4200.00),
        ("ITM-B011","SP-5004","กล้อง Mirrorless Sony",    "ELEC-SNY-M",  1, 9800.00),
        ("ITM-B012","SP-5005","หลอดไฟ LED Smart",         "ELEC-LED-S",  3,  500.00),
        ("ITM-B013","SP-5006","เซรั่มหน้าใส SPF50",       "BMT-SRM-01",  2, 1650.00),
        ("ITM-B014","SP-5007","กางเกงวิ่ง Dry Fit",       "FHB-RUN-02",  1, 2200.00),
        ("ITM-B015","SP-1025","ถุงเท้ากีฬา 3 คู่",        "SPZ-SOC-3",   1,  600.00),
        ("ITM-B016","SP-1025","สายรัดข้อมือ Sport",       "SPZ-BAND-01", 2,  600.00),
        ("ITM-B017","SP-1026","ลำโพง Bluetooth JBL",      "ELEC-JBL-G3", 1, 3400.00),
        ("ITM-B018","SP-5008","ชุดออกกำลังกายหญิง",       "SPZ-SET-F01", 1, 2200.00),
        ("ITM-B019","SP-5008","สายกระโดดเชือก Smart",     "SPZ-JUMP-1",  1,  890.00),
        ("ITM-B020","SP-5009","แป้งพัฟแต่งหน้า",          "BMT-PDR-02",  1,  980.00),
    ]
    for iid, oid, pn, sku, qty, price in items:
        if not _exists(db, OrderItem, iid):
            db.add(OrderItem(id=iid, order_id=oid, product_name=pn, sku=sku,
                             quantity=qty, unit_price=price, created_at=now))

    # ══════════════════════════════════════════════════════════════
    # 4. SHIPMENTS + EVENTS — ครอบคลุมทุกสถานะ
    # ══════════════════════════════════════════════════════════════
    # (ship_id, order_id, carrier, tracking, status, risk, eta_offset, last_update_offset_h)
    shipments = [
        ("SHP-B001","SP-3001","Kerry Express",  "KRY-B001","in_transit",     25, 5,  -8),
        ("SHP-B002","SP-4001","Flash Express",  "FLE-B002","in_transit",     18, 4, -12),
        ("SHP-B003","SP-4002","J&T Express",    "JNT-B003","out_for_delivery",5, 0,  -2),
        ("SHP-B004","SP-5003","Kerry Express",  "KRY-B004","in_transit",     62, 4,  -6),  # high risk
        ("SHP-B005","SP-5006","Flash Express",  "FLE-B005","out_for_delivery",8, 0,  -1),
        ("SHP-B006","SP-1025","J&T Express",    "JNT-B006","in_transit",     15, 4,  -5),
        ("SHP-B007","SP-4003","Kerry Express",  "KRY-B007","delivered",       0,-20, -500),
        ("SHP-B008","SP-5004","Flash Express",  "FLE-B008","delivered",       0,-15, -360),
        ("SHP-B009","SP-1026","J&T Express",    "JNT-B009","delivered",       0,-10, -240),
        ("SHP-B010","SP-5009","Kerry Express",  "KRY-B010","delivered",       0,-18, -432),
    ]
    for sid, oid, car, trk, st, risk, eta_off, lu_h in shipments:
        if not _exists(db, Shipment, sid):
            eta = (now + timedelta(days=eta_off)).date() if eta_off >= 0 else (now - timedelta(days=-eta_off)).date()
            lu  = now + timedelta(hours=lu_h)
            db.add(Shipment(id=sid, order_id=oid, carrier=car, tracking_no=trk,
                            shipment_status=st, eta=eta, last_update=lu,
                            delay_risk_score=risk,
                            created_at=now - timedelta(days=3), updated_at=now))

    si_list = [
        ("SITM-B01","SHP-B001","ITM-B001",1),
        ("SITM-B02","SHP-B002","ITM-B005",1),
        ("SITM-B03","SHP-B003","ITM-B006",1),
        ("SITM-B04","SHP-B004","ITM-B010",1),
        ("SITM-B05","SHP-B005","ITM-B013",2),
        ("SITM-B06","SHP-B006","ITM-B015",1),
        ("SITM-B07","SHP-B007","ITM-B007",1),
        ("SITM-B08","SHP-B008","ITM-B011",1),
        ("SITM-B09","SHP-B009","ITM-B017",1),
        ("SITM-B10","SHP-B010","ITM-B020",1),
    ]
    for siid, shid, oiid, qty in si_list:
        if not _exists(db, ShipmentItem, siid):
            db.add(ShipmentItem(id=siid, shipment_id=shid, order_item_id=oiid,
                                quantity=qty, created_at=now))

    # Shipment Events
    events = [
        # SHP-B001 — in_transit Kerry (CUST-003, SP-3001 Galaxy)
        ("EVT-B001","SHP-B001","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง ElecHub",          now-timedelta(days=3)),
        ("EVT-B002","SHP-B001","sorted",      "คัดแยกพัสดุที่ศูนย์กระจายสินค้า",   "กรุงเทพฯ — ศูนย์บางนา",            now-timedelta(days=2)),
        ("EVT-B003","SHP-B001","in_transit",  "อยู่ระหว่างขนส่ง",                   "อยุธยา — ศูนย์กระจาย",             now-timedelta(hours=8)),
        # SHP-B002 — in_transit Flash (CUST-004, SP-4001 ครีมบำรุง)
        ("EVT-B010","SHP-B002","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง BeautyMart",       now-timedelta(days=2)),
        ("EVT-B011","SHP-B002","sorted",      "คัดแยกพัสดุ",                        "กรุงเทพฯ — ศูนย์ลาดกระบัง",        now-timedelta(days=1)),
        ("EVT-B012","SHP-B002","in_transit",  "อยู่ระหว่างขนส่ง",                   "สมุทรปราการ — ศูนย์บางพลี",        now-timedelta(hours=12)),
        # SHP-B003 — out_for_delivery J&T (CUST-004, SP-4002 หูฟัง)
        ("EVT-B020","SHP-B003","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง ElecHub",          now-timedelta(days=5)),
        ("EVT-B021","SHP-B003","sorted",      "คัดแยกพัสดุ",                        "กรุงเทพฯ — ศูนย์บางนา",            now-timedelta(days=4)),
        ("EVT-B022","SHP-B003","in_transit",  "อยู่ระหว่างขนส่ง",                   "นนทบุรี — ศูนย์ปากเกร็ด",          now-timedelta(days=1)),
        ("EVT-B023","SHP-B003","out_for_delivery","กำลังนำส่ง",                      "นนทบุรี — ปากเกร็ด สาขา 3",        now-timedelta(hours=2)),
        # SHP-B004 — in_transit Kerry RISK HIGH (CUST-005, SP-5003 ลู่วิ่ง)
        ("EVT-B030","SHP-B004","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง SportZone",        now-timedelta(days=4)),
        ("EVT-B031","SHP-B004","sorted",      "คัดแยกพัสดุ",                        "กรุงเทพฯ — ศูนย์สุวรรณภูมิ",       now-timedelta(days=3)),
        ("EVT-B032","SHP-B004","in_transit",  "อยู่ระหว่างขนส่ง — พบปัญหาถนนปิด","เชียงใหม่ — ระหว่างทาง",           now-timedelta(hours=6)),
        # SHP-B005 — out_for_delivery Flash (CUST-005, SP-5006 เซรั่ม)
        ("EVT-B040","SHP-B005","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง BeautyMart",       now-timedelta(days=3)),
        ("EVT-B041","SHP-B005","in_transit",  "อยู่ระหว่างขนส่ง",                   "กรุงเทพฯ — ศูนย์ลาดพร้าว",         now-timedelta(days=1)),
        ("EVT-B042","SHP-B005","out_for_delivery","กำลังนำส่ง",                      "ปทุมธานี — ธัญบุรี สาขา 2",        now-timedelta(hours=1)),
        # SHP-B006 — in_transit J&T (CUST-001, SP-1025 ถุงเท้า)
        ("EVT-B050","SHP-B006","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง SportZone",        now-timedelta(days=5)),
        ("EVT-B051","SHP-B006","sorted",      "คัดแยกพัสดุ",                        "กรุงเทพฯ — ศูนย์บางนา",            now-timedelta(days=4)),
        ("EVT-B052","SHP-B006","in_transit",  "อยู่ระหว่างขนส่ง",                   "สมุทรสาคร — ศูนย์กระจาย",          now-timedelta(hours=5)),
        # SHP-B007 — delivered Kerry (CUST-004, SP-4003 แล็ปท็อป)
        ("EVT-B060","SHP-B007","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง ElecHub",          now-timedelta(days=30)),
        ("EVT-B061","SHP-B007","in_transit",  "อยู่ระหว่างขนส่ง",                   "กรุงเทพฯ — ศูนย์บางรัก",           now-timedelta(days=28)),
        ("EVT-B062","SHP-B007","delivered",   "จัดส่งสำเร็จ — เซ็นรับแล้ว",        "กรุงเทพฯ — สาทร",                  now-timedelta(days=20)),
        # SHP-B008 — delivered Flash (CUST-005, SP-5004 กล้อง)
        ("EVT-B070","SHP-B008","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง ElecHub",          now-timedelta(days=20)),
        ("EVT-B071","SHP-B008","in_transit",  "อยู่ระหว่างขนส่ง",                   "ชลบุรี — ศูนย์กระจาย",             now-timedelta(days=18)),
        ("EVT-B072","SHP-B008","out_for_delivery","กำลังนำส่ง",                      "ชลบุรี — พัทยา",                   now-timedelta(days=15)),
        ("EVT-B073","SHP-B008","delivered",   "จัดส่งสำเร็จ — ผู้รับเซ็น",          "ชลบุรี",                            now-timedelta(days=15)),
        # SHP-B009 — delivered J&T (CUST-001, SP-1026 ลำโพง)
        ("EVT-B080","SHP-B009","picked_up",   "พัสดุถูกรับจากผู้ส่ง",                "กรุงเทพฯ — คลัง ElecHub",          now-timedelta(days=25)),
        ("EVT-B081","SHP-B009","delivered",   "จัดส่งสำเร็จ",                       "กรุงเทพฯ",                          now-timedelta(days=10)),
    ]
    for eid, shid, et, msg, loc, t in events:
        if not _exists(db, ShipmentEvent, eid):
            db.add(ShipmentEvent(id=eid, shipment_id=shid, event_type=et,
                                 event_message=msg, location=loc,
                                 event_time=t, created_at=t))

    # ══════════════════════════════════════════════════════════════
    # 5. CONVERSATIONS (diverse intents + channels)
    # ══════════════════════════════════════════════════════════════
    convs = [
        # CUST-003
        ("CONV-B001","CUST-003","track_shipment",    "closed", now-timedelta(days=3)),
        ("CONV-B002","CUST-003","cancellation",      "closed", now-timedelta(days=14)),
        ("CONV-B003","CUST-003","general_inquiry",   "open",   now-timedelta(hours=2)),
        # CUST-004
        ("CONV-B004","CUST-004","track_shipment",    "open",   now-timedelta(hours=5)),
        ("CONV-B005","CUST-004","refund_request",    "closed", now-timedelta(days=7)),
        ("CONV-B006","CUST-004","product_complaint", "open",   now-timedelta(hours=1)),
        # CUST-005
        ("CONV-B007","CUST-005","track_shipment",    "open",   now-timedelta(days=1)),
        ("CONV-B008","CUST-005","refund_request",    "closed", now-timedelta(days=10)),
        ("CONV-B009","CUST-005","general_inquiry",   "closed", now-timedelta(days=20)),
        # CUST-001 (เพิ่มเติม)
        ("CONV-B010","CUST-001","track_shipment",    "closed", now-timedelta(days=6)),
        ("CONV-B011","CUST-001","product_complaint", "open",   now-timedelta(hours=3)),
        # CUST-002 (เพิ่มเติม)
        ("CONV-B012","CUST-002","track_shipment",    "open",   now-timedelta(hours=4)),
        ("CONV-B013","CUST-002","cancellation",      "closed", now-timedelta(days=3)),
    ]
    msgs_data = [
        ("MSG-B001","CONV-B001","customer","CUST-003","พัสดุ KRY-B001 ไปถึงไหนแล้วครับ"),
        ("MSG-B002","CONV-B002","customer","CUST-003","ขอยกเลิกออเดอร์ SP-3003 ครับ"),
        ("MSG-B003","CONV-B003","customer","CUST-003","สอบถามนโยบายการรับประกันสินค้า"),
        ("MSG-B004","CONV-B004","customer","CUST-004","ติดตาม SP-4001 ครีมบำรุงครับ"),
        ("MSG-B005","CONV-B005","customer","CUST-004","สินค้าหมดอายุ ขอคืนเงิน"),
        ("MSG-B006","CONV-B006","customer","CUST-004","ลำโพง SP-4002 มีเสียงแตก"),
        ("MSG-B007","CONV-B007","customer","CUST-005","ลู่วิ่งยังไม่ถึงเลย ช้ามาก"),
        ("MSG-B008","CONV-B008","customer","CUST-005","กล้อง SP-5004 ได้รับแล้วแต่ฟังก์ชันผิดรุ่น"),
        ("MSG-B009","CONV-B009","customer","CUST-005","สอบถามเรื่องออเดอร์ผ่านมา 3 สัปดาห์"),
        ("MSG-B010","CONV-B010","customer","CUST-001","ถุงเท้า SP-1025 จัดส่งถึงไหน"),
        ("MSG-B011","CONV-B011","customer","CUST-001","ลำโพง SP-1026 เสียงไม่ดีอย่างที่โฆษณา"),
        ("MSG-B012","CONV-B012","customer","CUST-002","ออเดอร์ SP-5008 ส่งเมื่อไหร่"),
        ("MSG-B013","CONV-B013","customer","CUST-002","ขอยกเลิก SP-5009 ได้ไหม"),
    ]
    for cid, cust, intent, status, t in convs:
        if not _exists(db, Conversation, cid):
            db.add(Conversation(id=cid, customer_id=cust, channel="web_chat",
                                status=status, latest_intent=intent,
                                created_at=t, updated_at=t))
    for mid, cid, st, sid, content in msgs_data:
        if not _exists(db, Message, mid):
            db.add(Message(id=mid, conversation_id=cid, sender_type=st,
                           sender_id=sid, content=content,
                           metadata_json={"language": "th"}, created_at=now))

    # ══════════════════════════════════════════════════════════════
    # 6. CASES — 12 รายการ หลากหลายประเภทและสถานะ
    # ══════════════════════════════════════════════════════════════
    # (id, cust, order, type, priority, status, summary, dago)
    cases = [
        # refund cases
        ("CS-B001","CUST-004","SP-4005","refund",           "low",    "resolved",
         "ลูกค้า cancel SP-4005 หมวก — คืนเงินอัตโนมัติ","CUST-004",7),
        ("CS-B002","CUST-005","SP-5004","refund",           "high",   "open",
         "กล้อง Sony ได้รับสินค้าผิดรุ่น — รอตรวจสอบหลักฐาน","admin",10),
        ("CS-B003","CUST-003","SP-3003","cancellation",     "medium", "resolved",
         "ลูกค้ายกเลิกก่อนจัดส่ง — ดำเนินการคืนเงินแล้ว","CUST-003",14),
        ("CS-B004","CUST-004","SP-4001","product_complaint","medium", "open",
         "ครีมบำรุงหมดอายุ — รอเอกสารยืนยันจากลูกค้า","admin",5),
        ("CS-B005","CUST-004","SP-4002","product_complaint","high",   "pending_review",
         "หูฟัง TWS เสียงแตก — AI แนะนำเปลี่ยนสินค้า","admin",5),
        ("CS-B006","CUST-005","SP-5003","shipping_delay",   "high",   "open",
         "ลู่วิ่งล่าช้าเกิน ETA — risk score 62 สูง","ai",4),
        ("CS-B007","CUST-001","SP-1026","product_complaint","low",    "open",
         "ลำโพง JBL เสียงไม่ตรงสเปก — ลูกค้าร้องเรียน","admin",3),
        ("CS-B008","CUST-005","SP-5007","cancellation",     "medium", "resolved",
         "ลูกค้ายกเลิก SP-5007 กางเกงวิ่ง — คืนเงินแล้ว","admin",10),
        ("CS-B009","CUST-003","SP-3002","general_inquiry",  "low",    "resolved",
         "สอบถามนโยบายการรับประกัน — AI ตอบครบถ้วน","ai",1),
        ("CS-B010","CUST-002","SP-5008","shipping_inquiry", "low",    "open",
         "สอบถามสถานะจัดส่ง SP-5008 — รอการยืนยัน","admin",0),
        ("CS-B011","CUST-004","SP-4003","general_inquiry",  "low",    "resolved",
         "สอบถามใบเสร็จรับเงิน — ส่งอีเมลให้แล้ว","ai",25),
        ("CS-B012","CUST-001","SP-1025","shipping_inquiry", "low",    "resolved",
         "ติดตามพัสดุ SP-1025 — อัพเดทสถานะให้ครบแล้ว","ai",6),
    ]
    for cid, cust, oid, ct, pri, st, summary, by, dago in cases:
        if not _exists(db, Case, cid):
            t = now - timedelta(days=dago)
            db.add(Case(id=cid, customer_id=cust, order_id=oid, case_type=ct,
                        priority=pri, status=st, ai_summary=summary,
                        assigned_role="admin", created_by=by,
                        created_at=t, updated_at=t))

    # ══════════════════════════════════════════════════════════════
    # 7. REFUND REQUESTS — 7 รายการ
    # ══════════════════════════════════════════════════════════════
    refunds = [
        ("RF-B001","SP-5004","CUST-005","CS-B002",
         "ได้รับกล้องผิดรุ่น Sony A7IV แทน A7III","refund","under_review",65,
         "risk สูง — ต้องเปรียบเทียบสินค้าที่ส่งไป","pending",10),
        ("RF-B002","SP-4001","CUST-004","CS-B004",
         "ครีมบำรุงหมดอายุ 3 เดือนก่อนรับ","refund","eligible",20,
         "ยืนยันวันหมดอายุจากรูปที่ลูกค้าส่งมา — แนะนำอนุมัติ","pending",5),
        ("RF-B003","SP-4002","CUST-004","CS-B005",
         "หูฟัง TWS ขวาเสียงแตก ใช้ไปเพียง 2 วัน","exchange","eligible",35,
         "ในรอบรับประกัน — แนะนำเปลี่ยนสินค้า","pending",5),
        ("RF-B004","SP-3003","CUST-003","CS-B003",
         "ยกเลิกออเดอร์ก่อนจัดส่ง","refund","eligible",0,
         "ยกเลิกก่อนจัดส่ง — อนุมัติอัตโนมัติ","approved",14),
        ("RF-B005","SP-4005","CUST-004","CS-B001",
         "ยกเลิกออเดอร์ก่อนจัดส่ง","refund","eligible",0,
         "ยกเลิกก่อนจัดส่ง — อนุมัติอัตโนมัติ","approved",7),
        ("RF-B006","SP-5007","CUST-005","CS-B008",
         "ยกเลิกออเดอร์ก่อนจัดส่ง","refund","eligible",0,
         "ยกเลิกก่อนจัดส่ง — อนุมัติอัตโนมัติ","approved",10),
        ("RF-B007","SP-1026","CUST-001","CS-B007",
         "ลำโพงเสียงต่ำกว่าที่โฆษณาไว้ ทดสอบในร้านต่างกันมาก","refund","under_review",40,
         "กรณีไม่ตรงสเปก — ต้องตรวจสอบสเปคที่โฆษณา","pending",3),
    ]
    for rid, oid, cust, csid, reason, res_type, elig, risk, ai_rec, st, dago in refunds:
        if not _exists(db, RefundRequest, rid):
            t = now - timedelta(days=dago)
            db.add(RefundRequest(id=rid, order_id=oid, customer_id=cust, case_id=csid,
                                 reason=reason, requested_resolution=res_type,
                                 eligibility_status=elig, risk_score=risk,
                                 ai_recommendation=ai_rec, status=st,
                                 created_at=t, updated_at=t))

    # ══════════════════════════════════════════════════════════════
    # 8. APPROVALS — 10 รายการ (pending/approved/rejected)
    # ══════════════════════════════════════════════════════════════
    approvals = [
        # pending — รอ admin ตัดสินใจ
        ("APR-B001","CS-B002","refund",
         "คืนเงิน ฿9,800 — SP-5004 กล้องผิดรุ่น",
         9800,"THB","high","pending",
         "Risk 65 — กรณีสินค้าผิดรุ่นมูลค่าสูง ต้องตรวจสอบ",10),
        ("APR-B002","CS-B004","refund",
         "คืนเงิน ฿12,500 — SP-4001 ครีมหมดอายุ",
         12500,"THB","medium","pending",
         "Risk 20 — มีหลักฐานวันหมดอายุ แนะนำอนุมัติ",5),
        ("APR-B003","CS-B005","exchange",
         "เปลี่ยนสินค้า — SP-4002 หูฟัง TWS เสียงแตก",
         3600,"THB","medium","pending",
         "Risk 35 — ในรอบประกัน แนะนำเปลี่ยนสินค้า",5),
        ("APR-B004","CS-B006","compensation",
         "ชดเชยค่าจัดส่ง ฿150 — SP-5003 ลู่วิ่งล่าช้า",
         150,"THB","low","pending",
         "Risk 62 — ล่าช้าเกิน 3 วัน ตามนโยบายชดเชย",4),
        ("APR-B005","CS-B007","refund",
         "คืนเงิน ฿3,400 — SP-1026 ลำโพงไม่ตรงสเปก",
         3400,"THB","medium","pending",
         "Risk 40 — ต้องพิสูจน์สเปคสินค้า",3),
        # approved — อนุมัติแล้ว
        ("APR-B006","CS-B001","refund",
         "คืนเงิน ฿680 — SP-4005 ยกเลิกก่อนส่ง",
         680,"THB","low","approved",
         "ยกเลิกก่อนจัดส่ง — อนุมัติตามนโยบาย",7),
        ("APR-B007","CS-B003","refund",
         "คืนเงิน ฿1,290 — SP-3003 ยกเลิกก่อนส่ง",
         1290,"THB","low","approved",
         "ยกเลิกก่อนจัดส่ง — อนุมัติตามนโยบาย",14),
        ("APR-B008","CS-B008","refund",
         "คืนเงิน ฿2,200 — SP-5007 ยกเลิกก่อนส่ง",
         2200,"THB","low","approved",
         "ยกเลิกก่อนจัดส่ง — อนุมัติตามนโยบาย",10),
        # rejected — ปฏิเสธ
        ("APR-B009","CS-B007","refund",
         "คืนเงิน ฿3,400 — SP-1026 ลูกค้าร้องเรียนสเปค",
         3400,"THB","low","rejected",
         "ตรวจสอบแล้วสเปคตรงตามที่โฆษณา — ปฏิเสธคำร้อง",3),
    ]
    for aid, csid, atype, action, amt, cur, risk, st, reason, dago in approvals:
        if not _exists(db, Approval, aid):
            t = now - timedelta(days=dago)
            db.add(Approval(id=aid, case_id=csid, approval_type=atype,
                            requested_action=action, amount=amt, currency=cur,
                            risk_level=risk, status=st, ai_reason=reason,
                            created_at=t))

    # ══════════════════════════════════════════════════════════════
    # 9. PROACTIVE ALERTS — 6 รายการ
    # ══════════════════════════════════════════════════════════════
    alerts = [
        # open alerts
        ("ALT-B001","SP-5003","SHP-B004","shipment_delay",62,"open",
         "ติดตาม Kerry Express — ล่าช้าจากการปิดถนน",
         "สวัสดีครับ คุณธนกร พัสดุ KRY-B004 (ลู่วิ่ง) ล่าช้ากว่ากำหนด 2 วัน ขอโทษในความไม่สะดวกครับ",
         "CS-B006", now-timedelta(days=4)),
        ("ALT-B002","SP-4002","SHP-B003","out_for_delivery_failed",10,"open",
         "ส่งไม่ได้ครั้งแรก — นัดหมายจัดส่งรอบสอง",
         "สวัสดีค่ะ คุณพรทิพย์ เราพยายามจัดส่งหูฟัง TWS แล้วแต่ไม่มีคนรับ",
         None, now-timedelta(hours=3)),
        ("ALT-B003","SP-3001","SHP-B001","shipment_delay",25,"open",
         "ล่าช้าเล็กน้อย — อัพเดทสถานะให้ลูกค้า",
         "สวัสดีครับ คุณมนัส พัสดุ KRY-B001 (Galaxy A55) มีล่าช้าเล็กน้อย",
         None, now-timedelta(hours=8)),
        # resolved alerts
        ("ALT-B004","SP-4003","SHP-B007","shipment_delay",0,"resolved",
         "จัดส่งสำเร็จแล้ว",
         "จัดส่งสำเร็จ — ปิด alert",
         None, now-timedelta(days=25)),
        ("ALT-B005","SP-5004","SHP-B008","shipment_delay",0,"resolved",
         "จัดส่งสำเร็จแล้ว",
         "จัดส่งสำเร็จ — ปิด alert",
         None, now-timedelta(days=20)),
        ("ALT-B006","SP-1025","SHP-B006","shipment_delay",15,"open",
         "ล่าช้าจากสภาพอากาศ — แจ้งลูกค้า",
         "สวัสดีค่ะ คุณนริศรา พัสดุ JNT-B006 (ถุงเท้า) ล่าช้าเล็กน้อยจากฝนตก",
         None, now-timedelta(hours=5)),
    ]
    for aid, oid, shid, atype, risk, st, rec, draft, csid, t in alerts:
        if not _exists(db, ProactiveAlert, aid):
            db.add(ProactiveAlert(id=aid, order_id=oid, shipment_id=shid,
                                  alert_type=atype, risk_score=risk, status=st,
                                  recommended_action=rec, message_draft=draft,
                                  case_id=csid, created_at=t))

    # ══════════════════════════════════════════════════════════════
    # 10. AGENT TRACES — หลากหลาย intent + status สำหรับ AI Portal
    # ══════════════════════════════════════════════════════════════
    traces = [
        # track_shipment
        ("TR-B001","CONV-B001",None,"workflow_01_track_shipment","track_shipment",0.96,"success",False,now-timedelta(days=3),40),
        ("TR-B002","CONV-B004",None,"workflow_01_track_shipment","track_shipment",0.98,"success",False,now-timedelta(hours=5),35),
        ("TR-B003","CONV-B007","CS-B006","workflow_01_track_shipment","track_shipment",0.94,"success",True, now-timedelta(days=1),55),
        ("TR-B004","CONV-B010",None,"workflow_01_track_shipment","track_shipment",0.97,"success",False,now-timedelta(days=6),38),
        ("TR-B005","CONV-B012",None,"workflow_01_track_shipment","track_shipment",0.95,"success",False,now-timedelta(hours=4),42),
        # refund_request
        ("TR-B006","CONV-B005","CS-B001","workflow_02_refund","refund_request",0.89,"success",True, now-timedelta(days=7),52),
        ("TR-B007","CONV-B008","CS-B002","workflow_02_refund","refund_request",0.82,"success",True, now-timedelta(days=10),61),
        ("TR-B008","CONV-B011","CS-B007","workflow_02_refund","refund_request",0.75,"failed", True, now-timedelta(hours=3),48),
        # product_complaint
        ("TR-B009","CONV-B006","CS-B005","workflow_02_refund","product_complaint",0.91,"success",True, now-timedelta(hours=1),58),
        # cancellation
        ("TR-B010","CONV-B002","CS-B003","workflow_02_refund","cancellation",0.99,"success",False,now-timedelta(days=14),30),
        ("TR-B011","CONV-B013","CS-B008","workflow_02_refund","cancellation",0.99,"success",False,now-timedelta(days=3),28),
        # general_inquiry
        ("TR-B012","CONV-B003",None,"workflow_01_track_shipment","general_inquiry",0.87,"success",False,now-timedelta(hours=2),44),
        ("TR-B013","CONV-B009",None,"workflow_01_track_shipment","general_inquiry",0.90,"success",False,now-timedelta(days=20),39),
        # proactive_delay_alert
        ("TR-B014",None,"CS-B006","workflow_03_proactive","proactive_delay_alert",0.99,"success",True, now-timedelta(days=4),22),
        ("TR-B015",None,None,"workflow_03_proactive","proactive_delay_alert",0.98,"success",True, now-timedelta(hours=8),18),
        ("TR-B016",None,None,"workflow_03_proactive","proactive_delay_alert",0.97,"success",True, now-timedelta(hours=5),20),
    ]
    for tid, cid, csid, wf, intent, conf, st, human, t, lat in traces:
        if not _exists(db, AgentTrace, tid):
            db.add(AgentTrace(
                id=tid, conversation_id=cid, case_id=csid,
                workflow_name=wf, intent=intent, confidence=conf,
                status=st, requires_human_approval=human,
                final_response=f"[{wf}] {intent} processed",
                state_snapshot={"bulk_demo": True},
                started_at=t, ended_at=t+timedelta(seconds=lat),
            ))

    # ── Tool Logs สำหรับ traces ใหม่ ─────────────────────────────
    tlogs = [
        ("TL-B001","TR-B001","router_node","detect_intent","success",29),
        ("TL-B002","TR-B001","shipping_node","get_shipments","success",45),
        ("TL-B003","TR-B001","respond_node","generate_response","success",39100),
        ("TL-B004","TR-B002","router_node","detect_intent","success",26),
        ("TL-B005","TR-B002","shipping_node","get_shipments","success",38),
        ("TL-B006","TR-B002","respond_node","generate_response","success",34200),
        ("TL-B007","TR-B006","router_node","detect_intent","success",31),
        ("TL-B008","TR-B006","refund_node","validate_refund","success",60),
        ("TL-B009","TR-B006","policy_node","search_policy","success",110),
        ("TL-B010","TR-B006","risk_node","assess_risk","success",19),
        ("TL-B011","TR-B006","respond_node","generate_response","success",47800),
        ("TL-B012","TR-B007","router_node","detect_intent","success",33),
        ("TL-B013","TR-B007","refund_node","validate_refund","success",71),
        ("TL-B014","TR-B007","policy_node","search_policy","success",128),
        ("TL-B015","TR-B007","risk_node","assess_risk","success",22),
        ("TL-B016","TR-B007","respond_node","generate_response","success",60500),
        ("TL-B017","TR-B008","router_node","detect_intent","success",35),
        ("TL-B018","TR-B008","refund_node","validate_refund","failed",52),
        ("TL-B019","TR-B010","router_node","detect_intent","success",25),
        ("TL-B020","TR-B010","refund_node","process_cancellation","success",42),
        ("TL-B021","TR-B010","respond_node","generate_response","success",28900),
        ("TL-B022","TR-B014","event_node","ingest_event","success",14),
        ("TL-B023","TR-B014","risk_node","assess_risk","success",17),
        ("TL-B024","TR-B014","alert_node","send_alert","success",22),
    ]
    for lid, tid, agent, tool, st, lat in tlogs:
        if not _exists(db, ToolLog, lid):
            db.add(ToolLog(id=lid, trace_id=tid, agent_name=agent,
                           tool_name=tool, status=st, latency_ms=lat,
                           input_payload={"bulk_demo": True},
                           output_payload={"bulk_demo": True},
                           created_at=now))

    db.flush()
    print("[bulk_demo_seed] Done!")
