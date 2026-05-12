from fastapi.testclient import TestClient
from app.main import app
from app.processors import order_processor


def test_health_endpoint():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_orders_create_webhook_accepts_order(monkeypatch):
    async def fake_process(self, order_gid, correlation_id=None):
        assert order_gid == "gid://shopify/Order/123"
        return "corr"
    monkeypatch.setattr(order_processor.OrderProcessor, "process_order_created", fake_process)
    with TestClient(app) as client:
        response = client.post("/webhooks/orders/create", json={"id": 123})
    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "correlation_id": "corr"}
