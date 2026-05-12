import asyncio
from typing import Any
from uuid import uuid4
import httpx
from app.config.logging import logger
from app.config.settings import settings
from app.utils.exceptions import ShopifyApiError

log = logger(__name__)

class ShopifyGraphQLClient:
    """Async Shopify Admin GraphQL client with retry and rate-limit handling."""
    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._external_client = http_client is not None
        self._client = http_client or httpx.AsyncClient(timeout=30)

    async def close(self) -> None:
        if not self._external_client:
            await self._client.aclose()

    async def execute(self, query: str, variables: dict[str, Any] | None = None, retries: int = 3) -> dict[str, Any]:
        headers = {"X-Shopify-Access-Token": settings.shopify_access_token, "Content-Type": "application/json"}
        payload = {"query": query, "variables": variables or {}}
        for attempt in range(retries + 1):
            try:
                response = await self._client.post(settings.shopify_graphql_url, headers=headers, json=payload)
            except httpx.HTTPError as exc:
                if attempt >= retries:
                    raise ShopifyApiError(f"Shopify request failed: {exc}") from exc
                await asyncio.sleep(2 ** attempt)
                continue
            if response.status_code == 429 and attempt < retries:
                retry_after = float(response.headers.get("Retry-After", "1"))
                log.warning("shopify_rate_limited", retry_after=retry_after, attempt=attempt)
                await asyncio.sleep(retry_after)
                continue
            if response.status_code in {500, 502, 503, 504} and attempt < retries:
                await asyncio.sleep(2 ** attempt)
                continue
            if response.status_code >= 400:
                raise ShopifyApiError(f"Shopify HTTP {response.status_code}: {response.text[:500]}")
            body = response.json()
            if body.get("errors"):
                raise ShopifyApiError(f"Shopify GraphQL errors: {body['errors']}")
            log.info("shopify_graphql_success", cost=body.get("extensions", {}).get("cost"))
            return body["data"]
        raise ShopifyApiError("Shopify retries exhausted")

    @staticmethod
    def idempotency_key() -> str:
        return str(uuid4())
