from dataclasses import dataclass

import numpy as np
from sklearn.neighbors import LocalOutlierFactor


@dataclass(frozen=True)
class LofResult:
    anomaly_scores: np.ndarray
    raw_scores: np.ndarray
    predictions: np.ndarray
    n_neighbors: int


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    minimum = float(scores.min())
    maximum = float(scores.max())
    if maximum == minimum:
        return np.zeros_like(scores, dtype=float)
    return (scores - minimum) / (maximum - minimum)


def run_lof(
    data: np.ndarray,
    *,
    contamination: float = 0.05,
    n_neighbors: int = 20,
) -> LofResult:
    """Detect local-density anomalies with a sample-safe neighbor count."""
    values = np.asarray(data, dtype=float)
    if values.ndim != 2 or values.shape[0] < 3:
        raise ValueError("LOF 至少需要三条记录")
    if not np.isfinite(values).all():
        raise ValueError("LOF 输入不能包含缺失值或无穷值")

    effective_neighbors = min(n_neighbors, values.shape[0] - 1)
    model = LocalOutlierFactor(
        n_neighbors=effective_neighbors,
        contamination=contamination,
    )
    predictions = model.fit_predict(values)
    raw_scores = -model.negative_outlier_factor_
    return LofResult(
        anomaly_scores=_normalize_scores(raw_scores),
        raw_scores=raw_scores,
        predictions=predictions,
        n_neighbors=effective_neighbors,
    )
