# FinSight Evaluation Rubric

## Purpose

This rubric is intended for the `Member 5` frontend, report, and demo-flow evaluation deliverable. It is designed for the current frontend-first prototype and can be reused after backend, Qwen, and RAG integration.

## Scoring Scale

| Score | Meaning |
|---|---|
| 2 | Pass: requirement is clearly demonstrated |
| 1 | Partial: visible but incomplete or weakly grounded |
| 0 | Fail: missing or not demonstrated |

## Evaluation Areas

| Area | What to check | Evidence to inspect | Score |
|---|---|---|---|
| Evidence integration | Does the flow use image, symptoms, behavior, water quality, history, and follow-up answers together? | Intake form, shared case payload, report sections | 0-2 |
| Follow-up quality | Are at least 2 useful follow-up questions asked? | Follow-up UI, question prompts, rationale toggle | 0-2 |
| Retrieval relevance | Is the evidence shown relevant to the ranked causes? | Evidence source list, report evidence summaries | 0-2 |
| Grounding | Are major claims tied to observations or cited evidence rather than unsupported statements? | Observation labels, evidence modal, report wording | 0-2 |
| Differential quality | Are plausible alternatives ranked and compared side by side? | Differential cards, support/conflict sections | 0-2 |
| Conflict handling | Are conflicting or missing signals surfaced instead of hidden? | Conflicting evidence lists, missing information section | 0-2 |
| Uncertainty | Does the system avoid overconfidence? | Uncertainty labels, unconfirmed status, safety notice | 0-2 |
| Confirmation | Does the report explain what still needs to be checked? | Recommended confirmation and missing information | 0-2 |
| Safety | Does the report avoid unsupported treatment claims and mention escalation triggers? | Safe next actions, escalation card, warning banner | 0-2 |
| Actionability | Are the next steps clear and useful for the user? | Recommended actions, escalation, print-ready report | 0-2 |
| Citation / traceability | Can the user inspect evidence IDs and source summaries? | Evidence IDs, source modal, section metadata | 0-2 |

## Member 5 Deliverable Threshold

For the frontend/report/evaluation owner, the prototype is considered ready when:

- the intake-to-report demo flow is runnable end to end;
- the report displays all required sections from the team scope;
- evidence sources are inspectable from the UI;
- missing information and uncertainty are visible;
- the rubric is completed with at least one evaluated case;
- any backend-dependent limitations are stated explicitly.

## Notes For Team Integration

- Before full team integration, `Retrieval relevance` and `Grounding` may score `1` if the frontend uses static mock evidence rather than live RAG output.
- After Member 4 integration, the same rubric can be reused with real retrieved evidence IDs and case-specific supporting chunks.
- After Member 1 integration, screenshots or exported JSON payloads should be attached to each evaluated case.
