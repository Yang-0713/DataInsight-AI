from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.dependencies import CurrentUser, DatabaseSession, DatasetStorage
from app.core.config import get_settings
from app.schemas.dataset import DatasetResponse
from app.services.dataset import (
    DatasetTooLargeError,
    DatasetUploadError,
    delete_dataset,
    get_user_dataset,
    get_user_datasets,
    save_dataset_upload,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    current_user: CurrentUser,
    database: DatabaseSession,
    storage_root: DatasetStorage,
    file: UploadFile = File(...),
) -> DatasetResponse:
    settings = get_settings()
    try:
        return await save_dataset_upload(
            database=database,
            upload=file,
            user_id=current_user.id,
            storage_root=storage_root,
            max_size_bytes=settings.max_upload_size_mb * 1024 * 1024,
        )
    except DatasetTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(error),
        ) from error
    except DatasetUploadError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> list[DatasetResponse]:
    return get_user_datasets(database, current_user.id)


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> DatasetResponse:
    dataset = get_user_dataset(database, dataset_id, current_user.id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在",
        )
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_dataset(
    dataset_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
    storage_root: DatasetStorage,
) -> None:
    dataset = get_user_dataset(database, dataset_id, current_user.id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在",
        )
    delete_dataset(database, dataset, storage_root)
