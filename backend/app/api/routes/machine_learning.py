from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession, DatasetStorage
from app.core.config import get_settings
from app.schemas.analysis import AnalysisResultResponse
from app.schemas.machine_learning import (
    MachineLearningFeaturesResponse,
    MachineLearningRequest,
)
from app.services.dataset import get_user_dataset
from app.services.machine_learning import (
    MachineLearningError,
    get_machine_learning_features,
    run_machine_learning_analysis,
)

router = APIRouter(prefix="/ml", tags=["machine-learning"])


@router.get(
    "/{dataset_id}/features",
    response_model=MachineLearningFeaturesResponse,
)
def list_machine_learning_features(
    dataset_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
    storage_root: DatasetStorage,
) -> MachineLearningFeaturesResponse:
    dataset = get_user_dataset(database, dataset_id, current_user.id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在",
        )
    try:
        return get_machine_learning_features(
            dataset,
            storage_root,
            get_settings().max_ml_rows,
        )
    except MachineLearningError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.post(
    "/{dataset_id}",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_dataset_with_machine_learning(
    dataset_id: int,
    request: MachineLearningRequest,
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
        return run_machine_learning_analysis(
            database=database,
            dataset=dataset,
            storage_root=storage_root,
            request=request,
            max_rows=get_settings().max_ml_rows,
        )
    except MachineLearningError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
