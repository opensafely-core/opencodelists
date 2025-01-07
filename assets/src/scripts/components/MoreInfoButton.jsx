import PropTypes from "prop-types";
import React from "react";
import { Button } from "react-bootstrap";

function MoreInfoButton({ code, showMoreInfoModal }) {
  return (
    <Button
      className="py-0 border-0"
      onClick={showMoreInfoModal.bind(null, code)}
      variant="outline-secondary"
    >
      &hellip;
    </Button>
  );
}

export default MoreInfoButton;

MoreInfoButton.propTypes = {
  code: PropTypes.string,
  showMoreInfoModal: PropTypes.func,
};
