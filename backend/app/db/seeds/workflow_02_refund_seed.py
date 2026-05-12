from datetime import datetime


def get_workflow_02_seed_data() -> dict[str, list[dict]]:
    now = datetime.utcnow()

    return {
        "conversations": [
            {
                "id": "CONV-002",
                "customer_id": "CUST-001",
                "channel": "web_chat",
                "status": "open",
                "latest_intent": "refund_request",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "messages": [
            {
                "id": "MSG-002",
                "conversation_id": "CONV-002",
                "sender_type": "customer",
                "sender_id": "CUST-001",
                "content": "สินค้าเสียหาย ขอคืนเงิน",
                "metadata_json": {"language": "th"},
                "created_at": now,
            }
        ],
        "cases": [
            {
                "id": "CS-5521",
                "customer_id": "CUST-001",
                "order_id": "SP-1024",
                "case_type": "refund",
                "priority": "medium",
                "status": "open",
                "ai_summary": "Customer reported damaged item and asked for refund.",
                "assigned_role": "admin",
                "assigned_user_id": None,
                "created_by": "ai",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "refund_requests": [
            {
                "id": "RF-5521",
                "order_id": "SP-1024",
                "customer_id": "CUST-001",
                "case_id": "CS-5521",
                "reason": "Damaged item",
                "requested_resolution": "refund",
                "eligibility_status": "under_review",
                "risk_score": 45,
                "ai_recommendation": "Evidence is present and can proceed to review.",
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "attachments": [
            {
                "id": "ATT-001",
                "owner_type": "refund_request",
                "message_id": None,
                "case_id": "CS-5521",
                "refund_request_id": "RF-5521",
                "policy_id": None,
                "attachment_type": "image",
                "evidence_group": "damaged_item",
                "display_order": 1,
                "description": "Damaged item photo",
                "bucket_name": "evidence",
                "object_key": "refund_request/RF-5521/damaged_item/01_front-crack.jpg",
                "file_name": "01_front-crack.jpg",
                "mime_type": "image/jpeg",
                "file_size_bytes": 120034,
                "uploaded_by_type": "customer",
                "uploaded_by_customer_id": "CUST-001",
                "uploaded_by_user_id": None,
                "upload_status": "uploaded",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "ATT-002",
                "owner_type": "refund_request",
                "message_id": None,
                "case_id": "CS-5521",
                "refund_request_id": "RF-5521",
                "policy_id": None,
                "attachment_type": "image",
                "evidence_group": "parcel_package",
                "display_order": 2,
                "description": "Package photo",
                "bucket_name": "evidence",
                "object_key": "refund_request/RF-5521/parcel_package/02_box-damaged.jpg",
                "file_name": "02_box-damaged.jpg",
                "mime_type": "image/jpeg",
                "file_size_bytes": 110210,
                "uploaded_by_type": "customer",
                "uploaded_by_customer_id": "CUST-001",
                "uploaded_by_user_id": None,
                "upload_status": "uploaded",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "ATT-003",
                "owner_type": "refund_request",
                "message_id": None,
                "case_id": "CS-5521",
                "refund_request_id": "RF-5521",
                "policy_id": None,
                "attachment_type": "image",
                "evidence_group": "parcel_label",
                "display_order": 3,
                "description": "Shipping label photo",
                "bucket_name": "evidence",
                "object_key": "refund_request/RF-5521/parcel_label/03_shipping-label.jpg",
                "file_name": "03_shipping-label.jpg",
                "mime_type": "image/jpeg",
                "file_size_bytes": 90344,
                "uploaded_by_type": "customer",
                "uploaded_by_customer_id": "CUST-001",
                "uploaded_by_user_id": None,
                "upload_status": "uploaded",
                "created_at": now,
                "updated_at": now,
            },
        ],
        "policies": [
            {
                "id": "POL-001",
                "title": "Refund Policy",
                "category": "refund",
                "version": "v2.0",
                "content": (
                    "นโยบายการคืนเงิน ShopEasy (Refund Policy)\n\n"
                    "1. เงื่อนไขการคืนเงิน\n"
                    "ลูกค้าสามารถขอคืนเงินได้ภายใน 7 วันนับจากวันที่ได้รับสินค้า หากสินค้าเสียหาย ชำรุด หรือไม่ตรงกับที่สั่ง "
                    "โดยต้องแนบหลักฐานภาพถ่ายสินค้าที่เสียหาย ภาพกล่องพัสดุ และใบปะหน้าพัสดุ\n\n"
                    "2. ขั้นตอนการขอคืนเงิน\n"
                    "ลูกค้าแจ้งผ่านระบบแชท AI พร้อมแนบหลักฐาน ระบบจะเปิด Case อัตโนมัติ "
                    "จากนั้นเจ้าหน้าที่ตรวจสอบภายใน 3-5 วันทำการ และดำเนินการคืนเงินภายใน 7-14 วันทำการ\n\n"
                    "3. กรณีที่ต้องอนุมัติจากเจ้าหน้าที่\n"
                    "คำขอคืนเงินมูลค่าเกิน 5,000 บาท หรือ risk score เกิน 70 จะถูกส่งให้เจ้าหน้าที่อนุมัติก่อน "
                    "ลูกค้าจะได้รับแจ้งทาง email ภายใน 1 วันทำการ\n\n"
                    "4. สินค้าที่ไม่สามารถคืนเงินได้\n"
                    "สินค้าดิจิทัล บัตรของขวัญ สินค้าลดราคาพิเศษที่ระบุว่า Final Sale และสินค้าที่ใช้งานแล้ว "
                    "ไม่สามารถขอคืนเงินได้ เว้นแต่มีความเสียหายจากการจัดส่ง\n\n"
                    "5. การคืนเงิน\n"
                    "คืนเงินผ่านช่องทางเดิมที่ชำระ ภายใน 7-14 วันทำการหลังอนุมัติ "
                    "สำหรับบัตรเครดิตอาจใช้เวลา 1-2 รอบบิล"
                ),
                "status": "active",
                "effective_from": None,
                "effective_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "POL-002",
                "title": "Return Policy",
                "category": "return",
                "version": "v2.0",
                "content": (
                    "นโยบายการคืนสินค้า ShopEasy (Return Policy)\n\n"
                    "1. เงื่อนไขการคืนสินค้า\n"
                    "ลูกค้าสามารถคืนสินค้าได้ภายใน 7 วันนับจากวันที่ได้รับสินค้า "
                    "ในกรณีที่สินค้าชำรุด ส่งผิดรุ่น หรือไม่ตรงตามคำสั่งซื้อ "
                    "สินค้าต้องอยู่ในสภาพเดิม ไม่ผ่านการใช้งาน พร้อมบรรจุภัณฑ์ครบถ้วน\n\n"
                    "2. ขั้นตอนการคืนสินค้า\n"
                    "แจ้งผ่านระบบ ShopEasy พร้อมภาพสินค้าและเหตุผล รอการยืนยันจากร้านค้าภายใน 2 วันทำการ "
                    "จัดส่งสินค้าคืนตาม label ที่ระบบสร้างให้ ค่าส่งคืนร้านค้าเป็นผู้รับผิดชอบกรณีสินค้าชำรุดจากการผลิต\n\n"
                    "3. การตรวจสอบสินค้าคืน\n"
                    "ร้านค้าตรวจสอบสินค้าภายใน 3 วันทำการหลังได้รับคืน หากผ่านการตรวจสอบจะดำเนินการคืนเงิน "
                    "หากไม่ผ่านจะแจ้งเหตุผลและส่งสินค้ากลับให้ลูกค้า\n\n"
                    "4. สินค้าที่ไม่รับคืน\n"
                    "สินค้าที่ผ่านการใช้งาน สินค้าสุขภาพและความงามที่เปิดแล้ว อาหารและเครื่องดื่ม "
                    "และสินค้าที่ระบุว่าไม่รับคืน"
                ),
                "status": "active",
                "effective_from": None,
                "effective_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "POL-003",
                "title": "Compensation Policy",
                "category": "compensation",
                "version": "v1.5",
                "content": (
                    "นโยบายการชดเชย ShopEasy (Compensation Policy)\n\n"
                    "1. กรณีที่ได้รับการชดเชย\n"
                    "การจัดส่งล่าช้าเกิน 7 วันจากวันที่สัญญา การส่งสินค้าผิดรุ่นหรือเสียหาย "
                    "และกรณีที่ร้านค้าไม่จัดส่งสินค้าภายใน 5 วันทำการหลังชำระเงิน\n\n"
                    "2. รูปแบบการชดเชย\n"
                    "คูปองส่วนลด ShopEasy Coins คืนเงินเต็มจำนวน หรือการจัดส่งฟรีในครั้งถัดไป "
                    "ขึ้นอยู่กับความรุนแรงของปัญหาและมูลค่าคำสั่งซื้อ\n\n"
                    "3. การอนุมัติชดเชย\n"
                    "การชดเชยมูลค่าเกิน 2,000 บาท หรือ risk score เกิน 80 ต้องผ่านการอนุมัติจาก Supervisor "
                    "และบันทึกใน audit log ทุกครั้ง\n\n"
                    "4. ระยะเวลาการพิจารณา\n"
                    "ร้องเรียนปกติ 3-5 วันทำการ กรณีเร่งด่วน 1 วันทำการ "
                    "กรณีที่ต้องอนุมัติจากเจ้าหน้าที่ 2-3 วันทำการ"
                ),
                "status": "active",
                "effective_from": None,
                "effective_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "POL-004",
                "title": "Shipping Policy",
                "category": "shipping",
                "version": "v3.2",
                "content": (
                    "นโยบายการจัดส่ง ShopEasy (Shipping Policy)\n\n"
                    "1. ระยะเวลาจัดส่ง\n"
                    "กรุงเทพและปริมณฑล 1-3 วันทำการ ต่างจังหวัด 3-7 วันทำการ "
                    "พื้นที่ห่างไกล 5-10 วันทำการ Express delivery 1 วันทำการ (เฉพาะกรุงเทพ)\n\n"
                    "2. การติดตามพัสดุ\n"
                    "ลูกค้าสามารถติดตามสถานะพัสดุได้ผ่านแท็บ 'การจัดส่ง' ในแอป ShopEasy "
                    "หรือผ่าน AI chat ด้วยการพิมพ์ 'ของฉันอยู่ไหนแล้ว' ระบบจะแสดงสถานะล่าสุดทันที\n\n"
                    "3. กรณีพัสดุล่าช้า\n"
                    "หากไม่มีอัปเดตสถานะเกิน 48 ชั่วโมง ระบบจะแจ้งเตือนอัตโนมัติ (Proactive Alert) "
                    "และส่ง Case ให้เจ้าหน้าที่ติดตามร้านค้าและบริษัทขนส่ง\n\n"
                    "4. ค่าจัดส่ง\n"
                    "ฟรีค่าจัดส่งสำหรับคำสั่งซื้อเกิน 500 บาท ต่ำกว่า 500 บาทคิด 50 บาทต่อครั้ง "
                    "Express delivery คิดเพิ่ม 100 บาท\n\n"
                    "5. ผู้ให้บริการขนส่ง\n"
                    "Flash Express, Kerry Express, J&T Express, Thailand Post และ Lalamove สำหรับ same-day delivery"
                ),
                "status": "active",
                "effective_from": None,
                "effective_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "POL-005",
                "title": "Seller SLA Policy",
                "category": "seller",
                "version": "v2.3",
                "content": (
                    "นโยบาย SLA ร้านค้า ShopEasy (Seller SLA Policy)\n\n"
                    "1. ข้อตกลงระดับการบริการ\n"
                    "ร้านค้าต้องยืนยันคำสั่งซื้อภายใน 24 ชั่วโมง จัดส่งสินค้าภายใน 2 วันทำการหลังยืนยัน "
                    "และแนบเลขติดตามพัสดุภายใน 48 ชั่วโมงหลังจัดส่ง\n\n"
                    "2. บทลงโทษกรณีละเมิด SLA\n"
                    "ยืนยันช้ากว่า 24 ชั่วโมง: ปรับ 50 บาทต่อออเดอร์ "
                    "ไม่จัดส่งภายใน 5 วัน: ลูกค้าได้รับสิทธิ์ยกเลิกอัตโนมัติพร้อมคืนเงิน "
                    "ละเมิด SLA สะสมเกิน 3 ครั้งต่อเดือน: ระงับการขายชั่วคราว\n\n"
                    "3. การตรวจสอบ SLA\n"
                    "ระบบ AI ตรวจสอบ SLA อัตโนมัติทุก 6 ชั่วโมง และส่ง proactive alert ให้เจ้าหน้าที่ "
                    "เมื่อตรวจพบการละเมิด"
                ),
                "status": "active",
                "effective_from": None,
                "effective_to": None,
                "created_at": now,
                "updated_at": now,
            },
        ],
        "policy_chunks": [
            # POL-001 Refund Policy chunks
            {
                "id": "PCH-001",
                "policy_id": "POL-001",
                "chunk_index": 0,
                "chunk_text": "ลูกค้าสามารถขอคืนเงินได้ภายใน 7 วันนับจากวันที่ได้รับสินค้า หากสินค้าเสียหาย ชำรุด หรือไม่ตรงกับที่สั่ง โดยต้องแนบหลักฐานภาพถ่ายสินค้าที่เสียหาย ภาพกล่องพัสดุ และใบปะหน้าพัสดุ",
                "metadata_json": {"policy": "Refund Policy", "section": "1"},
                "embedding_id": None,
                "created_at": now,
            },
            {
                "id": "PCH-002",
                "policy_id": "POL-001",
                "chunk_index": 1,
                "chunk_text": "ลูกค้าแจ้งผ่านระบบแชท AI พร้อมแนบหลักฐาน ระบบจะเปิด Case อัตโนมัติ จากนั้นเจ้าหน้าที่ตรวจสอบภายใน 3-5 วันทำการ และดำเนินการคืนเงินภายใน 7-14 วันทำการ",
                "metadata_json": {"policy": "Refund Policy", "section": "2"},
                "embedding_id": None,
                "created_at": now,
            },
            {
                "id": "PCH-003",
                "policy_id": "POL-001",
                "chunk_index": 2,
                "chunk_text": "คำขอคืนเงินมูลค่าเกิน 5,000 บาท หรือ risk score เกิน 70 จะถูกส่งให้เจ้าหน้าที่อนุมัติก่อน ลูกค้าจะได้รับแจ้งทาง email ภายใน 1 วันทำการ",
                "metadata_json": {"policy": "Refund Policy", "section": "3"},
                "embedding_id": None,
                "created_at": now,
            },
            {
                "id": "PCH-004",
                "policy_id": "POL-001",
                "chunk_index": 3,
                "chunk_text": "คืนเงินผ่านช่องทางเดิมที่ชำระ ภายใน 7-14 วันทำการหลังอนุมัติ สำหรับบัตรเครดิตอาจใช้เวลา 1-2 รอบบิล สินค้าดิจิทัล บัตรของขวัญ และสินค้า Final Sale ไม่สามารถขอคืนเงินได้",
                "metadata_json": {"policy": "Refund Policy", "section": "4-5"},
                "embedding_id": None,
                "created_at": now,
            },
            # POL-002 Return Policy chunks
            {
                "id": "PCH-011",
                "policy_id": "POL-002",
                "chunk_index": 0,
                "chunk_text": "ลูกค้าสามารถคืนสินค้าได้ภายใน 7 วันนับจากวันที่ได้รับสินค้า ในกรณีที่สินค้าชำรุด ส่งผิดรุ่น หรือไม่ตรงตามคำสั่งซื้อ สินค้าต้องอยู่ในสภาพเดิม ไม่ผ่านการใช้งาน พร้อมบรรจุภัณฑ์ครบถ้วน",
                "metadata_json": {"policy": "Return Policy", "section": "1"},
                "embedding_id": None,
                "created_at": now,
            },
            {
                "id": "PCH-012",
                "policy_id": "POL-002",
                "chunk_index": 1,
                "chunk_text": "แจ้งผ่านระบบ ShopEasy พร้อมภาพสินค้าและเหตุผล รอการยืนยันจากร้านค้าภายใน 2 วันทำการ จัดส่งสินค้าคืนตาม label ที่ระบบสร้างให้ ค่าส่งคืนร้านค้าเป็นผู้รับผิดชอบกรณีสินค้าชำรุดจากการผลิต",
                "metadata_json": {"policy": "Return Policy", "section": "2"},
                "embedding_id": None,
                "created_at": now,
            },
            # POL-003 Compensation Policy chunks
            {
                "id": "PCH-021",
                "policy_id": "POL-003",
                "chunk_index": 0,
                "chunk_text": "การจัดส่งล่าช้าเกิน 7 วันจากวันที่สัญญา การส่งสินค้าผิดรุ่นหรือเสียหาย และกรณีที่ร้านค้าไม่จัดส่งสินค้าภายใน 5 วันทำการหลังชำระเงิน ลูกค้าจะได้รับการชดเชย",
                "metadata_json": {"policy": "Compensation Policy", "section": "1"},
                "embedding_id": None,
                "created_at": now,
            },
            {
                "id": "PCH-022",
                "policy_id": "POL-003",
                "chunk_index": 1,
                "chunk_text": "การชดเชยมูลค่าเกิน 2,000 บาท หรือ risk score เกิน 80 ต้องผ่านการอนุมัติจาก Supervisor ร้องเรียนปกติ 3-5 วันทำการ กรณีเร่งด่วน 1 วันทำการ",
                "metadata_json": {"policy": "Compensation Policy", "section": "3-4"},
                "embedding_id": None,
                "created_at": now,
            },
            # POL-004 Shipping Policy chunks
            {
                "id": "PCH-031",
                "policy_id": "POL-004",
                "chunk_index": 0,
                "chunk_text": "กรุงเทพและปริมณฑล 1-3 วันทำการ ต่างจังหวัด 3-7 วันทำการ พื้นที่ห่างไกล 5-10 วันทำการ Express delivery 1 วันทำการ (เฉพาะกรุงเทพ)",
                "metadata_json": {"policy": "Shipping Policy", "section": "1"},
                "embedding_id": None,
                "created_at": now,
            },
            {
                "id": "PCH-032",
                "policy_id": "POL-004",
                "chunk_index": 1,
                "chunk_text": "หากไม่มีอัปเดตสถานะเกิน 48 ชั่วโมง ระบบจะแจ้งเตือนอัตโนมัติ (Proactive Alert) และส่ง Case ให้เจ้าหน้าที่ติดตามร้านค้าและบริษัทขนส่ง ลูกค้าสามารถติดตามพัสดุผ่านแท็บ การจัดส่ง หรือ AI chat",
                "metadata_json": {"policy": "Shipping Policy", "section": "2-3"},
                "embedding_id": None,
                "created_at": now,
            },
            {
                "id": "PCH-033",
                "policy_id": "POL-004",
                "chunk_index": 2,
                "chunk_text": "ฟรีค่าจัดส่งสำหรับคำสั่งซื้อเกิน 500 บาท ต่ำกว่า 500 บาทคิด 50 บาทต่อครั้ง Express delivery คิดเพิ่ม 100 บาท ผู้ให้บริการขนส่ง: Flash Express, Kerry Express, J&T Express, Thailand Post",
                "metadata_json": {"policy": "Shipping Policy", "section": "4-5"},
                "embedding_id": None,
                "created_at": now,
            },
            # POL-005 Seller SLA Policy chunks
            {
                "id": "PCH-041",
                "policy_id": "POL-005",
                "chunk_index": 0,
                "chunk_text": "ร้านค้าต้องยืนยันคำสั่งซื้อภายใน 24 ชั่วโมง จัดส่งสินค้าภายใน 2 วันทำการหลังยืนยัน และแนบเลขติดตามพัสดุภายใน 48 ชั่วโมงหลังจัดส่ง ไม่จัดส่งภายใน 5 วัน ลูกค้าได้รับสิทธิ์ยกเลิกอัตโนมัติพร้อมคืนเงิน",
                "metadata_json": {"policy": "Seller SLA Policy", "section": "1-2"},
                "embedding_id": None,
                "created_at": now,
            },
        ],
        "approvals": [
            {
                "id": "APR-1001",
                "case_id": "CS-5521",
                "approval_type": "refund",
                "requested_action": "Review refund recommendation",
                "amount": 2490.00,
                "currency": "THB",
                "risk_level": "medium",
                "status": "pending",
                "ai_reason": "Refund request queued for manual review.",
                "policy_citation": {"policy_ids": ["POL-001", "POL-003"]},
                "reviewer_id": None,
                "reviewed_at": None,
                "created_at": now,
            }
        ],
    }
