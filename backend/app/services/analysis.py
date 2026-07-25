from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis_result import AnalysisResult
from app.models.dataset import Dataset
from app.services.data_loader import InvalidCsvError, load_csv
from app.services.profiler import build_profile, build_statistics
from app.services.visualization import build_visualizations


class AnalysisSourceError(ValueError):
    """Raised when a stored dataset can no longer be analyzed."""


def run_eda(
    *,
    database: Session,
    dataset: Dataset,
    storage_root: Path,
) -> AnalysisResult:
    root = storage_root.resolve()
    stored_path = (root / dataset.filepath).resolve()
    if not stored_path.is_relative_to(root) or not stored_path.is_file():
        raise AnalysisSourceError("数据集源文件不存在，请重新上传")

    try:
        frame = load_csv(stored_path)
    except InvalidCsvError as error:
        raise AnalysisSourceError(str(error)) from error

    result_json = {
        "dataset": {
            "id": dataset.id,
            "filename": dataset.filename,
            "rows": dataset.rows,
            "columns": dataset.columns,
        },
        "profile": build_profile(frame),
        "statistics": build_statistics(frame),
        "visualizations": build_visualizations(frame),
    }
    analysis = AnalysisResult(
        dataset_id=dataset.id,
        analysis_type="EDA",
        result_json=result_json,
    )
    database.add(analysis)
    database.commit()
    database.refresh(analysis)
    return analysis


def get_user_analysis_result(
    database: Session,
    result_id: int,
    user_id: int,
) -> AnalysisResult | None:
    statement = (
        select(AnalysisResult)
        .join(AnalysisResult.dataset)
        .where(
            AnalysisResult.id == result_id,
            Dataset.user_id == user_id,
        )
    )
    return database.scalar(statement)
