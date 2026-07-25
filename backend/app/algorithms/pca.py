from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA


@dataclass(frozen=True)
class PcaResult:
    coordinates: np.ndarray
    components: np.ndarray
    explained_variance_ratio: np.ndarray


def run_pca(data: np.ndarray, n_components: int = 2) -> PcaResult:
    """Project finite, standardized feature data into principal components."""
    values = np.asarray(data, dtype=float)
    if values.ndim != 2:
        raise ValueError("PCA 输入必须是二维数组")
    if not np.isfinite(values).all():
        raise ValueError("PCA 输入不能包含缺失值或无穷值")
    if values.shape[0] < 2 or values.shape[1] < n_components:
        raise ValueError("PCA 至少需要两条记录和两个数值字段")

    model = PCA(n_components=n_components)
    coordinates = model.fit_transform(values)
    return PcaResult(
        coordinates=coordinates,
        components=model.components_,
        explained_variance_ratio=model.explained_variance_ratio_,
    )
