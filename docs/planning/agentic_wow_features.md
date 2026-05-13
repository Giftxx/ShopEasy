# ShopEasy — Agentic "Wow" Features
### ฟีเจอร์ที่ทำให้คนดูแล้วต้องบอกว่า "อยากได้เลย"

> **วัตถุประสงค์:** Feature เหล่านี้ออกแบบมาเพื่อแสดงให้เห็นว่า AI ในระบบ "คิดเอง ทำเอง ปรับเองได้" ไม่ใช่แค่ chatbot ตอบคำถาม  
> เหมาะสำหรับ Demo ต่อนักลงทุน, Showcase ต่อลูกค้าองค์กร, หรือ Portfolio สำหรับ Interview

---

## ภาพรวม — สิ่งที่มีแล้ว vs สิ่งที่จะทำให้ WOW

| มีแล้ว | เพิ่มเพื่อ WOW |
|--------|---------------|
| Workflow ตายตัว (A→B→C) | AI วางแผนและสร้าง workflow เองแบบ Real-time |
| แจ้งเตือนลูกค้าคนเดียวที่ delay | ตรวจจับปัญหาระดับ "Carrier ทั้งเจ้า" แล้ว resolve แบบ Bulk |
| Admin ต้อง approve ทีละรายการ | AI ทำ Batch Decision พร้อม Summary ว่า "ทำไมถึงตัดสินใจแบบนี้" |
| ลูกค้าถามก่อน AI ถึงตอบ | AI โทรหา (แจ้งเตือน) ลูกค้าก่อนที่เขาจะรู้ว่ามีปัญหา |
| ดู Trace ของ workflow ย้อนหลัง | Admin เห็น "ความคิด" ของ AI แบบ Real-time ขณะทำงาน |

---

## Feature 1 — Carrier Intelligence: ตรวจจับ "วิกฤตเจ้าเดียวกัน" แบบ Real-time

### ทำไมถึง WOW?
> ระบบอื่น: แจ้งเตือนลูกค้าคนที่ delay  
> ShopEasy: ตรวจจับว่า Flash Express มีพัสดุ delay **40 ชิ้นภายใน 2 ชั่วโมง** แล้วสร้าง Bulk Campaign ชดเชยทุกคนพร้อมกัน โดยไม่มีใคร trigger

### Flow:
```
[Background Job ทุก 15 นาที]
    ↓
[AI วิเคราะห์ pattern: carrier X, region Y, time window Z]
    ↓
[ถ้า delay rate > threshold → สร้าง "Carrier Incident"]
    ↓
[AI draft email/notification สำหรับลูกค้าที่ได้รับผลกระทบทั้งหมด]
    ↓
[Admin เห็น Dashboard: "Flash Express: 40 พัสดุล่าช้า | AI เสนอ: คูปอง 50฿ ทุกคน | [Approve All]"]
    ↓
[กด Approve once → แจ้งลูกค้า 40 คนพร้อมกัน]
```

### สิ่งที่เพิ่ม:
- Background scheduler ใน `workflow_03_proactive.py`
- Carrier Incident table ใน DB
- Admin Dashboard: "Carrier Health" panel
- Bulk Approval endpoint: `POST /api/v1/admin/incidents/{id}/approve-all`

### คนดูแล้วรู้สึก:
> "AI รู้ก่อนที่ลูกค้าจะโทรหาเลย"

---

## Feature 2 — Adversarial Review: AI สองตัวโต้เถียงกันก่อนตัดสินใจ Refund

### ทำไมถึง WOW?
> ระบบอื่น: AI ตัดสินใจแล้วบอกผล  
> ShopEasy: Admin เห็น AI สองตัว "ถกกัน" ก่อน — ตัวหนึ่งฝั่ง Policy ตัวหนึ่งฝั่ง Customer ก่อนสรุปผล

### Flow:
```
ลูกค้าขอ Refund ORD-2001
    ↓
[Policy Agent]: "นโยบายระบุ: คืนเงินได้ก็ต่อเมื่อแจ้งภายใน 7 วัน — รายนี้แจ้งวันที่ 8 ปฏิเสธ"
[Customer Agent]: "ลูกค้า Gold tier, ซื้อมา 18 เดือน, ยังไม่เคยขอ Refund — ควรยืดหยุ่น"
    ↓
[Arbitrator Agent]: สรุปจาก 2 ฝั่ง → "Approve partial 70%"
    ↓
Admin เห็น Panel: [Policy Case] vs [Customer Case] vs [Final Verdict]
                  พร้อม Confidence Score ของแต่ละฝั่ง
```

### สิ่งที่เพิ่ม:
- `adversarial_review_node()` ใน `refund_nodes.py`
- Frontend: Debate Panel ใน Admin Portal (แสดง argument ของแต่ละ agent)
- Schema: `RefundDebate` table บันทึก argument history

### คนดูแล้วรู้สึก:
> "มันไม่ใช่แค่ IF-ELSE มันคิดจริงๆ และมี rationale"

---

## Feature 3 — NLOps (Natural Language Operations): Admin สั่งงานด้วยภาษาธรรมชาติ

### ทำไมถึง WOW?
> ระบบอื่น: Admin ต้องคลิกผ่าน UI ทีละ step  
> ShopEasy: Admin พิมพ์ว่า "ส่งคูปอง 100 บาทให้ลูกค้าที่รอเกิน 5 วันทุกคนที่สั่งซื้อเดือนนี้" แล้ว AI execute เอง

### ตัวอย่าง Commands:
```
"Pause รับ order จาก Kerry ทุก region จนกว่าจะแก้ปัญหา"
→ AI: disable Kerry orders, แจ้ง 12 ลูกค้าที่ order ค้างอยู่

"สรุปให้หน่อยว่าสัปดาห์นี้ refund เยอะขึ้นเพราะอะไร"
→ AI: วิเคราะห์ data, ตอบ "สาเหตุหลัก 80%: Flash Express ล่าช้าใน region กรุงเทพ"

"ให้ VIP ทุกคนที่มี open complaint นานกว่า 48 ชั่วโมง ได้รับ free shipping ครั้งถัดไป"
→ AI: query ลูกค้าที่ตรงเงื่อนไข 7 คน, สร้าง coupon, แจ้งผ่าน chat
```

### Flow:
```
Admin พิมพ์ command ใน "AI Operations Console"
    ↓
[Intent Parser Agent]: แยก action + target + condition
    ↓
[Plan Agent]: สร้าง execution plan: ["query_customers", "create_coupon", "send_notification"]
    ↓
[Confirmation Step]: แสดง plan ให้ Admin confirm ก่อน execute
    ↓
[Executor Agent]: execute ทีละ step พร้อม log
    ↓
Admin เห็น: "ดำเนินการเสร็จ: ส่งคูปองให้ลูกค้า 7 คน [ดู Log]"
```

### สิ่งที่เพิ่ม:
- `nlops_agent.py` ใน agents/
- AI Operations Console ใน Admin Portal (input box + execution log)
- Dry-run mode: แสดงว่า AI จะทำอะไรก่อน Execute จริง

### คนดูแล้วรู้สึก:
> "มันคือ AI ที่เอาไปใช้งานจริงได้เลย ไม่ต้องเขียน code เพิ่ม"

---

## Feature 4 — Predictive Churn Shield: AI รู้ก่อนว่าลูกค้าคนไหนจะ "หนี"

### ทำไมถึง WOW?
> ระบบอื่น: รู้ว่าลูกค้าไม่พอใจตอนที่เขา submit complaint แล้ว  
> ShopEasy: AI คำนวณ Churn Risk Score ทุกวัน และ "โทรหา" ลูกค้าก่อนที่เขาจะรู้ว่ากำลังไม่พอใจ

### Churn Risk Signals ที่ AI ดู:
- Order ล่าช้า > 3 วัน + ไม่ได้เปิด app เลย 5 วัน = Risk 85%
- เคย refund แล้ว order ใหม่ที่ล่าช้า = Risk 90%
- ซื้อซ้ำลดลง 50% เทียบเดือนก่อน + มี open complaint = Risk 95%

### Flow:
```
[Daily Job 06:00]
    ↓
[Churn Analyzer Agent]: คำนวณ score ลูกค้าทุกคน
    ↓
[ลูกค้าที่ score > 70%] → สร้าง "At-Risk" alert
    ↓
[Retention Agent]: เลือก intervention ที่เหมาะสม:
    - Score 70-80%: ส่ง "เราเห็นว่า order ของคุณล่าช้า ขอโทษนะคะ 🎁 50฿"
    - Score 80-90%: customer service โทรหา (สร้าง task ใน Admin)
    - Score 90%+: offer พิเศษ + ยกเว้นค่าส่งทั้งปี
    ↓
Admin เห็น: Dashboard "At-Risk Customers: 3 คน | AI Interventions Sent: 2 | Saved: 1"
```

### สิ่งที่เพิ่ม:
- Churn Score ใน `users` table
- `workflow_04_churn_prevention.py`
- Admin: "Customer Health" tab แสดง at-risk list + intervention history

### คนดูแล้วรู้สึก:
> "ระบบนี้รักษาลูกค้าก่อนที่จะสายเกินไป — คือ Business Value จริงๆ"

---

## Feature 5 — Live Thought Stream: เห็น AI คิดอะไรอยู่แบบ Real-time

### ทำไมถึง WOW?
> ระบบอื่น: รอ... รอ... ได้ผลลัพธ์  
> ShopEasy: Admin/ลูกค้าเห็น "ความคิด" ของ AI streaming ออกมาทีละ step เหมือน Chain-of-Thought

### ตัวอย่าง UI ที่ลูกค้าเห็น:
```
ลูกค้าถาม: "Order ของฉันอยู่ไหน?"

💭 กำลังตรวจสอบ order ORD-1001...
💭 พบว่าพัสดุอยู่กับ Flash Express (tracking: TH123456)
💭 สถานะล่าสุด: "ออกจากคลัง 2 วันแล้ว" — ตรวจสอบ SLA...
💭 SLA ปกติ 1-2 วัน, ขณะนี้เลยมา 1 วัน — ความเสี่ยงล่าช้า: กลาง
💭 ดูนโยบายชดเชย: ถ้าเกิน 3 วันมีสิทธิ์รับคูปอง 50฿
✅ ตอบลูกค้า: "พัสดุอยู่ระหว่างขนส่งครับ คาดว่าถึงพรุ่งนี้..."
```

### สิ่งที่เพิ่ม:
- SSE (Server-Sent Events) endpoint: `GET /api/v1/chat/stream`
- Frontend: Typing indicator + thought bubble animation
- LangGraph: emit thought event ที่แต่ละ node transition

### คนดูแล้วรู้สึก:
> "โปร่งใสมาก เห็นเลยว่า AI ทำอะไร ไม่ใช่ blackbox"

---

## Feature 6 — Self-Optimizing Thresholds: AI ปรับพารามิเตอร์ตัวเองตามผลลัพธ์จริง

### ทำไมถึง WOW?
> ระบบอื่น: threshold ตายตัว (delay > 48h = alert)  
> ShopEasy: AI วิเคราะห์ว่า threshold ไหนให้ผลลัพธ์ที่ดีที่สุด แล้วปรับตัวเองทุกสัปดาห์

### Logic:
```
สัปดาห์ที่แล้ว:
- threshold 48h → alert 20 รายการ → Admin approve 15 → ลูกค้า happy 13 / ไม่ happy 2
- threshold 72h → alert 8 รายการ → Admin approve 7 → ลูกค้า happy 7 / ไม่ happy 0

[Optimizer Agent]: "72h ให้ precision สูงกว่า → ปรับ threshold เป็น 65h สัปดาห์หน้า"
```

### สิ่งที่เพิ่ม:
- `ThresholdConfig` table: บันทึก parameter history + performance
- Weekly optimizer job
- Admin: "AI Parameters" panel แสดง current settings + เหตุผลที่ปรับ

### คนดูแล้วรู้สึก:
> "มันเรียนรู้จากตัวเองได้ ไม่ต้อง maintain ตลอด"

---

## สรุป: Roadmap ตามความยาก

| Feature | Impact | ความยาก | เวลาโดยประมาณ |
|---------|--------|---------|--------------|
| **F5: Live Thought Stream** | ⭐⭐⭐⭐⭐ | 🟡 กลาง | 1-2 วัน |
| **F1: Carrier Intelligence** | ⭐⭐⭐⭐⭐ | 🟡 กลาง | 2-3 วัน |
| **F2: Adversarial Review** | ⭐⭐⭐⭐⭐ | 🟠 ปานกลาง-ยาก | 3-4 วัน |
| **F3: NLOps Console** | ⭐⭐⭐⭐⭐ | 🔴 ยาก | 4-5 วัน |
| **F4: Predictive Churn** | ⭐⭐⭐⭐ | 🟠 ปานกลาง-ยาก | 3-4 วัน |
| **F6: Self-Optimizing** | ⭐⭐⭐ | 🟡 กลาง | 2-3 วัน |

---

## แนะนำ: เริ่มต้นด้วย F5 + F1 ก่อน

เหตุผล:
1. **F5 (Live Thought Stream)** — เห็นผลทันที, Demo ได้ทุกที่, ไม่ต้องเพิ่ม backend logic มาก แค่เปิด SSE streaming
2. **F1 (Carrier Intelligence)** — แสดง Business Value ชัดที่สุด: "AI ประหยัดเงินได้ X บาทต่อเดือนจาก proactive resolution"

สองอย่างนี้ถ้า Demo พร้อมกันจะทำให้คนดูเห็นทั้ง **ความโปร่งใสของ AI** และ **ผลลัพธ์ทางธุรกิจจริง** ซึ่งคือสิ่งที่บริษัทองค์กรมองหา

---

*อัปเดต: 12 พฤษภาคม 2026 | ShopEasy Agentic Platform*
