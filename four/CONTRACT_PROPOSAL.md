# CONTRACT_PROPOSAL — Member 4 → Member 1/2 接口草案（RFC）

> 状态：**待确认**。这是 Member 4（RAG + Agent）提出的接口约定，请 Member 1、Member 2 审阅。
> 确认后归档到 `docs/MEMBER4_CONTRACT.md`。

---

## 1. 给 Member 2：`data/knowledge/knowledge_chunks.jsonl` 字段

每行一个 JSON 对象，字段如下（`chunk_id` 必填且全局唯一）：

```json
{
  "chunk_id": "KB_D01_001",
  "condition_id": "D01",
  "condition_name": "Streptococcosis",
  "evidence_type": "symptom",
  "text": "……一句话~三句话的知识片段……",
  "source_id": "SRC_001",
  "source_title": "WOAH Manual of Diagnostic Tests for Aquatic Animals",
  "section": "Clinical signs",
  "source_url": "https://……"
}
```

约定：

| 字段 | 说明 |
|---|---|
| `chunk_id` | 唯一 ID，格式 `KB_{condition_id}_{seq}`（如 `KB_D01_001`）。RAG 返回时会映射为 `EVID_xxx` |
| `condition_id` | 受控值 `D01`–`D05`，与 `conditions.json` 对齐 |
| `evidence_type` | 受控词表，见下方 §4 |
| `text` | 检索主文本，建议 1–3 句、语义完整，避免过短（<10 词）或过长（>200 词） |
| `source_id` | 指向 `sources.json` 的 ID |
| `source_title` / `section` / `source_url` | 用于报告中的证据溯源（traceability），**建议保留** |

> 我们的 mock 版本在 `four/mock_kb/knowledge_chunks.jsonl`，可先照这个格式跑通，真数据就绪后替换即可。

---

## 2. 给 Member 1：`RagService` 真实接口

现在 `backend/app/services/rag_service.py` 只有：

```python
class RagService:
    def retrieve(self, query: str) -> list[dict]:
        raise NotImplementedError
```

建议扩成下面这套（输入输出全部对齐 `app/schemas/case.py` 的 Pydantic 模型）：

```python
class RagService:
    def retrieve(self, case: CaseRecord, n_results: int = 10) -> list[EvidenceItem]: ...
    def detect_missing(self, case: CaseRecord) -> list[MissingItem]: ...
    def follow_up_questions(self, case: CaseRecord) -> list[AgentQuestion]: ...
    def rank_differential(self, case: CaseRecord, evidence: list[EvidenceItem]) -> list[DifferentialItem]: ...
    def assess_uncertainty(self, case: CaseRecord, missing: list[MissingItem], diff: list[DifferentialItem]) -> str: ...
    def safety_check(self, case: CaseRecord, diff: list[DifferentialItem]) -> tuple[list[str], list[str]]: ...
    def run(self, case: CaseRecord) -> CaseReport: ...
```

说明：

- `run()` 是编排入口，内部按状态机顺序调用以上方法，返回完整 `CaseReport`。
- `MissingItem` 是**新增**的轻量结构，建议 Member 1 在 `schemas/case.py` 加：

```python
class MissingItem(BaseModel):
    field: str
    label: str
    importance: str   # critical | important | secondary
    why: str
```

- `retrieve()` 的 `query` 由 Member 4 内部用 `observations + water 异常项 + history` 拼接，Member 1 只需传完整 `case`。

---

## 3. 证据 ID 命名（全员对齐）

| 前缀 | 含义 | 生成方 |
|---|---|---|
| `OBS_xxx` | 图像/行为观察（Qwen 输出） | Member 3 |
| `EVID_xxx` | RAG 检索证据片段 | Member 4 |
| `Q_xxx` | 追问问题 | Member 4 |
| `KB_xxx` | 知识库原始条目 | Member 2 |
| `COND_xxx` / `D01–D05` | 疾病档 | Member 2 |
| `CASE_xxx` | 案例 | Member 1/后端 |

`EVID_xxx` 可反查回 `KB_xxx`（`EVID_KB_D01_001` → `KB_D01_001`），用于证据溯源。

---

## 4. `evidence_type` 受控词表

| 值 | 含义 |
|---|---|
| `symptom` | 视觉/行为症状 |
| `risk_factor` | 风险因素 |
| `water_quality` | 水质关联 |
| `differential` | 鉴别诊断 |
| `confirmation` | 确认/检测方法 |
| `safe_action` | 安全处置 |
| `escalation` | 升级触发 |
| `conflicting` | 冲突/例外证据 |

> 这条词表同时约束 Member 2 写库和 Member 4 的评分逻辑，请勿随意新增。

---

## 5. 待确认清单

- [ ] `knowledge_chunks.jsonl` 字段是否增加 `species` / `evidence_label`？
- [ ] `RagService` 是否直接拿 `CaseRecord` 还是单独建 `RagRequest`？
- [ ] 向量库最终落盘路径：`backend/data/vector_db/` 还是 `backend/.chroma/`？
- [ ] 嵌入模型是否仍用 `all-MiniLM-L6-v2`，还是统一走 Qwen embedding？

---

## 6. 给 Member 3：Qwen 图像观察对接

Member 4 的 agent 在 ImageObs 步骤调用 Member 3 的 Qwen 客户端，把图像变成可检索、可溯源的观察证据。当前 `four/src/qwen_client.py` 已提供该接口定义 + `MockQwenClient`（按文件名返回预设观察），Member 3 实现真接口后直接替换。

### 6.1 接口契约

`backend/app/services/qwen_client.py` 现有占位只返回 `list[str]`，建议升级为结构化 `ImageObservation`：

```python
@dataclass
class ImageObservation:
    visual: list[str]      # 可见发现，如 ["flank ulcer", "scale loss"]
    behavioral: list[str]  # 图像可见的行为，如 ["lethargy"]
    quality_ok: bool = True
    note: str = ""

class QwenClient:
    def analyze_image(self, image_path: str) -> ImageObservation: ...
```

- **铁律**（worksplit §5）：Qwen 返回的是*观察*，不是诊断。不要让模型直接输出病名。
- agent 注入方式：`Agent(db_path=..., qwen_client=QwenClient())`；不注入时回退到纯 RAG（用 case 里预填的 visible_findings）。

### 6.2 OBS_xxx 证据体系

agent 把每条图像观察转成 `OBS_{image_id}_{seq}`（如 `OBS_IMG_001_001`），`label="OBSERVED"`，并入 `case.retrieved_evidence`：

- 报告可引用「图像观察到溃疡」作为支持某病名的证据（traceability）；
- differential 评分时，图像观察通过症状关键词命中加权（**不直接 prove 诊断**）。

### 6.3 图像质量降级

若 Qwen 返回 `quality_ok=False`（图像模糊/不符），agent 跳过该图、不生成 OBS 证据，并在 trace 记录原因；不会用残缺观察驱动检索。

### 6.4 对接 checklist

- [ ] Member 3 把 `analyze_image` 返回值从 `list[str]` 改为 `ImageObservation`
- [ ] 统一 `image_path` 传参方式（路径还是 base64？建议路径，后端存图后传路径）
- [ ] 确认图像质量检查字段名（`quality_ok` / `note`）
- [ ] visual findings 用**小写英文短词**（与知识库文本一致，利于检索），如 `flank ulcer` 而非整句
