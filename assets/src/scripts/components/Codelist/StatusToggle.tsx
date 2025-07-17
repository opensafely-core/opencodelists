import React from "react";
import { Code, Status } from "../../types";

interface StatusToggleProps {
  code: Code;
  status: Status;
  symbol: "+" | "-";
  updateStatus: Function;
}

export default function StatusToggle({
  code,
  status,
  symbol,
  updateStatus,
}: StatusToggleProps) {
  return (
    <button
      className={`py-0 text-monospace btn btn-sm ${
        status === symbol
          ? "btn-primary"
          : status === `(${symbol})`
            ? "btn-secondary"
            : "btn-outline-secondary"
      }`}
      data-symbol={symbol}
      onClick={updateStatus && updateStatus.bind(null, code, symbol)}
    >
      {symbol === "+" ? <>+</> : <>&minus;</>}
    </button>
  );
}
