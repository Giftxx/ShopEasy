"""Test that AI chat can access all customer data."""
import requests
import json
import sys

BASE = "http://localhost:8000"

# Login
r = requests.post(f"{BASE}/api/v1/auth/login", json={
    "email": "customer_demo@shopeasy.local",
    "password": "demo1234"
})
data = r.json()
token = data["access_token"]
cid = data["customer_id"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Logged in as {cid}")

# Test questions
questions = [
    "ฉันชื่ออะไร",
    "ฉันมีออเดอร์อะไรบ้าง",
    "นโยบายคืนเงินเป็นยังไง",
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"{'='*60}")
    try:
        r2 = requests.post(f"{BASE}/api/v1/chat", json={
            "message": q,
            "customer_id": cid,
            "conversation_id": f"test-ctx-{hash(q) % 10000}",
        }, headers=headers, timeout=120)
        
        if r2.status_code == 200:
            d = r2.json()
            reply = d.get("response_text", "")
            wf = d.get("workflow_name", "")
            intent = d.get("intent", "")
            print(f"Workflow: {wf} | Intent: {intent}")
            print(f"Reply: {reply[:400]}")
        else:
            print(f"ERROR {r2.status_code}: {r2.text[:200]}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

print("\n\nDone!")
