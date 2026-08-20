from __future__ import annotations

from app.models import ChartSpec


def build_chart_spec(question: str, columns: list[str], rows: list[dict]) -> ChartSpec:
    q = question
    if not rows:
        return ChartSpec(chart_type="table", title="查询结果")
    if len(columns) == 1:
        return ChartSpec(chart_type="table", x_field=columns[0], y_fields=[], title="查询结果")
    if any(word in q for word in ["趋势", "变化", "按天", "日"]):
        x = next((c for c in columns if "day" in c or "date" in c or "time" in c), columns[0])
        y = [c for c in columns if c != x][:1]
        return ChartSpec(chart_type="line", x_field=x, y_fields=y, title="趋势图")
    if any(word in q for word in ["占比", "构成"]):
        x = columns[0]
        y = [columns[1]]
        return ChartSpec(chart_type="pie", x_field=x, y_fields=y, title="占比图")
    if len(columns) >= 2:
        return ChartSpec(chart_type="bar", x_field=columns[0], y_fields=columns[1:2], title="对比图")
    return ChartSpec(chart_type="table", title="查询结果")
