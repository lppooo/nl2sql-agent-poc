# 架构说明

1. `schema_retriever` 负责召回相关表和指标口径。
2. `planner` 负责把业务问题转成结构化 SQL 计划。
3. `sql_safety` 负责只读与白名单校验。
4. `executor` 负责执行 SQL。
5. `charting` 负责图表类型选择。
6. `agent` 串起全链路并返回 trace。
7. `api` 和 `ui_streamlit` 负责外部交互。

