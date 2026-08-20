import React from "react";

import Button from "../ui/Button";

export default function EvidenceList({ items, onSelect }) {
  return (
    <div className="evidence-list">
      {items.map((item) => (
        <div key={item.id} className="evidence-list__item">
          <div>
            <p className="evidence-list__id">{item.id}</p>
            <h4>{item.title}</h4>
            <p>
              {item.organization}
              <span className="evidence-list__separator">•</span>
              Section: {item.section}
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onSelect(item.id)}>
            View source
          </Button>
        </div>
      ))}
    </div>
  );
}
