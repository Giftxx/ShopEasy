from pydantic import BaseModel, Field
from app.schemas.business import UserResponse


class MockLoginRequest(BaseModel):
    role: str = Field(..., description="Role to simulate login for: customer, admin, or ai_control")


class MockLoginResponse(BaseModel):
    user: UserResponse
    access_token: str
