"""Verify Member 4 real RAG is wired into the backend.

Run with:  FINSIGHT_USE_RAG=1 python verify_rag.py
(On Windows bash: FINSIGHT_USE_RAG=1 python verify_rag.py)
"""
import os

os.environ["FINSIGHT_USE_RAG"] = "1"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# A clear Aeromonas-style case.
r = client.post(
    "/api/v1/cases",
    json={
        "observations": {
            "visual": ["flank ulcer", "scale loss"],
            "behavioral": ["lethargy"],
        },
        "water_quality": {
            "temperature_c": 29.0,
            "dissolved_oxygen_mg_l": 3.5,
            "ammonia_mg_l": 0.8,
        },
        "history": {"mortality_trend": "increasing"},
    },
)
assert r.status_code == 200, r.text
case_id = r.json()["case_id"]

# Generate + fetch follow-up questions.
client.post(f"/api/v1/cases/{case_id}/follow-up")
qs = client.post(f"/api/v1/cases/{case_id}/follow-up").json()
print(f"follow-up questions: {len(qs)}")

# Answer the first two so the report can proceed.
client.post(
    f"/api/v1/cases/{case_id}/follow-up/answers",
    json={
        "answers": [
            {"question_id": qs[0]["question_id"], "answer": "3.5 mg/L"},
            {"question_id": qs[1]["question_id"], "answer": "no recent change"},
        ]
    },
)

# Generate report via real RAG.
rep = client.post(f"/api/v1/cases/{case_id}/report").json()
print("\n=== REAL RAG REPORT ===")
print("STATUS:", rep["status"])
print("SUMMARY:", rep["summary"])
print("EVIDENCE count:", len(rep["case"]["retrieved_evidence"]))
print("DIFFERENTIAL:")
for d in rep["case"]["differential"]:
    print(
        f"  #{d['rank']} {d['condition_id']} "
        f"strength={d['evidence_strength']} uncertainty={d['uncertainty']}"
    )
print("ACTIONS:", rep["case"]["recommended_actions"][:2])
if rep["case"]["escalation"]:
    print("ESCALATION:", rep["case"]["escalation"])
