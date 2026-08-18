import React, { useEffect } from "react";
import { X } from "lucide-react";
import Button from "../ui/Button";

export default function SourceModal({ onClose, source }) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  if (!source) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="source-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal__header">
          <div>
            <p className="modal__eyebrow">{source.id}</p>
            <h3 id="source-modal-title">{source.title}</h3>
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={onClose}
            aria-label="Close source details"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <dl className="modal__details">
          <div>
            <dt>Organization</dt>
            <dd>{source.organization}</dd>
          </div>
          <div>
            <dt>Section</dt>
            <dd>{source.section}</dd>
          </div>
          <div>
            <dt>Retrieved passage</dt>
            <dd>{source.passage}</dd>
          </div>
          <div>
            <dt>How this evidence was used</dt>
            <dd>{source.usage}</dd>
          </div>
        </dl>

        <div className="modal__footer">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
