from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.business import get_user_by_username
from app.schemas.auth import MockLoginRequest, MockLoginResponse
from app.schemas.business import UserResponse

router = APIRouter()

MOCK_USERS = {
    "customer": "customer_demo",
    "admin": "admin_demo",
    "ai_control": "ai_system_admin",
}


@router.post("/mock-login", response_model=MockLoginResponse)
def mock_login(payload: MockLoginRequest, db: Session = Depends(get_db)) -> MockLoginResponse:
    username = MOCK_USERS.get(payload.role)
    if not username:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    user = get_user_by_username(db, username=username)
    if not user:
        # This is a fallback for seeding issues, in a real app this would be a 404
        raise HTTPException(status_code=500, detail=f"Mock user '{username}' not found in database. Please seed the database.")

    user_response = UserResponse.from_orm(user)
    return MockLoginResponse(
        user=user_response,
        access_token=f"mock_token_for_{user.role}_{user.id}",
    )


@router.get("/me", response_model=UserResponse)
def read_current_user(db: Session = Depends(get_db)) -> UserResponse:
    # In a real app, this would come from a dependency that decodes a JWT
    # For now, we'll return the default customer user
    username = MOCK_USERS.get("customer")
    user = get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=500, detail=f"Mock user '{username}' not found in database. Please seed the database.")

    return UserResponse.from_orm(user)
