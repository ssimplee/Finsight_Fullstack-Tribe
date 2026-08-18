import React from "react";
import {
  behavioralSignOptions,
  lifeStageOptions,
  recentHistoryOptions,
  visibleSymptomOptions,
} from "../../data/mockCase";

const waterQualityFields = [
  {
    id: "temperatureC",
    label: "Temperature (°C)",
  },
  {
    id: "ph",
    label: "pH",
  },
  {
    id: "dissolvedOxygenMgL",
    label: "Dissolved Oxygen (mg/L)",
  },
  {
    id: "ammoniaMgL",
    label: "Ammonia (mg/L)",
  },
  {
    id: "nitriteMgL",
    label: "Nitrite (mg/L)",
  },
  {
    id: "nitrateMgL",
    label: "Nitrate (mg/L)",
  },
];

function CheckboxGroup({
  error,
  legend,
  name,
  onToggle,
  options,
  selectedValues,
}) {
  return (
    <fieldset className="field-group">
      <legend className="field-group__legend">{legend}</legend>
      <div className="checkbox-grid">
        {options.map((option) => (
          <label key={option} className="checkbox-card">
            <input
              type="checkbox"
              name={name}
              value={option}
              checked={selectedValues.includes(option)}
              onChange={() => onToggle(option)}
            />
            <span>{option}</span>
          </label>
        ))}
      </div>
      {error ? <p className="field-error">{error}</p> : null}
    </fieldset>
  );
}

export default function CaseForm({
  caseForm,
  errors,
  onFieldChange,
  onToggleSelection,
  onWaterQualityChange,
  phWarning,
}) {
  return (
    <div className="case-form">
      <section className="form-section">
        <h3>Basic case profile</h3>
        <div className="form-grid form-grid--two-up">
          <label className="field">
            <span>Species</span>
            <input
              type="text"
              name="species"
              value={caseForm.species}
              onChange={(event) =>
                onFieldChange("species", event.target.value)
              }
            />
            {errors.species ? <p className="field-error">{errors.species}</p> : null}
          </label>

          <label className="field">
            <span>Life Stage</span>
            <select
              name="lifeStage"
              value={caseForm.lifeStage}
              onChange={(event) =>
                onFieldChange("lifeStage", event.target.value)
              }
            >
              {lifeStageOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.lifeStage ? (
              <p className="field-error">{errors.lifeStage}</p>
            ) : null}
          </label>

          <label className="field">
            <span>Symptom Duration</span>
            <input
              type="text"
              name="symptomDuration"
              placeholder="For example: 3 days"
              value={caseForm.symptomDuration}
              onChange={(event) =>
                onFieldChange("symptomDuration", event.target.value)
              }
            />
            {errors.symptomDuration ? (
              <p className="field-error">{errors.symptomDuration}</p>
            ) : null}
          </label>

          <label className="field">
            <span>Mortality Trend</span>
            <input
              type="text"
              name="mortalityTrend"
              placeholder="Describe the recent trend"
              value={caseForm.mortalityTrend}
              onChange={(event) =>
                onFieldChange("mortalityTrend", event.target.value)
              }
            />
            {errors.mortalityTrend ? (
              <p className="field-error">{errors.mortalityTrend}</p>
            ) : null}
          </label>
        </div>
      </section>

      <section className="form-section">
        <CheckboxGroup
          legend="Visible Symptoms"
          name="visibleSymptoms"
          options={visibleSymptomOptions}
          selectedValues={caseForm.visibleSymptoms}
          onToggle={(value) => onToggleSelection("visibleSymptoms", value)}
        />

        <CheckboxGroup
          legend="Behavioral Signs"
          name="behavioralSigns"
          options={behavioralSignOptions}
          selectedValues={caseForm.behavioralSigns}
          onToggle={(value) => onToggleSelection("behavioralSigns", value)}
        />

        <label className="field">
          <span>Additional observations</span>
          <textarea
            name="additionalObservations"
            rows="4"
            placeholder="Describe lesion distribution, tank behavior, or anything else worth preserving."
            value={caseForm.additionalObservations}
            onChange={(event) =>
              onFieldChange("additionalObservations", event.target.value)
            }
          />
        </label>

        {errors.clinicalSigns ? (
          <p className="field-error">{errors.clinicalSigns}</p>
        ) : null}
      </section>

      <section className="form-section">
        <div className="form-section__heading">
          <div>
            <h3>Water-quality information</h3>
            <p className="field-hint">
              Unknown values may be left blank. FinSight may ask about important
              missing measurements.
            </p>
          </div>
        </div>

        <div className="form-grid form-grid--two-up">
          {waterQualityFields.map((field) => (
            <label key={field.id} className="field">
              <span>{field.label}</span>
              <input
                type="number"
                step="any"
                min="0"
                name={field.id}
                value={caseForm.waterQuality[field.id]}
                onChange={(event) =>
                  onWaterQualityChange(field.id, event.target.value)
                }
              />
              {errors[field.id] ? (
                <p className="field-error">{errors[field.id]}</p>
              ) : null}
              {field.id === "ph" && phWarning ? (
                <p className="field-warning">{phWarning}</p>
              ) : null}
            </label>
          ))}
        </div>
      </section>

      <section className="form-section">
        <CheckboxGroup
          legend="Recent management history"
          name="recentHistory"
          options={recentHistoryOptions}
          selectedValues={caseForm.recentHistory}
          onToggle={(value) => onToggleSelection("recentHistory", value)}
        />

        <label className="field">
          <span>Additional management history</span>
          <textarea
            name="historyNotes"
            rows="4"
            placeholder="Add context about feeding, treatments, movement, or system failures."
            value={caseForm.historyNotes}
            onChange={(event) => onFieldChange("historyNotes", event.target.value)}
          />
        </label>
      </section>
    </div>
  );
}
