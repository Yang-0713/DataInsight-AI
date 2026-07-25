from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession, DatasetStorage
from app.schemas.analysis import AnalysisResultResponse
from app.services.analysis import (
    AnalysisSourceError,
    get_user_analysis_result,
    run_eda,
)
from app.services.dataset import get_user_dataset

router = APIRouter(tags=["analysis"])


@router.post(
    "/analysis/{dataset_id}",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_dataset(
    dataset_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
    storage_root: DatasetStorage,
) -> AnalysisResultResponse:
    dataset = get_user_dataset(database, dataset_id, current_user.id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在",
        )
    try:
        return run_eda(
            database=database,
            dataset=dataset,
            storage_root=storage_root,
        )
    except AnalysisSourceError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.get(
    "/results/{result_id}",
    response_model=AnalysisResultResponse,
)
def get_analysis_result(
    result_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> AnalysisResultResponse:
    result = get_user_analysis_result(database, result_id, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在",
        )
    return result
