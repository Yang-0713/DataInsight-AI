from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest


@dataclass(frozen=True)
class IsolationForestResult:
    anomaly_scores: np.ndarray
    raw_scores: np.ndarray
    predictions: np.ndarray


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    minimum = float(scores.min())
    maximum = float(scores.max())
    if maximum == minimum:
        return np.zeros_like(scores, dtype=float)
    return (scores - minimum) / (maximum - minimum)


def run_isolation_forest(
    data: np.ndarray,
    *,
    contamination: float = 0.05,
    random_state: int = 42,
) -> IsolationForestResult:
    """Detect global anomalies with deterministic Isolation Forest settings."""
    values = np.asarray(data, dtype=float)
    if values.ndim != 2 or values.shape[0] < 2:
        raise ValueError("Isolation Forest 至少需要两条记录")
    if not np.isfinite(values).all():
        raise ValueError("Isolation Forest 输入不能包含缺失值或无穷值")

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
    )
    predictions = model.fit_predict(values)
    raw_scores = -model.decision_function(values)
    return IsolationForestResult(
        anomaly_scores=_normalize_scores(raw_scores),
        raw_scores=raw_scores,
        predictions=predictions,
    )
