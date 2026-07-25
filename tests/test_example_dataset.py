from pathlib import Path

from app.services.data_loader import load_csv
from app.services.profiler import build_profile, build_statistics
from app.services.visualization import build_visualizations


EXAMPLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "datasets"
    / "retail_sales.csv"
)


def test_retail_example_dataset_is_valid_and_documented() -> None:
    frame = load_csv(EXAMPLE_PATH)
    profile = build_profile(frame)
    statistics = build_statistics(frame)
    visualizations = build_visualizations(frame)

    assert frame.shape == (40, 11)
    assert frame["sample_id"].is_unique
    assert profile["missing_cells"] == 2
    assert profile["duplicate_rows"] == 0
    assert {
        "orders",
        "units",
        "revenue",
        "cost",
        "discount_rate",
        "satisfaction_score",
    } <= {
        item["column"] for item in statistics["numerical"]
    }
    assert {"histogram", "boxplot", "bar", "heatmap", "line"} <= {
        item["type"] for item in visualizations
    }
