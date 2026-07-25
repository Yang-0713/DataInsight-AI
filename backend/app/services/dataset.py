from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.services.data_loader import InvalidCsvError, inspect_csv

UPLOAD_CHUNK_SIZE = 1024 * 1024


class DatasetUploadError(ValueError):
    """Base error for a rejected dataset upload."""


class DatasetTooLargeError(DatasetUploadError):
    """Raised when an upload exceeds the configured maximum size."""


def get_user_datasets(database: Session, user_id: int) -> list[Dataset]:
    statement = (
        select(Dataset)
        .where(Dataset.user_id == user_id)
        .order_by(Dataset.created_at.desc(), Dataset.id.desc())
    )
    return list(database.scalars(statement))


def get_user_dataset(
    database: Session, dataset_id: int, user_id: int
) -> Dataset | None:
    statement = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.user_id == user_id,
    )
    return database.scalar(statement)


async def save_dataset_upload(
    *,
    database: Session,
    upload: UploadFile,
    user_id: int,
    storage_root: Path,
    max_size_bytes: int,
) -> Dataset:
    original_filename = Path(upload.filename or "").name
    if not original_filename or Path(original_filename).suffix.lower() != ".csv":
        raise DatasetUploadError("仅支持上传 .csv 文件")
    if len(original_filename) > 255:
        raise DatasetUploadError("文件名不能超过 255 个字符")

    user_directory = storage_root / str(user_id)
    user_directory.mkdir(parents=True, exist_ok=True)
    relative_path = Path(str(user_id)) / f"{uuid4().hex}.csv"
    final_path = storage_root / relative_path
    temporary_path = final_path.with_suffix(".part")
    bytes_written = 0
    committed = False

    try:
        with temporary_path.open("wb") as destination:
            while chunk := await upload.read(UPLOAD_CHUNK_SIZE):
                bytes_written += len(chunk)
                if bytes_written > max_size_bytes:
                    raise DatasetTooLargeError("文件大小超过上传限制")
                destination.write(chunk)

        if bytes_written == 0:
            raise DatasetUploadError("不能上传空文件")

        temporary_path.replace(final_path)
        metadata = inspect_csv(final_path)
        dataset = Dataset(
            user_id=user_id,
            filename=original_filename,
            filepath=relative_path.as_posix(),
            rows=metadata.rows,
            columns=metadata.columns,
        )
        database.add(dataset)
        database.commit()
        database.refresh(dataset)
        committed = True
        return dataset
    except InvalidCsvError as error:
        database.rollback()
        raise DatasetUploadError(str(error)) from error
    except Exception:
        database.rollback()
        raise
    finally:
        await upload.close()
        temporary_path.unlink(missing_ok=True)
        if not committed:
            final_path.unlink(missing_ok=True)


def delete_dataset(
    database: Session,
    dataset: Dataset,
    storage_root: Path,
    report_storage_root: Path | None = None,
) -> None:
    stored_path = (storage_root / dataset.filepath).resolve()
    root = storage_root.resolve()
    report_paths: list[Path] = []
    if report_storage_root is not None:
        report_root = report_storage_root.resolve()
        for result in dataset.analysis_results:
            relative = result.result_json.get("report_path")
            if result.analysis_type != "AI_REPORT" or not isinstance(relative, str):
                continue
            candidate = (report_root / relative).resolve()
            if candidate.is_relative_to(report_root):
                report_paths.append(candidate)

    database.delete(dataset)
    database.commit()

    if stored_path.is_relative_to(root):
        stored_path.unlink(missing_ok=True)
        try:
            stored_path.parent.rmdir()
        except OSError:
            pass
    for report_path in report_paths:
        report_path.unlink(missing_ok=True)
        try:
            report_path.parent.rmdir()
        except OSError:
            pass
