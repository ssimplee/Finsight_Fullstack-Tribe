# four/ — Member 4 个人开发区

> Member 4（RAG + Agent 推理）的工作副本。
> 这里的代码先独立迭代，等接口与 Member 1/2 确认后再迁入 `backend/app/services/rag/`。

## 目录约定

- `run_demo.py` — **主入口**，一键跑 3 个 mock case 的端到端演示（不依赖 Qwen）
- `src/` — 模块化代码：
  - `models.py` — Pydantic 模型，字段与 `backend/app/schemas/case.py` 对齐
  - `ingest.py` — 读 jsonl → embed → ChromaDB（幂等 upsert）
  - `retriever.py` — query 拼接 + 检索 + 元数据过滤
  - `missing_info.py` / `follow_up.py` / `differential.py` / `uncertainty.py` / `safety.py` / `agent.py` — 推理层
- `mock_kb/knowledge_chunks.jsonl` — 自造的 5 条件 mock 知识库（D01–D05，33 条）
- `models/all-MiniLM-L6-v2/` — 本地嵌入模型（已下载，离线可用）
- `fin_sight_db/` — ChromaDB 向量库（运行时生成）
- `test_rag.py` / `knowledge_chunks_sample.jsonl` — 早期 smoke test + 占位数据（保留，已被上面取代）
- `PREP_PLAN.md` — 准备计划清单
- `CONTRACT_PROPOSAL.md` — 发给 Member 1/2 的接口草案

## 运行（端到端 demo）

```bash
cd four
python run_demo.py
```

会依次：建库（幂等 upsert）→ 跑 `CASE_MOCK_CLEAR` / `CASE_MOCK_INCOMPLETE` / `CASE_MOCK_OVERLAP` 三个 case，打印追问、鉴别排序、不确定性、安全行动与 escalation。

**依赖**：`chromadb` + `sentence-transformers`（你已 `pip install` 过）。

**嵌入模型**：默认优先用本地 `models/all-MiniLM-L6-v2/`（已下载好，**离线可用**，无需翻墙）。也可用环境变量覆盖：

```bash
FINSIGHT_MODEL_PATH=/path/to/model python run_demo.py
```

## 国内网络说明

HuggingFace 直连常超时。两个办法：

1. **用已下载的本地模型**（默认已配好，见上）。
2. 需要在线下载时挂镜像：`HF_ENDPOINT=https://hf-mirror.com python run_demo.py`

## 下一站

1. 读 `PREP_PLAN.md` 看剩余项（Git init、venv、单测等）
2. `CONTRACT_PROPOSAL.md` 发给 Member 1 和 Member 2 等确认
3. Member 2 真数据就绪后，替换 `mock_kb/` 输入、重新 `python run_demo.py` 即可
