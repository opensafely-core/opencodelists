import React from "react";
import { Button } from "react-bootstrap";

interface MoreInfoButtonProps {
  code: string;
  showMoreInfoModal: Function;
}

function MoreInfoButton({ code, showMoreInfoModal }: MoreInfoButtonProps) {
  return (
    <div className="btn-group btn-group-sm mx-2" role="group">
      <Button
        className="py-0 border-0"
        onClick={showMoreInfoModal.bind(null, code)}
        variant="outline-secondary"
      >
        ...
      </Button>
    </div>
  );
}

export default MoreInfoButton;
