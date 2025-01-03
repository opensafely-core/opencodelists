import React from "react";
import { Button } from "react-bootstrap";

interface StatusToggleProps {
  code: string;
  status: string;
  symbol: string;
  updateStatus: Function;
}

function StatusToggle({
  code,
  status,
  symbol,
  updateStatus,
}: StatusToggleProps) {
  return (
    <Button
      className="py-0"
      data-symbol={symbol}
      onClick={updateStatus && updateStatus.bind(null, code, symbol)}
      variant={
        status === symbol
          ? "primary"
          : status === `(${symbol})`
            ? "secondary"
            : "outline-secondary"
      }
    >
      {symbol}
    </Button>
  );
}

export default StatusToggle;
