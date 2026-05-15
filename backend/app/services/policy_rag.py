"""
Policy RAG service.

Responsibilities:
- Chunk policy text into searchable pieces (~500 chars each)
- Store / delete policies and their chunks (with heading, tags, page_number)
- Store original file reference (MinIO path)
- Keyword search via PostgreSQL ILIKE (no Qdrant needed for MVP)
- Return relevant chunks to agent nodes so the LLM gets real policy text
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.refund import Policy, PolicyChunk

if TYPE_CHECKING:
    from app.services.pdf_extractor import ExtractedSection

CHUNK_SIZE = 500       # characters
CHUNK_OVERLAP = 80    # characters overlap between consecutive chunks

# Sentence boundary pattern: Thai/English sentence endings
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+|(?<=\n)')


# ──────────────────────────────────────────────────────────────────────────────
# Text chunking
# ──────────────────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into semantically-aware overlapping chunks.

    Strategy (in priority order):
    1. Split on paragraph boundaries (blank lines).
    2. If a paragraph is still too long, split on sentence/line boundaries.
    3. Last resort: character split with overlap.

    Adjacent short paragraphs are merged until the chunk_size limit is reached,
    so the LLM always receives complete thoughts rather than mid-sentence fragments.
    """
    text = text.strip()
    if not text:
        return []

    # ── Step 1: paragraph split ──────────────────────────────────────────────
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    units: list[str] = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            units.append(para)
        else:
            # ── Step 2: sentence / line split ────────────────────────────────
            sentences = [s.strip() for s in re.split(r'(?<=[.!?ๆ])\s+|\n', para) if s.strip()]
            buf = ""
            for sent in sentences:
                if len(sent) > chunk_size:
                    # ── Step 3: character split ──────────────────────────────
                    if buf:
                        units.append(buf)
                        buf = ""
                    start = 0
                    while start < len(sent):
                        units.append(sent[start:start + chunk_size])
                        start += chunk_size - overlap
                else:
                    candidate = (buf + " " + sent).strip() if buf else sent
                    if len(candidate) <= chunk_size:
                        buf = candidate
                    else:
                        if buf:
                            units.append(buf)
                        buf = sent
            if buf:
                units.append(buf)

    # ── Merge adjacent short units & build final chunks with overlap ─────────
    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = (current + "\n\n" + unit).strip() if current else unit
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # Start next chunk with overlap from the end of the previous one
            tail = current[-overlap:].strip() if len(current) > overlap else current
            current = (tail + "\n\n" + unit).strip() if tail else unit
    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


# ──────────────────────────────────────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────────────────────────────────────

def create_policy(
    db: Session,
    *,
    title: str,
    category: str,
    content: str,
    version: str = "v1.0",
    policy_id: str | None = None,
    source_file_path: str | None = None,
    source_filename: str | None = None,
    file_size_bytes: int | None = None,
) -> Policy:
    """Create a Policy record + auto-chunk its content."""
    now = datetime.utcnow()
    pid = policy_id or f"POL-{uuid.uuid4().hex[:8].upper()}"

    policy = Policy(
        id=pid,
        title=title,
        category=category,
        version=version,
        content=content,
        status="active",
        source_file_path=source_file_path,
        source_filename=source_filename,
        file_size_bytes=file_size_bytes,
        created_at=now,
        updated_at=now,
    )
    db.add(policy)
    db.flush()

    _create_chunks(db, policy_id=pid, text=content)
    return policy


def create_policy_from_sections(
    db: Session,
    *,
    title: str,
    category: str,
    version: str = "v1.0",
    sections: "list[ExtractedSection]",
    policy_id: str | None = None,
    source_file_path: str | None = None,
    source_filename: str | None = None,
    file_size_bytes: int | None = None,
) -> Policy:
    """
    Create a Policy from structured extracted sections.
    Each section becomes one or more PolicyChunks with heading, tags and page_number.
    """
    from app.services.pdf_extractor import sections_to_full_text

    now = datetime.utcnow()
    pid = policy_id or f"POL-{uuid.uuid4().hex[:8].upper()}"
    full_text = sections_to_full_text(sections)

    policy = Policy(
        id=pid,
        title=title,
        category=category,
        version=version,
        content=full_text,
        status="active",
        source_file_path=source_file_path,
        source_filename=source_filename,
        file_size_bytes=file_size_bytes,
        created_at=now,
        updated_at=now,
    )
    db.add(policy)
    db.flush()

    _create_chunks_from_sections(db, policy_id=pid, sections=sections)
    return policy


def _create_chunks(db: Session, *, policy_id: str, text: str) -> None:
    """Delete existing chunks for the policy and recreate them (plain text, no headings)."""
    _delete_chunks(db, policy_id)

    chunks = _chunk_text(text)
    now = datetime.utcnow()
    for idx, chunk_text in enumerate(chunks):
        db.add(
            PolicyChunk(
                id=f"PCH-{uuid.uuid4().hex[:8].upper()}",
                policy_id=policy_id,
                chunk_index=idx,
                chunk_text=chunk_text,
                heading=None,
                tags=None,
                page_number=None,
                metadata_json={"section": str(idx + 1)},
                created_at=now,
            )
        )
    db.flush()


def _create_chunks_from_sections(
    db: Session,
    *,
    policy_id: str,
    sections: "list[ExtractedSection]",
) -> None:
    """Delete existing chunks and recreate from structured sections."""
    _delete_chunks(db, policy_id)

    now = datetime.utcnow()
    chunk_idx = 0
    for section in sections:
        body = section.text.strip()
        if not body and not section.heading:
            continue

        # Combine heading + body for the chunk text if body is short enough
        if len(body) <= CHUNK_SIZE:
            # Single chunk for this section
            chunk_text = f"{section.heading}\n{body}".strip() if section.heading else body
            db.add(
                PolicyChunk(
                    id=f"PCH-{uuid.uuid4().hex[:8].upper()}",
                    policy_id=policy_id,
                    chunk_index=chunk_idx,
                    chunk_text=chunk_text,
                    heading=section.heading or None,
                    tags=section.tags or None,
                    page_number=section.page_number or None,
                    metadata_json={"section": section.heading or str(chunk_idx + 1)},
                    created_at=now,
                )
            )
            chunk_idx += 1
        else:
            # Split long section bodies into sub-chunks, all carrying the same heading/tags
            sub_chunks = _chunk_text(body)
            for sub_text in sub_chunks:
                chunk_text = f"{section.heading}\n{sub_text}".strip() if section.heading else sub_text
                db.add(
                    PolicyChunk(
                        id=f"PCH-{uuid.uuid4().hex[:8].upper()}",
                        policy_id=policy_id,
                        chunk_index=chunk_idx,
                        chunk_text=chunk_text,
                        heading=section.heading or None,
                        tags=section.tags or None,
                        page_number=section.page_number or None,
                        metadata_json={"section": section.heading or str(chunk_idx + 1)},
                        created_at=now,
                    )
                )
                chunk_idx += 1

    db.flush()


def _delete_chunks(db: Session, policy_id: str) -> None:
    old_chunks = db.scalars(
        select(PolicyChunk).where(PolicyChunk.policy_id == policy_id)
    ).all()
    for c in old_chunks:
        db.delete(c)
    db.flush()


def update_policy_content(db: Session, policy: Policy, content: str) -> Policy:
    """Replace policy content and re-chunk."""
    policy.content = content
    policy.updated_at = datetime.utcnow()
    db.flush()
    _create_chunks(db, policy_id=policy.id, text=content)
    return policy


def delete_policy(db: Session, policy: Policy) -> None:
    """Delete policy and all its chunks."""
    _delete_chunks(db, policy.id)
    db.delete(policy)
    db.flush()


# ──────────────────────────────────────────────────────────────────────────────
# Search
# ──────────────────────────────────────────────────────────────────────────────

def _tokenize_query(query: str) -> list[str]:
    """
    Build a list of search tokens that work for both Thai (no spaces) and
    English. Strips common Thai question particles and short stop-words so
    keyword ILIKE matching can hit policy chunks.
    """
    if not query:
        return []

    # Common particles / stop-words to strip from the query.
    stopwords = [
        "นโยบาย", "เกี่ยวกับ", "อะไร", "ยังไง", "เป็นยังไง", "เป็นอย่างไร",
        "อย่างไร", "ไหม", "มั้ย", "คือ", "ของ", "เรา", "ฉัน", "ผม", "ครับ",
        "ค่ะ", "นะ", "หน่อย", "ช่วย", "ขอ", "ดู", "บอก", "ที", "ที่",
        "what", "is", "the", "a", "an", "your", "policy", "policies", "tell",
        "me", "about", "how", "do", "i", "can",
    ]

    tokens: set[str] = set()

    # 1) Whitespace split (covers English + mixed messages).
    for w in query.split():
        w = w.strip().lower()
        if len(w) >= 2 and w not in stopwords:
            tokens.add(w)

    # 2) Strip stop-words from the raw string and keep what remains as tokens.
    cleaned = query
    for sw in stopwords:
        cleaned = cleaned.replace(sw, " ")
    for w in cleaned.split():
        w = w.strip()
        if len(w) >= 2:
            tokens.add(w)

    # 3) Also try the original query as a whole (covers exact phrases).
    raw = query.strip()
    if raw:
        tokens.add(raw)

    return list(tokens)


def search_policy_chunks(
    db: Session,
    query: str,
    limit: int = 5,
    category: str | None = None,
) -> list[dict]:
    """
    Keyword search across policy_chunks.chunk_text and policies.title.
    Returns list of dicts: policy_id, policy_title, category,
    chunk_index, chunk_text, heading, tags, page_number.
    """
    if not query or not query.strip():
        return []

    words = _tokenize_query(query)
    if not words:
        return []

    conditions = []
    for word in words:
        pattern = f"%{word}%"
        conditions.append(PolicyChunk.chunk_text.ilike(pattern))
        conditions.append(PolicyChunk.heading.ilike(pattern))
        conditions.append(Policy.title.ilike(pattern))

    stmt = (
        select(PolicyChunk)
        .join(Policy, PolicyChunk.policy_id == Policy.id)
        .where(Policy.status == "active")
        .where(or_(*conditions))
    )
    if category:
        stmt = stmt.where(Policy.category == category)

    stmt = stmt.limit(limit)

    chunks = db.scalars(stmt).all()

    results = []
    for chunk in chunks:
        policy = db.get(Policy, chunk.policy_id)
        if policy:
            results.append(
                {
                    "policy_id": chunk.policy_id,
                    "policy_title": policy.title or "",
                    "category": policy.category or "",
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text or "",
                    "heading": chunk.heading or "",
                    "tags": chunk.tags or [],
                    "page_number": chunk.page_number,
                }
            )
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Qdrant Vector Search (enhanced RAG)
# ──────────────────────────────────────────────────────────────────────────────

_COLLECTION_NAME = "policy_chunks"
_VECTOR_SIZE = 1024  # bge-m3 output dimension


def _get_qdrant_client():
    """Lazy-load Qdrant client. Returns None if unavailable."""
    try:
        from qdrant_client import QdrantClient
        from app.core.config import get_settings
        settings = get_settings()
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=5)
        # Quick health check
        client.get_collections()
        return client
    except Exception:
        return None


def _embed_text(text: str) -> list[float] | None:
    """Embed text using Ollama bge-m3 model. Returns None on failure."""
    try:
        import httpx
        from app.core.config import get_settings
        settings = get_settings()
        base_url = (settings.ollama_base_url or "http://host.docker.internal:11434/v1").replace("/v1", "")
        resp = httpx.post(
            f"{base_url}/api/embeddings",
            json={"model": "bge-m3", "prompt": text},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json().get("embedding")
    except Exception:
        return None


def ensure_qdrant_collection():
    """Create Qdrant collection if it doesn't exist."""
    client = _get_qdrant_client()
    if client is None:
        return False
    try:
        from qdrant_client.models import Distance, VectorParams
        collections = [c.name for c in client.get_collections().collections]
        if _COLLECTION_NAME not in collections:
            client.create_collection(
                collection_name=_COLLECTION_NAME,
                vectors_config=VectorParams(size=_VECTOR_SIZE, distance=Distance.COSINE),
            )
        return True
    except Exception:
        return False


def index_policy_chunks(db: Session, policy_id: str) -> int:
    """Index all chunks of a policy into Qdrant. Returns number of indexed chunks."""
    client = _get_qdrant_client()
    if client is None:
        return 0

    ensure_qdrant_collection()

    chunks = db.scalars(
        select(PolicyChunk).where(PolicyChunk.policy_id == policy_id)
    ).all()
    if not chunks:
        return 0

    from qdrant_client.models import PointStruct

    points = []
    for chunk in chunks:
        embedding = _embed_text(chunk.chunk_text or "")
        if embedding is None:
            continue
        # Use a stable numeric ID from the chunk ID hash
        point_id = abs(hash(chunk.id)) % (2**63)
        points.append(PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "chunk_id": chunk.id,
                "policy_id": chunk.policy_id,
                "chunk_text": chunk.chunk_text or "",
                "heading": chunk.heading or "",
                "chunk_index": chunk.chunk_index,
                "tags": chunk.tags or [],
                "page_number": chunk.page_number,
            },
        ))

    if points:
        client.upsert(collection_name=_COLLECTION_NAME, points=points)

    return len(points)


def search_policy_vector(query: str, limit: int = 5) -> list[dict]:
    """Search policy chunks using Qdrant vector similarity."""
    client = _get_qdrant_client()
    if client is None:
        return []

    query_embedding = _embed_text(query)
    if query_embedding is None:
        return []

    try:
        response = client.query_points(
            collection_name=_COLLECTION_NAME,
            query=query_embedding,
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "policy_id": hit.payload.get("policy_id", ""),
                "policy_title": "",  # will be enriched by caller
                "category": "",
                "chunk_index": hit.payload.get("chunk_index", 0),
                "chunk_text": hit.payload.get("chunk_text", ""),
                "heading": hit.payload.get("heading", ""),
                "tags": hit.payload.get("tags", []),
                "page_number": hit.payload.get("page_number"),
                "score": hit.score,
            }
            for hit in response.points
        ]
    except Exception:
        return []


def search_policy_hybrid(
    db: Session, query: str, limit: int = 5, category: str | None = None,
) -> list[dict]:
    """
    Hybrid search: try Qdrant vector search first, fall back to keyword search.
    Enriches vector results with policy titles from DB.
    """
    # Try vector search first
    vector_results = search_policy_vector(query, limit=limit)
    if vector_results:
        # Enrich with policy titles
        for r in vector_results:
            policy = db.get(Policy, r["policy_id"])
            if policy:
                r["policy_title"] = policy.title or ""
                r["category"] = policy.category or ""
        if category:
            vector_results = [r for r in vector_results if r["category"] == category]
        results = vector_results[:limit]
    else:
        # Fallback to keyword search
        results = search_policy_chunks(db, query=query, limit=limit, category=category)

    # Deduplicate by (policy_id, chunk_index) so the same DB row is never
    # returned twice even when vector + keyword overlap.
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for r in results:
        key = (r.get("policy_id", ""), r.get("chunk_index", -1))
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


# ──────────────────────────────────────────────────────────────────────────────
# Accessors
# ──────────────────────────────────────────────────────────────────────────────

def list_policies(db: Session) -> list[Policy]:
    return list(db.scalars(select(Policy).order_by(Policy.created_at)).all())


def get_policy(db: Session, policy_id: str) -> Policy | None:
    return db.get(Policy, policy_id)


def get_policy_chunks(db: Session, policy_id: str) -> list[PolicyChunk]:
    return list(
        db.scalars(
            select(PolicyChunk)
            .where(PolicyChunk.policy_id == policy_id)
            .order_by(PolicyChunk.chunk_index)
        ).all()
    )
