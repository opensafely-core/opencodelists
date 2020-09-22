import React from "react";

const statusToColour = {
  "!": "red",
  "-": "gray",
  "(-)": "gray",
};

const Term = (props) => {
  const style = { color: statusToColour[props.status] };

  return <span style={style}>{props.term}</span>;
};

export default Term;
