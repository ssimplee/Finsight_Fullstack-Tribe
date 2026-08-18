# FinSight — Project Scope, Data Plan & 5-Person Work Split

## 1. Project Goal

FinSight is a **multimodal fish-health diagnostic triage assistant**.

It should combine:

- fish image(s);
- visible symptoms;
- behaviour;
- water-quality data;
- recent farming/care history;
- follow-up answers;
- evidence from a curated fish-health knowledge base.

The system should **not immediately give one diagnosis**.

It should:

1. collect the initial case;
2. analyse the image and symptoms;
3. identify missing information;
4. ask at least **2 relevant follow-up questions**;
5. retrieve evidence from the knowledge base;
6. rank possible causes;
7. explain supporting and conflicting evidence;
8. state uncertainty;
9. recommend confirmation steps and safe next actions;
10. indicate when professional help is needed.

---

# 2. Recommended Scope

Use **Nile tilapia in freshwater aquaculture**.

Recommended 5 conditions:

1. **Streptococcosis** — *Streptococcus iniae / S. agalactiae*
2. **Motile Aeromonas Septicemia** — *Aeromonas hydrophila*
3. **Columnaris disease**
4. **Tilapia Lake Virus disease (TiLV)**
5. **Water-quality stress / hypoxia / ammonia or nitrite stress**

Why this scope:

- stays within the required 4–6 conditions;
- matches the provided FishDiag example;
- has strong FAO/WOAH literature;
- gives overlapping symptoms, which is good for differential diagnosis;
- allows all required data types to be used.

Do **not** expand to all fish species or many diseases.

---

# 3. Data We Need

There are 3 main data groups.

## A. Knowledge-Base Data

For each condition, collect:

- disease/condition name;
- pathogen/cause;
- affected species;
- visual signs;
- behavioural signs;
- important water-quality associations;
- risk factors;
- recent-history clues;
- supporting evidence;
- conflicting evidence;
- common differential diagnoses;
- recommended confirmation methods;
- safe next actions;
- escalation triggers;
- source references.

Suggested structure:

```json
{
  "condition_id": "D01",
  "name": "Streptococcosis",
  "visual_signs": [],
  "behavioral_signs": [],
  "water_quality_associations": {},
  "risk_factors": [],
  "supporting_evidence": [],
  "conflicting_evidence": [],
  "differentials": [],
  "confirmation_methods": [],
  "safe_actions": [],
  "escalation_triggers": [],
  "source_ids": []
}
```

### Recommended sources

Prioritise:

1. FAO
2. WOAH
3. government / university veterinary sources
4. peer-reviewed papers
5. recognised textbooks/reviews

Avoid using random blogs/forums as diagnostic evidence.

### Target amount

For each of 5 conditions:

- 2–4 strong references;
- around 8–15 useful knowledge chunks;
- important symptoms and risk factors;
- confirmation methods;
- conflicting evidence.

Around **50 high-quality chunks total** is enough for a prototype.

---

## B. Image Data

Images are used for **visual observation**, not to prove a diagnosis.

The AI should say:

> “Visible flank ulceration”

rather than:

> “This image confirms Aeromonas infection.”

Recommended:

- 8–20 representative images per condition;
- around 40–100 images total;
- store source and licence/usage information;
- prefer confirmed cases from papers, datasets, universities or official sources.

Image metadata:

```json
{
  "image_id": "IMG_D02_004",
  "condition_id": "D02",
  "species": "Nile tilapia",
  "visible_findings": ["flank ulcer", "scale loss"],
  "source_id": "SRC_014"
}
```

---

## C. Evaluation / Test Cases

Build cases containing:

- image;
- symptoms;
- behaviour;
- water readings;
- recent history;
- some intentionally missing information;
- expected follow-up topics;
- expected differential diagnoses.

Recommended case types:

- clear case;
- incomplete case;
- overlapping-symptom case;
- contradictory case;
- environmental-stress case;
- mixed / co-infection-style case.

Target:

**30–45 evaluation cases**

Only 2–3 need to be shown during the live demo.

---

# 4. Case Input Fields

## Fish information

- species;
- age/life stage if known.

## Behaviour

Examples:

- abnormal swimming;
- lethargy;
- reduced appetite;
- rapid breathing;
- surface gasping;
- circling;
- loss of balance;
- isolation.

## Water quality

At minimum:

| Field | Unit |
|---|---|
| Temperature | °C |
| pH | pH |
| Dissolved oxygen | mg/L |
| Ammonia | mg/L |
| Nitrite | mg/L |
| Nitrate | mg/L |

If unknown, store it as `null`.

Do not assume missing values are normal.

## Recent history

Useful fields:

- symptom duration;
- mortality trend;
- recent fish introduction;
- recent stocking-density change;
- transport/handling;
- feed change;
- recent treatment;
- water change;
- filtration/oxygenation failure;
- recent temperature change.

---

# 5. Recommended AI Architecture

```text
Frontend
   ↓
Case API / Backend
   ↓
Qwen Multimodal Image Analysis
   ↓
Missing-Information Detection
   ↓
Follow-Up Questions
   ↓
RAG Knowledge Retrieval
   ↓
Differential Reasoning
   ↓
Safety / Grounding Check
   ↓
Explainable Report
```

## Qwen's role

Use Qwen for:

- image observation;
- understanding user input;
- generating relevant follow-up questions;
- reasoning over retrieved evidence;
- producing structured output;
- writing the final explanation.

Qwen should **not** be the knowledge base.

The facts should come from the team's curated sources.

---

# 6. Agent Flow

Use a staged workflow.

## Step 1 — Case Intake

Collect image, symptoms, water data and history.

## Step 2 — Image Observation

Qwen extracts visible findings.

Do not ask it for the final diagnosis yet.

## Step 3 — Missing Information

Identify important unknowns.

## Step 4 — Follow-Up

Ask at least 2 case-specific questions.

Example:

> What is the dissolved oxygen level?

> Have mortality or stocking conditions changed recently?

## Step 5 — RAG Retrieval

Retrieve evidence for the most plausible conditions.

## Step 6 — Differential Diagnosis

Return ranked possible causes with:

- supporting evidence;
- conflicting evidence;
- uncertainty;
- missing confirmation.

## Step 7 — Safe Action

Return:

- monitoring advice;
- confirmation/testing suggestions;
- safe immediate steps;
- escalation guidance.

---

# 7. Structured Output

Do not rely only on free-text AI responses.

Use JSON first, then display it nicely in the frontend.

Example:

```json
{
  "differential": [
    {
      "condition_id": "D01",
      "rank": 1,
      "evidence_strength": "strong",
      "uncertainty": "moderate",
      "supporting_evidence_ids": ["OBS_003", "KB_D01_004"],
      "conflicting_evidence_ids": [],
      "confirmation_status": "unconfirmed"
    }
  ],
  "missing_information": [],
  "recommended_actions": [],
  "escalation": []
}
```

---

# 8. Shared Case Format

All members should use the same structure.

```json
{
  "case_id": "CASE_001",

  "fish": {
    "species": "Nile tilapia"
  },

  "images": [],

  "observations": {
    "visual": [],
    "behavioral": []
  },

  "water_quality": {
    "temperature_c": null,
    "ph": null,
    "dissolved_oxygen_mg_l": null,
    "ammonia_mg_l": null,
    "nitrite_mg_l": null,
    "nitrate_mg_l": null
  },

  "history": {},

  "agent_questions": [],
  "retrieved_evidence": [],
  "differential": [],
  "recommended_actions": [],
  "escalation": []
}
```

Agree on this before each member starts separate development.

---

# 9. 5-Person Work Split

## Member 1 — Backend & Integration Lead

Owns:

- shared JSON/data contract;
- FastAPI/backend;
- case/session storage;
- image-upload endpoint;
- frontend ↔ AI ↔ RAG integration;
- API/error handling;
- deployment;
- final integration.

Main deliverables:

```text
/backend
API contract
shared schemas
deployment
integration tests
```

---

## Member 2 — Fish-Health Knowledge & Case Data

Owns:

- final 5-condition scope;
- authoritative sources;
- disease profiles;
- symptoms/risk factors;
- water-quality associations;
- supporting/conflicting evidence;
- confirmation methods;
- source IDs;
- representative images;
- evaluation cases.

Main deliverables:

```text
conditions.json
sources.json
knowledge_chunks.jsonl
images/
30–45 test cases
```

---

## Member 3 — Qwen Multimodal AI

Owns:

- Qwen API integration;
- image analysis;
- image-quality checks;
- prompts for visual observations;
- structured model output;
- prompt testing;
- API retry/error handling;
- model/cost testing.

Main deliverables:

```text
qwen_client
vision_analysis
vision prompts
structured output schema
AI tests
```

Important rule:

Qwen image analysis returns **observations**, not a final diagnosis.

---

## Member 4 — Agent Reasoning & RAG

Owns:

- knowledge ingestion;
- embeddings/vector database;
- evidence retrieval;
- missing-information detection;
- follow-up-question logic;
- differential ranking;
- supporting/conflicting evidence;
- uncertainty;
- evidence IDs;
- safety checks.

Main deliverables:

```text
RAG ingestion
retriever
agent workflow/state machine
follow-up logic
differential logic
safety checks
```

This member owns the main **agent behaviour**.

---

## Member 5 — Frontend, Report & Evaluation

Owns:

### Frontend

- case intake form;
- image upload;
- symptoms/water/history input;
- follow-up-question UI;
- diagnosis/report screen.

### Report

Display:

- top-ranked cause;
- alternatives;
- supporting evidence;
- conflicting evidence;
- uncertainty;
- missing information;
- recommended confirmation;
- safe next steps;
- escalation;
- evidence sources.

### Evaluation

Measure:

- follow-up relevance;
- retrieval relevance;
- evidence grounding;
- differential quality;
- uncertainty;
- safe guidance;
- citation/traceability.

Main deliverables:

```text
/frontend
report UI
evaluation rubric
evaluation results
demo flow
```

---


# 9A. Recommended Start Order

The team does **not** need to wait for one member to fully finish before the others begin.

Recommended order:

```text
1. Member 2 starts first
   Finalise the fish scope, 5 conditions, key sources, sample images and a few sample cases.

2. Member 1 starts once the shared case/data format is agreed
   Build the backend/API using mock data if needed.

3. Member 3 can start early
   Once Member 2 provides 1–2 sample images and expected observations, begin Qwen image-analysis testing.

4. Member 4 follows once the first disease profiles / knowledge chunks are ready
   Build RAG, retrieval, follow-up logic and differential reasoning.

5. Member 5 can start in parallel using mock JSON
   Build the frontend and report UI before the real AI pipeline is fully connected.
```

Dependency view:

```text
                 ┌→ Member 3: Qwen / image analysis
Member 2 ────────┼→ Member 4: RAG + reasoning
     │           │
     └→ shared data format → Member 1: backend / integration
                                  │
                                  └→ Member 5: frontend / report
```

The key first step is for **Member 2 and Member 1 to agree on the shared case schema**, after which most of the team can work in parallel.

# 10. Development Order

Do not build everything separately and integrate at the end.

Use this order:

```text
1. Confirm tilapia + 5 conditions
2. Confirm shared JSON schema
3. Create 3–5 sample cases
4. Build one disease profile + KB
5. Test one image through Qwen
6. Build RAG retrieval
7. Build follow-up question flow
8. Build differential output
9. Connect backend
10. Connect frontend
11. Make 1 case work end-to-end
12. Expand to all 5 conditions
13. Run evaluation
14. Polish demo
```

The first milestone should be **one complete working case**.

---

# 11. Minimum Final Demo

A good demo:

1. user uploads fish image;
2. enters symptoms;
3. leaves some important water/history fields blank;
4. Qwen extracts visible findings;
5. FinSight asks 2 relevant follow-up questions;
6. user answers;
7. RAG retrieves evidence;
8. FinSight ranks 2–3 possible causes;
9. report explains support + conflict;
10. report states uncertainty;
11. report recommends confirmation and safe next steps;
12. report shows source/evidence references.

---

# 12. Evaluation

Do not evaluate only diagnosis accuracy.

Use:

| Area | What to check |
|---|---|
| Evidence integration | Did it use multiple modalities? |
| Follow-up quality | Were questions useful? |
| Retrieval relevance | Was the retrieved evidence relevant? |
| Grounding | Were major claims supported? |
| Differential quality | Were plausible alternatives considered? |
| Conflict handling | Did it identify contradictions? |
| Uncertainty | Did it avoid overconfidence? |
| Confirmation | Did it explain what is still needed? |
| Safety | Did it avoid unsupported treatment claims? |
| Actionability | Were the next steps useful? |

---

# 13. High-Value Optional Improvements

These improve the existing deliverables without changing the project scope.

## Priority 1 — Evidence Source Viewer

Allow users to click an evidence item and see:

- evidence ID;
- source;
- page/section;
- retrieved passage.

This strengthens traceability and RAG explainability.

---

## Priority 2 — Evidence Completeness

Show which important evidence is available/missing.

Example:

```text
Image              ✓
Behaviour          ✓
Temperature        ✓
Dissolved oxygen   Missing
Ammonia            Missing
Mortality trend    ✓
```

Do **not** call this diagnosis confidence.

---

## Priority 3 — Contradiction Detection

Example:

```text
Image:
Ulcer supports Aeromonas.

Behaviour:
Neurological signs support Streptococcosis.

Water:
Low oxygen may explain rapid breathing.

Conclusion:
Current findings may have more than one explanation.
```

This directly supports the project's focus on overlapping symptoms.

---

## Priority 4 — Observation vs Inference Labels

Label statements as:

- `OBSERVED`
- `USER-REPORTED`
- `RETRIEVED EVIDENCE`
- `AI INFERENCE`
- `LAB CONFIRMED`

This makes the report much easier to trust.

---

## Priority 5 — Explain Why Follow-Up Questions Were Asked

Example:

```text
Question:
What is the dissolved oxygen level?

Why:
Low dissolved oxygen can cause similar respiratory symptoms and may change the differential.
```

This makes the adaptive-agent logic visible.

---

## Priority 6 — Agent Decision Trace

Keep a simple system audit trail:

```text
Image analysed
↓
Missing DO/ammonia detected
↓
2 follow-up questions asked
↓
12 KB chunks retrieved
↓
Top 3 conditions compared
↓
Safety check passed
```

This is a workflow log, not hidden model reasoning.

---

## Priority 7 — Insufficient Evidence State

Allow FinSight to say:

> Current evidence is insufficient for a meaningful ranking.

Then ask for the most useful missing information.

Do not force a diagnosis for every case.

---

## Priority 8 — Evaluation Dashboard

Optional internal page showing real test results such as:

```text
Cases tested
Follow-up relevance
Retrieval relevance
Valid evidence citations
Uncertainty included
Safety checks passed
```

Only show values produced by actual evaluation.

---

## Priority 9 — Failure-Case Analysis

Include 2–3 examples where the system made a weak decision.

For each:

```text
What went wrong
Why it happened
What was changed
Whether the fix improved the case
```

This is useful for the final presentation/report.

---

## Priority 10 — Multimodal Ablation Test

Run the same case with:

```text
Image only
Image + symptoms
Image + symptoms + water
Full case
```

Show how uncertainty/reasoning improves as more evidence is provided.

This directly proves why the project needs multimodal evidence.

---

# 14. Recommended Build Priority

## Level 1 — Required

```text
✓ 4–6 conditions
✓ image + behaviour + water + history
✓ curated knowledge base
✓ Qwen image understanding
✓ at least 2 adaptive questions
✓ RAG retrieval
✓ ranked differential
✓ supporting/conflicting evidence
✓ uncertainty
✓ safe next steps
✓ escalation
✓ traceable report
```

## Level 2 — Best Optional Additions

```text
+ evidence source viewer
+ evidence completeness
+ contradiction detection
+ observation vs inference labels
+ follow-up question reasons
+ insufficient-evidence state
+ agent trace
```

## Level 3 — If Time Allows

```text
+ evaluation dashboard
+ failure-case analysis
+ multimodal ablation testing
+ prompt/model/KB version tracking
+ PDF report export
```

Prioritise **Level 1 first**, then selected Level 2 features.

---

# 15. Recommended Tech Stack

| Component | Recommendation |
|---|---|
| Frontend | React / Next.js |
| Backend | FastAPI |
| AI | Qwen multimodal API |
| RAG | Chroma / FAISS / pgvector |
| Structured DB | SQLite initially, PostgreSQL if needed |
| Validation | Pydantic |
| Evaluation | Python + JSON/CSV |

Use the simplest stack the team can integrate reliably.

---

# 16. Final Team Summary

```text
Member 1
Backend + integration + deployment

Member 2
Fish-health data + sources + images + test cases

Member 3
Qwen multimodal/image AI

Member 4
RAG + follow-up agent + differential reasoning

Member 5
Frontend + report + evaluation
```

The goal is not to build the biggest system.

The goal is to build a **small, reliable, explainable agent that collects missing evidence, retrieves trusted information, compares multiple causes, and clearly explains what is known, what is uncertain, and what should happen next.**
