function normalizeNullableNumber(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const parsedValue = Number(value);

  return Number.isNaN(parsedValue) ? null : parsedValue;
}

function buildImageEntries(caseId, imageFileName) {
  if (!imageFileName) {
    return [];
  }

  return [
    {
      image_id: `${caseId}_IMG_001`,
      filename: imageFileName,
      source: "user_upload",
    },
  ];
}

function buildVisualObservations(observation, caseForm) {
  const observationEntries = [];

  if (observation?.findings?.length) {
    observation.findings.forEach((finding) => {
      observationEntries.push(finding);
    });
  }

  caseForm.visibleSymptoms.forEach((symptom) => {
    observationEntries.push(symptom);
  });

  return observationEntries;
}

function buildBehavioralObservations(caseForm) {
  return caseForm.behavioralSigns;
}

function buildHistoryObject(caseForm) {
  return {
    symptom_duration: caseForm.symptomDuration || null,
    mortality_trend: caseForm.mortalityTrend || null,
    recent_events: caseForm.recentHistory,
    notes: caseForm.historyNotes || null,
    additional_observations: caseForm.additionalObservations || null,
  };
}

function buildAgentQuestions(followUpAnswers) {
  return Object.entries(followUpAnswers).map(([questionId, answer]) => ({
    question_id: questionId,
    question: "",
    reason: "",
    answer: [answer.value, answer.choice, answer.notes].filter(Boolean).join(". "),
  }));
}

export function buildSharedCaseRecord({
  caseId,
  caseForm,
  followUpAnswers = {},
  imageFileName = null,
  observation = null,
  retrievedEvidence = [],
  differential = [],
  recommendedActions = [],
  escalation = [],
}) {
  return {
    case_id: caseId,
    fish: {
      species: caseForm.species || "Nile tilapia",
      life_stage: caseForm.lifeStage || "Unknown",
    },
    images: buildImageEntries(caseId, imageFileName),
    observations: {
      visual: buildVisualObservations(observation, caseForm),
      behavioral: buildBehavioralObservations(caseForm),
    },
    water_quality: {
      temperature_c: normalizeNullableNumber(caseForm.waterQuality.temperatureC),
      ph: normalizeNullableNumber(caseForm.waterQuality.ph),
      dissolved_oxygen_mg_l: normalizeNullableNumber(
        caseForm.waterQuality.dissolvedOxygenMgL,
      ),
      ammonia_mg_l: normalizeNullableNumber(caseForm.waterQuality.ammoniaMgL),
      nitrite_mg_l: normalizeNullableNumber(caseForm.waterQuality.nitriteMgL),
      nitrate_mg_l: normalizeNullableNumber(caseForm.waterQuality.nitrateMgL),
    },
    history: buildHistoryObject(caseForm),
    agent_questions: buildAgentQuestions(followUpAnswers),
    retrieved_evidence: retrievedEvidence,
    differential,
    recommended_actions: recommendedActions,
    escalation,
  };
}
