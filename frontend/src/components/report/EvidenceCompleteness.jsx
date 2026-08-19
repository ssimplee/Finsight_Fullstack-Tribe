import React from "react";

export default function EvidenceCompleteness({ items }) {
  return (
    <div className="evidence-completeness">
      {items.map((item) => (
        <div key={item.id} className="evidence-completeness__item">
          <span>{item.label}</span>
          <strong
            className={
              item.status === "Available"
                ? "status-text status-text--success"
                : "status-text status-text--warning"
            }
          >
            {item.status}
          </strong>
        </div>
      ))}
    </div>
  );
}
