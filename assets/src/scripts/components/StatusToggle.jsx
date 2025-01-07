import PropTypes from "prop-types";
import React from "react";
import { Button } from "react-bootstrap";

function StatusToggle({ code, status, symbol, updateStatus }) {
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

StatusToggle.propTypes = {
  code: PropTypes.string,
  status: PropTypes.string,
  symbol: PropTypes.string,
  updateStatus: PropTypes.func,
};
