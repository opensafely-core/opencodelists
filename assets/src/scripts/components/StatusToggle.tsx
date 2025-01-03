import React from "react";
import { Button } from "react-bootstrap";
import { StatusState } from "../types";

interface StatusToggleProps {
  code: string;
  icon: "+" | "&minus;";
  status: StatusState;
  symbol: "+" | "-";
  updateStatus: Function;
}

function StatusToggle({
  code,
  icon,
  status,
  symbol,
  updateStatus,
}: StatusToggleProps) {
  return (
    <Button
      className="py-0 text-monospace"
      data-symbol={symbol}
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
      {icon}
    </Button>
  );
}

export default StatusToggle;
