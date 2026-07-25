from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    rows: int
    columns: int
    created_at: datetime
