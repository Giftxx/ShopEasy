from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, verify_password
from app.db.models import User
from app.repositories.business import get_user_by_email, get_user_by_username
from app.schemas.auth import LoginRequest, LoginResponse, MockLoginRequest, MockLoginResponse
from app.schemas.business import UserResponse

router = APIRouter()

# --- Role display name used in JWT claims ---
_ROLE_MAP_DB_TO_FRONTEND: dict[str, str] = {
    "customer": "customer",
    "admin": "admin",
    "ai_control": "ai-engineer",
}

_MOCK_USERS: dict[str, str] = {
    "customer": "customer_demo@shopeasy.local",
    "admin": "admin_demo@shopeasy.local",
    "ai_control": "ai_system_admin@shopeasy.local",
}


def _build_token(user: User) -> tuple[str, str | None]:
    """Build JWT and extract customer_id (if any)."""
    customer_id: str | None = None
    if user.customer_profile:
        customer_id = user.customer_profile.id

    token_data: dict = {"sub": user.id, "role": user.role}
    if customer_id:
        token_data["customer_id"] = customer_id

    return create_access_token(data=token_data), customer_id


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = get_user_by_email(db, email=payload.email)
    if user is None or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    access_token, customer_id = _build_token(user)
    return LoginResponse(
        user=UserResponse.from_orm(user),
        access_token=access_token,
        customer_id=customer_id,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_orm(current_user)


# --- Kept for backward compatibility / dev convenience ---
@router.post("/mock-login", response_model=MockLoginResponse)
def mock_login(payload: MockLoginRequest, db: Session = Depends(get_db)) -> MockLoginResponse:
    email = _MOCK_USERS.get(payload.role)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    user = get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=500, detail=f"Demo user for role '{payload.role}' not found. Please seed the database.")

    access_token, _ = _build_token(user)
    return MockLoginResponse(user=UserResponse.from_orm(user), access_token=access_token)
