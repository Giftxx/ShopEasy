"""
Policy management routes — under /ai/policies.

Endpoints:
  GET    /ai/policies                  List all policies
  POST   /ai/policies                  Create policy from plain text
  POST   /ai/policies/upload           Upload PDF / TXT / MD file
  GET    /ai/policies/search           Keyword search across chunks
  GET    /ai/policies/{id}             Get policy + chunks
  GET    /ai/policies/{id}/download    Presigned download URL for source file
  PUT    /ai/policies/{id}             Update content (re-chunks)
  DELETE /ai/policies/{id}             Delete policy + chunks + MinIO file
"""
from __future__ import annotations

import io
import re
import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import policy_rag

router = APIRouter()

POLICIES_BUCKET = "policies"
MAX_FILE_MB = 50


# ─── Request / Response schemas ──────────────────────────────────────────────

class PolicyCreate(BaseModel):
    title: str
    category: str = "general"
    version: str = "v1.0"
    content: str


class PolicyUpdate(BaseModel):
    content: str


class PolicyChunkOut(BaseModel):
    id: str
    chunk_index: int | None
    chunk_text: str | None
    heading: str | None = None
    tags: list[str] | None = None
    page_number: int | None = None

    model_config = {"from_attributes": True}


class PolicyOut(BaseModel):
    id: str
    title: str | None
    category: str | None
    version: str | None
    content: str | None
    status: str | None
    source_filename: str | None = None
    file_size_bytes: int | None = None
    chunk_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class PolicyDetailOut(PolicyOut):
    chunks: list[PolicyChunkOut] = []


class SearchResult(BaseModel):
    policy_id: str
    policy_title: str
    category: str
    chunk_index: int | None
    chunk_text: str
    heading: str = ""
    tags: list[str] = []
    page_number: int | None = None


class DownloadUrlOut(BaseModel):
    url: str
    filename: str


# ─── MinIO helpers ───────────────────────────────────────────────────────────

def _get_minio():
    from minio import Minio
    from app.core.config import get_settings
    s = get_settings()
    return Minio(s.minio_endpoint, access_key=s.minio_access_key, secret_key=s.minio_secret_key, secure=s.minio_use_ssl)


def _ensure_policies_bucket(client) -> None:
    if not client.bucket_exists(POLICIES_BUCKET):
        client.make_bucket(POLICIES_BUCKET)


def _upload_to_minio(client, policy_id: str, filename: str, data: bytes, content_type: str) -> str:
    """Upload bytes to MinIO policies bucket; return object key."""
    _ensure_policies_bucket(client)
    object_key = f"{policy_id}/{filename}"
    client.put_object(
        POLICIES_BUCKET,
        object_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_key


def _clean_filename(title: str, version: str, original_filename: str) -> str:
    """Generate a clean, storage-safe filename: {slug}_{ver}.{ext}

    Example: "Refund Policy" v2.0 refund_policy.pdf → refund_policy_v20.pdf
    """
    ext = ""
    if "." in original_filename:
        ext = "." + original_filename.rsplit(".", 1)[-1].lower()

    # Slugify title: lowercase, keep alphanumerics + spaces, replace spaces with _
    slug = re.sub(r"[^\w\s]", "", title.lower())
    slug = re.sub(r"\s+", "_", slug.strip()).strip("_")
    slug = slug[:50]  # max 50 chars

    # Clean version: v1.0 → v1_0, v2.3.1 → v2_3_1
    ver = re.sub(r"[^\w]", "_", version.lower().strip()).strip("_")

    return f"{slug}_{ver}{ext}"


def _delete_from_minio(object_key: str) -> None:
    try:
        client = _get_minio()
        client.remove_object(POLICIES_BUCKET, object_key)
    except Exception:
        pass  # best-effort


def _presigned_download(object_key: str) -> str:
    from app.core.config import get_settings
    s = get_settings()
    client = _get_minio()
    url = client.presigned_get_object(POLICIES_BUCKET, object_key, expires=timedelta(hours=24))
    # Rewrite internal hostname to public endpoint
    public = s.minio_public_endpoint.strip()
    if public:
        scheme = "https" if s.minio_use_ssl else "http"
        internal = f"{scheme}://{s.minio_endpoint.strip()}"
        url = url.replace(internal, f"{scheme}://{public}", 1)
    return url


# ─── Shared output builder ───────────────────────────────────────────────────

def _build_detail(policy, chunks) -> PolicyDetailOut:
    return PolicyDetailOut(
        id=policy.id,
        title=policy.title,
        category=policy.category,
        version=policy.version,
        content=policy.content,
        status=policy.status,
        source_filename=policy.source_filename,
        file_size_bytes=policy.file_size_bytes,
        chunk_count=len(chunks),
        created_at=policy.created_at.isoformat() if policy.created_at else None,
        updated_at=policy.updated_at.isoformat() if policy.updated_at else None,
        chunks=[
            PolicyChunkOut(
                id=c.id,
                chunk_index=c.chunk_index,
                chunk_text=c.chunk_text,
                heading=c.heading,
                tags=c.tags,
                page_number=c.page_number,
            )
            for c in chunks
        ],
    )


def _policy_out(policy, db) -> PolicyOut:
    chunks = policy_rag.get_policy_chunks(db, policy.id)
    return PolicyOut(
        id=policy.id,
        title=policy.title,
        category=policy.category,
        version=policy.version,
        content=policy.content,
        status=policy.status,
        source_filename=policy.source_filename,
        file_size_bytes=policy.file_size_bytes,
        chunk_count=len(chunks),
        created_at=policy.created_at.isoformat() if policy.created_at else None,
        updated_at=policy.updated_at.isoformat() if policy.updated_at else None,
    )


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/policies", response_model=list[PolicyOut], summary="List all policies")
def list_policies(db: Session = Depends(get_db)) -> list[PolicyOut]:
    return [_policy_out(p, db) for p in policy_rag.list_policies(db)]


@router.post(
    "/policies",
    response_model=PolicyDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a policy from plain text",
)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)) -> PolicyDetailOut:
    policy = policy_rag.create_policy(
        db,
        title=payload.title,
        category=payload.category,
        content=payload.content,
        version=payload.version,
    )
    db.commit()
    return _build_detail(policy, policy_rag.get_policy_chunks(db, policy.id))


@router.post(
    "/policies/upload",
    response_model=PolicyDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF, TXT or MD file as a policy document",
)
async def upload_policy_document(
    file: Annotated[UploadFile, File(description="PDF, TXT or MD file (max 50 MB)")],
    title: Annotated[str, Form()],
    category: Annotated[str, Form()] = "general",
    version: Annotated[str, Form()] = "v1.0",
    db: Session = Depends(get_db),
) -> PolicyDetailOut:
    from app.services.pdf_extractor import extract_sections

    content_bytes = await file.read()

    if len(content_bytes) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_MB} MB limit.")
    if not content_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = file.filename or "upload.txt"
    content_type = file.content_type or "application/octet-stream"

    # Clean storage name: title-slug + version + original extension
    storage_name = _clean_filename(title, version, filename)

    # Generate policy ID up-front so we can use it for MinIO path
    policy_id = f"POL-{uuid.uuid4().hex[:8].upper()}"

    # 1. Store original file in MinIO using the clean filename
    minio_path: str | None = None
    try:
        minio_client = _get_minio()
        minio_path = _upload_to_minio(minio_client, policy_id, storage_name, content_bytes, content_type)
    except Exception as exc:
        # Non-fatal — proceed without file storage
        import logging
        logging.getLogger(__name__).warning("MinIO upload failed: %s", exc)

    # 2. Intelligent extraction with heading/tag detection
    sections = extract_sections(content_bytes, filename)
    if not sections:
        raise HTTPException(status_code=400, detail="Could not extract any text from the file.")

    # 3. Persist policy + structured chunks
    policy = policy_rag.create_policy_from_sections(
        db,
        title=title,
        category=category,
        version=version,
        sections=sections,
        policy_id=policy_id,
        source_file_path=minio_path,
        source_filename=storage_name,  # store the clean name
        file_size_bytes=len(content_bytes),
    )
    db.commit()
    return _build_detail(policy, policy_rag.get_policy_chunks(db, policy.id))


@router.get(
    "/policies/search",
    response_model=list[SearchResult],
    summary="Keyword search policy chunks",
)
def search_policies(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=5, ge=1, le=20),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SearchResult]:
    results = policy_rag.search_policy_chunks(db, query=q, limit=limit, category=category)
    return [SearchResult(**r) for r in results]


@router.get(
    "/policies/{policy_id}/download",
    response_model=DownloadUrlOut,
    summary="Get presigned download URL for the source file",
)
def download_policy_file(policy_id: str, db: Session = Depends(get_db)) -> DownloadUrlOut:
    policy = policy_rag.get_policy(db, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    if not policy.source_file_path:
        raise HTTPException(status_code=404, detail="No source file attached to this policy.")
    try:
        url = _presigned_download(policy.source_file_path)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not generate download URL: {exc}") from exc
    return DownloadUrlOut(url=url, filename=policy.source_filename or "policy_file")


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyDetailOut,
    summary="Get policy detail with chunks",
)
def get_policy(policy_id: str, db: Session = Depends(get_db)) -> PolicyDetailOut:
    policy = policy_rag.get_policy(db, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    return _build_detail(policy, policy_rag.get_policy_chunks(db, policy.id))


@router.put(
    "/policies/{policy_id}",
    response_model=PolicyDetailOut,
    summary="Update policy content and re-chunk",
)
def update_policy(policy_id: str, payload: PolicyUpdate, db: Session = Depends(get_db)) -> PolicyDetailOut:
    policy = policy_rag.get_policy(db, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    policy = policy_rag.update_policy_content(db, policy, payload.content)
    db.commit()
    return _build_detail(policy, policy_rag.get_policy_chunks(db, policy.id))


@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete policy, chunks, and MinIO source file",
)
def delete_policy(policy_id: str, db: Session = Depends(get_db)) -> None:
    policy = policy_rag.get_policy(db, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    # Best-effort MinIO cleanup
    if policy.source_file_path:
        _delete_from_minio(policy.source_file_path)
    policy_rag.delete_policy(db, policy)
    db.commit()


# ─── Qdrant Vector Indexing ──────────────────────────────────────────────────

class IndexResult(BaseModel):
    policy_id: str
    indexed_chunks: int


@router.post(
    "/policies/{policy_id}/index",
    response_model=IndexResult,
    summary="Index policy chunks into Qdrant for vector search",
)
def index_policy(policy_id: str, db: Session = Depends(get_db)) -> IndexResult:
    policy = policy_rag.get_policy(db, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found.")
    count = policy_rag.index_policy_chunks(db, policy_id)
    return IndexResult(policy_id=policy_id, indexed_chunks=count)


@router.post(
    "/policies/index-all",
    response_model=list[IndexResult],
    summary="Index all active policies into Qdrant",
)
def index_all_policies(db: Session = Depends(get_db)) -> list[IndexResult]:
    policies = policy_rag.list_policies(db)
    results = []
    for p in policies:
        count = policy_rag.index_policy_chunks(db, p.id)
        results.append(IndexResult(policy_id=p.id, indexed_chunks=count))
    return results

