from __future__ import annotations

from fastapi import FastAPI

from app.agent import NL2SQLAgent
from app.bootstrap import build_sample_database
from app.models import AgentRequest, AgentResponse


app = FastAPI(title="NL2SQL Agent POC", version="0.1.0")
agent = NL2SQLAgent()


@app.on_event("startup")
def _startup() -> None:
    build_sample_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=AgentResponse)
def query(payload: AgentRequest) -> AgentResponse:
    return agent.run(payload.question, include_trace=payload.include_trace)

