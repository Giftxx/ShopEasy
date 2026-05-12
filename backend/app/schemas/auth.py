from pydantic import BaseModel, EmailStr, Field

from app.schemas.business import UserResponse


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    customer_id: str | None = None


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., description="Google ID token from Google Identity Services")


# kept for backward-compat during transition
class MockLoginRequest(BaseModel):
    role: str = Field(..., description="Role: customer, admin, or ai_control")


class MockLoginResponse(BaseModel):
    user: UserResponse
    access_token: str
