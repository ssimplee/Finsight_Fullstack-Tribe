from pydantic import BaseModel, Field


class FishInfo(BaseModel):
    species: str = "Nile tilapia"
    life_stage: str | None = None


class WaterQuality(BaseModel):
    temperature_c: float | None = None
    ph: float | None = None
    dissolved_oxygen_mg_l: float | None = None
    ammonia_mg_l: float | None = None
    nitrite_mg_l: float | None = None
    nitrate_mg_l: float | None = None


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
    condition_id: str | None = None
    source_id: str | None = None
    label: str
    text: str


class AgentQuestion(BaseModel):
    question_id: str
    question: str
    reason: str
    answer: str | None = None


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
    history: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


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
