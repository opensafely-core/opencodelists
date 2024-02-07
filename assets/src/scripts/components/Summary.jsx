import React from "react";

function Summary({ counts }) {
  return (
    <>
      <p>
        Found <span id="summary-total">{counts.total}</span> matching concepts
        (including descendants).
      </p>
      {counts["+"] > 0 && (
        <p>
          <span id="summary-included">{counts["+"] + counts["(+)"]}</span> have
          been <a href="?filter=included">included</a> in the codelist.
        </p>
      )}
      {counts["-"] > 0 && (
        <p>
          <span id="summary-excluded">{counts["-"] + counts["(-)"]}</span> have
          been <a href="?filter=excluded">excluded</a> from the codelist.
        </p>
      )}
      {counts["?"] > 0 && (
        <p>
          <span id="summary-unresolved">{counts["?"]}</span> are{" "}
          <a href="?filter=unresolved">unresolved</a>.
        </p>
      )}
      {counts["!"] > 0 && (
        <p>
          <span id="summary-in-conflict">{counts["!"]}</span> are{" "}
          <a href="?filter=in-conflict">in conflict</a>.
        </p>
      )}
    </>
  );
}

export default Summary;
