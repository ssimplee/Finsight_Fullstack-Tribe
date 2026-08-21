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

const recentHistoryFieldMap = {
  "Recent fish introduction": "recent_introduction",
  "Stocking-density change": "stocking_density_change",
  "Recent transport or handling": "transport_handling",
  "Feed change": "feed_change",
  "Recent treatment": "treatment",
  "Water change": "water_change",
  "Filtration or oxygenation failure": "filtration_failure",
  "Recent temperature change": "temperature_change",
};

function mapCaseFormToBackend(caseData) {
  const history = {
    symptom_duration: caseData.symptomDuration || null,
    mortality_trend: caseData.mortalityTrend || null,
    notes: caseData.historyNotes || null,
  };

  // Map each checked management-history item to the semantic field the RAG
  // modules key off (missing_info / differential key on exact keys like
  // `filtration_failure`, not a rolled-up `recent_events` blob).
  for (const item of caseData.recentHistory) {
    const field = recentHistoryFieldMap[item];
    if (field) {
      history[field] = item;
    }
  }

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
    history,
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
  return questions.map((question) => {
    const lower = question.question.toLowerCase();

    // Yes/No 问句 → 单选（Yes / No / Unknown）
    const isYesNo = /^(have|has|are|is|do|did|can|was|were)\b/.test(lower);
    // 数值测量类（浓度/温度/pH/时长）→ 数字输入
    const isMeasurement =
      /(level|temperature|ph\b|how long|duration|oxygen|ammonia|nitrite|nitrate)/.test(
        lower,
      );

    let inputType = "number";
    let choices;

    if (isYesNo) {
      inputType = "choice";
      choices = ["Yes", "No", "Unknown"];
    } else if (isMeasurement) {
      inputType = "number";
    } else {
      // 无法明确归类时用单选兜底，避免误渲染成数字框导致无法输入
      inputType = "choice";
      choices = ["Yes", "No", "Unknown"];
    }

    return {
      id: question.question_id,
      prompt: question.question,
      rationale: question.reason,
      inputType,
      choices,
      unitLabel: lower.includes("temperature")
        ? "°C"
        : lower.includes("level") ||
            lower.includes("oxygen") ||
            lower.includes("ammonia") ||
            lower.includes("nitrite") ||
            lower.includes("nitrate")
          ? "mg/L"
          : "",
      placeholder: "Enter answer",
    };
  });
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

  const imageFindings = (record.images ?? []).flatMap(
    (image) => image.visible_findings ?? [],
  );

  return {
    ...localReport,
    caseId: record.case_id,
    summary: report.summary || "",
    fish: {
      species: record.fish.species,
      lifeStage: record.fish.life_stage || "Unknown",
    },
    status: {
      assessment:
        report.status === "report_ready" || report.status === "mock_report_ready"
          ? "Triage complete"
          : "Needs follow-up",
      confirmation: "Unconfirmed",
      uncertainty: record.differential[0]?.uncertainty || "Moderate",
    },
    observations: {
      ...localReport.observations,
      visual:
        imageFindings.length > 0
          ? imageFindings.map((text, index) => ({
              id: `backend-visual-${index + 1}`,
              label: "OBSERVED",
              text,
            }))
          : record.observations.visual.map((text, index) => ({
              id: `backend-reported-${index + 1}`,
              label: "USER-REPORTED",
              text,
            })),
      userReported: [
        ...record.observations.visual.map((text, index) => ({
          id: `backend-reported-${index + 1}`,
          label: "USER-REPORTED",
          text,
        })),
        ...record.observations.behavioral.map((text, index) => ({
          id: `backend-behavior-${index + 1}`,
          label: "USER-REPORTED",
          text,
        })),
      ],
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
            organization: item.source_id || "Knowledge base",
            section: item.condition_id || "General evidence",
            passage: item.text,
            usage: "Retrieved from the fish-disease knowledge base for this assessment.",
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

function buildObservationFromUpload(uploaded) {
  const images = uploaded?.images ?? [];
  const findings = images.flatMap((image) => image.visible_findings ?? []);
  const realFindings = findings.filter(
    (text) => text && !/pending|unavailable|none/i.test(text),
  );

  if (realFindings.length === 0) {
    return mockObservation;
  }

  return {
    id: "observation-backend",
    label: "Observed, not confirmed",
    findings: realFindings,
    limitations: [
      "Image findings are decision support only and cannot confirm a disease.",
      "Laboratory testing is still required for a confirmed diagnosis.",
    ],
  };
}

export async function uploadFishImage(caseId, imageFile) {
  const record = ensureCase(caseId);
  const formData = new FormData();
  formData.append("file", imageFile);

  const uploaded = await requestJson(`/cases/${caseId}/images`, {
    method: "POST",
    body: formData,
  });

  record.imageFileName = imageFile?.name ?? null;
  record.observation = buildObservationFromUpload(uploaded);
  refreshSharedCaseRecord(record);

  return { success: true, observation: record.observation };
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
