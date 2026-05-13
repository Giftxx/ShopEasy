# Autonomous Multi-Agent Socratic Commerce Intelligence (AMSCI)
### Feature ที่ไม่มีใครทำมาก่อนในวงการ E-Commerce AI

> **ระดับความยาก:** Senior AI Engineer  
> **โดดเด่นตรงไหน:** ระบบไม่แค่ "detect แล้ว respond" — มันสร้าง workflow ใหม่แบบ real-time, ให้ agent หลายตัว debate กัน, แล้ว execute เองโดยไม่ต้องมีคน trigger  
> **สิ่งที่ไม่มีใครทำ:** Socratic Debate Protocol ระหว่าง AI Agents ก่อนตัดสินใจ  
> วันที่: 12 พฤษภาคม 2026

---

## 1. ทำไมถึง WOW และแตกต่างจากทุกอย่างที่มีอยู่

### ปัญหาของระบบ AI ปัจจุบัน (รวมถึง ShopEasy V3/V4)

| สิ่งที่ระบบส่วนใหญ่ทำ | ข้อจำกัด |
|---------------------|---------|
| Detect event → Execute fixed workflow | ทำได้แค่ปัญหาที่ programmer คาดไว้ล่วงหน้า |
| Single agent ตัดสินใจคนเดียว | Bias ตามมุมมองเดียว ไม่มี cross-check |
| Human-in-the-loop ทุกการตัดสินใจ | Bottleneck, ไม่ scale, ต้องมีคนตลอด 24 ชั่วโมง |
| Multi-agent แค่แบ่งงานกัน | ไม่มีการ debate หรือโต้แย้งกัน |
| Memory เก็บแค่ event ที่เกิดขึ้น | ไม่ได้ distill เป็น "strategy knowledge" |

### สิ่งที่ AMSCI ทำแตกต่าง

```
ปัญหาเดิม:
  Customer complaint เยอะขึ้น 3x ในวันนี้
  → ระบบเดิม: ทำอะไรไม่ได้ เพราะไม่มี workflow สำหรับ "complaint surge"

AMSCI:
  1. Watchdog Agent ตรวจพบ: complaint +300%, refund +180%, carrier SLA -40%
     ทั้งหมดเกิดใน region "กรุงเทพ ฝั่งเหนือ" ใน 4 ชั่วโมงที่ผ่านมา
  
  2. Meta-Planner สร้าง workflow ใหม่แบบ real-time:
     "incident ประเภท: regional_carrier_collapse"
     "spawning 4 agents: [CarrierNegotiator, CustomerAdvocate, BudgetGuardian, PolicyExpert]"
  
  3. ทั้ง 4 agents debate กันผ่าน Socratic Protocol:
     CarrierNegotiator: "ต้องส่ง formal complaint ไป Flash Express ทันที"
     BudgetGuardian: "คูปองชดเชย 50 บาท × 40 คน = 2,000 บาท อนุมัติได้"
     CustomerAdvocate: "ต้องแจ้งลูกค้าก่อนที่เขาจะโทรหา" 
     PolicyExpert: "นโยบายข้อ 3.2 รองรับ auto-compensate กรณี carrier failure"
     
     ประเด็นขัดแย้ง: BudgetGuardian โต้ว่า "Gold tier ควรได้ 100 บาท ไม่ใช่ 50 บาท"
     → Arbitrator Agent วิเคราะห์: 32 คน = Standard (50฿), 8 คน = Gold (100฿)
     → Consensus ภายใน 45 วินาที
  
  4. Execute ทั้งหมดโดยอัตโนมัติ:
     ✓ สร้าง coupon 40 รายการ
     ✓ ส่ง proactive notification ลูกค้า 40 คน
     ✓ สร้าง formal incident report ส่ง carrier
     ✓ Update risk model สำหรับ Flash Express ใน region นี้
  
  5. Post-Mortem อัตโนมัติ:
     "Incident #INC-0042 | Duration: 4h 23m | Affected: 40 customers
      Root Cause: Flash Express sorting facility กรุงเทพเหนือ offline
      Resolution: Auto-compensated, carrier notified, monitoring active
      New Policy Proposed: ถ้า carrier SLA drop >40% ใน region → auto-switch coupon tier"
```

**ไม่มี e-commerce platform ใดในโลกที่ทำแบบนี้ได้**

---

## 2. สถาปัตยกรรม — 5 Layer

```
┌────────────────────────────────────────────────────────────────┐
│                    LAYER 5: VISIBILITY                         │
│         Real-time "AI War Room" dashboard (WebSocket)         │
│   เห็น agent debate, thought stream, execution log live       │
└────────────────────────────────────────────────────────────────┘
                              ↑
┌────────────────────────────────────────────────────────────────┐
│                    LAYER 4: EXECUTION                          │
│    Autonomous Action Engine (ใช้ tool_chain_executor เดิม)    │
│    + Kill Switch: Admin สามารถ halt ได้ทุก step               │
└────────────────────────────────────────────────────────────────┘
                              ↑
┌────────────────────────────────────────────────────────────────┐
│                    LAYER 3: SOCRATIC DEBATE                    │
│    N specialized agents debate via shared scratchpad           │
│    Arbitrator resolves disagreements with evidence scoring     │
└────────────────────────────────────────────────────────────────┘
                              ↑
┌────────────────────────────────────────────────────────────────┐
│                    LAYER 2: META-PLANNER                       │
│    ตรวจจับ incident type → สร้าง agent roster ที่เหมาะสม     │
│    ถ้า incident ใหม่ → reason from scratch ว่าต้อง spawn ใคร  │
└────────────────────────────────────────────────────────────────┘
                              ↑
┌────────────────────────────────────────────────────────────────┐
│                    LAYER 1: WATCHDOG                           │
│    Background loop ทุก 3 นาที                                  │
│    Cross-signal fusion: WF01 + WF02 + WF03 + customer signals  │
│    Anomaly detection ด้วย statistical + LLM reasoning          │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. สิ่งที่ Novel จริงๆ — Socratic Debate Protocol

นี่คือหัวใจของ AMSCI และสิ่งที่ไม่มีใครทำ

### 3.1 วิธีทำงาน

```python
# Pseudocode ของ Socratic Debate
class SocraticDebateProtocol:
    """
    ก่อนตัดสินใจใดๆ ที่มีผลกระทบสูง,
    ให้ agent หลายมุมมอง argue กัน แล้ว arbitrate
    """
    
    def run_debate(self, incident: Incident) -> ConsensusDecision:
        # 1. Spawn agents ตาม incident type
        agents = self.spawn_perspective_agents(incident)
        # e.g., [PolicyExpert, CustomerAdvocate, BudgetGuardian, RiskAnalyst]
        
        # 2. Each agent develops their position independently
        positions = [agent.develop_position(incident) for agent in agents]
        
        # 3. Cross-examination: แต่ละ agent ตอบโต้ position ของคนอื่น
        rebuttals = self.run_cross_examination(agents, positions)
        
        # 4. Find consensus points (สิ่งที่ทุกคนเห็นด้วย)
        consensus_points = self.extract_consensus(positions, rebuttals)
        
        # 5. Identify disagreement points (สิ่งที่ยังเถียงกันอยู่)
        conflicts = self.extract_conflicts(positions, rebuttals)
        
        # 6. For each conflict, demand evidence with confidence score
        resolutions = self.arbitrate_conflicts(agents, conflicts)
        
        # 7. Synthesize final decision
        return self.synthesize_decision(consensus_points, resolutions)
```

### 3.2 ตัวอย่าง Debate Log ที่ Admin จะเห็นใน Real-time

```
[INCIDENT #INC-0042] Flash Express regional collapse
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 PolicyExpert:    ข้อ 3.2 ระบุ: carrier failure → auto-compensate
                    Confidence: 0.95 | Evidence: policy_v2.pdf page 14
                    
🤖 CustomerAdvocate: แนะนำ notify ทันทีก่อน coupon เพราะ 78% ของลูกค้า 
                    segment นี้ rate "communication" สูงกว่า "discount"
                    Confidence: 0.81 | Evidence: CSAT survey Q1/2026
                    
🤖 BudgetGuardian:  budget เดือนนี้เหลือ 8,400฿ | คูปองทั้งหมด 2,800฿ = 33%
                    ผ่าน threshold (max 40%) | Confidence: 1.00
                    
🤖 RiskAnalyst:     Flash Express ใน region นี้เคย fail 3 ครั้งใน 6 เดือน
                    แนะนำ: escalate risk tier → "Watch" status
                    Confidence: 0.88

⚡ CONFLICT DETECTED:
   PolicyExpert: "Gold tier = 100฿" 
   BudgetGuardian: "50฿ เพียงพอตามมาตรฐาน"
   
   → Arbitrator วิเคราะห์: 8 คนเป็น Gold tier, มีประวัติ LTV สูง
     Gold churn cost > coupon upgrade cost → Gold = 100฿ ✓

✅ CONSENSUS REACHED (47 seconds)
   Action Plan: [notify_all → apply_coupon → flag_carrier → update_risk]
   Estimated Impact: +0.3 CSAT | Cost: 2,800฿ | Churn prevention: ~2 customers
```

---

## 4. Cross-Signal Fusion — สิ่งที่ WF01/WF02/WF03 ไม่ทำ

Watchdog Agent ไม่ได้ดูแค่ shipment delay แต่รวม signal จากทุก workflow:

```python
SIGNAL_MATRIX = {
    # WF01 signals
    "shipment_delay_rate": {"window": "4h", "baseline": "7d_avg"},
    "carrier_sla_compliance": {"per_carrier": True, "per_region": True},
    "untracked_shipment_rate": {"threshold": 0.15},
    
    # WF02 signals
    "refund_request_rate": {"window": "4h", "spike_threshold": 2.0},
    "refund_approval_rate": {"trending": True},
    "high_risk_refund_count": {"threshold": 5},
    
    # WF03 signals
    "proactive_alert_volume": {"window": "4h"},
    "carrier_contacted_rate": {"per_carrier": True},
    
    # Customer signals
    "chat_sentiment_score": {"rolling": "1h", "drop_threshold": -0.3},
    "repeat_contact_rate": {"threshold": 0.2},
    "no_reply_rate": {"window": "24h"},
    
    # Business signals
    "order_volume": {"anomaly_detection": True},
    "cart_abandonment_rate": {"spike_threshold": 1.5},
}

# Incident patterns ที่ watchdog รู้จัก
KNOWN_INCIDENT_PATTERNS = {
    "regional_carrier_collapse": {
        "signals": ["shipment_delay_rate", "carrier_sla_compliance", "refund_request_rate"],
        "correlation": "same_carrier + same_region",
        "threshold": 0.7,
    },
    "product_defect_wave": {
        "signals": ["refund_request_rate", "repeat_contact_rate", "chat_sentiment_score"],
        "correlation": "same_product_sku",
        "threshold": 0.8,
    },
    "payment_gateway_issue": {
        "signals": ["order_volume", "cart_abandonment_rate"],
        "correlation": "time_correlated",
        "threshold": 0.85,
    },
}

# ถ้าไม่ match pattern ใดเลย → Meta-Planner จะ reason จาก scratch
# นี่คือ zero-shot incident classification
```

---

## 5. Implementation Plan — ต่อบนของที่มีอยู่

### 5.1 ไฟล์ที่ต้องสร้างใหม่

```
backend/app/agents/
├── watchdog.py              # Background loop + cross-signal fusion
├── meta_planner.py          # Dynamic workflow generation
├── socratic_debate.py       # Debate protocol + arbitration
├── incident_commander.py    # Orchestrates full AMSCI pipeline
└── nodes/
    └── amsci_nodes.py       # LangGraph nodes สำหรับ AMSCI workflow

backend/app/api/routes/
└── incidents.py             # REST + WebSocket endpoints

backend/app/db/models/
└── incident.py              # Incident, DebateLog, AgentPosition tables

backend/app/services/
└── workflow_04_autonomous.py  # Main AMSCI orchestration service
```

### 5.2 ไฟล์ที่ต้องแก้ไข (เล็กน้อย)

```
backend/app/main.py          # เพิ่ม startup watchdog loop + WebSocket
backend/app/api/router.py    # เพิ่ม incidents router
frontend/src/pages/ai/       # เพิ่ม "Operations Room" tab
```

### 5.3 DB Tables ที่ต้องเพิ่ม

```sql
-- Incidents detected by watchdog
CREATE TABLE incidents (
    id VARCHAR PRIMARY KEY,              -- INC-0001
    incident_type VARCHAR,               -- regional_carrier_collapse / unknown
    severity VARCHAR,                    -- low / medium / high / critical
    affected_entity_type VARCHAR,        -- carrier / product / region
    affected_entity_id VARCHAR,
    signal_snapshot JSONB,               -- raw signals ที่ detect ได้
    status VARCHAR,                      -- detecting / debating / executing / resolved
    created_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);

-- Each agent's position in a debate
CREATE TABLE debate_positions (
    id VARCHAR PRIMARY KEY,
    incident_id VARCHAR REFERENCES incidents(id),
    agent_role VARCHAR,                  -- PolicyExpert / CustomerAdvocate / etc.
    position_text TEXT,                  -- ความเห็นของ agent
    confidence FLOAT,
    evidence_refs JSONB,                 -- อ้างอิงเอกสาร, data, etc.
    created_at TIMESTAMPTZ
);

-- Conflict resolution records
CREATE TABLE debate_resolutions (
    id VARCHAR PRIMARY KEY,
    incident_id VARCHAR REFERENCES incidents(id),
    conflict_description TEXT,
    resolution_text TEXT,
    winning_position VARCHAR,            -- agent_role ที่ชนะ
    arbitration_reasoning TEXT,
    created_at TIMESTAMPTZ
);

-- Strategy knowledge distilled from past incidents
CREATE TABLE strategy_memory (
    id VARCHAR PRIMARY KEY,
    incident_type VARCHAR,
    situation_description TEXT,
    effective_strategy TEXT,
    outcome_metrics JSONB,               -- CSAT change, cost, churn prevention
    confidence_score FLOAT,
    times_used INT DEFAULT 0,
    last_used_at TIMESTAMPTZ
);
```

---

## 6. Frontend — "AI War Room" (สิ่งที่จะทำให้คนอ้าปากค้าง)

### 6.1 Layout

```
AI Control Portal
└── Operations Room Tab (ใหม่)
    ├── [Left Panel] Active Incidents
    │   ├── INC-0042 🔴 CRITICAL — Flash Express Collapse
    │   ├── INC-0041 🟡 RESOLVED — Product defect wave SKU-202
    │   └── [+] เพิ่มขึ้น real-time ผ่าน WebSocket
    │
    ├── [Center Panel] Live Debate Stream
    │   ├── 🤖 PolicyExpert: "ข้อ 3.2 ระบุว่า..." [typing animation]
    │   ├── ⚡ CONFLICT: BudgetGuardian vs PolicyExpert
    │   ├── ⚖️  Arbitrator กำลังวิเคราะห์... [progress bar]
    │   └── ✅ CONSENSUS: "Action Plan approved in 47s"
    │
    └── [Right Panel] Execution Log
        ├── [✓] 10:42:01 notify_all_customers — 40 sent
        ├── [✓] 10:42:03 apply_coupons — 40 created  
        ├── [⏳] 10:42:05 flag_carrier — in progress
        └── [🛑] Kill Switch — "Halt All Actions"
```

### 6.2 WebSocket Events ที่ Backend จะ emit

```typescript
type AMSCIEvent =
  | { type: "incident_detected"; incident: Incident }
  | { type: "agents_spawned"; agents: AgentRole[]; incidentId: string }
  | { type: "agent_position"; agentRole: string; position: string; confidence: number }
  | { type: "conflict_detected"; agents: string[]; topic: string }
  | { type: "consensus_reached"; plan: ActionStep[]; debateDurationMs: number }
  | { type: "action_executing"; step: ActionStep }
  | { type: "action_completed"; step: ActionStep; result: string }
  | { type: "incident_resolved"; incidentId: string; postMortem: PostMortem }
  | { type: "strategy_learned"; newRule: string }  // ← ที่น่าทึ่งที่สุด
```

---

## 7. สิ่งที่ทำให้ AMSCI ต่างจาก AutoGPT / CrewAI / LangGraph ทั่วไป

| Feature | AutoGPT | CrewAI | LangGraph | **AMSCI** |
|---------|---------|--------|-----------|-----------|
| Agent spawn dynamically | ✗ | ✗ | ✗ | **✓** |
| Agents debate + disagree | ✗ | Limited | ✗ | **✓ (Socratic Protocol)** |
| Cross-workflow signal fusion | ✗ | ✗ | ✗ | **✓** |
| Zero-shot incident classification | ✗ | ✗ | ✗ | **✓** |
| Strategy memory distillation | ✗ | ✗ | ✗ | **✓** |
| Real-time debate visibility | ✗ | ✗ | ✗ | **✓ (War Room)** |
| Domain: E-Commerce Operations | ✗ | ✗ | ✗ | **✓** |
| Kill switch for safety | ✗ | ✗ | Partial | **✓** |

---

## 8. Demo Script — 5 นาทีที่จะทำให้ทุกคนตกใจ

```
นาทีที่ 0:00
  เปิด "AI Operations Room" — แสดงว่า system running, no active incidents
  "นี่คือระบบที่รัน 24/7 โดยไม่ต้องมีใคร monitor"

นาทีที่ 0:30
  Trigger simulation: simulate Flash Express failure ใน region กรุงเทพเหนือ
  → Watchdog ตรวจพบใน 3 นาที (หรือ demo mode: 5 วินาที)
  → INC-0042 ปรากฏขึ้น: "🔴 CRITICAL: regional_carrier_collapse detected"

นาทีที่ 1:00
  "AI กำลังสร้าง team ของตัวเอง..."
  → "Spawning 4 agents: PolicyExpert, CustomerAdvocate, BudgetGuardian, RiskAnalyst"
  → แต่ละ agent ปรากฏขึ้นใน panel พร้อม typing animation

นาทีที่ 1:30
  "ดูว่า AI debate กัน..."
  → แสดง live debate stream ทีละ agent
  → Conflict detected ปรากฏขึ้น (highlight สีแดง)
  → Arbitrator เริ่มทำงาน progress bar

นาทีที่ 2:00
  "CONSENSUS REACHED in 47 seconds"
  → Action plan ปรากฏขึ้น
  → Execution log เริ่ม: tick... tick... tick...

นาทีที่ 2:30
  เปิด Customer Portal → เห็นว่าลูกค้า 40 คนได้รับ notification แล้ว
  เปิด Admin Portal → เห็น case และ coupon ที่สร้างอัตโนมัติ

นาทีที่ 3:00
  กลับไปที่ War Room
  "INCIDENT RESOLVED"
  Post-mortem ปรากฏขึ้นอัตโนมัติ
  "📚 Strategy Learned: เพิ่ม rule ใหม่ใน knowledge base"

นาทีที่ 4:00
  "ทั้งหมดนี้ ไม่มีใคร trigger เลย ไม่มีใคร approve เลย 
   ระบบทำงานตั้งแต่ detect จนถึง resolve เองทั้งหมด"
```

---

## 9. สิ่งที่ AMSCI แสดงให้เห็นว่าคุณทำอะไรได้ในฐานะ AI Engineer

1. **LangGraph Mastery** — สร้าง dynamic workflow ที่ generate ตอน runtime ไม่ใช่ compile time
2. **Multi-Agent Coordination** — ออกแบบ protocol ที่ agent communicate และ resolve conflict
3. **System Design** — WebSocket + background jobs + relational state management
4. **Domain Knowledge** — เข้าใจ e-commerce operations ลึกพอที่จะ model เป็น AI signals
5. **AI Safety** — Kill switch, confidence scoring, evidence-based decisions
6. **Production Thinking** — Circuit breaker (มีอยู่แล้ว), error recovery (มีอยู่แล้ว), observability

---

## 10. Roadmap การ Implement — แบ่งเป็น Phase

### Phase 1 (2-3 วัน): Foundation
- [ ] `watchdog.py` — Background loop + signal aggregation
- [ ] `incident.py` DB model + migration
- [ ] `incidents.py` API route (REST only ก่อน)
- [ ] Admin Portal: แสดง list of incidents (static)

**Demo ได้:** แสดงว่าระบบ detect incidents เองได้

### Phase 2 (3-4 วัน): Debate Engine
- [ ] `socratic_debate.py` — Core debate protocol
- [ ] `meta_planner.py` — Dynamic agent spawning
- [ ] `debate_positions` + `debate_resolutions` tables
- [ ] WebSocket endpoint: emit debate events
- [ ] Frontend War Room: แสดง live debate stream

**Demo ได้:** แสดง AI debate แบบ real-time

### Phase 3 (2-3 วัน): Execution + Memory
- [ ] `incident_commander.py` — Autonomous execution pipeline
- [ ] `strategy_memory` table
- [ ] Post-mortem generation
- [ ] Kill switch mechanism
- [ ] Full end-to-end test

**Demo ได้:** Full autonomous incident resolution

### Phase 4 (1-2 วัน): Polish
- [ ] Demo simulation mode (fast-forward for presentation)
- [ ] War Room UI animations
- [ ] Metrics dashboard: "Incidents handled autonomously: 42 | Human override needed: 1"

---

## 11. สรุป — ทำไมบริษัทจะอยากได้สิ่งนี้

**ในแง่ธุรกิจ:**
- ลด operational cost: ไม่ต้องมี on-call team 24/7
- ลด MTTR (Mean Time to Resolve): จาก 2-4 ชั่วโมงเหลือ < 5 นาที
- ป้องกัน churn ก่อนลูกค้าเลิกซื้อ
- Audit trail ครบทุก decision พร้อมเหตุผล (compliance-ready)

**ในแง่ AI Engineering:**
- แสดงความเข้าใจ Multi-Agent System ระดับ advanced
- แสดงความสามารถ design protocol (ไม่ใช่แค่ใช้ framework)
- แสดง production thinking (safety, observability, kill switch)
- แสดงว่าเข้าใจ tradeoff ระหว่าง autonomy และ human oversight

**ประโยค 1 ประโยคที่อธิบาย AMSCI:**
> "ระบบที่ทำงานเหมือน SRE team ผู้เชี่ยวชาญหลายคน ที่ถกกันและตัดสินใจเองได้ตลอด 24 ชั่วโมง โดยมี audit trail ครบทุก reasoning step"

---

*ShopEasy AMSCI Specification | 12 พฤษภาคม 2026*
