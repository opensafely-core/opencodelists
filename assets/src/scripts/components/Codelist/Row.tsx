import React from "react";
import type Hierarchy from "../../_hierarchy";
import type {
  Code,
  CodeToUsage,
  IsExpanded,
  PageData,
  Path,
  Pipe,
  Status,
  Term,
  ToggleVisibility,
  UpdateStatus,
  UsagePillDisplayOptions,
} from "../../types";
import DescendantToggle from "./DescendantToggle";
import MoreInfoModal from "./MoreInfoModal";
import Pipes from "./Pipes";
import StatusToggle from "./StatusToggle";

interface RowProps {
  allCodes: PageData["allCodes"];
  code: Code;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  codeToUsage: CodeToUsage;
  hasDescendants: boolean;
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  isExpanded: IsExpanded;
  path: Path;
  pipes: Pipe[];
  status: Status;
  term: Term;
  toggleVisibility: ToggleVisibility;
  updateStatus: UpdateStatus;
  usagePillDisplayOptions: UsagePillDisplayOptions;
}

export default function Row({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  codeToUsage,
  hasDescendants,
  hierarchy,
  isEditable,
  isExpanded,
  path,
  pipes,
  status,
  term,
  toggleVisibility,
  updateStatus,
  usagePillDisplayOptions,
}: RowProps) {
  const statusTermColor = {
    "+": "text-body",
    "(+)": "text-body",
    "-": "text-secondary",
    "(-)": "text-secondary",
    "!": "text-danger",
    "?": "text-body",
  };

  const statusCodeColor = {
    "+": "",
    "(+)": "",
    "-": "text-secondary",
    "(-)": "text-secondary",
    "!": "text-danger",
    "?": "",
  };

  const isUsagePillOnLeft = usagePillDisplayOptions.position === "left";

  return (
    <div
      className={`builder__row${pipes.length === 0 ? " builder__row--mt" : ""}`}
      data-code={code}
      data-path={path}
    >
      {isUsagePillOnLeft ? (
        <UsagePill
          code={code}
          codeToUsage={codeToUsage}
          usagePillDisplayOptions={usagePillDisplayOptions}
        />
      ) : null}
      <div className="btn-group">
        <StatusToggle
          code={code}
          status={status}
          symbol="+"
          updateStatus={updateStatus}
        />
        <StatusToggle
          code={code}
          status={status}
          symbol="-"
          updateStatus={updateStatus}
        />
      </div>

      <div className="pl-2 whitespace-nowrap">
        <Pipes pipes={pipes} />
        {hasDescendants ? (
          <DescendantToggle
            isExpanded={isExpanded}
            path={path}
            toggleVisibility={toggleVisibility}
          />
        ) : null}
        <span className={statusTermColor[status]}>{term} </span>
        <code className={statusCodeColor[status]}>{code}</code>
      </div>

      {isEditable ? (
        <MoreInfoModal
          allCodes={allCodes}
          code={code}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          hierarchy={hierarchy}
          status={status}
          term={term}
        />
      ) : null}

      {!isUsagePillOnLeft ? (
        <UsagePill
          code={code}
          codeToUsage={codeToUsage}
          usagePillDisplayOptions={usagePillDisplayOptions}
        />
      ) : null}
    </div>
  );
}

function UsagePill({
  code,
  codeToUsage,
  usagePillDisplayOptions,
}: {
  code: Code;
  codeToUsage: CodeToUsage;
  usagePillDisplayOptions: UsagePillDisplayOptions;
}) {
  if (!codeToUsage || Object.keys(codeToUsage).length === 0) {
    return null;
  }

  const usage = codeToUsage[code];
  const metaClassName = `builder__meta builder__meta--${usagePillDisplayOptions.position} ${usagePillDisplayOptions.numberFormat === "condensed" ? "" : "builder__meta--uncondensed"}`;

  // Code not in usage data at all — render empty placeholder to keep buttons aligned
  if (usage === undefined) {
    return usagePillDisplayOptions.position === "left" ? (
      <div className={`${metaClassName} builder__meta--placeholder`} />
    ) : null;
  }

  let pillClass = "usage-pill";
  let label: React.ReactNode;

  function formatUsage(usage: number): string {
    if (usagePillDisplayOptions.numberFormat === "full") {
      return usage.toLocaleString();
    }

    if (usage >= 1000000) {
      return `${(usage / 1000000).toFixed(1)}M`;
    }

    if (usage >= 1000) {
      return `${(usage / 1000).toFixed(1)}K`;
    }

    return usage.toString();
  }

  if (usage === null) {
    // Suppressed: fewer than 10 uses
    pillClass += " usage-pill--suppressed";
    label = (
      <>
        <strong>&lt;10</strong> uses
      </>
    );
  } else {
    const formattedUsage = formatUsage(usage);
    // TODO might want to make this dynamic
    // based on the codes returned in the current codelist,
    // rather than hardcoding thresholds
    if (usage >= 10000000) {
      pillClass += " usage-pill--ultra";
    } else if (usage >= 1000000) {
      pillClass += " usage-pill--extreme";
    } else if (usage >= 100000) {
      pillClass += " usage-pill--very-heavy";
    } else if (usage >= 10000) {
      pillClass += " usage-pill--heavy";
    } else if (usage >= 1000) {
      pillClass += " usage-pill--high";
    } else if (usage >= 100) {
      pillClass += " usage-pill--mid";
    }
    label = (
      <>
        <strong>{formattedUsage}</strong> uses
      </>
    );
  }

  return (
    <div className={metaClassName}>
      <span className={pillClass}>{label}</span>
    </div>
  );
}
