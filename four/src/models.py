"""Pydantic models aligned 1:1 with backend/app/schemas/case.py.

These are the contract types for Member 4's outputs. When the module moves
into backend/app/services/rag/, replace these definitions with:
    from app.schemas.case import (FishInfo, WaterQuality, ...)
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class FishInfo(BaseModel):
    species: str = "Nile tilapia"
    life_stage: Optional[str] = None


class WaterQuality(BaseModel):
    temperature_c: Optional[float] = None
    ph: Optional[float] = None
    dissolved_oxygen_mg_l: Optional[float] = None
    ammonia_mg_l: Optional[float] = None
    nitrite_mg_l: Optional[float] = None
    nitrate_mg_l: Optional[float] = None


class Observations(BaseModel):
    visual: list[str] = Field(default_factory=list)
    behavioral: list[str] = Field(default_factory=list)


class CaseImage(BaseModel):
    image_id: str
    filename: str
    visible_findings: list[str] = Field(default_factory=list)
    source: str = "user_upload"


class EvidenceItem(BaseModel):
    evidence_id: str
    condition_id: Optional[str] = None
    source_id: Optional[str] = None
    label: str
    text: str


class AgentQuestion(BaseModel):
    question_id: str
    question: str
    reason: str
    answer: Optional[str] = None


class DifferentialItem(BaseModel):
    condition_id: str
    rank: int
    evidence_strength: str
    uncertainty: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    conflicting_evidence_ids: list[str] = Field(default_factory=list)
    confirmation_status: str = "unconfirmed"


class CaseCreate(BaseModel):
    fish: FishInfo = Field(default_factory=FishInfo)
    images: list[CaseImage] = Field(default_factory=list)
    observations: Observations = Field(default_factory=Observations)
    water_quality: WaterQuality = Field(default_factory=WaterQuality)
    history: dict[str, Any] = Field(default_factory=dict)


class CaseRecord(CaseCreate):
    case_id: str
    agent_questions: list[AgentQuestion] = Field(default_factory=list)
    retrieved_evidence: list[EvidenceItem] = Field(default_factory=list)
    differential: list[DifferentialItem] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    escalation: list[str] = Field(default_factory=list)


class CaseReport(BaseModel):
    case: CaseRecord
    status: str
    summary: str
