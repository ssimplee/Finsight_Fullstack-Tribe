import { buildMockReport } from "../data/mockReport";
import { mockObservation } from "../data/mockCase";
import { buildSharedCaseRecord } from "../data/sharedCaseSchema";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";
const mockCaseStore = new Map();

function deepCopy(value) {
  return JSON.parse(JSON.stringify(value));
}

function ensureCase(caseId) {
  const storedCase = mockCaseStore.get(caseId);

  if (!storedCase) {
    throw new Error("Case record is not available in mock storage.");
  }

  return storedCase;
}

function delay(response, timeout = 250) {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(response), timeout);
  });
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
  // Mock implementation for future POST /api/cases using VITE_API_BASE_URL.
  void API_BASE_URL;

  const caseId = `CASE-${String(mockCaseStore.size + 1).padStart(3, "0")}`;
  const record = {
    caseId,
    caseData: deepCopy(caseData),
    followUpAnswers: {},
    imageFileName: null,
    observation: null,
    analysisRequested: false,
    createdAt: new Date().toISOString(),
    sharedCase: null,
    reportSnapshot: null,
  };

  refreshSharedCaseRecord(record);

  mockCaseStore.set(caseId, record);

  return delay({
    caseId,
  });
}

export async function uploadFishImage(caseId, imageFile) {
  // Mock implementation for future POST /api/cases/{caseId}/images.
  const record = ensureCase(caseId);

  record.imageFileName = imageFile?.name ?? null;
  record.observation = mockObservation;
  refreshSharedCaseRecord(record);

  return delay({
    success: true,
  });
}

export async function submitFollowUpAnswers(caseId, answers) {
  // Mock implementation for future POST /api/cases/{caseId}/follow-up.
  const record = ensureCase(caseId);

  record.followUpAnswers = deepCopy(answers);
  refreshSharedCaseRecord(record);

  return delay({
    success: true,
  });
}

export async function requestAnalysis(caseId) {
  // Mock implementation for future POST /api/cases/{caseId}/analyze.
  const record = ensureCase(caseId);

  record.analysisRequested = true;
  refreshSharedCaseRecord(record);

  return delay({
    success: true,
  });
}

export async function getReport(caseId) {
  // Mock implementation for future GET /api/cases/{caseId}/report.
  const record = ensureCase(caseId);

  if (!record.observation) {
    record.observation = mockObservation;
  }

  record.reportSnapshot = buildMockReport(record);
  refreshSharedCaseRecord(record);

  return delay(record.reportSnapshot, 350);
}
