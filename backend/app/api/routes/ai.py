from fastapi import APIRouter, HTTPException, status

from app.ai.provider import AIProviderError
from app.api.dependencies import (
    AIProviderDependency,
    CurrentUser,
    DatabaseSession,
    DatasetStorage,
)
from app.core.config import get_settings
from app.schemas.ai import AIChatRequest, AIChatResponse, AIStatusResponse
from app.services.ai_analysis import run_ai_chat, stable_safety_identifier
from app.services.analysis import AnalysisSourceError
from app.services.dataset import get_user_dataset

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status(current_user: CurrentUser) -> AIStatusResponse:
    del current_user
    settings = get_settings()
    return AIStatusResponse(
        configured=settings.ai_configured,
        provider="openai-compatible",
        model=settings.openai_model,
        api_mode=settings.openai_api_mode,
    )


@router.post("/chat", response_model=AIChatResponse)
def chat_with_data(
    request: AIChatRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
    storage_root: DatasetStorage,
    provider: AIProviderDependency,
) -> AIChatResponse:
    dataset = get_user_dataset(database, request.dataset_id, current_user.id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在",
        )
    settings = get_settings()
    try:
        result, completion = run_ai_chat(
            database=database,
            dataset=dataset,
            storage_root=storage_root,
            provider=provider,
            request=request,
            max_history_messages=settings.ai_max_history_messages,
            safety_identifier=stable_safety_identifier(
                current_user.id,
                settings.jwt_secret_key.get_secret_value(),
            ),
        )
    except AnalysisSourceError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except AIProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return AIChatResponse(
        result_id=result.id,
        dataset_id=dataset.id,
        answer=completion.text,
        provider=completion.provider,
        model=completion.model,
        created_at=result.created_at,
    )
