from app.services.policy_rag import _get_qdrant_client, _embed_text

client = _get_qdrant_client()

# Try direct vector search
query = "นโยบายการคืนสินค้า"
embedding = _embed_text(query)
print(f"Query embedding dim: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")

# Search directly
results = client.search(
    collection_name="policy_chunks",
    query_vector=embedding,
    limit=3,
)
print(f"Search results: {len(results)}")
for hit in results:
    text = hit.payload.get("chunk_text", "")[:80]
    print(f"  score={hit.score:.4f} | {text}")

print()

# Check what's stored in the collection
from qdrant_client.models import ScrollRequest
scroll_result = client.scroll(
    collection_name="policy_chunks",
    limit=3,
    with_vectors=True,
)
points = scroll_result[0]
print(f"Sample stored point vector dim: {len(points[0].vector) if points else 'empty'}")
if points:
    print(f"Sample stored first 5: {points[0].vector[:5]}")
    print(f"Sample text: {points[0].payload.get('chunk_text', '')[:80]}")
