from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.config import PROJECT_ROOT


@dataclass
class RetrievedContext:
    question: str
    tables: list[str]
    metrics: list[str]
    schema_text: str
    metric_text: str


def _load_json(name: str) -> dict:
    path = PROJECT_ROOT / "data" / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema_dictionary() -> dict:
    return _load_json("schema_dictionary.json")


def load_metric_dictionary() -> dict:
    return _load_json("metric_dictionary.json")


def retrieve_context(question: str) -> RetrievedContext:
    schema = load_schema_dictionary()
    metrics = load_metric_dictionary()
    q = question.lower()

    table_hits: list[str] = []
    metric_hits: list[str] = []

    table_keywords = {
        "orders": ["订单", "gmv", "销售", "支付", "成交", "客单", "销量", "下单"],
        "users": ["用户", "注册", "留存", "新客", "新用户"],
        "products": ["商品", "品类", "类目", "产品"],
        "channels": ["渠道", "来源", "拉新"],
        "user_events": ["行为", "活跃", "访问", "事件"],
        "order_items": ["明细", "件数", "数量"],
    }
    for table, keywords in table_keywords.items():
        if any(k in q for k in keywords):
            table_hits.append(table)
    if not table_hits:
        table_hits = ["orders", "users"]

    for metric in metrics:
        if metric in q:
            metric_hits.append(metric)
    if any(word in q for word in ["gmv", "销售额", "成交额"]):
        metric_hits.append("gmv")
    if "订单量" in q or "订单数" in q:
        metric_hits.append("order_count")
    if any(word in q for word in ["客单价", "aov"]):
        metric_hits.append("aov")
    if any(word in q for word in ["活跃用户", "活跃人数"]):
        metric_hits.append("active_user_count")
    if any(word in q for word in ["件数", "销量"]):
        metric_hits.append("item_quantity")

    metric_hits = list(dict.fromkeys(metric_hits))
    table_hits = list(dict.fromkeys(table_hits))

    schema_lines = []
    for table in table_hits:
        meta = schema.get(table, {})
        schema_lines.append(f"[{table}] {meta.get('description', '')}")
        cols = meta.get("columns", {})
        for col, desc in cols.items():
            schema_lines.append(f"  - {col}: {desc}")
    metric_lines = []
    for metric in metric_hits:
        meta = metrics.get(metric, {})
        metric_lines.append(
            f"[{metric}] {meta.get('definition', '')} | expression={meta.get('expression', '')}"
        )

    return RetrievedContext(
        question=question,
        tables=table_hits,
        metrics=metric_hits,
        schema_text="\n".join(schema_lines),
        metric_text="\n".join(metric_lines),
    )

