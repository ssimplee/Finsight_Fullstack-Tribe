import React from "react";
import { CheckCircle2 } from "lucide-react";

const steps = [
  "Case Intake",
  "Image Observation",
  "Follow-up Questions",
  "Evidence Retrieval",
  "Differential Analysis",
  "Final Report",
];

export default function ProgressPanel({
  completedSteps = [],
  currentStep = 1,
}) {
  return (
    <aside className="progress-panel" aria-label="Consultation progress">
      <div className="progress-panel__summary">
        <p className="progress-panel__eyebrow">Progress</p>
        <h2 className="progress-panel__title">
          Fish-health triage workflow
        </h2>
      </div>

      <ol className="progress-panel__list">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = completedSteps.includes(stepNumber);
          const isCurrent = currentStep === stepNumber;

          return (
            <li
              key={step}
              className={[
                "progress-panel__item",
                isCompleted ? "is-completed" : "",
                isCurrent ? "is-current" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <span className="progress-panel__icon">
                {isCompleted ? (
                  <CheckCircle2 size={16} aria-hidden="true" />
                ) : (
                  <span>{stepNumber}</span>
                )}
              </span>
              <span className="progress-panel__label">{step}</span>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}
