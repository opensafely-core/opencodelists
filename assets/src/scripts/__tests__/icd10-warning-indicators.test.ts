import { describe, expect, it } from "vitest";
import {
  activeMovedCodes,
  activeTermDifferences,
  icd10WarningIndicators,
} from "../icd10-warning-indicators";

const termDifferences = {
  M770: {
    combined_2016: "Old term",
    who_2019: "New term",
  },
};

const movedCodes = [
  {
    title: "Pneumocystosis",
    comment: "",
    nhs2016: ["B59"],
    who2019: ["B485"],
  },
];

describe("activeTermDifferences", () => {
  it("returns term differences only when the code is included", () => {
    expect(activeTermDifferences(termDifferences, new Set(["M770"]))).toEqual([
      { code: "M770", combined_2016: "Old term", who_2019: "New term" },
    ]);
    expect(activeTermDifferences(termDifferences, new Set())).toEqual([]);
  });
});

describe("activeMovedCodes", () => {
  it("returns moved codes only when they are partially included", () => {
    expect(activeMovedCodes(movedCodes, new Set(["B59"]))).toEqual(movedCodes);
    expect(activeMovedCodes(movedCodes, new Set(["B59", "B485"]))).toEqual([]);
    expect(activeMovedCodes(movedCodes, new Set())).toEqual([]);
  });

  it("deduplicates codes that are present in both releases", () => {
    const movedCodeWithSharedCode = [
      {
        title: "Irritable bowel syndrome",
        nhs2016: ["K58", "K580", "K589"],
        who2019: ["K58", "K581", "K582", "K583", "K588"],
      },
    ];

    expect(activeMovedCodes(movedCodeWithSharedCode, new Set(["K58"]))).toEqual(
      movedCodeWithSharedCode,
    );
    expect(
      activeMovedCodes(
        movedCodeWithSharedCode,
        new Set(["K58", "K580", "K589", "K581", "K582", "K583", "K588"]),
      ),
    ).toEqual([]);
  });
});

describe("icd10WarningIndicators", () => {
  it("marks included known-difference codes", () => {
    const indicators = icd10WarningIndicators({
      includedCodes: new Set(["M770"]),
      termDifferences,
    });

    expect(indicators.M770).toMatchObject({
      hasTermDifference: true,
      hasMovedCodes: false,
      label: "ICD-10 warning: conflicting definitions need review",
    });
  });

  it("marks only included codes from partially included moved code sets", () => {
    const indicators = icd10WarningIndicators({
      includedCodes: new Set(["B59"]),
      movedCodes,
    });

    expect(indicators.B59).toMatchObject({
      hasTermDifference: false,
      hasMovedCodes: true,
      label: "ICD-10 warning: this concept may be missing equivalent codes",
    });
    expect(indicators.B485).toBeUndefined();
  });

  it("combines labels when a code has both warning types", () => {
    const indicators = icd10WarningIndicators({
      includedCodes: new Set(["B59"]),
      termDifferences: {
        B59: {
          combined_2016: "Old term",
          who_2019: "New term",
        },
      },
      movedCodes,
    });

    expect(indicators.B59).toMatchObject({
      hasTermDifference: true,
      hasMovedCodes: true,
      label:
        "ICD-10 warning: conflicting definitions and missing equivalent codes need review",
    });
  });
});
