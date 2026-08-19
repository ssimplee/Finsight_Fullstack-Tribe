"""Tests for the observable-finding vocabulary and few-shot examples (Member 3)."""

from __future__ import annotations

import json

from app.services.vision_prompts import build_vision_prompt, build_vision_prompt_with_terms
from app.services.vision_terms import (
    FEWSHOT_EXAMPLES,
    TILAPIA_OBSERVABLE_TERMS,
    TILAPIA_TERMS_CN,
)

_DIAGNOSTIC_WORDS = [
    "disease",
    "pathogen",
    "bacteria",
    "virus",
    "streptococc",
    "aeromonas",
    "columnaris",
    "tilv",
    "infection",
    "diagnosis",
    "treatment",
    "antibiotic",
]


def test_terms_contain_no_diagnostic_words():
    joined = " ".join(TILAPIA_OBSERVABLE_TERMS).lower()
    for word in _DIAGNOSTIC_WORDS:
        assert word not in joined


def test_cn_mapping_is_complete():
    assert set(TILAPIA_TERMS_CN) == set(TILAPIA_OBSERVABLE_TERMS)


def test_fewshot_examples_are_valid_json_with_fields():
    for example in FEWSHOT_EXAMPLES:
        obj = json.loads(example)
        assert "quality" in obj
        assert "findings" in obj


def test_build_vision_prompt_includes_vocabulary_and_examples():
    prompt = build_vision_prompt()
    assert "skin ulcer" in prompt
    assert FEWSHOT_EXAMPLES[0] in prompt


def test_build_vision_prompt_with_terms_accepts_custom_input():
    prompt = build_vision_prompt_with_terms(
        terms=["custom ulcer"],
        examples=['{"quality": "usable", "findings": []}'],
    )
    assert "custom ulcer" in prompt
    assert "custom ulcer" not in build_vision_prompt()  # default prompt unchanged