from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import settings
from app.db.session import get_session
from app.processors.order_processor import OrderProcessor
from app.schemas.shopify import ShopifyWebhookOrderCreate
from app.schemas.webhook import WebhookAccepted
from app.utils.security import verify_shopify_hmac

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/orders/create", response_model=WebhookAccepted, status_code=status.HTTP_202_ACCEPTED)
async def orders_create(request: Request, x_shopify_hmac_sha256: str | None = Header(default=None), session: AsyncSession = Depends(get_session)) -> WebhookAccepted:
    """Handle Shopify order/create webhook, generate ORDERS02, and upload it to SFTP."""
    raw_body = await request.body()
    if not verify_shopify_hmac(raw_body, settings.shopify_webhook_secret, x_shopify_hmac_sha256):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Shopify HMAC")
    payload = ShopifyWebhookOrderCreate.model_validate_json(raw_body)
    order_gid = payload.order_gid
    if not order_gid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing Shopify order id")
    correlation_id = await OrderProcessor(session).process_order_created(order_gid)
    return WebhookAccepted(status="accepted", correlation_id=correlation_id)
