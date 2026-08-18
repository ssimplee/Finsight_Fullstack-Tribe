export const lifeStageOptions = [
  "Fingerling",
  "Juvenile",
  "Adult",
  "Unknown",
];

export const visibleSymptomOptions = [
  "Skin ulcer",
  "Scale loss",
  "Discoloration",
  "Eye abnormality",
  "Fin erosion",
  "Gill abnormality",
  "Swelling",
  "No obvious external lesion",
];

export const behavioralSignOptions = [
  "Lethargy",
  "Reduced appetite",
  "Rapid breathing",
  "Surface gasping",
  "Abnormal swimming",
  "Circling",
  "Loss of balance",
  "Isolation",
];

export const recentHistoryOptions = [
  "Recent fish introduction",
  "Stocking-density change",
  "Recent transport or handling",
  "Feed change",
  "Recent treatment",
  "Water change",
  "Filtration or oxygenation failure",
  "Recent temperature change",
];

export const mockObservation = {
  id: "observation-001",
  label: "Observed, not confirmed",
  findings: [
    "Localized flank ulceration",
    "Partial scale loss around the lesion",
    "Mild body discoloration",
  ],
  limitations: [
    "Gill condition cannot be assessed from this angle",
    "Image findings alone cannot confirm a specific disease",
  ],
};

export function createInitialFollowUpAnswers() {
  return {
    "dissolved-oxygen": {
      value: "",
      choice: "",
      notes: "",
    },
    "mortality-trend": {
      value: "",
      choice: "Unknown",
      notes: "",
    },
  };
}

export function createInitialConsultationState() {
  return {
    caseId: "",
    caseForm: {
      species: "Nile tilapia",
      lifeStage: "Unknown",
      symptomDuration: "",
      mortalityTrend: "",
      visibleSymptoms: [],
      behavioralSigns: [],
      additionalObservations: "",
      waterQuality: {
        temperatureC: "",
        ph: "",
        dissolvedOxygenMgL: "",
        ammoniaMgL: "",
        nitriteMgL: "",
        nitrateMgL: "",
      },
      recentHistory: [],
      historyNotes: "",
    },
    imageFile: null,
    imagePreviewUrl: "",
    imageAltText: "",
    isSampleCase: false,
    observation: null,
    followUpAnswers: createInitialFollowUpAnswers(),
    consultationStage: "intake",
    currentStep: 1,
    analysisRequested: false,
    reportReady: false,
  };
}

export const sampleCaseData = {
  caseForm: {
    species: "Nile tilapia",
    lifeStage: "Adult",
    symptomDuration: "3 days",
    mortalityTrend: "Losses increased over the last 48 hours in one production tank.",
    visibleSymptoms: ["Skin ulcer", "Scale loss", "Discoloration"],
    behavioralSigns: ["Lethargy", "Reduced appetite"],
    additionalObservations:
      "Fish show a single flank lesion with mild redness around the site.",
    waterQuality: {
      temperatureC: "28.1",
      ph: "7.5",
      dissolvedOxygenMgL: "",
      ammoniaMgL: "",
      nitriteMgL: "",
      nitrateMgL: "18",
    },
    recentHistory: ["Recent transport or handling", "Recent temperature change"],
    historyNotes:
      "Fish were handled for grading three days ago, followed by a warm afternoon spike.",
  },
  followUpAnswers: {
    "dissolved-oxygen": {
      value: "",
      choice: "",
      notes: "Meter reading was not taken during the first inspection.",
    },
    "mortality-trend": {
      value: "",
      choice: "Yes",
      notes: "Mortality has increased during the last 3 to 5 days.",
    },
  },
};
