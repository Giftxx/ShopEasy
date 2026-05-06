from pydantic import BaseModel, Field


class PresignRequest(BaseModel):
    file_name: str = Field(..., description="The name of the file to be uploaded.")
    content_type: str = Field(..., description="The MIME type of the file.")
    refund_request_id: str = Field(..., description="The ID of the refund request this attachment belongs to.")
    evidence_group: str = Field("other", description="The category of the evidence.")


class PresignResponse(BaseModel):
    upload_url: str = Field(..., description="The presigned URL for uploading the file.")
    object_name: str = Field(..., description="The generated object name for the file in the storage.")


class ConfirmUploadRequest(BaseModel):
    object_name: str = Field(..., description="The object name of the uploaded file.")
    file_name: str = Field(..., description="The original name of the file.")
    content_type: str = Field(..., description="The MIME type of the file.")
    refund_request_id: str = Field(..., description="The ID of the refund request this attachment belongs to.")
    evidence_group: str = Field(..., description="The category of the evidence.")
    description: str | None = None
    file_size_bytes: int | None = None
