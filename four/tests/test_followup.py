"""Tests for follow-up question generation."""
from src.follow_up import build_questions
from src.models import CaseRecord, FishInfo


def test_at_least_two_questions():
    case = CaseRecord(case_id="T", fish=FishInfo())
    qs = build_questions(case)
    assert len(qs) >= 2


def test_every_question_has_reason():
    case = CaseRecord(case_id="T", fish=FishInfo())
    qs = build_questions(case)
    assert all(q.reason for q in qs)


def test_questions_target_missing_fields():
    case = CaseRecord(case_id="T", fish=FishInfo())
    qs = build_questions(case)
    text = " ".join(q.question.lower() for q in qs)
    assert "dissolved oxygen" in text or "temperature" in text


def test_question_ids_unique():
    case = CaseRecord(case_id="T", fish=FishInfo())
    qs = build_questions(case)
    ids = [q.question_id for q in qs]
    assert len(ids) == len(set(ids))
