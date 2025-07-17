import React, { useState, useCallback } from "react";
import { useCodelistContext } from "../../context/codelist-context";
import { Path } from "../../types";
import Section from "./Section";

export default function Container({
  updateStatus,
}: { updateStatus: Function }) {
  const {
    hierarchy,
    treeTables,
    visiblePaths: initialVisiblePaths,
  } = useCodelistContext();
  const [visiblePaths, setVisiblePaths] = useState(initialVisiblePaths);

  const handleToggleVisibility = useCallback(
    (path: Path) => {
      setVisiblePaths((prevVisiblePaths) => {
        const newVisiblePaths = new Set(prevVisiblePaths);
        hierarchy.toggleVisibility(newVisiblePaths, path);
        return newVisiblePaths;
      });
    },
    [hierarchy],
  );

  return (
    <>
      {treeTables.map(([heading, ancestorCodes]) => (
        <Section
          key={heading}
          ancestorCodes={ancestorCodes}
          heading={heading}
          toggleVisibility={handleToggleVisibility}
          updateStatus={updateStatus}
          visiblePaths={visiblePaths}
        />
      ))}
    </>
  );
}
