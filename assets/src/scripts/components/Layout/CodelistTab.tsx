import React, { useId, useMemo, useState } from "react";
import type Hierarchy from "../../_hierarchy";
import type {
  CodeToUsage,
  PageData,
  UpdateStatus,
  UsagePillDisplayOptions,
  UsagePillNumberFormat,
  UsagePillPosition,
} from "../../types";
import Container from "../Codelist/Container";
import EmptySearch from "../Codelist/EmptySearch";

const ALL_TIME = "all-time";

interface CodelistTabProps {
  allCodes: PageData["allCodes"];
  ancestorCodes?: string[];
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  resultsHeading: PageData["resultsHeading"];
  treeTables: PageData["treeTables"];
  updateStatus: UpdateStatus;
  usageData: PageData["usageData"];
  visiblePaths: PageData["visiblePaths"];
}

function computeAllTimeUsage(usageData: PageData["usageData"]): CodeToUsage {
  const result: CodeToUsage = {};
  for (const period of usageData.periods) {
    const periodData = usageData.byPeriod[period];
    for (const [code, usage] of Object.entries(periodData)) {
      if (!(code in result)) {
        result[code] = null;
      }
      if (usage !== null) {
        result[code] = (result[code] ?? 0) + usage;
      }
    }
  }
  return result;
}

export default function CodelistTab({
  allCodes,
  codeToStatus,
  codeToTerm,
  hierarchy,
  isEditable,
  resultsHeading,
  treeTables,
  updateStatus,
  usageData,
  visiblePaths,
}: CodelistTabProps) {
  const hasUsageData = usageData?.periods?.length > 0;
  const [selectedPeriod, setSelectedPeriod] = useState<string>(
    hasUsageData ? usageData.periods[0] : "",
  );
  const [showUsage, setShowUsage] = useState(true);
  const [usagePillPosition, setUsagePillPosition] =
    useState<UsagePillPosition>("left");
  const [usagePillNumberFormat, setUsagePillNumberFormat] =
    useState<UsagePillNumberFormat>("condensed");
  const selectedPeriodSourceUrl =
    selectedPeriod && selectedPeriod !== ALL_TIME
      ? usageData?.sourceByPeriod?.[selectedPeriod]
      : "";

  const codeToUsage = useMemo<CodeToUsage>(() => {
    if (!hasUsageData || !showUsage) return {};
    if (selectedPeriod === ALL_TIME) return computeAllTimeUsage(usageData);
    return usageData.byPeriod[selectedPeriod] ?? {};
  }, [hasUsageData, showUsage, selectedPeriod, usageData]);

  const usagePillDisplayOptions: UsagePillDisplayOptions = {
    position: usagePillPosition,
    numberFormat: usagePillNumberFormat,
  };

  const usageSelectId = useId();
  const usageCheckboxId = useId();
  const usagePositionLeftId = useId();
  const usagePositionRightId = useId();
  const usageNumberCondensedId = useId();
  const usageNumberFullId = useId();

  return (
    <>
      <h3 className="h4">{resultsHeading}</h3>
      <hr />
      {hasUsageData && (
        <section
          className="usage-bar usage-bar-temp-css"
          aria-label="Clinical code usage controls"
        >
          <div className="temp-wrapper">
            <div className="usage-bar__controls">
              <label htmlFor={usageCheckboxId} className="usage-bar__toggle">
                <input
                  className="usage-bar__checkbox-input"
                  id={usageCheckboxId}
                  type="checkbox"
                  checked={showUsage}
                  onChange={(e) => setShowUsage(e.target.checked)}
                />
                <span className="usage-bar__toggle-text">
                  Show usage values in results
                </span>
              </label>
              <div className="usage-bar__period-control">
                <label htmlFor={usageSelectId} className="usage-bar__label">
                  for
                </label>
                <select
                  id={usageSelectId}
                  className="usage-bar__select-input"
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  disabled={!showUsage}
                >
                  {usageData.periods.map((period) => (
                    <option key={period} value={period}>
                      {period}
                    </option>
                  ))}
                  <option value={ALL_TIME}>All time</option>
                </select>
                <span className="usage-bar__info-group">
                  <button
                    type="button"
                    className="usage-bar__info-icon"
                    aria-label="More information"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <path d="M12 16v-4" />
                      <path d="M12 8h.01" />
                    </svg>
                  </button>
                  <div className="usage-bar__info-tooltip">
                    <p className="usage-bar__info-tooltip-title">Code usage</p>
                    <p className="usage-bar__info-tooltip-body">
                      The NHS publishes data on how often clinical codes are
                      used in practice. This data can be used to understand
                      which codes are commonly used, and to identify codes that
                      are rarely used or not used at all.
                      <br />
                      <br />
                      The data is provided in yearly releases covering a 12
                      month period, April 1st to March 31st. Selecting "All
                      time" will show the total usage across all available
                      periods.
                    </p>
                  </div>
                </span>
              </div>
            </div>
            <p className="usage-bar__source">
              {selectedPeriodSourceUrl && (
                <>
                  {"Data source: "}
                  <a
                    href={selectedPeriodSourceUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    published release for {selectedPeriod}
                  </a>
                </>
              )}
            </p>
          </div>
          <div className="usage-bar__experiment-panel">
            <div className="usage-bar__option-control">
              <fieldset className="usage-bar__btn-fieldset">
                <legend className="usage-bar__option-title">Position</legend>
                <div className="btn-group btn-group-sm usage-bar__btn-group">
                  <label
                    className={`btn ${
                      usagePillPosition === "left"
                        ? "btn-primary"
                        : "btn-outline-primary"
                    }`}
                    htmlFor={usagePositionLeftId}
                  >
                    Left
                  </label>
                  <input
                    type="radio"
                    name="usage-pill-position"
                    id={usagePositionLeftId}
                    className="usage-bar__radio-input"
                    checked={usagePillPosition === "left"}
                    onChange={() => setUsagePillPosition("left")}
                    disabled={!showUsage}
                  />
                  <input
                    type="radio"
                    name="usage-pill-position"
                    id={usagePositionRightId}
                    className="usage-bar__radio-input"
                    checked={usagePillPosition === "right"}
                    onChange={() => setUsagePillPosition("right")}
                    disabled={!showUsage}
                  />
                  <label
                    className={`btn ${
                      usagePillPosition === "right"
                        ? "btn-primary"
                        : "btn-outline-primary"
                    }`}
                    htmlFor={usagePositionRightId}
                  >
                    Right
                  </label>
                </div>
              </fieldset>
            </div>

            <div className="usage-bar__option-control">
              <fieldset className="usage-bar__btn-fieldset">
                <legend className="usage-bar__option-title">Numbers</legend>
                <div className="btn-group btn-group-sm usage-bar__btn-group">
                  <label
                    className={`btn btn-sm ${
                      usagePillNumberFormat === "condensed"
                        ? "btn-primary"
                        : "btn-outline-primary"
                    }`}
                    htmlFor={usageNumberCondensedId}
                  >
                    Condensed
                  </label>
                  <input
                    type="radio"
                    name="usage-pill-number-format"
                    id={usageNumberCondensedId}
                    className="usage-bar__radio-input"
                    checked={usagePillNumberFormat === "condensed"}
                    onChange={() => setUsagePillNumberFormat("condensed")}
                    disabled={!showUsage}
                  />
                  <input
                    type="radio"
                    name="usage-pill-number-format"
                    id={usageNumberFullId}
                    className="usage-bar__radio-input"
                    checked={usagePillNumberFormat === "full"}
                    onChange={() => setUsagePillNumberFormat("full")}
                    disabled={!showUsage}
                  />
                  <label
                    className={`btn ${
                      usagePillNumberFormat === "full"
                        ? "btn-primary"
                        : "btn-outline-primary"
                    }`}
                    htmlFor={usageNumberFullId}
                  >
                    Full
                  </label>
                </div>
              </fieldset>
            </div>
          </div>
        </section>
      )}
      {treeTables.length > 0 ? (
        <Container
          allCodes={allCodes}
          codeToStatus={codeToStatus}
          codeToTerm={codeToTerm}
          codeToUsage={codeToUsage}
          hierarchy={hierarchy}
          isEditable={isEditable}
          treeTables={treeTables}
          updateStatus={updateStatus}
          usagePillDisplayOptions={usagePillDisplayOptions}
          visiblePaths={visiblePaths}
        />
      ) : (
        <EmptySearch />
      )}
    </>
  );
}
