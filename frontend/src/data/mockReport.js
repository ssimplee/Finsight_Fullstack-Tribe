const SOURCE_SUMMARIES = [
  {
    id: "SRC-001",
    title: "FAO fish-health guidance",
    organization: "FAO",
    section: "Bacterial disease and farm management",
    passage:
      "Farm-level lesion review should be paired with husbandry context and water-quality checks before treatment decisions are made.",
    usage:
      "Used to support the need for a differential assessment rather than an image-only conclusion.",
  },
  {
    id: "SRC-002",
    title: "WOAH Aquatic Animal Health resources",
    organization: "WOAH",
    section: "Diagnostic principles and confirmation",
    passage:
      "Visible lesions may justify triage, but laboratory confirmation is still needed before a disease is treated as confirmed.",
    usage:
      "Used to label the outcome as unconfirmed and keep the report grounded in decision support.",
  },
  {
    id: "SRC-003",
    title: "Peer-reviewed review of tilapia bacterial diseases",
    organization: "Peer-reviewed review",
    section: "Clinical signs and differential diagnosis",
    passage:
      "Ulceration, appetite loss, and mortality can fit multiple bacterial or environmental conditions and should be compared side by side.",
    usage:
      "Used to justify the ranked list of possible causes and the uncertainty wording.",
  },
];

function normalizeNumber(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const parsedValue = Number(value);

  return Number.isNaN(parsedValue) ? null : parsedValue;
}

function buildUserReportedItems(caseForm, followUpAnswers) {
  const items = [];

  if (caseForm.behavioralSigns.includes("Reduced appetite")) {
    items.push({
      id: "user-reduced-appetite",
      label: "USER-REPORTED",
      text: "Reduced appetite",
    });
  }

  if (caseForm.behavioralSigns.includes("Lethargy")) {
    items.push({
      id: "user-lethargy",
      label: "USER-REPORTED",
      text: "Lethargy",
    });
  }

  const mortalityAnswer = followUpAnswers["mortality-trend"]?.choice;
  if (
    caseForm.mortalityTrend.trim() ||
    mortalityAnswer === "Yes"
  ) {
    items.push({
      id: "user-mortality",
      label: "USER-REPORTED",
      text: "Increased mortality",
    });
  }

  if (items.length === 0) {
    items.push({
      id: "user-observation-generic",
      label: "USER-REPORTED",
      text: "Clinical history provided by the user",
    });
  }

  return items;
}

function buildUnknownItems(caseForm, dissolvedOxygenMgL, ammoniaMgL, nitriteMgL) {
  const unknownItems = [];

  if (!caseForm.visibleSymptoms.includes("Gill abnormality")) {
    unknownItems.push({
      id: "unknown-gill-condition",
      label: "AI INFERENCE",
      text: "Gill condition",
    });
  }

  if (ammoniaMgL === null) {
    unknownItems.push({
      id: "unknown-ammonia",
      label: "AI INFERENCE",
      text: "Ammonia level",
    });
  }

  if (nitriteMgL === null) {
    unknownItems.push({
      id: "unknown-nitrite",
      label: "AI INFERENCE",
      text: "Nitrite level",
    });
  }

  if (dissolvedOxygenMgL === null) {
    unknownItems.push({
      id: "unknown-dissolved-oxygen",
      label: "AI INFERENCE",
      text: "Dissolved oxygen level",
    });
  }

  return unknownItems;
}

function buildMissingInformation(caseForm, waterQuality) {
  const missingItems = [];

  if (waterQuality.dissolvedOxygenMgL === null) {
    missingItems.push({
      id: "missing-do",
      text: "Dissolved oxygen concentration",
    });
  }

  if (waterQuality.ammoniaMgL === null) {
    missingItems.push({
      id: "missing-ammonia",
      text: "Ammonia concentration",
    });
  }

  if (waterQuality.nitriteMgL === null) {
    missingItems.push({
      id: "missing-nitrite",
      text: "Nitrite concentration",
    });
  }

  if (!caseForm.visibleSymptoms.includes("Gill abnormality")) {
    missingItems.push({
      id: "missing-gill-image",
      text: "Close-up gill image",
    });
  }

  missingItems.push({
    id: "missing-lab-culture",
    text: "Laboratory bacterial culture",
  });

  return missingItems;
}

function buildEvidenceCompleteness(record, waterQuality) {
  return [
    {
      id: "evidence-image",
      label: "Image",
      status: record.observation ? "Available" : "Missing",
    },
    {
      id: "evidence-behavior",
      label: "Behavior",
      status:
        record.caseData.behavioralSigns.length > 0 ? "Available" : "Missing",
    },
    {
      id: "evidence-temperature",
      label: "Temperature",
      status: waterQuality.temperatureC === null ? "Missing" : "Available",
    },
    {
      id: "evidence-do",
      label: "Dissolved oxygen",
      status:
        waterQuality.dissolvedOxygenMgL === null ? "Missing" : "Available",
    },
    {
      id: "evidence-ammonia",
      label: "Ammonia",
      status: waterQuality.ammoniaMgL === null ? "Missing" : "Available",
    },
    {
      id: "evidence-nitrite",
      label: "Nitrite",
      status: waterQuality.nitriteMgL === null ? "Missing" : "Available",
    },
    {
      id: "evidence-mortality",
      label: "Mortality trend",
      status:
        record.caseData.mortalityTrend.trim() ||
        record.followUpAnswers["mortality-trend"]?.choice !== "Unknown"
          ? "Available"
          : "Missing",
    },
  ];
}

function buildDifferential() {
  return [
    {
      id: "dx-aeromonas",
      rank: 1,
      diagnosis: "Motile Aeromonas Septicemia",
      evidenceStrength: "Strong",
      uncertainty: "Moderate",
      confirmationStatus: "Unconfirmed",
      supportingEvidence: [
        "Flank ulceration and scale loss are compatible with Aeromonas-associated disease.",
        "Increased mortality supports an active health event.",
        "Handling stress may increase susceptibility.",
      ],
      conflictingEvidence: [
        "No laboratory culture result is available.",
        "Water-quality data are incomplete.",
        "The image cannot establish the pathogen.",
      ],
    },
    {
      id: "dx-streptococcosis",
      rank: 2,
      diagnosis: "Streptococcosis",
      evidenceStrength: "Moderate",
      uncertainty: "Moderate",
      confirmationStatus: "Unconfirmed",
      supportingEvidence: [
        "Reduced appetite and lethargy are compatible with systemic infection.",
        "Mortality increase may support an infectious cause.",
      ],
      conflictingEvidence: [
        "No clear neurological behavior was reported.",
        "External ulceration is less specific for this condition.",
        "Bacterial confirmation is unavailable.",
      ],
    },
    {
      id: "dx-water-quality",
      rank: 3,
      diagnosis: "Water-quality stress",
      evidenceStrength: "Moderate",
      uncertainty: "High",
      confirmationStatus: "Unconfirmed",
      supportingEvidence: [
        "Missing dissolved oxygen and ammonia measurements leave an environmental cause unresolved.",
        "Water-quality stress can worsen infectious disease signs.",
      ],
      conflictingEvidence: [
        "A localized ulcer is not fully explained by water-quality stress alone.",
        "Current water measurements are insufficient.",
      ],
    },
  ];
}

export function buildMockReport(record) {
  const dissolvedOxygenAnswer = record.followUpAnswers["dissolved-oxygen"]?.value;
  const caseWaterQuality = record.caseData.waterQuality ?? {};
  const waterQuality = {
    temperatureC: normalizeNumber(caseWaterQuality.temperatureC),
    ph: normalizeNumber(caseWaterQuality.ph),
    dissolvedOxygenMgL:
      normalizeNumber(caseWaterQuality.dissolvedOxygenMgL) ??
      normalizeNumber(dissolvedOxygenAnswer),
    ammoniaMgL: normalizeNumber(caseWaterQuality.ammoniaMgL),
    nitriteMgL: normalizeNumber(caseWaterQuality.nitriteMgL),
    nitrateMgL: normalizeNumber(caseWaterQuality.nitrateMgL),
  };

  return {
    caseId: record.caseId,
    fish: {
      species: record.caseData.species || "Nile tilapia",
      lifeStage: record.caseData.lifeStage || "Unknown",
    },
    status: {
      assessment: "Triage complete",
      confirmation: "Unconfirmed",
      uncertainty: "Moderate",
    },
    generatedAt: new Date().toISOString(),
    observations: {
      visual: [
        {
          id: "obs-ulcer",
          label: "OBSERVED",
          text: "Localized flank ulceration",
        },
        {
          id: "obs-scale-loss",
          label: "OBSERVED",
          text: "Partial scale loss",
        },
        {
          id: "obs-discoloration",
          label: "OBSERVED",
          text: "Mild discoloration",
        },
      ],
      userReported: buildUserReportedItems(
        record.caseData,
        record.followUpAnswers,
      ),
      unknown: buildUnknownItems(
        record.caseData,
        waterQuality.dissolvedOxygenMgL,
        waterQuality.ammoniaMgL,
        waterQuality.nitriteMgL,
      ),
    },
    waterQuality,
    differential: buildDifferential(),
    evidenceCompleteness: buildEvidenceCompleteness(record, waterQuality),
    missingInformation: buildMissingInformation(record.caseData, waterQuality),
    recommendedConfirmation: [
      {
        id: "confirm-water-quality",
        text: "Recheck dissolved oxygen, ammonia and nitrite",
      },
      {
        id: "confirm-gills",
        text: "Inspect the gills and additional affected fish",
      },
      {
        id: "confirm-mortality",
        text: "Review mortality over the next 24 hours",
      },
      {
        id: "confirm-lab",
        text: "Seek bacterial culture or PCR testing where available",
      },
      {
        id: "confirm-professional",
        text: "Consult an aquatic animal-health professional if mortality continues",
      },
    ],
    recommendedActions: [
      {
        id: "action-aeration",
        text: "Verify aeration and water-quality equipment",
      },
      {
        id: "action-stress",
        text: "Reduce avoidable handling stress",
      },
      {
        id: "action-separate",
        text: "Separate severely affected fish when appropriate",
      },
      {
        id: "action-record",
        text: "Record new symptoms and mortality",
      },
      {
        id: "action-antimicrobial",
        text: "Avoid unsupported antimicrobial treatment without professional guidance",
      },
    ],
    escalation: [
      {
        id: "escalation-mortality",
        text: "Rapidly increasing mortality",
      },
      {
        id: "escalation-respiratory",
        text: "Severe respiratory distress",
      },
      {
        id: "escalation-multiple-systems",
        text: "Multiple ponds or tanks affected",
      },
      {
        id: "escalation-neurological",
        text: "Neurological signs such as circling or loss of balance",
      },
      {
        id: "escalation-water-quality",
        text: "Major ammonia, nitrite or dissolved-oxygen abnormality",
      },
    ],
    sources: SOURCE_SUMMARIES,
  };
}

export const mockReport = {
  caseId: "CASE-001",
  fish: {
    species: "Nile tilapia",
    lifeStage: "Adult",
  },
  observations: {
    visual: [],
    behavioral: [],
  },
  waterQuality: {
    temperatureC: null,
    ph: null,
    dissolvedOxygenMgL: null,
    ammoniaMgL: null,
    nitriteMgL: null,
    nitrateMgL: null,
  },
  differential: [],
  missingInformation: [],
  recommendedConfirmation: [],
  recommendedActions: [],
  escalation: [],
  sources: [],
};
