import React from "react";
import Badge from "../ui/Badge";

export default function DiagnosisCard({ item }) {
  return (
    <article className="diagnosis-card">
      <div className="diagnosis-card__header">
        <div>
          <p className="diagnosis-card__rank">Rank {item.rank}</p>
          <h3>{item.diagnosis}</h3>
        </div>

        <div className="diagnosis-card__badges">
          <Badge tone="success">{item.evidenceStrength} evidence</Badge>
          <Badge tone="warning">{item.uncertainty} uncertainty</Badge>
          <Badge>{item.confirmationStatus}</Badge>
        </div>
      </div>

      <div className="diagnosis-card__body">
        <div>
          <h4>Supporting evidence</h4>
          <ul>
            {item.supportingEvidence.map((entry) => (
              <li key={entry}>{entry}</li>
            ))}
          </ul>
        </div>

        <div>
          <h4>Conflicting or missing evidence</h4>
          <ul>
            {item.conflictingEvidence.map((entry) => (
              <li key={entry}>{entry}</li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}
