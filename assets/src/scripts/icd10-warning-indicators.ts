import type { Code, ICD10MovedCode, ICD10TermDifferences } from "./types";

export type ICD10WarningIndicator = {
  hasTermDifference: boolean;
  hasMovedCodes: boolean;
  label: string;
};

export type ICD10WarningIndicatorMap = Record<Code, ICD10WarningIndicator>;

export const codeIsIncluded = (includedCodes: Set<string>, code: string) =>
  includedCodes.has(code);

export const codesForMovedCode = (movedCode: ICD10MovedCode) =>
  Array.from(new Set([...movedCode.nhs2016, ...movedCode.who2019]));

export function activeTermDifferences(
  termDifferences: ICD10TermDifferences,
  includedCodes: Set<string>,
) {
  return [...includedCodes]
    .filter((code) => termDifferences[code])
    .map((code) => ({ code, ...termDifferences[code] }));
}

export function activeMovedCodes(
  movedCodes: ICD10MovedCode[] = [],
  includedCodes: Set<string>,
) {
  return movedCodes.filter((movedCode) => {
    const codes = codesForMovedCode(movedCode);
    const includedCount = codes.filter((code) =>
      codeIsIncluded(includedCodes, code),
    ).length;
    return includedCount > 0 && includedCount < codes.length;
  });
}

function indicatorLabel({
  hasTermDifference,
  hasMovedCodes,
}: {
  hasTermDifference: boolean;
  hasMovedCodes: boolean;
}) {
  if (hasTermDifference && hasMovedCodes) {
    return "ICD-10 warning: conflicting definitions and missing equivalent codes need review";
  }

  if (hasTermDifference) {
    return "ICD-10 warning: conflicting definitions need review";
  }

  return "ICD-10 warning: this concept may be missing equivalent codes";
}

function addIndicator(
  indicators: ICD10WarningIndicatorMap,
  code: string,
  warningType: "hasTermDifference" | "hasMovedCodes",
) {
  const current = indicators[code] ?? {
    hasTermDifference: false,
    hasMovedCodes: false,
    label: "",
  };
  const updated = {
    ...current,
    [warningType]: true,
  };

  indicators[code] = {
    ...updated,
    label: indicatorLabel(updated),
  };
}

export function icd10WarningIndicators({
  includedCodes,
  termDifferences = {},
  movedCodes = [],
}: {
  includedCodes: Set<string>;
  termDifferences?: ICD10TermDifferences;
  movedCodes?: ICD10MovedCode[];
}) {
  const indicators: ICD10WarningIndicatorMap = {};

  for (const { code } of activeTermDifferences(
    termDifferences,
    includedCodes,
  )) {
    addIndicator(indicators, code, "hasTermDifference");
  }

  for (const movedCode of activeMovedCodes(movedCodes, includedCodes)) {
    const codes = codesForMovedCode(movedCode);
    for (const code of codes.filter((code) =>
      codeIsIncluded(includedCodes, code),
    )) {
      addIndicator(indicators, code, "hasMovedCodes");
    }
  }

  return indicators;
}
