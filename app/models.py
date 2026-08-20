from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    include_trace: bool = True


class TraceStep(BaseModel):
    step: str
    thought: str
    action: str
    observation: str


class SQLPlan(BaseModel):
    intent: str
    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    time_range: dict[str, str] = Field(default_factory=dict)
    filters: list[dict[str, Any]] = Field(default_factory=list)
    sql: str
    chart_type: Literal["table", "kpi", "bar", "line", "pie", "scatter"] = "table"
    answer_hint: str = ""


class ValidationResult(BaseModel):
    ok: bool
    sql: str | None = None
    reason: str | None = None
    touched_tables: list[str] = Field(default_factory=list)


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    elapsed_ms: float


class ChartSpec(BaseModel):
    chart_type: str
    x_field: str | None = None
    y_fields: list[str] = Field(default_factory=list)
    title: str


class AgentResponse(BaseModel):
    question: str
    answer: str
    sql: str | None
    columns: list[str]
    rows: list[dict[str, Any]]
    chart: ChartSpec
    trace: list[TraceStep] = Field(default_factory=list)
    latency_ms: float
    safety_passed: bool
