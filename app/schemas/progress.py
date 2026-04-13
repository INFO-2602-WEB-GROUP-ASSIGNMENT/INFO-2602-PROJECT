from pydantic import BaseModel
from typing import Any, Mapping


class ProgressSaveRequest(BaseModel):
    logs: Mapping[str, Any]
