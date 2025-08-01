import React from "react";
import type { Code, Status, UpdateStatus } from "../../types";

interface StatusToggleProps {
  code: Code;
  status: Status;
  symbol: "+" | "-";
  updateStatus: UpdateStatus;
}

export default function StatusToggle({
  code,
  status,
  symbol,
  updateStatus,
}: StatusToggleProps) {
  let className = "outline-secondary";
  const explicitSelection = status === symbol;
  const implicitSelection = status === `(${symbol})`;
  if (explicitSelection) {
    className = "primary";
  } else if (implicitSelection) {
    className = "secondary";
  }

  return (
    <button
      className={`py-0 text-monospace btn btn-sm btn-${className}`}
      data-symbol={symbol}
      onClick={updateStatus?.bind(null, code, symbol)}
      type="button"
    >
      {symbol === "+" ? "+" : <>&minus;</>}
    </button>
  );
}
