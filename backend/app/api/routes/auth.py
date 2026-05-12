from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
    _GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    _GOOGLE_AUTH_AVAILABLE = False

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.db.models import Customer, User
from app.repositories.business import get_user_by_email, get_user_by_username
from app.schemas.auth import GoogleLoginRequest, LoginRequest, LoginResponse, MockLoginRequest, MockLoginResponse
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


@router.post("/google", response_model=LoginResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    if not _GOOGLE_AUTH_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="google-auth package is not installed on this server.")
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google login is not configured on this server.")

    try:
        idinfo = google_id_token.verify_oauth2_token(  # type: ignore[union-attr]
            payload.credential,
            google_requests.Request(),  # type: ignore[union-attr]
            settings.google_client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token.") from exc

    email: str = idinfo["email"]
    name: str = idinfo.get("name", email.split("@")[0])

    user = get_user_by_email(db, email=email)

    if user is None:
        user_id = str(uuid4())
        user = User(
            id=user_id,
            name=name,
            email=email,
            role="customer",
            status="active",
            hashed_password=None,
        )
        db.add(user)
        db.flush()

        customer = Customer(
            id=f"CUST-{uuid4().hex[:8].upper()}",
            user_id=user.id,
            name=name,
            email=email,
        )
        db.add(customer)
        db.commit()
        db.refresh(user)

    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")

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
