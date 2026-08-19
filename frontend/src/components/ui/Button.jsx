import React from "react";

export default function Button({
  children,
  className = "",
  fullWidth = false,
  iconLeft = null,
  iconRight = null,
  loading = false,
  size = "md",
  type = "button",
  variant = "primary",
  ...props
}) {
  return (
    <button
      type={type}
      className={[
        "button",
        `button--${variant}`,
        `button--${size}`,
        fullWidth ? "button--full-width" : "",
        loading ? "is-loading" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      disabled={loading || props.disabled}
      {...props}
    >
      {iconLeft ? <span className="button__icon">{iconLeft}</span> : null}
      <span>{children}</span>
      {iconRight ? <span className="button__icon">{iconRight}</span> : null}
    </button>
  );
}
