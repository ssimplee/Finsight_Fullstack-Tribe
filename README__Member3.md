# Qwen 多模态视觉分析模块（Member 3）

FinSight 的**视觉观察层**，负责让系统"看懂"上传的鱼图，提取结构化的可见观察结果，供下游的 RAG / 推理（Member 4）做鉴别诊断。

## 文件清单

| 文件                   | 职责                                                                           |
| -------------------- | ---------------------------------------------------------------------------- |
| `qwen_client.py`     | OpenAI 兼容 Qwen 客户端：超时、指数退避重试、可读异常；优先 `response_format=json_object`，失败自动回退纯文本 |
| `vision_prompts.py`  | 观察类提示词（质量判定 + 可见体征，仅 JSON 输出，明确禁止诊断词）                                        |
| `vision_terms.py`    | 罗非鱼可见体征词典（英文 + 中文对照）与 few-shot 示例                                            |
| `vision_schemas.py`  | `VisionResult` / `VisionFinding` / `ImageQuality` 结构化输出模型                    |
| `vision_analysis.py` | 编排层：本地预检 → 缓存 → Qwen 调用 → 质量门 → 诊断词过滤 → 度量                                   |
| `vision_cache.py`    | 进程内 LRU 缓存（按图片内容哈希），重复图不重复计费                                                 |
| `vision_metrics.py`  | `VisionMetrics` 成本/可观测性度量模型                                                  |

## 处理流程

```
本地预检 precheck_image（非图片/太小直接拦截，省 token）
        ↓ 通过
缓存查询（同图命中直接返回）
        ↓ 未命中
Qwen 调用（response_format 硬约束 → 失败回退纯文本）
        ↓ 解析失败
quality-only 兜底重试 → 仍失败返回 poor_quality（不抛异常）
        ↓ 成功
质量门（不可用图绝不输出观察）
        ↓
诊断词过滤（过滤掉模型漏出的"感染/细菌/病原"等词）
        ↓
附加 metrics（latency / tokens / retry / hash / quality / timestamp）
        ↓
写回缓存并返回 VisionResult
```

## 结构化输出

```python
VisionResult(
    quality: "usable" | "poor_quality" | "no_relevant_subject",
    quality_reason: str,
    findings: [VisionFinding(finding, region, modality="image")],
    metrics: dict | None,   # 本次调用的成本/可观测数据
)
```

## 配置

| 环境变量              | 默认值                              | 说明                 |
| ----------------- | -------------------------------- | ------------------ |
| `QWEN_API_KEY`    | 空                                | 智算中心 API key（必填）   |
| `QWEN_MODEL`      | `qwen3-vl-8b`                    | 模型 ID              |
| `QWEN_BASE_URL`   | `https://model.ai.szu.edu.cn/v1` | OpenAI 兼容端点        |
| `QWEN_VERIFY_SSL` | `true`                           | 端点证书不可校验时设 `false` |
| `QWEN_CACHE_SIZE` | `128`                            | 视觉结果 LRU 缓存上限      |

代码支持但暂未写入 `.env.example` 的高级项：`QWEN_TIMEOUT_SEC`（默认 60）、`QWEN_MAX_RETRIES`（默认 3）。

## 使用方法（其他成员）

```python
from app.services.vision_analysis import analyze_image

result = analyze_image("path/to/fish.jpg")  # 也接受 bytes / data URL / http URL
# result.findings          -> 列表，含 finding 与 region
# result.quality           -> "usable" / "poor_quality" / "no_relevant_subject"
# result.metrics           -> 本次调用的成本/可观测数据（dict）
```

与后端对接点：`case_service.attach_image` 已接入本模块，Qwen 成功时把观察写入 `visible_findings`，Qwen 不可用时回落到 `["pending_qwen_observation"]`。

## 测试

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

- `tests/test_qwen_client.py` —— 客户端、重试、鉴权、图片处理、`response_format` 降级、回复解析
- `tests/test_vision_analysis.py` —— 预检、缓存、兜底、度量、诊断词过滤
- `tests/test_vision_terms.py` —— 术语表无诊断词、few-shot 格式、prompt 注入

全部为纯 mock，无需网络与真实 key。当前 **52 个测试通过**。

## 已知限制

- 视觉层只做单图观察，不主动诊断、不询问追问、不检索知识库 —— 这些属 Member 4 的职责。

---

# Qwen Multimodal Vision Analysis Module (Member 3)

The **visual observation layer** of FinSight. It lets the system "see" uploaded fish images and extract structured, visible-only observations, which then feed the downstream RAG / reasoning (Member 4) for differential diagnosis.

## File List

| File                  | Responsibility                                                                                               |
| --------------------- | ------------------------------------------------------------------------------------------------------------ |
| `qwen_client.py`      | OpenAI-compatible Qwen client: timeout, exponential backoff retry, readable exceptions; prefers `response_format=json_object`, falls back to plain text on failure |
| `vision_prompts.py`   | Observation prompts (quality assessment + visible signs, JSON-only output, explicitly forbids diagnostic terms) |
| `vision_terms.py`     | Tilapia visible-sign dictionary (English + Chinese) with few-shot examples                                    |
| `vision_schemas.py`   | `VisionResult` / `VisionFinding` / `ImageQuality` structured output models                                    |
| `vision_analysis.py`  | Orchestration: local precheck → cache → Qwen call → quality gate → diagnostic-term filter → metrics          |
| `vision_cache.py`     | In-process LRU cache (keyed by image content hash); duplicate images are not billed twice                     |
| `vision_metrics.py`   | `VisionMetrics` cost/observability metrics model                                                               |

## Pipeline

```
Local precheck precheck_image (reject non-images / too-small images, saving tokens)
        ↓ passed
Cache lookup (return directly on hit)
        ↓ miss
Qwen call (response_format hard constraint → fall back to plain text on failure)
        ↓ parse failure
quality-only fallback retry → still failing returns poor_quality (no exception raised)
        ↓ success
Quality gate (unusable images never emit observations)
        ↓
Diagnostic-term filter (drop any leaked "infection / bacteria / pathogen" terms)
        ↓
Attach metrics (latency / tokens / retry / hash / quality / timestamp)
        ↓
Write back to cache and return VisionResult
```

## Structured Output

```python
VisionResult(
    quality: "usable" | "poor_quality" | "no_relevant_subject",
    quality_reason: str,
    findings: [VisionFinding(finding, region, modality="image")],
    metrics: dict | None,   # cost / observability data for this call
)
```

## Configuration

| Environment Variable | Default                            | Description                                  |
| -------------------- | ---------------------------------- | -------------------------------------------- |
| `QWEN_API_KEY`       | empty                              | Campus AI platform API key (required)        |
| `QWEN_MODEL`         | `qwen3-vl-8b`                      | Model ID                                     |
| `QWEN_BASE_URL`      | `https://model.ai.szu.edu.cn/v1`   | OpenAI-compatible endpoint                   |
| `QWEN_VERIFY_SSL`    | `true`                             | Set `false` when the endpoint certificate cannot be verified |
| `QWEN_CACHE_SIZE`    | `128`                              | LRU cache size for vision results            |

Advanced options supported by the code but not yet written to `.env.example`: `QWEN_TIMEOUT_SEC` (default 60), `QWEN_MAX_RETRIES` (default 3).

## Usage (for other members)

```python
from app.services.vision_analysis import analyze_image

result = analyze_image("path/to/fish.jpg")  # also accepts bytes / data URL / http URL
# result.findings          -> list, each containing finding and region
# result.quality           -> "usable" / "poor_quality" / "no_relevant_subject"
# result.metrics           -> cost / observability data for this call (dict)
```

Backend integration point: `case_service.attach_image` is already wired to this module. On Qwen success it writes observations into `visible_findings`; when Qwen is unavailable it falls back to `["pending_qwen_observation"]`.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

- `tests/test_qwen_client.py` — client, retries, auth, image handling, `response_format` fallback, reply parsing
- `tests/test_vision_analysis.py` — precheck, cache, fallback, metrics, diagnostic-term filtering
- `tests/test_vision_terms.py` — glossary contains no diagnostic terms, few-shot format, prompt injection

All tests are fully mocked, requiring no network or real key. **52 tests pass** currently.

## Known Limitations

- The vision layer only observes a single image; it does not diagnose, ask follow-up questions, or query the knowledge base — those are the responsibility of Member 4.

---

# Qwen 멀티모달 비전 분석 모듈 (Member 3)

FinSight의 **비전 관찰 계층**입니다. 업로드된 어류 이미지를 시스템이 "보고" 구조화된 가시 관찰 결과를 추출하여, 하위 RAG / 추론(Member 4)이 감별 진단을 수행하도록 합니다.

## 파일 목록

| 파일                  | 역할                                                                                                       |
| --------------------- | ---------------------------------------------------------------------------------------------------------- |
| `qwen_client.py`      | OpenAI 호환 Qwen 클라이언트: 타임아웃, 지수 백오프 재시도, 가독성 있는 예외; `response_format=json_object` 우선, 실패 시 일반 텍스트로 폴백 |
| `vision_prompts.py`   | 관찰용 프롬프트(품질 판정 + 가시 징후, JSON 전용 출력, 진단 용어 명시적 금지)                                 |
| `vision_terms.py`     | 틸라피아 가시 징후 사전(영문 + 중문)과 few-shot 예시                                                          |
| `vision_schemas.py`   | `VisionResult` / `VisionFinding` / `ImageQuality` 구조화 출력 모델                                           |
| `vision_analysis.py`  | 오케스트레이션: 로컬 사전 검사 → 캐시 → Qwen 호출 → 품질 게이트 → 진단 용어 필터 → 메트릭                    |
| `vision_cache.py`     | 프로세스 내 LRU 캐시(이미지 콘텐츠 해시 기준), 중복 이미지는 중복 과금되지 않음                                |
| `vision_metrics.py`   | `VisionMetrics` 비용/가시성 메트릭 모델                                                                      |

## 처리 흐름

```
로컬 사전 검사 precheck_image (이미지가 아니거나 너무 작으면 차단, 토큰 절약)
        ↓ 통과
캐시 조회 (동일 이미지 적중 시 바로 반환)
        ↓ 미적중
Qwen 호출 (response_format 하드 제약 → 실패 시 일반 텍스트로 폴백)
        ↓ 파싱 실패
quality-only 폴백 재시도 → 그래도 실패하면 poor_quality 반환 (예외 미발생)
        ↓ 성공
품질 게이트 (사용 불가 이미지는 절대 관찰 결과를 출력하지 않음)
        ↓
진단 용어 필터 (누출된 "감염/세균/병원체" 등의 용어 제거)
        ↓
메트릭 부착 (latency / tokens / retry / hash / quality / timestamp)
        ↓
캐시에 기록 후 VisionResult 반환
```

## 구조화 출력

```python
VisionResult(
    quality: "usable" | "poor_quality" | "no_relevant_subject",
    quality_reason: str,
    findings: [VisionFinding(finding, region, modality="image")],
    metrics: dict | None,   # 이번 호출의 비용/가시성 데이터
)
```

## 설정

| 환경 변수            | 기본값                              | 설명                                     |
| -------------------- | ----------------------------------- | ---------------------------------------- |
| `QWEN_API_KEY`       | 비어 있음                           | AI 플랫폼 API 키 (필수)                  |
| `QWEN_MODEL`         | `qwen3-vl-8b`                       | 모델 ID                                  |
| `QWEN_BASE_URL`      | `https://model.ai.szu.edu.cn/v1`    | OpenAI 호환 엔드포인트                   |
| `QWEN_VERIFY_SSL`    | `true`                              | 엔드포인트 인증서를 검증할 수 없을 때 `false` |
| `QWEN_CACHE_SIZE`    | `128`                               | 비전 결과 LRU 캐시 크기                  |

코드에서 지원하지만 아직 `.env.example`에 기록하지 않은 고급 항목: `QWEN_TIMEOUT_SEC` (기본 60), `QWEN_MAX_RETRIES` (기본 3).

## 사용법 (다른 멤버용)

```python
from app.services.vision_analysis import analyze_image

result = analyze_image("path/to/fish.jpg")  # bytes / data URL / http URL도 허용
# result.findings          -> finding과 region을 포함하는 리스트
# result.quality           -> "usable" / "poor_quality" / "no_relevant_subject"
# result.metrics           -> 이번 호출의 비용/가시성 데이터 (dict)
```

백엔드 연동 지점: `case_service.attach_image`가 본 모듈에 이미 연결되어 있습니다. Qwen 성공 시 관찰 결과를 `visible_findings`에 기록하고, Qwen을 사용할 수 없을 때는 `["pending_qwen_observation"]`으로 폴백합니다.

## 테스트

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

- `tests/test_qwen_client.py` — 클라이언트, 재시도, 인증, 이미지 처리, `response_format` 폴백, 응답 파싱
- `tests/test_vision_analysis.py` — 사전 검사, 캐시, 폴백, 메트릭, 진단 용어 필터
- `tests/test_vision_terms.py` — 사전에 진단 용어 없음, few-shot 형식, 프롬프트 주입

모든 테스트는 순수 mock으로 네트워크와 실제 키가 필요 없습니다. 현재 **52개 테스트 통과**.

## 알려진 제한 사항

- 비전 계층은 단일 이미지 관찰만 수행하며, 진단하거나 후속 질문을 하거나 지식 베이스를 조회하지 않습니다 — 이는 Member 4의 책임입니다.

