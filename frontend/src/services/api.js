import { mockObservation } from "../data/mockCase";
import { buildMockReport } from "../data/mockReport";
import { buildSharedCaseRecord } from "../data/sharedCaseSchema";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
const localCaseStore = new Map();

function deepCopy(value) {
  return JSON.parse(JSON.stringify(value));
}

function ensureCase(caseId) {
  const storedCase = localCaseStore.get(caseId);

  if (!storedCase) {
    throw new Error("Case record is not available in local frontend state.");
  }

  return storedCase;
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

function normalizeNullableNumber(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const parsedValue = Number(value);
  return Number.isNaN(parsedValue) ? null : parsedValue;
}

function mapCaseFormToBackend(caseData) {
  return {
    fish: {
      species: caseData.species || "Nile tilapia",
      life_stage: caseData.lifeStage || null,
    },
    observations: {
      visual: [
        ...caseData.visibleSymptoms,
        ...(caseData.additionalObservations.trim()
          ? [caseData.additionalObservations.trim()]
          : []),
      ],
      behavioral: caseData.behavioralSigns,
    },
    water_quality: {
      temperature_c: normalizeNullableNumber(caseData.waterQuality.temperatureC),
      ph: normalizeNullableNumber(caseData.waterQuality.ph),
      dissolved_oxygen_mg_l: normalizeNullableNumber(
        caseData.waterQuality.dissolvedOxygenMgL,
      ),
      ammonia_mg_l: normalizeNullableNumber(caseData.waterQuality.ammoniaMgL),
      nitrite_mg_l: normalizeNullableNumber(caseData.waterQuality.nitriteMgL),
      nitrate_mg_l: normalizeNullableNumber(caseData.waterQuality.nitrateMgL),
    },
    history: {
      symptom_duration: caseData.symptomDuration || null,
      mortality_trend: caseData.mortalityTrend || null,
      recent_events:
        caseData.recentHistory.length > 0
          ? caseData.recentHistory.join("; ")
          : null,
      notes: caseData.historyNotes || null,
    },
  };
}

function mapFollowUpAnswersToBackend(questions, answers) {
  const mappedAnswers = questions.flatMap((question) => {
    const currentAnswer = answers[question.question_id];
    if (!currentAnswer) {
      return [];
    }

    const answerText = [
      currentAnswer.value
        ? `${currentAnswer.value}${question.question.toLowerCase().includes("level") ? " mg/L" : ""}`
        : "",
      currentAnswer.choice,
      currentAnswer.notes,
    ]
      .filter(Boolean)
      .join(". ");

    if (!answerText) {
      return [];
    }

    return [{ question_id: question.question_id, answer: answerText }];
  });

  return { answers: mappedAnswers };
}

function mapBackendQuestionsToFrontend(questions) {
  return questions.map((question) => ({
    id: question.question_id,
    prompt: question.question,
    rationale: question.reason,
    inputType: question.question.toLowerCase().includes("mortality")
      ? "choice"
      : "number",
    choices: question.question.toLowerCase().includes("mortality")
      ? ["Yes", "No", "Unknown"]
      : undefined,
    unitLabel:
      question.question.toLowerCase().includes("level") ||
      question.question.toLowerCase().includes("oxygen") ||
      question.question.toLowerCase().includes("ammonia")
        ? "mg/L"
        : "",
    placeholder: "Enter answer",
  }));
}

function conditionLabel(conditionId) {
  const labels = {
    D01: "Streptococcosis",
    D02: "Motile Aeromonas Septicemia",
    D03: "Columnaris disease",
    D04: "Tilapia Lake Virus disease",
    D05: "Water-quality stress",
  };

  return labels[conditionId] || conditionId;
}

function mapBackendReportToFrontend(report) {
  const record = report.case;
  const localRecord = localCaseStore.get(record.case_id);
  const localReport = buildMockReport({
    caseId: record.case_id,
    caseData: localRecord?.caseData ?? {
      species: record.fish.species,
      lifeStage: record.fish.life_stage || "Unknown",
      mortalityTrend: record.history?.mortality_trend || "",
      visibleSymptoms: record.observations.visual,
      behavioralSigns: record.observations.behavioral,
      waterQuality: {},
    },
    followUpAnswers: localRecord?.followUpAnswers ?? {},
    observation: localRecord?.observation ?? mockObservation,
  });

  return {
    ...localReport,
    caseId: record.case_id,
    fish: {
      species: record.fish.species,
      lifeStage: record.fish.life_stage || "Unknown",
    },
    status: {
      assessment:
        report.status === "mock_report_ready"
          ? "Mock triage complete"
          : "Needs follow-up",
      confirmation: "Unconfirmed",
      uncertainty: record.differential[0]?.uncertainty || "Moderate",
    },
    observations: {
      ...localReport.observations,
      visual: record.observations.visual.map((text, index) => ({
        id: `backend-visual-${index + 1}`,
        label: "USER-REPORTED",
        text,
      })),
      userReported: record.observations.behavioral.map((text, index) => ({
        id: `backend-behavior-${index + 1}`,
        label: "USER-REPORTED",
        text,
      })),
    },
    differential:
      record.differential.length > 0
        ? record.differential.map((item) => ({
            id: item.condition_id,
            rank: item.rank,
            diagnosis: conditionLabel(item.condition_id),
            evidenceStrength: item.evidence_strength,
            uncertainty: item.uncertainty,
            confirmationStatus: item.confirmation_status,
            supportingEvidence: item.supporting_evidence_ids,
            conflictingEvidence: item.conflicting_evidence_ids,
          }))
        : localReport.differential,
    recommendedActions:
      record.recommended_actions.length > 0
        ? record.recommended_actions.map((text, index) => ({
            id: `backend-action-${index + 1}`,
            text,
          }))
        : localReport.recommendedActions,
    escalation:
      record.escalation.length > 0
        ? record.escalation.map((text, index) => ({
            id: `backend-escalation-${index + 1}`,
            text,
          }))
        : localReport.escalation,
    sources:
      record.retrieved_evidence.length > 0
        ? record.retrieved_evidence.map((item) => ({
            id: item.evidence_id,
            title: item.label,
            organization: item.source_id || "Pending source",
            section: item.condition_id || "Mock evidence",
            passage: item.text,
            usage: "Returned by the backend mock workflow.",
          }))
        : localReport.sources,
  };
}

function refreshSharedCaseRecord(record) {
  record.sharedCase = buildSharedCaseRecord({
    caseId: record.caseId,
    caseForm: record.caseData,
    followUpAnswers: record.followUpAnswers,
    imageFileName: record.imageFileName,
    observation: record.observation,
    differential: record.reportSnapshot?.differential ?? [],
    recommendedActions: record.reportSnapshot?.recommendedActions ?? [],
    escalation: record.reportSnapshot?.escalation ?? [],
  });
}

export async function createCase(caseData) {
  const backendCase = await requestJson("/cases", {
    method: "POST",
    body: JSON.stringify(mapCaseFormToBackend(caseData)),
  });
  const caseId = backendCase.case_id;
  const record = {
    caseId,
    caseData: deepCopy(caseData),
    followUpAnswers: {},
    imageFileName: null,
    observation: null,
    backendQuestions: [],
    analysisRequested: false,
    createdAt: new Date().toISOString(),
    sharedCase: null,
    reportSnapshot: null,
  };

  refreshSharedCaseRecord(record);
  localCaseStore.set(caseId, record);

  return { caseId };
}

export async function uploadFishImage(caseId, imageFile) {
  const record = ensureCase(caseId);
  const formData = new FormData();
  formData.append("file", imageFile);

  await requestJson(`/cases/${caseId}/images`, {
    method: "POST",
    body: formData,
  });

  record.imageFileName = imageFile?.name ?? null;
  record.observation = mockObservation;
  refreshSharedCaseRecord(record);

  return { success: true };
}

export async function getFollowUpQuestions(caseId) {
  const record = ensureCase(caseId);
  const questions = await requestJson(`/cases/${caseId}/follow-up`, {
    method: "POST",
  });

  record.backendQuestions = questions;
  return mapBackendQuestionsToFrontend(questions);
}

export async function submitFollowUpAnswers(caseId, answers) {
  const record = ensureCase(caseId);
  await requestJson(`/cases/${caseId}/follow-up/answers`, {
    method: "POST",
    body: JSON.stringify(mapFollowUpAnswersToBackend(record.backendQuestions, answers)),
  });

  record.followUpAnswers = deepCopy(answers);
  refreshSharedCaseRecord(record);

  return { success: true };
}

export async function requestAnalysis(caseId) {
  const record = ensureCase(caseId);

  record.analysisRequested = true;
  refreshSharedCaseRecord(record);

  return { success: true };
}

export async function getReport(caseId) {
  const record = ensureCase(caseId);
  const backendReport = await requestJson(`/cases/${caseId}/report`, {
    method: "POST",
  });
  record.reportSnapshot = mapBackendReportToFrontend(backendReport);
  refreshSharedCaseRecord(record);

  return record.reportSnapshot;
}
