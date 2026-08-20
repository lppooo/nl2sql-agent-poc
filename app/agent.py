from __future__ import annotations

import time

from app.charting import build_chart_spec
from app.executor import execute_sql
from app.models import AgentResponse, TraceStep
from app.planner import plan_query
from app.schema_retriever import retrieve_context
from app.sql_safety import validate_sql


UNSAFE_SQL_PATTERNS = [
    "drop table",
    "delete from",
    "update ",
    "insert into",
    "alter table",
    "create table",
    "truncate table",
    "select *",
]


def _looks_like_raw_sql(question: str) -> bool:
    q = question.lower().strip()
    return ";" in q or any(pattern in q for pattern in UNSAFE_SQL_PATTERNS)


def _render_answer(question: str, rows: list[dict], chart_type: str) -> str:
    if not rows:
        return "没有查到匹配结果。"
    head = rows[0]
    summary_bits = [f"{k}={v}" for k, v in list(head.items())[:3]]
    if chart_type == "line":
        return f"已生成趋势结果，首行数据：{', '.join(summary_bits)}。"
    if chart_type == "bar":
        return f"已生成对比结果，首行数据：{', '.join(summary_bits)}。"
    return f"已返回查询结果，首行数据：{', '.join(summary_bits)}。"


class NL2SQLAgent:
    def run(self, question: str, include_trace: bool = True) -> AgentResponse:
        start = time.perf_counter()
        trace: list[TraceStep] = []

        if _looks_like_raw_sql(question):
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            trace.append(
                TraceStep(
                    step="input_guard",
                    thought="检测到疑似原生 SQL 或危险指令，直接拦截。",
                    action=question,
                    observation="blocked",
                )
            )
            return AgentResponse(
                question=question,
                answer="查询被拦截：检测到原生 SQL 或危险语句。",
                sql=None,
                columns=[],
                rows=[],
                chart=build_chart_spec(question, [], []),
                trace=trace if include_trace else [],
                latency_ms=latency_ms,
                safety_passed=False,
            )

        ctx = retrieve_context(question)
        trace.append(
            TraceStep(
                step="schema_recall",
                thought="先缩小可用表和指标范围，减少幻觉和错误 Join。",
                action=f"召回表={ctx.tables}, 指标={ctx.metrics}",
                observation=ctx.schema_text[:500],
            )
        )

        plan = plan_query(question, ctx)
        trace.append(
            TraceStep(
                step="sql_plan",
                thought="根据问题和业务口径生成结构化 SQL 计划。",
                action=plan.sql,
                observation=f"intent={plan.intent}, chart={plan.chart_type}",
            )
        )

        validation = validate_sql(plan.sql)
        trace.append(
            TraceStep(
                step="sql_validation",
                thought="执行前先做 AST 与权限校验。",
                action=validation.sql or plan.sql,
                observation=validation.reason or f"tables={validation.touched_tables}",
            )
        )

        if not validation.ok:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return AgentResponse(
                question=question,
                answer=f"查询被拦截：{validation.reason}",
                sql=None,
                columns=[],
                rows=[],
                chart=build_chart_spec(question, [], []),
                trace=trace if include_trace else [],
                latency_ms=latency_ms,
                safety_passed=False,
            )

        result = execute_sql(validation.sql or plan.sql)
        trace.append(
            TraceStep(
                step="sql_execution",
                thought="只读执行数据库查询并收集结果。",
                action=validation.sql or plan.sql,
                observation=f"row_count={result.row_count}, elapsed_ms={result.elapsed_ms}",
            )
        )

        chart = build_chart_spec(question, result.columns, result.rows)
        answer = _render_answer(question, result.rows, chart.chart_type)

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return AgentResponse(
            question=question,
            answer=answer,
            sql=validation.sql or plan.sql,
            columns=result.columns,
            rows=result.rows,
            chart=chart,
            trace=trace if include_trace else [],
            latency_ms=latency_ms,
            safety_passed=True,
        )
