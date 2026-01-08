from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
