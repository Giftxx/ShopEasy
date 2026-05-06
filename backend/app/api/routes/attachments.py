import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
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
