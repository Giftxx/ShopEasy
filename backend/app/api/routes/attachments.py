import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories import business as business_repo
from app.schemas.attachment import (
    ConfirmUploadRequest,
    PresignRequest,
    PresignResponse,
)
from app.schemas.business import AttachmentResponse
from app.storage import minio

router = APIRouter()


@router.post(
    "/presign-upload",
    response_model=PresignResponse,
    summary="Get Presigned URL for file upload",
)
def get_presigned_upload_url(
    data: PresignRequest,
):
    """
    Generates a unique object name and a presigned URL for the client to upload a file directly to MinIO.
    """
    file_ext = data.file_name.split(".")[-1]
    object_name = (
        f"refund_request/{data.refund_request_id}/{data.evidence_group}/"
        f"{uuid.uuid4()}.{file_ext}"
    )

    try:
        upload_url = minio.generate_presigned_upload_url(object_name)
        return PresignResponse(upload_url=upload_url, object_name=object_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not generate presigned URL: {e}",
        )


@router.post(
    "/confirm-upload",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm a file upload",
)
def confirm_upload(
    data: ConfirmUploadRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Confirms that a file has been uploaded to MinIO and creates a corresponding record in the database.
    """
    # Optional: Verify object exists in MinIO before creating DB record
    # try:
    #     minio.minio_client.stat_object(minio.settings.minio_bucket_name, data.object_name)
    # except Exception:
    #     raise HTTPException(status_code=404, detail="Object not found in storage")

    try:
        attachment = business_repo.create_attachment(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return AttachmentResponse(
        id=attachment.id,
        evidence_group=attachment.evidence_group,
        description=attachment.description,
        file_name=attachment.file_name,
        mime_type=attachment.mime_type,
        object_key=attachment.object_key,
        upload_status=attachment.upload_status,
        created_at=attachment.created_at,
    )


@router.post(
    "/upload-direct",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file directly through the backend to MinIO",
)
async def upload_direct(
    file: Annotated[UploadFile, File(description="The file to upload")],
    refund_request_id: Annotated[str, Form()],
    evidence_group: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> AttachmentResponse:
    """
    Upload a file to MinIO via the backend (no CORS/presign needed).
    Reads the file, streams it to MinIO, then creates a DB record.
    """
    minio.ensure_bucket_exists()

    file_ext = (file.filename or "file").rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
    object_name = (
        f"refund_request/{refund_request_id}/{evidence_group}/"
        f"{uuid.uuid4()}.{file_ext}"
    )

    content = await file.read()
    file_size = len(content)
    content_type = file.content_type or "application/octet-stream"

    try:
        minio.minio_client.put_object(
            bucket_name=minio.settings.minio_bucket_name,
            object_name=object_name,
            data=io.BytesIO(content),
            length=file_size,
            content_type=content_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {exc}",
        ) from exc

    try:
        attachment = business_repo.create_attachment(
            db,
            ConfirmUploadRequest(
                object_name=object_name,
                file_name=file.filename or object_name,
                content_type=content_type,
                refund_request_id=refund_request_id,
                evidence_group=evidence_group,
                description=description or file.filename,
                file_size_bytes=file_size,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return AttachmentResponse(
        id=attachment.id,
        evidence_group=attachment.evidence_group,
        description=attachment.description,
        file_name=attachment.file_name,
        mime_type=attachment.mime_type,
        object_key=attachment.object_key,
        upload_status=attachment.upload_status,
        created_at=attachment.created_at,
    )


@router.get(
    "/{attachment_id}/download",
    summary="Proxy download of an attachment directly from MinIO",
)
async def download_attachment_proxy(
    attachment_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Streams the file from MinIO directly to the browser.
    Works without CORS or presigned URL configuration.
    """
    from fastapi.responses import StreamingResponse

    attachment = business_repo.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    try:
        response = minio.minio_client.get_object(
            bucket_name=minio.settings.minio_bucket_name,
            object_name=attachment.object_key,
        )
        content_type = attachment.mime_type or "application/octet-stream"
        filename = attachment.file_name or attachment_id

        def iter_content():
            try:
                for chunk in response.stream(32 * 1024):
                    yield chunk
            finally:
                response.close()
                response.release_conn()

        return StreamingResponse(
            iter_content(),
            media_type=content_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found in storage: {exc}",
        ) from exc


@router.get(
    "/{attachment_id}/presign-download",
    response_model=PresignResponse,
    summary="Get Presigned URL for file download",
)
def get_presigned_download_url(
    attachment_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Generates a presigned URL for the client to download a file directly from MinIO.
    """
    attachment = business_repo.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    try:
        download_url = minio.generate_presigned_download_url(attachment.object_key)
        return PresignResponse(upload_url=download_url, object_name=attachment.object_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not generate presigned URL: {e}",
        )


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an attachment",
)
def delete_attachment(
    attachment_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Deletes an attachment record from the database and the corresponding file from MinIO.
    """
    attachment = business_repo.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    try:
        minio.remove_object(attachment.object_key)
    except Exception as e:
        # Log the error but don't fail the request if the object is already gone
        print(f"Could not remove object from MinIO: {e}")

    business_repo.delete_attachment(db, attachment_id)
    return None
