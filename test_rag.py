from app.services.policy_rag import search_policy_hybrid, search_policy_vector
from app.db.session import SessionLocal

db = SessionLocal()

# Test 1: keyword search (exact words)
print("=== Test 1: Keyword search (คืนเงิน) ===")
r1 = search_policy_hybrid(db, query="คืนเงิน")
print(f"Results: {len(r1)}")
for r in r1[:2]:
    title = r.get("policy_title", "")
    score = r.get("score", "N/A")
    text = r.get("chunk_text", "")[:100]
    print(f"  [{title}] score={score}")
    print(f"    {text}...")

print()

# Test 2: semantic search (no exact keywords from policy)
print("=== Test 2: Semantic (ถ้าสินค้าเสียหายต้องทำยังไง) ===")
r2 = search_policy_hybrid(db, query="ถ้าสินค้าเสียหายต้องทำยังไง")
print(f"Results: {len(r2)}")
for r in r2[:2]:
    title = r.get("policy_title", "")
    score = r.get("score", "N/A")
    text = r.get("chunk_text", "")[:100]
    print(f"  [{title}] score={score}")
    print(f"    {text}...")

print()

# Test 3: very indirect question
print("=== Test 3: Indirect (อยากได้เงินคืนแต่ไม่รู้ต้องทำอะไร) ===")
r3 = search_policy_hybrid(db, query="อยากได้เงินคืนแต่ไม่รู้ต้องทำอะไร")
print(f"Results: {len(r3)}")
for r in r3[:2]:
    title = r.get("policy_title", "")
    score = r.get("score", "N/A")
    text = r.get("chunk_text", "")[:100]
    print(f"  [{title}] score={score}")
    print(f"    {text}...")

print()

# Test 4: Check which method was used
print("=== Test 4: Vector-only search ===")
r4 = search_policy_vector("นโยบายการคืนสินค้า")
print(f"Vector results: {len(r4)}")
if r4:
    print("  -> Qdrant + bge-m3 is WORKING")
else:
    print("  -> Qdrant/bge-m3 NOT available, using keyword fallback only")

db.close()
