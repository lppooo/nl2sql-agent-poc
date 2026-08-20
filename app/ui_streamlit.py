from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.agent import NL2SQLAgent
from app.bootstrap import build_sample_database


st.set_page_config(page_title="NL2SQL Agent POC", layout="wide")
st.title("NL2SQL 数据分析 Agent POC")
st.caption("默认离线运行；配置 LLM 后可切到真实规划器。")

build_sample_database()
agent = NL2SQLAgent()

question = st.text_input(
    "输入你的业务问题",
    value="上个月各渠道GMV是多少？",
    placeholder="例如：近30天按天GMV趋势",
)
include_trace = st.checkbox("显示 Agent 轨迹", value=True)

if st.button("查询", type="primary"):
    response = agent.run(question, include_trace=include_trace)
    st.metric("端到端耗时(ms)", response.latency_ms)
    st.write(response.answer)
    st.code(response.sql or "", language="sql")

    if response.rows:
        df = pd.DataFrame(response.rows)
        st.dataframe(df, use_container_width=True)
        if response.chart.chart_type == "line" and response.chart.x_field and response.chart.y_fields:
            fig = px.line(df, x=response.chart.x_field, y=response.chart.y_fields[0], title=response.chart.title)
            st.plotly_chart(fig, use_container_width=True)
        elif response.chart.chart_type == "bar" and response.chart.x_field and response.chart.y_fields:
            fig = px.bar(df, x=response.chart.x_field, y=response.chart.y_fields[0], title=response.chart.title)
            st.plotly_chart(fig, use_container_width=True)
        elif response.chart.chart_type == "pie" and response.chart.x_field and response.chart.y_fields:
            fig = px.pie(df, names=response.chart.x_field, values=response.chart.y_fields[0], title=response.chart.title)
            st.plotly_chart(fig, use_container_width=True)

    if include_trace:
        st.subheader("Agent 轨迹")
        for step in response.trace:
            with st.expander(step.step, expanded=False):
                st.write("Thought:", step.thought)
                st.write("Action:", step.action)
                st.write("Observation:", step.observation)

