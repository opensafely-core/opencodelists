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
  let buttonClasses = ["btn"];
  if (status === symbol) {
    buttonClasses.push("btn-primary");
  } else if (status === `(${symbol})`) {
    buttonClasses.push("btn-secondary");
  } else {
    buttonClasses.push("btn-outline-secondary");
  }
  buttonClasses.push("py-0");
  return (
    <Button
      className="py-0"
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
      {symbol}
    </Button>
  );
}

export default StatusToggle;
