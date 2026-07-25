import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.algorithms import run_isolation_forest, run_lof, run_pca
from app.models.analysis_result import AnalysisResult
from app.models.dataset import Dataset
from app.schemas.machine_learning import MachineLearningRequest
from app.services.analysis import AnalysisSourceError, load_dataset_frame


class MachineLearningError(ValueError):
    """Raised when a dataset cannot satisfy machine-learning requirements."""


IDENTIFIER_NAMES = {"id", "sample_id", "sampleid", "index", "编号", "样本编号"}


def _round_number(value: Any) -> float | int:
    number = float(value)
    if not math.isfinite(number):
        raise MachineLearningError("机器学习结果包含无效数值")
    if number.is_integer():
        return int(number)
    return round(number, 6)


def _sample_ids(frame: pd.DataFrame) -> list[str]:
    for name in frame.columns:
        if str(name).strip().lower() in IDENTIFIER_NAMES:
            values = frame[name]
            if values.notna().all() and values.nunique() == len(values):
                return [str(value) for value in values]
    return [f"Row {index + 1}" for index in range(len(frame))]


def _select_features(
    frame: pd.DataFrame,
    requested_features: list[str] | None,
) -> tuple[pd.DataFrame, list[str]]:
    if requested_features:
        missing = [name for name in requested_features if name not in frame.columns]
        if missing:
            raise MachineLearningError(
                f"特征字段不存在：{', '.join(missing)}"
            )
        non_numeric = [
            name
            for name in requested_features
            if not is_numeric_dtype(frame[name]) or is_bool_dtype(frame[name])
        ]
        if non_numeric:
            raise MachineLearningError(
                f"以下字段不是数值类型：{', '.join(non_numeric)}"
            )
        feature_names = requested_features
    else:
        feature_names = [
            str(name)
            for name in frame.columns
            if is_numeric_dtype(frame[name])
            and not is_bool_dtype(frame[name])
            and not (
                str(name).strip().lower() in IDENTIFIER_NAMES
                and frame[name].notna().all()
                and frame[name].nunique() == len(frame)
            )
        ]

    usable_names = [
        name
        for name in feature_names
        if frame[name].replace([np.inf, -np.inf], np.nan).notna().any()
    ]
    if len(usable_names) < 2:
        raise MachineLearningError("机器学习分析至少需要两个有效数值字段")
    return frame[usable_names].replace([np.inf, -np.inf], np.nan), usable_names


def get_machine_learning_features(
    dataset: Dataset,
    storage_root: Path,
    max_rows: int,
) -> dict[str, Any]:
    try:
        frame = load_dataset_frame(dataset, storage_root)
    except AnalysisSourceError as error:
        raise MachineLearningError(str(error)) from error

    numeric_features = [
        str(name)
        for name in frame.columns
        if is_numeric_dtype(frame[name])
        and not is_bool_dtype(frame[name])
        and frame[name].replace([np.inf, -np.inf], np.nan).notna().any()
    ]
    recommended_features = [
        name
        for name in numeric_features
        if not (
            name.strip().lower() in IDENTIFIER_NAMES
            and frame[name].notna().all()
            and frame[name].nunique() == len(frame)
        )
    ]
    return {
        "dataset_id": dataset.id,
        "rows": len(frame),
        "numeric_features": numeric_features,
        "recommended_features": recommended_features,
        "max_rows": max_rows,
    }


def _anomaly_payload(
    *,
    sample_ids: list[str],
    anomaly_scores: np.ndarray,
    raw_scores: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, Any]:
    samples = [
        {
            "sample_id": sample_id,
            "anomaly_score": _round_number(anomaly_scores[index]),
            "raw_score": _round_number(raw_scores[index]),
            "prediction": int(predictions[index]),
            "label": "anomaly" if int(predictions[index]) == -1 else "normal",
        }
        for index, sample_id in enumerate(sample_ids)
    ]
    return {
        "anomaly_count": sum(sample["label"] == "anomaly" for sample in samples),
        "samples": samples,
    }


def run_machine_learning_analysis(
    *,
    database: Session,
    dataset: Dataset,
    storage_root: Path,
    request: MachineLearningRequest,
    max_rows: int,
) -> AnalysisResult:
    try:
        frame = load_dataset_frame(dataset, storage_root)
    except AnalysisSourceError as error:
        raise MachineLearningError(str(error)) from error

    if len(frame) < 3:
        raise MachineLearningError("机器学习分析至少需要三条记录")
    if len(frame) > max_rows:
        raise MachineLearningError(
            f"当前数据集有 {len(frame)} 行，机器学习分析上限为 {max_rows} 行"
        )

    feature_frame, feature_names = _select_features(frame, request.features)
    missing_values = int(feature_frame.isna().sum().sum())
    imputer = SimpleImputer(strategy="median")
    imputed = imputer.fit_transform(feature_frame)
    standardized = StandardScaler().fit_transform(imputed)
    sample_ids = _sample_ids(frame)

    pca = run_pca(standardized)
    isolation_forest = run_isolation_forest(
        standardized,
        contamination=request.contamination,
    )
    lof = run_lof(
        standardized,
        contamination=request.contamination,
        n_neighbors=request.lof_neighbors,
    )

    components = [
        {
            "component": f"PC{component_index + 1}",
            "loadings": [
                {
                    "feature": feature,
                    "weight": _round_number(
                        pca.components[component_index, feature_index]
                    ),
                }
                for feature_index, feature in enumerate(feature_names)
            ],
        }
        for component_index in range(pca.components.shape[0])
    ]
    pca_points = [
        {
            "sample_id": sample_id,
            "x": _round_number(pca.coordinates[index, 0]),
            "y": _round_number(pca.coordinates[index, 1]),
        }
        for index, sample_id in enumerate(sample_ids)
    ]
    result_json = {
        "dataset": {
            "id": dataset.id,
            "filename": dataset.filename,
            "rows": dataset.rows,
            "columns": dataset.columns,
        },
        "preprocessing": {
            "features": feature_names,
            "sample_count": len(frame),
            "missing_values_imputed": missing_values,
            "imputation": "median",
            "scaling": "standard",
        },
        "pca": {
            "components": components,
            "explained_variance_ratio": [
                _round_number(value) for value in pca.explained_variance_ratio
            ],
            "cumulative_explained_variance": _round_number(
                pca.explained_variance_ratio.sum()
            ),
            "visualization": pca_points,
        },
        "isolation_forest": {
            "contamination": request.contamination,
            **_anomaly_payload(
                sample_ids=sample_ids,
                anomaly_scores=isolation_forest.anomaly_scores,
                raw_scores=isolation_forest.raw_scores,
                predictions=isolation_forest.predictions,
            ),
        },
        "lof": {
            "contamination": request.contamination,
            "n_neighbors": lof.n_neighbors,
            **_anomaly_payload(
                sample_ids=sample_ids,
                anomaly_scores=lof.anomaly_scores,
                raw_scores=lof.raw_scores,
                predictions=lof.predictions,
            ),
        },
    }
    analysis = AnalysisResult(
        dataset_id=dataset.id,
        analysis_type="ML",
        result_json=result_json,
    )
    database.add(analysis)
    database.commit()
    database.refresh(analysis)
    return analysis
