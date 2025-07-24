import React from "react";
import { Button } from "react-bootstrap";
import type { Code, Status } from "../../types";

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
    <Button
      className="py-0 text-monospace"
      data-symbol={symbol}
      onClick={updateStatus?.bind(null, code, symbol)}
      size="sm"
      variant={
        status === symbol
          ? "primary"
          : status === `(${symbol})`
            ? "secondary"
            : "outline-secondary"
      }
    >
      {symbol === "+" ? "+" : <>&minus;</>}
    </Button>
  );
}
