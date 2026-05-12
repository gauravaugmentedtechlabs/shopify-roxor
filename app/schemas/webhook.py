from pydantic import BaseModel

class WebhookAccepted(BaseModel):
    status: str
    correlation_id: str
