from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_case_mock_workflow() -> None:
    create_response = client.post(
        "/api/v1/cases",
        json={
            "observations": {
                "visual": ["red patches near gills"],
                "behavioral": ["surface gasping", "reduced appetite"],
            },
            "water_quality": {
                "temperature_c": 29.0,
                "ph": 7.2,
                "dissolved_oxygen_mg_l": None,
                "ammonia_mg_l": None,
                "nitrite_mg_l": None,
                "nitrate_mg_l": None,
            },
            "history": {"symptom_duration_days": 2},
        },
    )
    assert create_response.status_code == 200
    case = create_response.json()
    case_id = case["case_id"]

    follow_up_response = client.post(f"/api/v1/cases/{case_id}/follow-up")
    assert follow_up_response.status_code == 200
    questions = follow_up_response.json()
    assert len(questions) >= 2
    assert questions[0]["answer"] is None

    early_report_response = client.post(f"/api/v1/cases/{case_id}/report")
    assert early_report_response.status_code == 200
    assert early_report_response.json()["status"] == "needs_follow_up"

    answer_response = client.post(
        f"/api/v1/cases/{case_id}/follow-up/answers",
        json={
            "answers": [
                {"question_id": questions[0]["question_id"], "answer": "3.2 mg/L"},
                {"question_id": questions[1]["question_id"], "answer": "0.25 mg/L"},
            ]
        },
    )
    assert answer_response.status_code == 200

    report_response = client.post(f"/api/v1/cases/{case_id}/report")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["status"] == "mock_report_ready"
    assert len(report["case"]["retrieved_evidence"]) == 2
    assert len(report["case"]["differential"]) == 2


def test_update_case() -> None:
    create_response = client.post("/api/v1/cases", json={})
    case_id = create_response.json()["case_id"]

    update_response = client.patch(
        f"/api/v1/cases/{case_id}",
        json={
            "history": {
                "recent_transport": True,
                "mortality_trend": "two fish died overnight",
            }
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["history"]["recent_transport"] is True


def test_missing_case_returns_404() -> None:
    response = client.get("/api/v1/cases/CASE_MISSING")
    assert response.status_code == 404
