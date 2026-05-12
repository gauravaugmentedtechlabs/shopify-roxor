from typing import Any
from pydantic import BaseModel

class RetryPayload(BaseModel):
    operation_type: str
    payload: dict[str, Any]
    correlation_id: str
