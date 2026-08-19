"""Tests for the Retriever auto-ingest guard (empty-DB self-heal).

The vector DB is gitignored, so a fresh clone has no four/fin_sight_db/ and
get_or_create_collection silently makes an empty collection. The Retriever
must detect count()==0 and ingest once, and must NOT re-ingest a populated DB.
These tests stub build_collection so the suite stays fast (no model load).
"""
from types import SimpleNamespace

import src.retriever as retriever_mod
from src.retriever import Retriever


class _FakeCollection:
    def __init__(self, count: int):
        self._count = count

    def count(self):
        return self._count


def _patch_build(monkeypatch, count, ingest_calls):
    def fake_build(db_path):
        return _FakeCollection(count)

    def fake_ingest(data_file, db_path=None):
        ingest_calls.append((data_file, db_path))
        return 29

    monkeypatch.setattr(retriever_mod, "build_collection", fake_build)
    # The Retriever imports DEFAULT_DATA/ingest lazily via `from .ingest import`
    # which resolves to the `src.ingest` module. Patch that sys.modules entry so
    # the lazy import picks up our fakes without loading the real ingest module.
    import sys
    fake_ingest_mod = SimpleNamespace(DEFAULT_DATA="MOCK_DATA", ingest=fake_ingest)
    monkeypatch.setitem(sys.modules, "src.ingest", fake_ingest_mod)


def test_empty_db_triggers_auto_ingest(monkeypatch):
    ingest_calls = []
    _patch_build(monkeypatch, count=0, ingest_calls=ingest_calls)
    Retriever(db_path="/tmp/ignored", auto_ingest=True)
    assert len(ingest_calls) == 1
    assert ingest_calls[0][1] == "/tmp/ignored"  # db_path forwarded


def test_populated_db_does_not_re_ingest(monkeypatch):
    ingest_calls = []
    _patch_build(monkeypatch, count=29, ingest_calls=ingest_calls)
    Retriever(db_path="/tmp/ignored", auto_ingest=True)
    assert ingest_calls == []  # already populated, no ingest


def test_auto_ingest_disabled_does_not_ingest_even_if_empty(monkeypatch):
    ingest_calls = []
    _patch_build(monkeypatch, count=0, ingest_calls=ingest_calls)
    Retriever(db_path="/tmp/ignored", auto_ingest=False)
    assert ingest_calls == []
