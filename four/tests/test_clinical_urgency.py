"""Tests for clinical-urgency weighting and the insufficient-evidence guard.

Both are grounded in actual case signals (not arbitrary boosting) so ordinary
single-cause cases are not distorted.
"""
from src import differential
from src.models import CaseRecord, EvidenceItem, FishInfo, Observations, WaterQuality


def _case(visual=None, behavioral=None, water=None, history=None, images=None):
    return CaseRecord(
        case_id="T",
        fish=FishInfo(),
        observations=Observations(visual=visual or [], behavioral=behavioral or []),
        water_quality=water or WaterQuality(),
        history=history or {},
        images=images or [],
    )


def test_low_do_triggers_d05_urgency_bonus():
    # DO=3.5 is low (<4) but not critical (>=3) -> single-signal +1.5 tier.
    case = _case(water=WaterQuality(dissolved_oxygen_mg_l=3.5))
    b = differential._urgency_bonus(case)
    assert b["D05"] == differential.URGENCY_BONUS["D05"]
    assert b["D04"] == 0.0


def test_critical_do_triggers_d05_severe_urgency():
    # DO<3 is a life-threatening acute emergency -> double (+3.0) tier.
    case = _case(water=WaterQuality(dissolved_oxygen_mg_l=2.0))
    b = differential._urgency_bonus(case)
    assert b["D05"] == differential.URGENCY_BONUS["D05"] * 2.0


def test_high_ammonia_triggers_d05_urgency_bonus():
    case = _case(water=WaterQuality(ammonia_mg_l=0.8))
    assert differential._urgency_bonus(case)["D05"] == differential.URGENCY_BONUS["D05"]


def test_aeration_failure_in_history_triggers_d05():
    case = _case(history={"aeration_failure": True})
    assert differential._urgency_bonus(case)["D05"] == differential.URGENCY_BONUS["D05"]


def test_fish_movement_triggers_d04_urgency_bonus():
    case = _case(history={"recent_introduction": "yes"})
    b = differential._urgency_bonus(case)
    assert b["D04"] == differential.URGENCY_BONUS["D04"]
    assert b["D05"] == 0.0


def test_mass_mortality_triggers_d04():
    case = _case(history={"mortality_trend": "mass mortality overnight"})
    assert differential._urgency_bonus(case)["D04"] == differential.URGENCY_BONUS["D04"]


def test_exophthalmia_haemorrhage_alone_does_not_boost_d04():
    # Aeromonas/Strep share these signs -> must NOT falsely boost TiLV.
    case = _case(visual=["exophthalmia", "haemorrhage"])
    assert differential._urgency_bonus(case)["D04"] == 0.0


def test_normal_bacterial_case_no_urgency_bonus():
    case = _case(
        visual=["flank ulcer", "scale loss"],
        water=WaterQuality(dissolved_oxygen_mg_l=6.0, ammonia_mg_l=0.02),
    )
    b = differential._urgency_bonus(case)
    assert all(v == 0.0 for v in b.values())


def test_insufficient_case_declines_to_rank():
    # No image, no visual, critical water triad missing -> empty differential.
    case = _case(behavioral=["lethargy"], water=WaterQuality())
    items, _ = differential.rank(case, [])
    assert items == []


def test_insufficient_does_not_fire_when_visual_present():
    case = _case(visual=["flank ulcer"], water=WaterQuality())
    # has visual -> not insufficient -> should rank (even with no evidence,
    # symptom keywords give D02 a score)
    items, _ = differential.rank(case, [])
    assert items  # non-empty


def test_insufficient_does_not_fire_when_image_findings_present():
    from src.models import CaseImage
    case = _case(
        water=WaterQuality(),
        images=[CaseImage(image_id="IMG_1", filename="x.jpg", visible_findings=["flank ulcer"])],
    )
    items, _ = differential.rank(case, [])
    assert items  # image findings count as signal -> rank


def test_insufficient_does_not_fire_when_water_present():
    # Even without images/visual, having the critical water triad filled means
    # we have enough environmental signal to rank D05.
    case = _case(
        water=WaterQuality(dissolved_oxygen_mg_l=2.0, temperature_c=28.0, ammonia_mg_l=0.01),
    )
    items, _ = differential.rank(case, [])
    assert items  # low DO + filled water -> D05 should rank
