from fastapi import FastAPI
from app.api import admin_router, health_router, webhook_router
from app.config.logging import configure_logging
from app.config.settings import settings
from app.workers.lifecycle import lifespan

configure_logging(settings.log_level)

app = FastAPI(title="Shopify Roxor ERP Middleware", version="1.0.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(admin_router)
