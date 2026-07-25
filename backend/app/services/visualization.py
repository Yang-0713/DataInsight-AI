import math
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


def _finite_number(value: Any) -> float | int | None:
    number = float(value)
    if not math.isfinite(number):
        return None
    if number.is_integer():
        return int(number)
    return round(number, 6)


def _base_axes() -> dict[str, Any]:
    return {
        "grid": {"left": 48, "right": 24, "top": 34, "bottom": 48},
        "tooltip": {"trigger": "axis"},
    }


def _histogram(name: str, series: pd.Series) -> dict[str, Any] | None:
    values = pd.to_numeric(series, errors="coerce").dropna().to_numpy()
    values = values[np.isfinite(values)]
    if values.size == 0:
        return None
    bin_count = min(12, max(5, int(math.sqrt(values.size))))
    counts, edges = np.histogram(values, bins=bin_count)
    labels = [
        f"{edges[index]:.4g} – {edges[index + 1]:.4g}"
        for index in range(len(counts))
    ]
    option = {
        **_base_axes(),
        "xAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"rotate": 30},
        },
        "yAxis": {"type": "value", "name": "频数"},
        "series": [
            {
                "name": str(name),
                "type": "bar",
                "data": [int(value) for value in counts],
                "itemStyle": {"color": "#5b5cf0", "borderRadius": [5, 5, 0, 0]},
            }
        ],
    }
    return {
        "id": f"histogram-{name}",
        "type": "histogram",
        "title": f"{name} 分布",
        "columns": [str(name)],
        "option": option,
    }


def _box_plot(name: str, series: pd.Series) -> dict[str, Any] | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    values = values[np.isfinite(values)]
    if values.empty:
        return None
    summary = [
        _finite_number(values.min()),
        _finite_number(values.quantile(0.25)),
        _finite_number(values.median()),
        _finite_number(values.quantile(0.75)),
        _finite_number(values.max()),
    ]
    option = {
        **_base_axes(),
        "tooltip": {"trigger": "item"},
        "xAxis": {"type": "category", "data": [str(name)]},
        "yAxis": {"type": "value", "scale": True},
        "series": [
            {
                "name": str(name),
                "type": "boxplot",
                "data": [summary],
                "itemStyle": {"color": "#dddfff", "borderColor": "#5b5cf0"},
            }
        ],
    }
    return {
        "id": f"boxplot-{name}",
        "type": "boxplot",
        "title": f"{name} 箱线图",
        "columns": [str(name)],
        "option": option,
    }


def _category_bar(name: str, series: pd.Series) -> dict[str, Any] | None:
    counts = series.dropna().astype(str).value_counts().head(12)
    if counts.empty:
        return None
    option = {
        **_base_axes(),
        "xAxis": {
            "type": "category",
            "data": [str(value) for value in counts.index],
            "axisLabel": {"interval": 0, "rotate": 30},
        },
        "yAxis": {"type": "value", "name": "频数"},
        "series": [
            {
                "name": str(name),
                "type": "bar",
                "data": [int(value) for value in counts.values],
                "itemStyle": {"color": "#2fc49a", "borderRadius": [5, 5, 0, 0]},
            }
        ],
    }
    return {
        "id": f"bar-{name}",
        "type": "bar",
        "title": f"{name} 类别分布",
        "columns": [str(name)],
        "option": option,
    }


def _correlation_heatmap(frame: pd.DataFrame) -> dict[str, Any] | None:
    numeric = frame.select_dtypes(include="number")
    numeric = numeric.loc[:, [not is_bool_dtype(dtype) for dtype in numeric.dtypes]]
    numeric = numeric.replace([np.inf, -np.inf], np.nan)
    if numeric.shape[1] < 2:
        return None
    numeric = numeric.iloc[:, :12]
    correlation = numeric.corr()
    names = [str(name) for name in correlation.columns]
    data: list[list[Any]] = []
    for x_index, x_name in enumerate(correlation.columns):
        for y_index, y_name in enumerate(correlation.index):
            value = correlation.loc[y_name, x_name]
            data.append([x_index, y_index, _finite_number(value)])
    option = {
        "grid": {"left": 78, "right": 52, "top": 24, "bottom": 64},
        "tooltip": {"position": "top"},
        "xAxis": {"type": "category", "data": names, "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": names, "splitArea": {"show": True}},
        "visualMap": {
            "min": -1,
            "max": 1,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": 4,
            "inRange": {"color": ["#3445a5", "#f5f6ff", "#ef725f"]},
        },
        "series": [
            {
                "name": "相关系数",
                "type": "heatmap",
                "data": data,
                "label": {"show": len(names) <= 8},
            }
        ],
    }
    return {
        "id": "correlation-heatmap",
        "type": "heatmap",
        "title": "数值字段相关性",
        "columns": names,
        "option": option,
    }


def _time_series(frame: pd.DataFrame) -> dict[str, Any] | None:
    numeric_names = [
        name
        for name in frame.select_dtypes(include="number").columns
        if not is_bool_dtype(frame[name])
    ][:4]
    if not numeric_names:
        return None

    date_name: Any | None = None
    parsed_dates: pd.Series | None = None
    for name in frame.columns:
        if name in numeric_names:
            continue
        parsed = pd.to_datetime(frame[name], errors="coerce", format="mixed")
        if len(parsed) and float(parsed.notna().mean()) >= 0.8:
            date_name = name
            parsed_dates = parsed
            break
    if date_name is None or parsed_dates is None:
        return None

    working = frame.loc[parsed_dates.notna(), numeric_names].copy()
    working = working.replace([np.inf, -np.inf], np.nan)
    working.insert(0, "__date", parsed_dates[parsed_dates.notna()])
    working = working.groupby("__date", as_index=False).mean(numeric_only=True)
    working = working.sort_values("__date").tail(300)
    dates = [value.isoformat() for value in working["__date"]]
    series = [
        {
            "name": str(name),
            "type": "line",
            "smooth": True,
            "showSymbol": len(dates) < 40,
            "data": [_finite_number(value) for value in working[name]],
        }
        for name in numeric_names
    ]
    option = {
        **_base_axes(),
        "legend": {"data": [str(name) for name in numeric_names]},
        "xAxis": {"type": "category", "data": dates, "boundaryGap": False},
        "yAxis": {"type": "value", "scale": True},
        "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 18}],
        "series": series,
    }
    return {
        "id": f"line-{date_name}",
        "type": "line",
        "title": f"按 {date_name} 的时间趋势",
        "columns": [str(date_name), *[str(name) for name in numeric_names]],
        "option": option,
    }


def build_visualizations(frame: pd.DataFrame) -> list[dict[str, Any]]:
    charts: list[dict[str, Any]] = []
    numeric_names = [
        name
        for name in frame.columns
        if is_numeric_dtype(frame[name]) and not is_bool_dtype(frame[name])
    ][:8]
    categorical_names = [
        name
        for name in frame.columns
        if name not in numeric_names and frame[name].nunique(dropna=True) <= 50
    ][:8]

    for name in numeric_names:
        for chart in (_histogram(str(name), frame[name]), _box_plot(str(name), frame[name])):
            if chart is not None:
                charts.append(chart)
    for name in categorical_names:
        chart = _category_bar(str(name), frame[name])
        if chart is not None:
            charts.append(chart)

    correlation = _correlation_heatmap(frame)
    if correlation is not None:
        charts.append(correlation)
    time_series = _time_series(frame)
    if time_series is not None:
        charts.append(time_series)
    return charts
