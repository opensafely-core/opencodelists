import React from "react";

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
    <button
      className={buttonClasses.join(" ")}
      data-symbol={symbol}
      onClick={updateStatus && updateStatus.bind(null, code, symbol)}
      type="button"
    >
      {symbol}
    </button>
  );
}

export default StatusToggle;
