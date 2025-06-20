import React from "react";
import { Button } from "react-bootstrap";
import { Code, Status } from "../types";

interface StatusToggleProps {
  code: Code;
  disabled?: boolean;
  status: Status;
  symbol: "+" | "-";
  updateStatus: Function;
}

export default function StatusToggle({
  code,
  disabled,
  status,
  symbol,
  updateStatus,
}: StatusToggleProps) {
  return (
    <Button
      className="py-0 text-monospace"
      data-symbol={symbol}
      disabled={disabled}
      onClick={updateStatus && updateStatus.bind(null, code, symbol)}
      size="sm"
      variant={
        status === symbol
          ? "primary"
          : status === `(${symbol})`
            ? "secondary"
            : "outline-secondary"
      }
    >
      {symbol === "+" ? <>+</> : <>&minus;</>}
    </Button>
  );
}
