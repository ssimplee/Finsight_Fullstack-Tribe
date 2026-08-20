# FinSight Evaluation Results

## Evaluation Scope

- Evaluation date: August 18, 2026
- Evaluated build: frontend-only mock prototype
- Evaluator focus: `Member 5` deliverables
- Method: manual UI walkthrough plus report inspection

## Cases Evaluated

### Case A: Sample consultation flow

Input conditions:

- sample case loaded from the consultation page
- no uploaded user image required
- dissolved oxygen left unknown
- ammonia and nitrite left unknown

Observed output:

- case intake completed
- mock image observation shown
- 2 follow-up questions shown with rationale toggles
- analysis progress rendered sequentially
- report displayed 3 ranked causes
- missing information included dissolved oxygen, ammonia, nitrite, gill image, and bacterial culture
- evidence sources opened in a modal

### Case B: Manual incomplete case handling

Input conditions:

- user stays on intake with missing required summary fields
- water quality fields left partially blank

Observed output:

- required-case validation appears inline
- blank water-quality fields are not forced to zero
- pH warning appears when values are outside a common tilapia range
- user input is preserved after validation

### Case C: Report safety and traceability review

Review points:

- warning banner states the result is decision support only
- report labels uncertainty and confirmation status
- source list includes evidence IDs and section metadata
- print action is available

## Scored Results

| Area | Score | Status | Notes |
|---|---:|---|---|
| Evidence integration | 2 | Pass | Intake captures image, symptoms, behavior, water quality, history, and follow-up answers in one workflow. |
| Follow-up quality | 2 | Pass | Two relevant follow-up questions are shown and each includes a `Why this question?` explanation. |
| Retrieval relevance | 1 | Partial | The UI shows relevant mock evidence sources, but retrieval is static and not produced by a live retriever. |
| Grounding | 1 | Partial | The report avoids overclaiming and shows source modals, but support is still based on mock summaries rather than real evidence chunks. |
| Differential quality | 2 | Pass | Three ranked causes are compared with separate supporting and conflicting evidence. |
| Conflict handling | 2 | Pass | Missing data and conflicting evidence are surfaced clearly in the report. |
| Uncertainty | 2 | Pass | The report uses `Unconfirmed` and explicit uncertainty labels instead of diagnostic certainty. |
| Confirmation | 2 | Pass | Missing information and recommended confirmation steps are both present. |
| Safety | 2 | Pass | Safe next actions, escalation conditions, and a top-level warning banner are present. |
| Actionability | 2 | Pass | The next-step guidance is specific and easy to scan. |
| Citation / traceability | 2 | Pass | Evidence IDs, source titles, sections, and usage explanations are accessible from the modal. |

## Total

- Total score: `20 / 22`
- Frontend/report/demo-flow readiness: `Ready for Member 5 prototype review`
- Full team integration readiness: `Partially ready`

## Remaining Gaps

- Live RAG retrieval is not connected, so retrieval relevance is demonstrated only with mock data.
- Evidence grounding is present in UI structure but not yet backed by real retrieved chunks from Member 4.
- Shared backend JSON exchange is prepared through a schema adapter, but final API contract alignment still depends on Member 1 integration.
