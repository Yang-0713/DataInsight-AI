import numpy as np
import pytest

from algorithms.isolation_forest import run_isolation_forest
from algorithms.lof import run_lof
from algorithms.pca import run_pca


def anomaly_fixture() -> np.ndarray:
    normal = np.array(
        [
            [-0.2, 0.1],
            [0.0, 0.0],
            [0.1, -0.1],
            [0.2, 0.2],
            [-0.1, -0.2],
            [0.15, 0.05],
            [-0.15, 0.0],
            [0.05, 0.15],
            [-0.05, -0.1],
        ]
    )
    return np.vstack([normal, np.array([[8.0, 8.0]])])


def test_pca_returns_two_dimensional_projection() -> None:
    result = run_pca(anomaly_fixture())

    assert result.coordinates.shape == (10, 2)
    assert result.components.shape == (2, 2)
    assert result.explained_variance_ratio.shape == (2,)
    assert result.explained_variance_ratio.sum() == pytest.approx(1.0)


def test_isolation_forest_detects_extreme_sample() -> None:
    result = run_isolation_forest(anomaly_fixture(), contamination=0.1)

    assert result.predictions[-1] == -1
    assert result.anomaly_scores[-1] == pytest.approx(1.0)
    assert set(result.predictions) == {-1, 1}


def test_lof_detects_extreme_sample() -> None:
    result = run_lof(anomaly_fixture(), contamination=0.1, n_neighbors=5)

    assert result.n_neighbors == 5
    assert result.predictions[-1] == -1
    assert result.anomaly_scores[-1] == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("algorithm", "data"),
    [
        (run_pca, np.array([[1.0], [2.0]])),
        (run_isolation_forest, np.array([[1.0]])),
        (run_lof, np.array([[1.0], [2.0]])),
    ],
)
def test_algorithms_reject_insufficient_data(algorithm, data: np.ndarray) -> None:
    with pytest.raises(ValueError):
        algorithm(data)
