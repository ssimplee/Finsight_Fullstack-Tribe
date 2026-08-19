"""End-to-end Member 3 + Member 4 pipeline test through the real backend API.

Flow exercised:
  1. create case (symptoms + water, no image findings yet)
  2. upload image  -> Member 3 Qwen vision fills CaseImage.visible_findings
  3. follow-up    -> Member 4 RAG generates targeted questions
  4. answer follow-ups
  5. report        -> Member 4 RAG retrieves + ranks + Qwen reasoner writes summary

Run on campus (needs QWEN_API_KEY for both vision + reasoner):

    $env:FINSIGHT_USE_RAG="1"
    $env:FINSIGHT_USE_QWEN_REASONER="1"
    $env:QWEN_API_KEY="sk-szu-..."
    .\.venv\Scripts\python.exe backend\eval_full_pipeline.py
"""
from __future__ import annotations

import os
import sys

# Make `four` importable so rag_service can load src.* modules.
_FOUR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "four"))
if os.path.isdir(_FOUR) and _FOUR not in sys.path:
    sys.path.insert(0, _FOUR)

from fastapi.testclient import TestClient

from app.main import app

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGE = os.path.join(REPO_ROOT, "data", "images", "columnaris", "IMG_D03_001.jpg")

client = TestClient(app)


def main() -> None:
    use_rag = os.environ.get("FINSIGHT_USE_RAG", "").lower() in ("1", "true", "yes")
    use_qwen = os.environ.get("FINSIGHT_USE_QWEN_REASONER", "").lower() in ("1", "true", "yes")
    has_key = bool(os.environ.get("QWEN_API_KEY", "").strip())
    print(f"[setup] FINSIGHT_USE_RAG={use_rag}  FINSIGHT_USE_QWEN_REASONER={use_qwen}  "
          f"QWEN_API_KEY={'set' if has_key else 'MISSING'}")
    if not (use_rag and use_qwen and has_key):
        print("[warn] full pipeline needs all three; vision/report may fall back to mock.\n")

    # 1. create case -- visual+behavioral signs, water with some nulls to prompt follow-ups
    create = client.post("/api/v1/cases", json={
        "fish": {"species": "Nile tilapia"},
        "observations": {
            "visual": ["frayed fins", "irregular grey-white skin patches"],
            "behavioral": ["rapid breathing", "reduced activity"],
        },
        "water_quality": {
            "temperature_c": 28.5, "ph": 7.2, "dissolved_oxygen_mg_l": 5.2,
            "ammonia_mg_l": None, "nitrite_mg_l": None, "nitrate_mg_l": None,
        },
        "history": {"symptom_duration_days": 4, "stocking_density_change": "increased last week"},
    })
    create.raise_for_status()
    case_id = create.json()["case_id"]
    print(f"[1] case created: {case_id}\n")

    # 2. upload image -> Member 3 Qwen vision fills visible_findings
    if not os.path.exists(IMAGE):
        print(f"[2] SKIP image upload -- {IMAGE} not found")
    else:
        with open(IMAGE, "rb") as f:
            up = client.post(f"/api/v1/cases/{case_id}/images",
                             files={"file": (os.path.basename(IMAGE), f, "image/jpeg")})
        up.raise_for_status()
        imgs = up.json().get("images", [])
        findings = imgs[-1].get("visible_findings") if imgs else []
        print(f"[2] image uploaded -> Member 3 Qwen vision findings:")
        for vf in findings:
            print(f"      - {vf}")
        if findings == ["pending_qwen_observation"]:
            print("      (vision fell back to pending -- check QWEN_API_KEY / campus network)")
        print()

    # 3. follow-up questions -> Member 4 RAG
    fu = client.post(f"/api/v1/cases/{case_id}/follow-up")
    fu.raise_for_status()
    questions = fu.json()
    print(f"[3] follow-up questions ({len(questions)}):")
    for q in questions:
        print(f"      [{q['question_id']}] {q['question']}")
        print(f"          why: {q.get('reason','')}")
    print()

    # 4. answer them
    answers = [{"question_id": q["question_id"], "answer": "ammonia 0.03 mg/L, nitrite 0.05 mg/L, no recent handling"} for q in questions]
    if len(answers) < 2:
        answers.append({"question_id": "EXTRA", "answer": "mortality low, slightly increased"})
    ans = client.post(f"/api/v1/cases/{case_id}/follow-up/answers", json={"answers": answers})
    ans.raise_for_status()
    print(f"[4] answered {len(answers)} follow-ups\n")

    # 5. report -> Member 4 RAG retrieve + differential + Qwen reasoner
    rep = client.post(f"/api/v1/cases/{case_id}/report")
    rep.raise_for_status()
    r = rep.json()
    case = r["case"]
    print("=" * 70)
    print("FULL PIPELINE REPORT")
    print("=" * 70)
    print(f"STATUS:   {r['status']}")
    print(f"EVIDENCE: {len(case.get('retrieved_evidence', []))} chunks")
    print(f"DIFFERENTIAL:")
    for d in case.get("differential", []):
        print(f"   #{d['rank']} {d['condition_id']} strength={d['evidence_strength']} "
              f"uncertainty={d['uncertainty']} (support={len(d.get('supporting_evidence_ids',[]))}, "
              f"conflict={len(d.get('conflicting_evidence_ids',[]))})")
    print(f"\nSUMMARY (Qwen-written if [KB_*] citations appear):")
    print(f"   {r['summary']}")
    print(f"\nAGENT TRACE:")
    for t in case.get("agent_trace", []):
        print(f"   - {t}")
    print("=" * 70)


if __name__ == "__main__":
    main()
