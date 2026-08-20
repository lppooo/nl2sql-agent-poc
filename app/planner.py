from __future__ import annotations

import json
import re
from datetime import date, timedelta

from app.config import get_settings
from app.models import SQLPlan
from app.schema_retriever import RetrievedContext


def _month_range_from_today(today: date) -> tuple[str, str]:
    first = today.replace(day=1)
    last_prev_month = first - timedelta(days=1)
    start = last_prev_month.replace(day=1)
    return start.isoformat(), last_prev_month.isoformat()


def _last_n_days(today: date, n: int) -> tuple[str, str]:
    start = today - timedelta(days=n - 1)
    return start.isoformat(), today.isoformat()


def _extract_first_date(question: str) -> tuple[str | None, str | None]:
    matches = re.findall(r"(20\d{2})[年/-](\d{1,2})(?:[月/-](\d{1,2})日?)?", question)
    if not matches:
        return None, None
    year, month, day = matches[0]
    if day:
        start = date(int(year), int(month), int(day))
        return start.isoformat(), start.isoformat()
    start = date(int(year), int(month), 1)
    if month == "12":
        end = date(int(year) + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(int(year), int(month) + 1, 1) - timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _extract_region(question: str) -> tuple[str | None, str | None]:
    region_map = {
        "华东区": "East China",
        "华南区": "South China",
        "华北区": "North China",
        "华西区": "West China",
        "east china": "East China",
        "south china": "South China",
        "north china": "North China",
        "west china": "West China",
    }
    q = question.lower()
    for key, value in region_map.items():
        if key in q:
            return key, value
    return None, None


def _guess_chart(question: str) -> str:
    if any(word in question for word in ["趋势", "变化", "按天", "按日", "走势"]):
        return "line"
    if any(word in question for word in ["占比", "构成"]):
        return "pie"
    if any(word in question for word in ["对比", "排名", "各", "渠道", "品类", "地区"]):
        return "bar"
    return "table"


def _date_predicate(column: str, start: str | None, end: str | None, today: date) -> str:
    dialect = get_settings().sql_dialect.lower()
    if dialect in {"postgres", "postgresql"}:
        date_expr = f"CAST({column} AS DATE)"
        if start and end:
            return f"{date_expr} BETWEEN DATE '{start}' AND DATE '{end}'"
        return f"{date_expr} BETWEEN DATE '{today.isoformat()}' - INTERVAL '29 days' AND DATE '{today.isoformat()}'"

    if start and end:
        return f"DATE({column}) BETWEEN DATE('{start}') AND DATE('{end}')"
    return f"DATE({column}) BETWEEN DATE('{today.isoformat()}', '-29 day') AND DATE('{today.isoformat()}')"


def _date_group(column: str) -> str:
    dialect = get_settings().sql_dialect.lower()
    if dialect in {"postgres", "postgresql"}:
        return f"CAST({column} AS DATE)"
    return f"DATE({column})"


def _offline_plan(question: str, ctx: RetrievedContext) -> SQLPlan:
    settings = get_settings()
    today = date.fromisoformat(settings.business_today)
    q = question.lower()
    chart_type = _guess_chart(q)
    filters = []
    start = end = None
    region_label, region_value = _extract_region(q)

    if "上个月" in q:
        start, end = _month_range_from_today(today)
    elif "近30天" in q or "最近30天" in q:
        start, end = _last_n_days(today, 30)
    else:
        start, end = _extract_first_date(q)

    if any(word in q for word in ["gmv", "销售额", "成交额"]):
        group_by_channel = any(word in q for word in ["渠道", "来源"])
        if region_value:
            sql = f"""
            SELECT users.region AS region, SUM(orders.pay_amount) AS gmv
            FROM orders
            JOIN users ON users.user_id = orders.user_id
            WHERE orders.status = 'paid'
              AND users.region = '{region_value}'
              AND {_date_predicate("orders.paid_at", start, end, today)}
            GROUP BY users.region
            ORDER BY gmv DESC
            """
            return SQLPlan(
                intent="gmv_by_region",
                metrics=["gmv"],
                dimensions=["region"],
                time_range={"start": start or "", "end": end or ""},
                filters=filters,
                sql=sql.strip(),
                chart_type="bar",
                answer_hint=f"{region_label}GMV",
            )
        if any(word in q for word in ["趋势", "按天", "日"]):
            sql = f"""
            SELECT {_date_group("orders.paid_at")} AS day, SUM(orders.pay_amount) AS gmv
            FROM orders
            WHERE orders.status = 'paid'
              AND {_date_predicate("orders.paid_at", start, end, today)}
            GROUP BY {_date_group("orders.paid_at")}
            ORDER BY day
            """
            return SQLPlan(
                intent="gmv_trend",
                metrics=["gmv"],
                dimensions=["day"],
                time_range={"start": start or "", "end": end or ""},
                filters=filters,
                sql=sql.strip(),
                chart_type="line",
                answer_hint="按天GMV趋势",
            )
        if group_by_channel:
            sql = f"""
            SELECT channels.channel_name AS channel, SUM(orders.pay_amount) AS gmv
            FROM orders
            JOIN channels ON channels.channel_id = orders.channel_id
            WHERE orders.status = 'paid'
              AND {_date_predicate("orders.paid_at", start, end, today)}
            GROUP BY channels.channel_name
            ORDER BY gmv DESC
            """
            return SQLPlan(
                intent="gmv_by_channel",
                metrics=["gmv"],
                dimensions=["channel"],
                time_range={"start": start or "", "end": end or ""},
                filters=filters,
                sql=sql.strip(),
                chart_type="bar",
                answer_hint="按渠道GMV",
            )

    if "订单" in q and any(word in q for word in ["量", "数", "多少"]):
        if region_value:
            sql = f"""
            SELECT users.region AS region, COUNT(DISTINCT orders.order_id) AS order_count
            FROM orders
            JOIN users ON users.user_id = orders.user_id
            WHERE orders.status = 'paid'
              AND users.region = '{region_value}'
              AND {_date_predicate("orders.paid_at", start, end, today)}
            GROUP BY users.region
            ORDER BY order_count DESC
            """
            return SQLPlan(
                intent="order_count_by_region",
                metrics=["order_count"],
                dimensions=["region"],
                time_range={"start": start or "", "end": end or ""},
                filters=filters,
                sql=sql.strip(),
                chart_type="bar",
                answer_hint=f"{region_label}订单量",
            )
        sql = f"""
        SELECT channels.channel_name AS channel, COUNT(DISTINCT orders.order_id) AS order_count
        FROM orders
        JOIN channels ON channels.channel_id = orders.channel_id
        WHERE orders.status = 'paid'
          AND {_date_predicate("orders.paid_at", start, end, today)}
        GROUP BY channels.channel_name
        ORDER BY order_count DESC
        """
        return SQLPlan(
            intent="order_count_by_channel",
            metrics=["order_count"],
            dimensions=["channel"],
            time_range={"start": start or "", "end": end or ""},
            filters=filters,
            sql=sql.strip(),
            chart_type="bar",
            answer_hint="按渠道订单量",
        )

    if any(word in q for word in ["客单价", "AOV"]):
        if region_value:
            sql = f"""
            SELECT users.region AS region, AVG(orders.pay_amount) AS aov
            FROM orders
            JOIN users ON users.user_id = orders.user_id
            WHERE orders.status = 'paid'
              AND users.region = '{region_value}'
              AND {_date_predicate("orders.paid_at", start, end, today)}
            GROUP BY users.region
            ORDER BY aov DESC
            """
            return SQLPlan(
                intent="aov_by_region",
                metrics=["aov"],
                dimensions=["region"],
                time_range={"start": start or "", "end": end or ""},
                filters=filters,
                sql=sql.strip(),
                chart_type="bar",
                answer_hint=f"{region_label}客单价",
            )
        sql = f"""
        SELECT channels.channel_name AS channel, AVG(orders.pay_amount) AS aov
        FROM orders
        JOIN channels ON channels.channel_id = orders.channel_id
        WHERE orders.status = 'paid'
          AND {_date_predicate("orders.paid_at", start, end, today)}
        GROUP BY channels.channel_name
        ORDER BY aov DESC
        """
        return SQLPlan(
            intent="aov_by_channel",
            metrics=["aov"],
            dimensions=["channel"],
            time_range={"start": start or "", "end": end or ""},
            filters=filters,
            sql=sql.strip(),
            chart_type="bar",
            answer_hint="按渠道客单价",
        )

    if any(word in q for word in ["活跃用户", "活跃人数"]):
        sql = f"""
        SELECT {_date_group("user_events.event_time")} AS day, COUNT(DISTINCT user_events.user_id) AS active_user_count
        FROM user_events
        WHERE {_date_predicate("user_events.event_time", start, end, today)}
        GROUP BY {_date_group("user_events.event_time")}
        ORDER BY day
        """
        return SQLPlan(
            intent="active_users_trend",
            metrics=["active_user_count"],
            dimensions=["day"],
            time_range={"start": start or "", "end": end or ""},
            filters=filters,
            sql=sql.strip(),
            chart_type="line",
            answer_hint="活跃用户趋势",
        )

    if any(word in q for word in ["品类", "类目", "商品"]) and any(word in q for word in ["销量", "件数"]):
        sql = f"""
        SELECT products.category AS category, SUM(orders.quantity) AS item_quantity
        FROM orders
        JOIN products ON products.product_id = orders.product_id
        WHERE orders.status = 'paid'
          AND {_date_predicate("orders.paid_at", start, end, today)}
        GROUP BY products.category
        ORDER BY item_quantity DESC
        """
        return SQLPlan(
            intent="item_quantity_by_category",
            metrics=["item_quantity"],
            dimensions=["category"],
            time_range={"start": start or "", "end": end or ""},
            filters=filters,
            sql=sql.strip(),
            chart_type="bar",
            answer_hint="按品类销量",
        )

    # generic fallback
    sql = f"""
    SELECT {_date_group("orders.paid_at")} AS day, SUM(orders.pay_amount) AS gmv
    FROM orders
    WHERE orders.status = 'paid'
      AND {_date_predicate("orders.paid_at", start, end, today)}
    GROUP BY {_date_group("orders.paid_at")}
    ORDER BY day
    """
    return SQLPlan(
        intent="fallback_gmv_trend",
        metrics=["gmv"],
        dimensions=["day"],
        time_range={"start": start or "", "end": end or ""},
        filters=filters,
        sql=sql.strip(),
        chart_type="line",
        answer_hint="默认按天GMV趋势",
    )


def _llm_plan(question: str, ctx: RetrievedContext) -> SQLPlan:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except Exception:
        return _offline_plan(question, ctx)

    settings = get_settings()
    prompt = f"""你是企业数据分析助手，只能输出 JSON，不能输出多余文本。
你必须生成单条只读 SQL，且只允许 SELECT 查询。
业务问题：{question}
可用表：
{ctx.schema_text}
可用指标：
{ctx.metric_text}
要求：
1. 如果信息不足，仍尽量给出最可能查询；
2. 结果必须可被 SQL 执行；
3. chart_type 只能是 table/kpi/bar/line/pie/scatter;
4. sql 不得包含写操作，不得包含多语句，不得使用 SELECT *;
5. 优先使用 orders, users, products, channels, user_events。

请输出字段：intent, metrics, dimensions, time_range, filters, sql, chart_type, answer_hint
"""
    llm = ChatOpenAI(
        model=settings.llm_model_name,
        temperature=0,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
    messages = [
        SystemMessage(content="You are a precise SQL planner."),
        HumanMessage(content=prompt),
    ]
    content = llm.invoke(messages).content
    if isinstance(content, str):
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            if raw.endswith("```"):
                raw = raw[:-3]
        raw = raw.strip()
        data = json.loads(raw)
        return SQLPlan.model_validate(data)
    return _offline_plan(question, ctx)


def plan_query(question: str, ctx: RetrievedContext) -> SQLPlan:
    settings = get_settings()
    if settings.use_llm and settings.llm_api_key:
        try:
            return _llm_plan(question, ctx)
        except Exception:
            return _offline_plan(question, ctx)
    return _offline_plan(question, ctx)
