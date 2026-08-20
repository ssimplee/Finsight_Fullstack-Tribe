"""Tests for differential scoring and ranking."""
from src import differential
from src.models import CaseRecord, EvidenceItem, FishInfo, Observations


def test_symptom_hits_drive_score():
    case = CaseRecord(
        case_id="T",
        fish=FishInfo(),
        observations=Observations(visual=["flank ulcer", "scale loss"], behavioral=[]),
    )
    scores = differential.score(case, [])
    assert scores["D02"] > 0


def test_conflicting_evidence_lowers_score():
    case = CaseRecord(case_id="T", fish=FishInfo())
    ev = [
        EvidenceItem(evidence_id="E1", condition_id="D02", label="supporting evidence", text="ulcer"),
        EvidenceItem(evidence_id="E2", condition_id="D02", label="conflicting evidence", text="x"),
    ]
    scores = differential.score(case, ev)
    # supporting (+2) + conflicting (-1.5) = 0.5
    assert scores["D02"] == 0.5


def test_rank_returns_sorted_items():
    case = CaseRecord(
        case_id="T",
        fish=FishInfo(),
        observations=Observations(visual=["flank ulcer"], behavioral=[]),
    )
    ev = [EvidenceItem(evidence_id="E1", condition_id="D02", label="supporting evidence", text="ulcer")]
    items, _ = differential.rank(case, ev)
    assert items
    assert items[0].rank == 1
    assert items[0].condition_id == "D02"
    ranks = [i.rank for i in items]
    assert ranks == sorted(ranks)


def test_supporting_and_conflicting_classification():
    case = CaseRecord(
        case_id="T", fish=FishInfo(),
        observations=Observations(visual=["eye haemorrhage"], behavioral=[]),
    )
    ev = [
        EvidenceItem(evidence_id="E1", condition_id="D01", label="supporting evidence", text="x"),
        EvidenceItem(evidence_id="E2", condition_id="D01", label="conflicting evidence", text="y"),
    ]
    items, _ = differential.rank(case, ev)
    d01 = next(i for i in items if i.condition_id == "D01")
    assert "E1" in d01.supporting_evidence_ids
    assert "E2" in d01.conflicting_evidence_ids


def test_zero_score_condition_not_ranked():
    case = CaseRecord(case_id="T", fish=FishInfo())
    ev = []
    items, _ = differential.rank(case, ev)
    # nothing observed, nothing retrieved -> no ranked condition
    assert items == []
