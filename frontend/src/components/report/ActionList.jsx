import React from "react";

export default function ActionList({ items }) {
  return (
    <ul className="report-list">
      {items.map((item) => (
        <li key={item.id}>{item.text}</li>
      ))}
    </ul>
  );
}
