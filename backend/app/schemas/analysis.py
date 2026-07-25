from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AnalysisResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    analysis_type: str
    result_json: dict[str, Any]
    created_at: datetime
