import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import ChatMessage from "./ChatMessage";

export default function FollowUpQuestion({ answer, onChange, question }) {
  const [isReasonVisible, setReasonVisible] = useState(false);
  const currentAnswer = answer ?? { value: "", choice: "", notes: "" };

  const answerSummary =
    question.inputType === "number"
      ? currentAnswer.value
        ? `${currentAnswer.value} ${question.unitLabel}`
        : "No value entered yet."
      : currentAnswer.choice || "Unknown";

  return (
    <div className="follow-up-question">
      <ChatMessage role="assistant" message={question.prompt} />

      <div className="follow-up-question__toggle">
        <button
          type="button"
          className="link-button"
          onClick={() => setReasonVisible((currentValue) => !currentValue)}
          aria-expanded={isReasonVisible}
        >
          Why this question?
          {isReasonVisible ? (
            <ChevronUp size={16} aria-hidden="true" />
          ) : (
            <ChevronDown size={16} aria-hidden="true" />
          )}
        </button>
      </div>

      {isReasonVisible ? (
        <p className="follow-up-question__rationale">{question.rationale}</p>
      ) : null}

      <div className="follow-up-question__response">
        <ChatMessage role="user" message={answerSummary} detail={currentAnswer.notes} />

        <div className="follow-up-question__inputs">
          {question.inputType === "number" ? (
            <label className="field">
              <span>{question.unitLabel}</span>
              <input
                type="number"
                step="any"
                min="0"
                value={currentAnswer.value}
                placeholder={question.placeholder}
                onChange={(event) => onChange({ value: event.target.value })}
              />
            </label>
          ) : (
            <fieldset className="field-group">
              <legend className="field-group__legend">Answer</legend>
              <div className="choice-row">
                {(question.choices ?? []).map((choice) => (
                  <label key={choice} className="choice-pill">
                    <input
                      type="radio"
                      name={question.id}
                      value={choice}
                      checked={currentAnswer.choice === choice}
                      onChange={(event) =>
                        onChange({ choice: event.target.value })
                      }
                    />
                    <span>{choice}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          <label className="field">
            <span>Additional note</span>
            <textarea
              rows="3"
              value={currentAnswer.notes}
              placeholder="Add context, uncertainty, or sampling notes."
              onChange={(event) => onChange({ notes: event.target.value })}
            />
          </label>
        </div>
      </div>
    </div>
  );
}
