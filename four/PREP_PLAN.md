# Member 4 — RAG + Agent 准备计划

> 负责人：Member 4（你）
> 状态：前面任务（Member 1/2/3）尚未交付；以下工作**不依赖**前面成员的产出，可立即推进。
> 最后更新：2026-08-18

---

## 1. 你的职责边界（对照 worksplit §9 Member 4）

- 知识入库（ingestion）
- 嵌入模型 + 向量库
- 证据检索
- 缺失信息检测
- 追问逻辑
- 鉴别诊断排序
- 支持/冲突证据标注
- 不确定性
- 证据 ID 体系
- 安全检查

**你不需要做**：后端 API、Qwen 客户端、前端、疾病领域知识收集（最后一条由 Member 2 提供数据）。

---

## 2. 现状盘点

| 项 | 现状 | 评价 |
|---|---|---|
| four/ 目录 | 已存在，含 `test_rag.py` + `knowledge_chunks_sample.jsonl` | OK |
| `pip install chromadb sentence-transformers` | 已运行 | OK |
| 嵌入模型 | `all-MiniLM-L6-v2`（轻量，~80MB） | 合理起步 |
| Python 环境 | 未见 venv，疑似全局安装 | **建议补 venv** |
| Git | 仓库无 `.git`，与 GitHub 脱钩 | **建议 init + remote** |
| `test_rag.py` | 跑通即丢的脚本 | 不是最终交付物，需替换 |
| 样本数据 | 金鱼 ICH/FINROT/STRESS/VELVET | **与项目 scope 不符**，需替换为罗非鱼 5 条件 mock |
| `backend/app/services/rag_service.py` | 仅 `raise NotImplementedError` | 需与 Member 1 共同扩成真实接口 |
| `backend/app/schemas/case.py` | 已定 `EvidenceItem` / `AgentQuestion` / `DifferentialItem` | **你的输出必须严格对齐这些 Pydantic 字段** |
| `shared/schemas/case.schema.json` | 已定 JSON Schema | 同上，是 source of truth |
| 证据 ID 约定 | FishDiag 参考样例使用 `EVID_xxx` / `OBS_xxx` | **照搬并扩充**为 `OBS_/EVID_/Q_/KB_/COND_` |

---

## 3. 可独立完成的准备工作（按优先级）

### A. 环境与工程化（今天）

- [ ] 在仓库根建 venv：`python -m venv .venv`
- [ ] 用 venv 重装依赖：`pip install chromadb sentence-transformers pydantic pytest`
- [ ] VSCode 选择 `.venv/bin/python`（或 Windows 的 `Scripts/python.exe`）作为工作区解释器
- [ ] 加 `.vscode/settings.json` + `.vscode/launch.json`，配置 retriever / follow-up / differential 三个调试入口
- [ ] 在仓库根 `git init` 并加 remote：`git remote add origin https://github.com/ssimplee/Finsight_Fullstack-Tribe.git`
- [ ] 从 main 拉分支：`git checkout -b feat/member4-rag-agent`
- [ ] `.gitignore` 排除 `.venv/`、`fin_sight_db/`、模型缓存 `~/.cache/torch/` 等

### B. 锁定契约（今天发出去）

- [ ] **给 Member 2** 发 `knowledge_chunks.jsonl` 字段确认：
  ```json
  {
    "chunk_id": "KB_D01_001",
    "condition_id": "D01",
    "evidence_type": "symptom | risk_factor | differential | confirmation | safe_action | conflicting | water_quality",
    "text": "……",
    "source_id": "SRC_001",
    "page_or_section": "p.12 / §3.2"
  }
  ```
  - condition_id 用 `D01–D05`
  - evidence_type 用上面的受控词表
- [ ] **给 Member 1** 发 `RagService` 真实接口提案（在 `four/CONTRACT_PROPOSAL.md` 写好）：
  ```python
  class RagService:
      def retrieve(self, query: str, case_ctx: dict) -> list[EvidenceItem]: ...
      def detect_missing(self, case: CaseRecord) -> list[str]: ...
      def follow_up_questions(self, case: CaseRecord, missing: list[str]) -> list[AgentQuestion]: ...
      def rank_differential(self, case: CaseRecord, evidence: list[EvidenceItem]) -> list[DifferentialItem]: ...
      def uncertainty(self, case: CaseRecord, diff: list[DifferentialItem]) -> str: ...
      def safety_check(self, case: CaseRecord, diff: list[DifferentialItem]) -> tuple[list[str], list[str]]: ...
      def run(self, case: CaseRecord) -> CaseReport: ...
  ```
- [ ] **全员**对齐证据 ID 命名：
  - `OBS_xxx` — Qwen 图像/行为观察
  - `EVID_xxx` — RAG 检索片段
  - `Q_xxx` — 追问问题
  - `KB_xxx` — 知识库原始条目
  - `COND_xxx` — 疾病档

### C. 独立可跑的 RAG 流水线（不依赖 Member 2 真实数据）

- [ ] 造一份 5 条件 mock 知识库 `four/mock_kb/knowledge_chunks.jsonl`，每条件 3–5 条；文件首行注明 `// MOCK — to be replaced by Member 2`：
  - D01 Streptococcosis
  - D02 Motile Aeromonas Septicemia
  - D03 Columnaris
  - D04 TiLV
  - D05 Water-quality stress / hypoxia / ammonia or nitrite
- [ ] 写 `four/src/ingest.py`：读 jsonl → embed（`all-MiniLM-L6-v2`）→ 写入 ChromaDB 集合 `fish_disease_kb`，路径 `four/fin_sight_db/`
- [ ] 写 `four/src/retriever.py`：
  - query 拼接：observations 文本 + symptoms 关键词 + water 数值异常项
  - `n_results=8~12`
  - 支持按 `condition_id` / `evidence_type` 元数据过滤
  - 返回 Pydantic `EvidenceItem` 列表
- [ ] 持久化路径最终落到 `backend/data/vector_db/`（等 Member 1 确认）
- [ ] 保证删 DB 后能用 `ingest.py` 一键重建

### D. 智能体推理层骨架（核心，数据/前端解耦）

- [ ] `four/src/missing_info.py`：
  - 6 项水质 `null` 检测
  - `history` 关键字段（mortality trend / recent introduction / feed change / treatment / water change 等）检测
  - observations 缺失检测
  - 返回结构化 `missing` 列表
- [ ] `four/src/follow_up.py`：
  - 基于 missing + 已观察到症状
  - 按优先级排序（关键 > 次要）
  - ≥2 个问题，每个带 `reason` 字段
  - 输出 Pydantic `AgentQuestion` 列表
- [ ] `four/src/differential.py`：
  - 对每条 evidence 打 supporting/conflicting（用 evidence_type + 关键词初版）
  - 打分：`score = supporting - 0.5*conflicting + 关键症状命中加权`
  - 排序后输出 Pydantic `DifferentialItem` 列表
  - `confirmation_status` 默认为 `unconfirmed`
- [ ] `four/src/uncertainty.py`：
  - 根据"关键字段缺失数"+"打分差距"输出 `low / medium / high`
- [ ] `four/src/safety.py`：
  - 拦截"立即用某药"、"确诊"等不当措辞
  - 强制出现 confirmation / escalation 段
  - 返回 `(recommended_actions, escalation)` 两个 list[str]
- [ ] `four/src/agent.py`：状态机
  ```text
  Intake → ImageObs → MissingInfo → FollowUp
        → Retrieve → Differential → Uncertainty → Safety → Report
  ```
  - 每步产出 trace 条目（实现 worksplit §13 Priority 6 的 Agent Decision Trace）

### E. 测试

- [ ] `four/tests/test_retriever.py` — mock 嵌入和 collection
- [ ] `four/tests/test_missing_info.py` — null 字段检测
- [ ] `four/tests/test_followup_priority.py` — 排序与 reason 字段
- [ ] `four/tests/test_differential_scoring.py` — 评分与 supporting/conflicting
- [ ] `four/tests/test_safety.py` — 不当措辞拦截
- [ ] `four/tests/test_e2e_mock_case.py` — 端到端 mock case（不调 Qwen），跑完整个 agent flow，断言 `CaseReport` 字段齐
- [ ] 跑分雏形：照 worksplit §12 评价表（follow-up / retrieval / grounding / conflict / uncertainty / safety / actionability）

### F. 文档与协作

- [ ] `four/README.md` — 模块说明、跑法、扩展点
- [ ] `four/PREP_PLAN.md` — 本文件
- [ ] `four/CONTRACT_PROPOSAL.md` — 上面 B 节的接口提案，整理成给 Member 1/2 的 RFC
- [ ] （可选）`docs/MEMBER4_CONTRACT.md` — 经全员确认后归档

---

## 4. 与其他成员的依赖

| 等谁 | 拿什么 | 你能怎么并行 |
|---|---|---|
| Member 2 | `conditions.json` / `sources.json` / `knowledge_chunks.jsonl` / 图像元数据 / 30–45 评测 case | 用 mock 知识库 + mock case 跑通整条管道；只等真数据时换 ingestion 输入 |
| Member 1 | `RagService` 真实签名 / FastAPI 路由 / 部署 | 在 four/ 按你提的接口实现；最后做一次 import 替换；提前准备好 PR |
| Member 3 | Qwen `observations.visual/behavioral` 喂入 | 用假 observations 写 retriever query 拼接；Member 3 接进来时只换数据源 |

---

## 5. 建议模块结构

```text
Finsight_Fullstack-Tribe-main/
  four/                          # 你现在的个人开发/实验区
    README.md
    PREP_PLAN.md                 # 本文件
    CONTRACT_PROPOSAL.md
    test_rag.py                  # 现有 smoke test（保留）
    knowledge_chunks_sample.jsonl # 现有 mock（保留，标注 MOCK）
    mock_kb/
      knowledge_chunks.jsonl     # 你造的 5 条件 mock
    src/                         # 个人版模块（先在这里迭代）
      ingest.py
      retriever.py
      missing_info.py
      follow_up.py
      differential.py
      uncertainty.py
      safety.py
      agent.py
    tests/
      test_retriever.py
      test_missing_info.py
      test_followup_priority.py
      test_differential_scoring.py
      test_safety.py
      test_e2e_mock_case.py
  backend/app/services/rag/      # 最终交付位置（等 Member 1 确认后迁）
    # 与 src/ 同结构
```

---

## 6. 一周推进表（建议）

| 天 | 目标 |
|---|---|
| D1 | A 节全部 + B 节草案发出 |
| D2 | C 节 mock KB + ingest.py + retriever.py + 跑通 smoke |
| D3 | D 节 missing_info + follow_up 完成 + 单测 |
| D4 | D 节 differential + uncertainty + safety 完成 + 单测 |
| D5 | D 节 agent.py 状态机 + e2e mock case 测试通过 |
| D6 | 性能/边界 case + evaluation rubric 雏形 |
| D7 | 文档 + PR 准备（等 Member 1/2 一就位就合入） |

---

## 7. 输出对齐 checklist（提交前自检）

- [ ] `EvidenceItem` 字段：`evidence_id` / `condition_id` / `source_id` / `label` / `text` 全部有值
- [ ] `AgentQuestion` 字段：`question_id` / `question` / `reason` 必填，`answer` 可空
- [ ] `DifferentialItem` 字段：`condition_id` / `rank` / `evidence_strength` / `uncertainty` / `supporting_evidence_ids` / `conflicting_evidence_ids` / `confirmation_status`
- [ ] 至少 2 个 follow-up 问题，每个带 reason
- [ ] differential 至少 2 个候选（命中时），不强行单诊断
- [ ] 不确定性字段非空
- [ ] recommended_actions 至少包含 1 条 confirmation + 1 条 monitoring
- [ ] escalation 至少 1 条（命中 escalation trigger 时）
- [ ] 所有证据 ID 可在 `retrieved_evidence` 里反查到
