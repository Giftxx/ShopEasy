"""Shopify Webhook handlers — receives events from Shopify store."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_shopify_webhook(body: bytes, hmac_header: str) -> bool:
    """Verify Shopify webhook HMAC-SHA256 signature."""
    settings = get_settings()
    secret = settings.shopify_webhook_secret
    if not secret:
        logger.warning("SHOPIFY_WEBHOOK_SECRET not configured — rejecting webhook")
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    computed = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(computed, hmac_header)


@router.post("/shopify/orders/create")
async def shopify_order_create(
    request: Request,
    db: Session = Depends(get_db),
    x_shopify_hmac_sha256: str = Header(...),
):
    """Handle Shopify order creation webhook."""
    body = await request.body()
    if not _verify_shopify_webhook(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid HMAC")

    payload = json.loads(body)
    shopify_order_id = str(payload.get("id", ""))

    # Idempotency check
    from app.db.models import Order
    existing = db.query(Order).filter(Order.shopify_order_id == shopify_order_id).first()
    if existing:
        return {"status": "already_processed"}

    # Map Shopify order → ShopEasy Order
    logger.info("Received Shopify order: %s", shopify_order_id)
    # TODO: Create Order + OrderItems from Shopify payload
    # For now, log and acknowledge
    return {"status": "received"}


@router.post("/shopify/fulfillments/update")
async def shopify_fulfillment_update(
    request: Request,
    db: Session = Depends(get_db),
    x_shopify_hmac_sha256: str = Header(...),
):
    """Handle Shopify fulfillment status update webhook."""
    body = await request.body()
    if not _verify_shopify_webhook(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid HMAC")

    payload = json.loads(body)
    fulfillment_id = str(payload.get("id", ""))
    status = payload.get("status", "")

    logger.info("Shopify fulfillment update: %s → %s", fulfillment_id, status)

    # Find shipment by shopify_fulfillment_id
    from app.db.models import Shipment
    shipment = db.query(Shipment).filter(
        Shipment.shopify_fulfillment_id == fulfillment_id
    ).first()

    if shipment:
        # Map Shopify status → ShopEasy status
        status_map = {
            "pending": "pending",
            "open": "in_transit",
            "success": "delivered",
            "cancelled": "cancelled",
            "error": "delayed",
            "failure": "delayed",
        }
        new_status = status_map.get(status, shipment.shipment_status)
        shipment.shipment_status = new_status
        db.commit()

        # If delayed, trigger proactive workflow
        if new_status == "delayed":
            from app.schemas.proactive import ProactiveEventRequest
            from app.services.workflow_03_proactive import handle_proactive_event
            try:
                handle_proactive_event(
                    db,
                    ProactiveEventRequest(
                        shipment_id=shipment.id,
                        event_type="shopify_fulfillment_delayed",
                    ),
                )
            except Exception as e:
                logger.error("Proactive workflow failed: %s", e)

    return {"status": "received"}


@router.post("/shopify/refunds/create")
async def shopify_refund_create(
    request: Request,
    db: Session = Depends(get_db),
    x_shopify_hmac_sha256: str = Header(...),
):
    """Handle Shopify refund creation webhook."""
    body = await request.body()
    if not _verify_shopify_webhook(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid HMAC")

    payload = json.loads(body)
    shopify_order_id = str(payload.get("order_id", ""))

    logger.info("Shopify refund for order: %s", shopify_order_id)

    # Find order by shopify_order_id
    from app.db.models import Order
    order = db.query(Order).filter(Order.shopify_order_id == shopify_order_id).first()

    if order:
        # Trigger refund workflow
        from app.schemas.chat import ChatRequest
        from app.services.workflow_02_refund import handle_refund_chat
        try:
            handle_refund_chat(
                db,
                ChatRequest(
                    conversation_id=f"shopify-refund-{shopify_order_id}",
                    customer_id=order.customer_id,
                    message=f"Shopify refund created for order {order.id}",
                    target_order_id=order.id,
                ),
            )
        except Exception as e:
            logger.error("Refund workflow failed: %s", e)

    return {"status": "received"}
