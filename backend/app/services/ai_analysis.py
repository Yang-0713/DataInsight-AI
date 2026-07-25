import hashlib
import html
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.prompts import (
    ANALYST_INSTRUCTIONS,
    REPORT_INSTRUCTIONS,
    build_chat_input,
    build_report_input,
)
from app.ai.provider import AICompletion, AIProvider
from app.models.analysis_result import AnalysisResult
from app.models.dataset import Dataset
from app.schemas.ai import AIChatRequest
from app.services.analysis import run_eda


class AIReportFormatError(ValueError):
    """Raised when the AI response is not a usable structured report."""


def stable_safety_identifier(user_id: int, secret: str) -> str:
    digest = hashlib.sha256(f"datainsight:{user_id}:{secret}".encode()).hexdigest()
    return f"di_{digest[:32]}"


def _latest_result(
    database: Session,
    dataset_id: int,
    analysis_type: str,
) -> AnalysisResult | None:
    statement = (
        select(AnalysisResult)
        .where(
            AnalysisResult.dataset_id == dataset_id,
            AnalysisResult.analysis_type == analysis_type,
        )
        .order_by(AnalysisResult.created_at.desc(), AnalysisResult.id.desc())
        .limit(1)
    )
    return database.scalar(statement)


def build_ai_context(
    *,
    database: Session,
    dataset: Dataset,
    storage_root: Path,
) -> dict[str, Any]:
    eda = _latest_result(database, dataset.id, "EDA")
    if eda is None:
        eda = run_eda(
            database=database,
            dataset=dataset,
            storage_root=storage_root,
        )
    ml = _latest_result(database, dataset.id, "ML")
    eda_data = eda.result_json
    profile = eda_data.get("profile", {})
    statistics = eda_data.get("statistics", {})

    context: dict[str, Any] = {
        "dataset": {
            "id": dataset.id,
            "filename": dataset.filename,
            "rows": dataset.rows,
            "columns": dataset.columns,
        },
        "data_quality": {
            "duplicate_rows": profile.get("duplicate_rows", 0),
            "missing_cells": profile.get("missing_cells", 0),
            "missing_percentage": profile.get("missing_percentage", 0),
            "columns": profile.get("column_profiles", [])[:30],
        },
        "statistics": {
            "numerical": statistics.get("numerical", [])[:16],
            "categorical": [
                {
                    **item,
                    "distribution": item.get("distribution", [])[:5],
                }
                for item in statistics.get("categorical", [])[:12]
            ],
        },
        "visualizations": [
            {
                "type": chart.get("type"),
                "title": chart.get("title"),
                "columns": chart.get("columns", []),
            }
            for chart in eda_data.get("visualizations", [])[:24]
        ],
        "machine_learning": None,
    }

    if ml is not None:
        ml_data = ml.result_json
        context["machine_learning"] = {
            "preprocessing": ml_data.get("preprocessing"),
            "pca": {
                "explained_variance_ratio": ml_data.get("pca", {}).get(
                    "explained_variance_ratio", []
                ),
                "cumulative_explained_variance": ml_data.get("pca", {}).get(
                    "cumulative_explained_variance"
                ),
                "components": ml_data.get("pca", {}).get("components", [])[:4],
            },
            "isolation_forest": _compact_anomalies(
                ml_data.get("isolation_forest", {})
            ),
            "lof": _compact_anomalies(ml_data.get("lof", {})),
        }
    return context


def _compact_anomalies(payload: dict[str, Any]) -> dict[str, Any]:
    samples = [
        {
            "sample_id": sample.get("sample_id"),
            "anomaly_score": sample.get("anomaly_score"),
        }
        for sample in payload.get("samples", [])
        if sample.get("label") == "anomaly"
    ]
    samples.sort(key=lambda item: item.get("anomaly_score") or 0, reverse=True)
    return {
        "anomaly_count": payload.get("anomaly_count", 0),
        "contamination": payload.get("contamination"),
        "top_anomalies": samples[:10],
    }


def run_ai_chat(
    *,
    database: Session,
    dataset: Dataset,
    storage_root: Path,
    provider: AIProvider,
    request: AIChatRequest,
    max_history_messages: int,
    safety_identifier: str,
) -> tuple[AnalysisResult, AICompletion]:
    context = build_ai_context(
        database=database,
        dataset=dataset,
        storage_root=storage_root,
    )
    history = (
        [
            item.model_dump()
            for item in request.history[-max_history_messages:]
        ]
        if max_history_messages
        else []
    )
    completion = provider.complete(
        instructions=ANALYST_INSTRUCTIONS,
        input_text=build_chat_input(
            context=context,
            question=request.message.strip(),
            history=history,
        ),
        safety_identifier=safety_identifier,
    )
    result = AnalysisResult(
        dataset_id=dataset.id,
        analysis_type="AI_CHAT",
        result_json={
            "question": request.message.strip(),
            "answer": completion.text,
            "provider": completion.provider,
            "model": completion.model,
        },
    )
    database.add(result)
    database.commit()
    database.refresh(result)
    return result, completion


def create_ai_report(
    *,
    database: Session,
    dataset: Dataset,
    dataset_storage_root: Path,
    report_storage_root: Path,
    provider: AIProvider,
    safety_identifier: str,
) -> AnalysisResult:
    context = build_ai_context(
        database=database,
        dataset=dataset,
        storage_root=dataset_storage_root,
    )
    completion = provider.complete(
        instructions=REPORT_INSTRUCTIONS,
        input_text=build_report_input(context),
        safety_identifier=safety_identifier,
    )
    report_data = parse_report_json(completion.text)
    title = f"{dataset.filename} 综合分析报告"
    relative_path = Path(str(dataset.user_id)) / f"{uuid4().hex}.html"
    final_path = (report_storage_root / relative_path).resolve()
    root = report_storage_root.resolve()
    if not final_path.is_relative_to(root):
        raise AIReportFormatError("报告保存路径无效")
    final_path.parent.mkdir(parents=True, exist_ok=True)

    result = AnalysisResult(
        dataset_id=dataset.id,
        analysis_type="AI_REPORT",
        result_json={
            "title": title,
            "summary": report_data["dataset_summary"],
            "findings": report_data["important_findings"],
            "possible_problems": report_data["possible_problems"],
            "recommendations": report_data["recommendations"],
            "report_path": relative_path.as_posix(),
            "provider": completion.provider,
            "model": completion.model,
        },
    )
    try:
        final_path.write_text(
            render_report_html(
                title=title,
                context=context,
                report_data=report_data,
            ),
            encoding="utf-8",
        )
        database.add(result)
        database.commit()
        database.refresh(result)
        return result
    except Exception:
        database.rollback()
        final_path.unlink(missing_ok=True)
        raise


def parse_report_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise AIReportFormatError("AI 未返回合法的报告 JSON") from error
    if not isinstance(data, dict):
        raise AIReportFormatError("AI 报告必须是 JSON 对象")

    summary = data.get("dataset_summary")
    if not isinstance(summary, str) or not summary.strip():
        raise AIReportFormatError("AI 报告缺少数据集概述")
    normalized: dict[str, Any] = {"dataset_summary": summary.strip()}
    for key in ("important_findings", "possible_problems", "recommendations"):
        values = data.get(key)
        if not isinstance(values, list) or not all(
            isinstance(value, str) for value in values
        ):
            raise AIReportFormatError(f"AI 报告字段 {key} 格式无效")
        normalized[key] = [
            value.strip() for value in values[:8] if value.strip()
        ]
    return normalized


def render_report_html(
    *,
    title: str,
    context: dict[str, Any],
    report_data: dict[str, Any],
) -> str:
    dataset = context["dataset"]
    quality = context["data_quality"]
    numerical = context["statistics"]["numerical"]
    categorical = context["statistics"]["categorical"]
    ml = context.get("machine_learning")

    def escape(value: Any) -> str:
        return html.escape(str(value))

    def list_html(values: list[str], empty_text: str) -> str:
        if not values:
            return f'<p class="empty">{escape(empty_text)}</p>'
        return "<ul>" + "".join(
            f"<li>{escape(value)}</li>" for value in values
        ) + "</ul>"

    numeric_rows = "".join(
        "<tr>"
        f"<td>{escape(item.get('column'))}</td>"
        f"<td>{escape(item.get('mean'))}</td>"
        f"<td>{escape(item.get('median'))}</td>"
        f"<td>{escape(item.get('min'))}</td>"
        f"<td>{escape(item.get('max'))}</td>"
        "</tr>"
        for item in numerical
    )
    category_rows = "".join(
        "<tr>"
        f"<td>{escape(item.get('column'))}</td>"
        f"<td>{escape(item.get('unique'))}</td>"
        f"<td>{escape(item.get('top'))}</td>"
        f"<td>{escape(item.get('frequency'))}</td>"
        "</tr>"
        for item in categorical
    )
    ml_html = (
        '<p class="empty">尚未运行机器学习分析，本报告不包含异常检测结论。</p>'
        if ml is None
        else (
            '<div class="metric-grid">'
            f"<div><span>分析特征</span><strong>{escape(', '.join(ml['preprocessing']['features']))}</strong></div>"
            f"<div><span>Isolation Forest 异常数</span><strong>{escape(ml['isolation_forest']['anomaly_count'])}</strong></div>"
            f"<div><span>LOF 异常数</span><strong>{escape(ml['lof']['anomaly_count'])}</strong></div>"
            "</div>"
        )
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{ color: #17213a; background: #f4f6fb; font-family: Inter, "Microsoft YaHei", sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 44px 20px; }}
    main {{ width: min(980px, 100%); margin: auto; }}
    header {{ padding: 38px; color: white; background: linear-gradient(135deg, #5556dc, #303b83); border-radius: 24px; }}
    h1 {{ margin: 8px 0 12px; font-size: 2rem; }}
    header p {{ margin: 0; color: #dfe2ff; }}
    .kicker {{ font-size: .72rem; font-weight: 800; letter-spacing: .14em; }}
    section {{ padding: 28px; margin-top: 18px; background: white; border: 1px solid #e5e8f2; border-radius: 18px; }}
    h2 {{ margin: 0 0 18px; font-size: 1.2rem; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
    .metric-grid div {{ display: grid; gap: 7px; padding: 17px; background: #f7f8fd; border-radius: 12px; }}
    .metric-grid span {{ color: #7d8498; font-size: .75rem; }}
    .metric-grid strong {{ overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .86rem; }}
    th, td {{ padding: 11px; text-align: left; border-bottom: 1px solid #eceef5; }}
    th {{ color: #71798e; background: #f8f9fc; }}
    ul {{ padding-left: 20px; margin: 0; }}
    li {{ margin: 9px 0; line-height: 1.65; }}
    .empty {{ color: #8b92a4; }}
    footer {{ padding: 22px; color: #8a91a4; font-size: .75rem; text-align: center; }}
    @media (max-width: 680px) {{ .metric-grid {{ grid-template-columns: 1fr; }} section, header {{ padding: 22px; }} }}
    @media print {{ body {{ padding: 0; background: white; }} section {{ break-inside: avoid; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="kicker">DATAINSIGHT AI · PHASE 6</div>
    <h1>{escape(title)}</h1>
    <p>{escape(report_data['dataset_summary'])}</p>
  </header>
  <section>
    <h2>数据概览</h2>
    <div class="metric-grid">
      <div><span>数据集</span><strong>{escape(dataset['filename'])}</strong></div>
      <div><span>记录数</span><strong>{escape(dataset['rows'])}</strong></div>
      <div><span>字段数</span><strong>{escape(dataset['columns'])}</strong></div>
      <div><span>重复记录</span><strong>{escape(quality['duplicate_rows'])}</strong></div>
      <div><span>缺失单元格</span><strong>{escape(quality['missing_cells'])}</strong></div>
      <div><span>缺失率</span><strong>{escape(quality['missing_percentage'])}%</strong></div>
    </div>
  </section>
  <section><h2>重要发现</h2>{list_html(report_data['important_findings'], '暂未发现有充分证据支持的重要结论。')}</section>
  <section><h2>可能的问题</h2>{list_html(report_data['possible_problems'], '当前摘要中未识别到明确问题。')}</section>
  <section><h2>建议</h2>{list_html(report_data['recommendations'], '暂无额外建议。')}</section>
  <section>
    <h2>数值字段统计</h2>
    <table><thead><tr><th>字段</th><th>均值</th><th>中位数</th><th>最小值</th><th>最大值</th></tr></thead>
    <tbody>{numeric_rows or '<tr><td colspan="5">无数值字段</td></tr>'}</tbody></table>
  </section>
  <section>
    <h2>类别字段统计</h2>
    <table><thead><tr><th>字段</th><th>唯一值</th><th>最高频值</th><th>频次</th></tr></thead>
    <tbody>{category_rows or '<tr><td colspan="4">无类别字段</td></tr>'}</tbody></table>
  </section>
  <section><h2>机器学习摘要</h2>{ml_html}</section>
  <footer>本报告由 AI 基于聚合统计生成，不代表因果结论；重要决策前请复核原始数据。</footer>
</main>
</body>
</html>"""


def get_user_reports(database: Session, user_id: int) -> list[AnalysisResult]:
    statement = (
        select(AnalysisResult)
        .join(AnalysisResult.dataset)
        .where(
            Dataset.user_id == user_id,
            AnalysisResult.analysis_type == "AI_REPORT",
        )
        .order_by(AnalysisResult.created_at.desc(), AnalysisResult.id.desc())
    )
    return list(database.scalars(statement))


def get_user_report(
    database: Session,
    result_id: int,
    user_id: int,
) -> AnalysisResult | None:
    statement = (
        select(AnalysisResult)
        .join(AnalysisResult.dataset)
        .where(
            AnalysisResult.id == result_id,
            AnalysisResult.analysis_type == "AI_REPORT",
            Dataset.user_id == user_id,
        )
    )
    return database.scalar(statement)


def resolve_report_path(result: AnalysisResult, report_root: Path) -> Path | None:
    relative = result.result_json.get("report_path")
    if not isinstance(relative, str):
        return None
    root = report_root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    return path
