"""Tests for the MockQwenClient (Member 3 stand-in)."""
from src.qwen_client import ImageObservation, MockQwenClient


def test_returns_canned_observation_by_filename():
    client = MockQwenClient()
    obs = client.analyze_image("any/dir/tilapia_flank_ulcer.jpg")
    assert obs.quality_ok
    assert "flank ulcer" in obs.visual
    assert "lethargy" in obs.behavioral


def test_unknown_file_marked_low_quality():
    client = MockQwenClient()
    obs = client.analyze_image("unknown.jpg")
    assert not obs.quality_ok
    assert obs.note  # has an explanation


def test_custom_canned_overrides_default():
    client = MockQwenClient(canned={"x.jpg": ImageObservation(visual=["custom finding"])})
    obs = client.analyze_image("x.jpg")
    assert obs.visual == ["custom finding"]
