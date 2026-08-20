import React from "react";

export default function SectionCard({
  actions = null,
  children,
  className = "",
  eyebrow = null,
  title,
  tone = "default",
}) {
  return (
    <section className={`section-card section-card--${tone} ${className}`.trim()}>
      {(eyebrow || title || actions) && (
        <div className="section-card__header">
          <div>
            {eyebrow ? <p className="section-card__eyebrow">{eyebrow}</p> : null}
            {title ? <h2 className="section-card__title">{title}</h2> : null}
          </div>
          {actions ? <div className="section-card__actions">{actions}</div> : null}
        </div>
      )}
      {children}
    </section>
  );
}
