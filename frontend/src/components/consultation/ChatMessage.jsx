import React from "react";
import { Bot, User } from "lucide-react";

export default function ChatMessage({ detail = null, message, role = "assistant" }) {
  const isAssistant = role === "assistant";

  return (
    <div
      className={[
        "chat-message",
        isAssistant ? "chat-message--assistant" : "chat-message--user",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="chat-message__avatar">
        {isAssistant ? (
          <Bot size={16} aria-hidden="true" />
        ) : (
          <User size={16} aria-hidden="true" />
        )}
      </span>

      <div className="chat-message__bubble">
        <p className="chat-message__role">
          {isAssistant ? "FinSight" : "Your response"}
        </p>
        <p>{message}</p>
        {detail ? <p className="chat-message__detail">{detail}</p> : null}
      </div>
    </div>
  );
}
