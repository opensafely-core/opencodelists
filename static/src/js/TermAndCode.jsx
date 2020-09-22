import React from "react";

import Code from "./Code";
import DescendantToggle from "./DescendantToggle";
import Pipes from "./Pipes";
import Term from "./Term";

export default function TermAndCode(props) {
  return (
    <div style={{ paddingLeft: "10px", whiteSpace: "nowrap" }}>
      <Pipes pipes={props.pipes} />

      {props.hasDescendants ? (
        <DescendantToggle
          code={props.code}
          isExpanded={props.isExpanded}
          toggleVisibility={props.toggleVisibility}
        />
      ) : null}

      <Term status={props.status} term={props.term} />

      <Code code={props.code} />
    </div>
  );
}
