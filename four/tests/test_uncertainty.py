"""Tests for uncertainty estimation."""
from src.models import CaseRecord, DifferentialItem
from src.uncertainty import assess


def test_high_when_many_critical_missing():
    case = CaseRecord(case_id="T")
    missing = [{"importance": "critical"}, {"importance": "critical"}]
    diff = [DifferentialItem(condition_id="D01", rank=1, evidence_strength="moderate", uncertainty="medium")]
    assert assess(case, missing, diff, {"D01": 5, "D02": 4}) == "high"


def test_high_when_top_two_close():
    case = CaseRecord(case_id="T")
    missing = []
    diff = [
        DifferentialItem(condition_id="D01", rank=1, evidence_strength="strong", uncertainty="low"),
        DifferentialItem(condition_id="D04", rank=2, evidence_strength="strong", uncertainty="low"),
    ]
    # close scores -> ambiguous -> high
    assert assess(case, missing, diff, {"D01": 5.0, "D04": 4.2}) == "high"


def test_medium_with_one_critical_missing():
    case = CaseRecord(case_id="T")
    missing = [{"importance": "critical"}]
    diff = [
        DifferentialItem(condition_id="D02", rank=1, evidence_strength="strong", uncertainty="medium"),
        DifferentialItem(condition_id="D05", rank=2, evidence_strength="weak", uncertainty="medium"),
    ]
    assert assess(case, missing, diff, {"D02": 8.0, "D05": 1.0}) == "medium"


def test_low_when_complete_and_clear_gap():
    case = CaseRecord(case_id="T")
    missing = []
    diff = [
        DifferentialItem(condition_id="D02", rank=1, evidence_strength="strong", uncertainty="low"),
        DifferentialItem(condition_id="D05", rank=2, evidence_strength="weak", uncertainty="low"),
    ]
    assert assess(case, missing, diff, {"D02": 10.0, "D05": 2.0}) == "low"
