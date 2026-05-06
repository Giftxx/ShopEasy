from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.attachments import router as attachments_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.customer import router as customer_router
from app.api.routes.health import router as health_router
from app.api.routes.observability import router as observability_router
from app.api.routes.proactive import router as proactive_router


api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(customer_router, prefix="/data", tags=["data"])
api_router.include_router(attachments_router, prefix="/attachments", tags=["attachments"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(observability_router, prefix="/ai", tags=["ai-control"])
api_router.include_router(proactive_router, prefix="/events", tags=["events"])
