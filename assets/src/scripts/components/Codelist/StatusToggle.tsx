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
  let buttonStyle = "outline-secondary";
  if (status === symbol) {
    buttonStyle = "primary";
  }
  if (status === `(${symbol})`) {
    buttonStyle = "secondary";
  }
  return (
    <button
      className={`py-0 text-monospace btn btn-sm btn-${buttonStyle}`}
      data-symbol={symbol}
      onClick={updateStatus?.bind(null, code, symbol)}
      type="button"
    >
      {symbol === "+" ? "+" : <>&minus;</>}
    </button>
  );
}
