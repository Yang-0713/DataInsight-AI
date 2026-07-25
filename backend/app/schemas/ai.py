from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AIHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AIChatRequest(BaseModel):
    dataset_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=4000)
    history: list[AIHistoryMessage] = Field(default_factory=list, max_length=30)


class AIChatResponse(BaseModel):
    result_id: int
    dataset_id: int
    answer: str
    provider: str
    model: str
    created_at: datetime


class AIStatusResponse(BaseModel):
    configured: bool
    provider: str
    model: str
    api_mode: str


class AIReportResponse(BaseModel):
    id: int
    dataset_id: int
    title: str
    summary: str
    findings: list[str]
    possible_problems: list[str]
    recommendations: list[str]
    download_url: str
    provider: str
    model: str
    created_at: datetime
