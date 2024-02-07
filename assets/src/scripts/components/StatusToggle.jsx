import React from "react";

function StatusToggle({ code, status, symbol, updateStatus }) {
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
