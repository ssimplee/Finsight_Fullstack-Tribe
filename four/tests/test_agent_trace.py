"""Tests for the agent decision trace (worksplit §13.6).

The trace is a workflow audit trail (case received -> missing info ->
follow-ups -> evidence -> conditions -> safety) that Member 5 surfaces in the
report. It must be populated and travel on the case into the report.
"""
from src.agent import Agent
from src.models import CaseRecord, FishInfo, Observations


class _FakeRetriever:
    """Avoid loading chromadb + the embedding model in unit tests."""

    def __init__(self, *_a, **_k):
        pass

    def retrieve(self, case, n_results=10, condition_id=None, evidence_type=None):
        from src.models import EvidenceItem
        return [
            EvidenceItem(
                evidence_id="E1", condition_id="D02",
                label="supporting evidence", text="flank ulcer scale loss",
            )
        ]


def _build_agent():
    # Bypass the heavy Retriever construction (model download) by injecting
    # the fake after instantiation.
    import src.agent as agent_mod
    original_init = agent_mod.Agent.__post_init__

    def _stub_post_init(self):
        self._retriever = _FakeRetriever()

    agent_mod.Agent.__post_init__ = _stub_post_init
    try:
        return Agent(db_path="unused")
    finally:
        agent_mod.Agent.__post_init__ = original_init


def test_trace_is_populated():
    agent = _build_agent()
    case = CaseRecord(
        case_id="T",
        fish=FishInfo(),
        observations=Observations(visual=["flank ulcer", "scale loss"], behavioral=[]),
    )
    report = agent.run(case)
    assert case.agent_trace, "trace must not be empty"
    assert len(case.agent_trace) >= 4
    # report carries the same case object, so the trace is reachable downstream
    assert report.case.agent_trace is case.agent_trace


def test_trace_mentions_key_stages():
    agent = _build_agent()
    case = CaseRecord(case_id="T", fish=FishInfo())
    agent.run(case)
    joined = " ".join(case.agent_trace).lower()
    # the audit trail should reference the main pipeline stages
    assert "received" in joined
    assert "evidence" in joined
    assert "conditions" in joined or "compared" in joined
    assert "safety" in joined or "missing" in joined
