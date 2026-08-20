"""Tests for missing-information detection."""
from src.missing_info import detect_missing
from src.models import CaseRecord, FishInfo, Observations, WaterQuality


def _full_case() -> CaseRecord:
    return CaseRecord(
        case_id="T",
        fish=FishInfo(),
        observations=Observations(visual=["ulcer"], behavioral=["lethargy"]),
        water_quality=WaterQuality(
            temperature_c=28,
            ph=7.5,
            dissolved_oxygen_mg_l=5.0,
            ammonia_mg_l=0.1,
            nitrite_mg_l=0.2,
            nitrate_mg_l=10.0,
        ),
        history={"mortality_trend": "stable"},
    )


def test_detects_missing_water_fields():
    case = CaseRecord(case_id="T", fish=FishInfo())
    fields = {m["field"] for m in detect_missing(case)}
    assert "dissolved_oxygen_mg_l" in fields
    assert "temperature_c" in fields
    assert "ammonia_mg_l" in fields


def test_no_critical_missing_when_complete():
    case = _full_case()
    missing = detect_missing(case)
    critical = [m for m in missing if m["importance"] == "critical"]
    assert not any(m["field"] in {"dissolved_oxygen_mg_l", "temperature_c", "ammonia_mg_l"} for m in critical)


def test_critical_sorted_before_secondary():
    case = CaseRecord(case_id="T", fish=FishInfo())
    missing = detect_missing(case)
    order = {"critical": 0, "important": 1, "secondary": 2}
    importances = [order[m["importance"]] for m in missing]
    assert importances == sorted(importances)


def test_missing_image_flagged():
    case = CaseRecord(case_id="T", fish=FishInfo())
    fields = {m["field"] for m in detect_missing(case)}
    assert "images" in fields
