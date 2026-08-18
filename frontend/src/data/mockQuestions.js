export const mockQuestions = [
  {
    id: "dissolved-oxygen",
    prompt: "What is the current dissolved oxygen level?",
    rationale:
      "Low dissolved oxygen can produce respiratory signs similar to infectious disease and may change the differential assessment.",
    inputType: "number",
    unitLabel: "mg/L",
    placeholder: "Enter dissolved oxygen",
  },
  {
    id: "mortality-trend",
    prompt: "Has mortality increased during the last 3-7 days?",
    rationale:
      "A recent mortality trend helps distinguish an isolated injury from an active disease or environmental event.",
    inputType: "choice",
    choices: ["Yes", "No", "Unknown"],
  },
];
