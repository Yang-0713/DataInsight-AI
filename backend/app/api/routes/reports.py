from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.ai.provider import AIProviderError
from app.api.dependencies import (
    AIProviderDependency,
    CurrentUser,
    DatabaseSession,
    DatasetStorage,
    ReportStorage,
)
from app.core.config import get_settings
from app.models.analysis_result import AnalysisResult
from app.schemas.ai import AIReportResponse
from app.services.ai_analysis import (
    AIReportFormatError,
    create_ai_report,
    get_user_report,
    get_user_reports,
    resolve_report_path,
    stable_safety_identifier,
)
from app.services.analysis import AnalysisSourceError
from app.services.dataset import get_user_dataset

router = APIRouter(prefix="/reports", tags=["reports"])


def _response(result: AnalysisResult) -> AIReportResponse:
    data = result.result_json
    return AIReportResponse(
        id=result.id,
        dataset_id=result.dataset_id,
        title=str(data.get("title", "数据分析报告")),
        summary=str(data.get("summary", "")),
        findings=list(data.get("findings", [])),
        possible_problems=list(data.get("possible_problems", [])),
        recommendations=list(data.get("recommendations", [])),
        download_url=f"/api/reports/{result.id}/download",
        provider=str(data.get("provider", "")),
        model=str(data.get("model", "")),
        created_at=result.created_at,
    )


@router.post(
    "/{dataset_id}",
    response_model=AIReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_report(
    dataset_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
    dataset_storage_root: DatasetStorage,
    report_storage_root: ReportStorage,
    provider: AIProviderDependency,
) -> AIReportResponse:
    dataset = get_user_dataset(database, dataset_id, current_user.id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在",
        )
    settings = get_settings()
    try:
        result = create_ai_report(
            database=database,
            dataset=dataset,
            dataset_storage_root=dataset_storage_root,
            report_storage_root=report_storage_root,
            provider=provider,
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
    except (AIProviderError, AIReportFormatError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    return _response(result)


@router.get("", response_model=list[AIReportResponse])
def list_reports(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> list[AIReportResponse]:
    return [
        _response(result)
        for result in get_user_reports(database, current_user.id)
    ]


@router.get("/{result_id}/download", response_class=FileResponse)
def download_report(
    result_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
    report_storage_root: ReportStorage,
) -> FileResponse:
    result = get_user_report(database, result_id, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在",
        )
    report_path = resolve_report_path(result, report_storage_root)
    if report_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告文件不存在",
        )
    title = str(result.result_json.get("title", f"report-{result.id}"))
    return FileResponse(
        path=Path(report_path),
        media_type="text/html; charset=utf-8",
        filename=f"{title}.html",
    )
