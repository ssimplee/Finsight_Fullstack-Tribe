# Member 4 交付 — RAG + Agent 推理 + Qwen 推理器（含 Member 3 对接）

分支：`person4-rag-agent`（已 merge 最新 `dev` + `person3-Vision-Analysis`）
本地 tip：`45cb9a3`　待推 commit：14 个

## 我交付了什么

### 核心模块（four/src/）
| 模块 | 作用 |
|---|---|
| `ingest.py` | 知识库 → ChromaDB 向量库（默认读 `data/knowledge/knowledge_chunks.jsonl`，空库自动灌） |
| `retriever.py` | 多模态 query 拼接 + 检索 + 元数据过滤；**空库自愈**（count==0 自动 ingest） |
| `missing_info.py` | 检测缺失的水质/病史字段，按重要性排序 |
| `follow_up.py` | 自适应追问生成，每问带 reason（worksplit §13.5） |
| `differential.py` | 鉴别排序（症状关键词 + 证据类型加权，supporting +2 / conflicting -1.5） |
| `uncertainty.py` | 不确定度评估（low/medium/high） |
| `safety.py` | 安全检查（blocked phrases）+ 安全行动 + escalation |
| `contradiction.py` | 跨模态矛盾检测（worksplit §13.3） |
| `agent.py` | 状态机：Intake→ImageObs→MissingInfo→FollowUp→Retrieve→Differential→Uncertainty→Safety→Report |
| `qwen_reasoner.py` | **Qwen LLM 推理**：读检索证据+排序，写带证据引用的最终解释（worksplit §5） |
| `qwen_client.py` | MockQwenClient + RealQwenAdapter（桥接 Member 3 的 VisionResult） |

### backend 接入
- `rag_service.py`：lazy 加载 four/src，`FINSIGHT_USE_RAG=1` 开启，默认走 Member 1 mock 不破坏现有测试
- `case_service.py`：`generate_follow_up_questions` + `generate_report` 接 rag_service
- `schemas/case.py`：加 `agent_trace` 字段（worksplit §13.6 决策轨迹）
- `eval_cases.py`：跑 Member 2 测试集打分（基线 3/5，2 个 miss 是症状重叠场景）
- `eval_full_pipeline.py`：**端到端真后端 API 测试**（TestClient 跑完整链路）
- `.env.example`：两个开关 + Qwen 配置

## 和 Member 3 的对接（已 merge 进本分支）

Member 3 的 `person3-Vision-Analysis` 已合进本分支，`case_service.py` 冲突已解：
- **Member 3**：`attach_image` 时调 Qwen vision，把观察填进 `CaseImage.visible_findings`
- **Member 4**：读 `visible_findings` 喂 retriever/differential，**不用直接调 Qwen**
- `case_service.py` 两人改不同方法（Member 3 改 attach_image，我改 follow_ups/report），互补不冲突
- 共享 `QWEN_API_KEY`（Member 3 vision + Member 4 reasoner 用同一个 key）

## 端到端验证结果（校园网真跑通）

`FINSIGHT_USE_RAG=1 FINSIGHT_USE_QWEN_REASONER=1 QWEN_API_KEY=sk-szu-... python backend/eval_full_pipeline.py`

```
[2] image uploaded -> Member 3 Qwen vision findings:
      - scale loss on flank / redness on flank / frayed caudal fin / eye opacity / mouth lesion
[3] follow-up questions (4): 氨氮/死亡率/过滤故障/亚硝酸盐（各带 reason）
[5] FULL PIPELINE REPORT
STATUS: report_ready
EVIDENCE: 10 chunks
DIFFERENTIAL: #1 D02(strong) > #2 D04(moderate) > #3 D03(moderate)
SUMMARY: Qwen 写的，带 7+ [EVID_KB_*] 证据引用，列 4 备选、标不确定、给安全建议
AGENT TRACE 末行: Summary: Qwen
```

## 给各 member 的对接说明

### Member 1（backend/集成）
- 把 `person4-rag-agent` 合进 `dev`。`case_service.py` 已和 Member 3 解过冲突，应该无冲突
- 默认 `FINSIGHT_USE_RAG=0` 走你原来的 mock，不影响现有测试；要开真 RAG 设 `FINSIGHT_USE_RAG=1`
- 依赖：`chromadb` + `sentence-transformers`（可选，没装自动回退 mock）
- 部署时首次启动 `four/fin_sight_db/` 不存在 → Retriever 自动 ingest 真数据，不用手动跑

### Member 3（Qwen vision）
- 你的分支已合进 `person4-rag-agent`，`case_service.attach_image` 的 `_observe_image` 保留
- 我没改你的 vision 代码，只读了 `visible_findings`
- `RealQwenAdapter`（four/src/qwen_client.py）给我独立跑 agent 时用，不影响你的 backend 流程
- 共享 `QWEN_API_KEY`，你的 vision 和我的 reasoner 用同一个

### Member 5（前端）
- 报告页可以多渲染一个字段：`case.agent_trace`（list[str]，agent 决策轨迹，worksplit §13.6）
- `summary` 字段现在可能是 Qwen 写的自然语言（带 `[EVID_KB_*]` 引用），比之前的模板句丰富，注意展示别截断
- 其他字段（differential/evidence/actions/escalation）结构没变

### Member 2（数据）
- 你的 8 个测试 case + 4 张图全保留，我 merge 了最新 dev
- `eval_cases.py` 跑你的 case 打分基线 3/5，2 个 miss（CASE_002 气单胞菌、CASE_003 柱状病）是症状重叠，D02 关键词太贪——可一起调 differential 关键词

## 待办
- [ ] `git push origin person4-rag-agent`
- [ ] Member 1 开 PR 合 dev
- [ ] 可选：调 differential 关键词把 CASE_002/003 的重叠症状打分拉正
- [ ] §13.4 observation/inference 标签：留作团队设计项（加独立 provenance 字段，不动现有 label）
