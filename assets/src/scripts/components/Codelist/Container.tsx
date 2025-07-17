import React, { useState, useCallback, useContext } from "react";
import Hierarchy from "../../_hierarchy";
import { PageData, Path } from "../../types";
import { CodelistContext } from "../Layout/CodelistTab";
import Section from "./Section";

export default function Container({
  hierarchy,
  treeTables,
  updateStatus,
}: {
  hierarchy: Hierarchy;
  treeTables: PageData["treeTables"];
  updateStatus: Function;
}) {
  const { visiblePaths: initialVisiblePaths } = useContext(CodelistContext);
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
          hierarchy={hierarchy}
          toggleVisibility={handleToggleVisibility}
          updateStatus={updateStatus}
          visiblePaths={visiblePaths}
        />
      ))}
    </>
  );
}
