import React from "react";
import {
  activeMovedCodes,
  activeTermDifferences,
  codeIsIncluded,
  codesForMovedCode,
} from "../../icd10-warning-indicators";
import type {
  ICD10MovedCode,
  ICD10TermDifference,
  ICD10TermDifferences,
} from "../../types";

interface CodelistWarningsProps {
  icd10TermDifferences: ICD10TermDifferences;
  icd10MovedCodes: ICD10MovedCode[];
  includedCodes: Set<string>;
}

const movedCodeKey = (codes: string[]) => codes.join("-");

function MovedCodeList({
  codes,
  status,
}: {
  codes: string[];
  status?: "included" | "missing";
}) {
  return (
    <>
      {codes.map((code, index) => (
        <React.Fragment key={code}>
          {index > 0 && ", "}
          <strong
            className={
              status ? `warning-code-token warning-code-token--${status}` : ""
            }
          >
            {code}
          </strong>
        </React.Fragment>
      ))}
    </>
  );
}

function TermDifferencesWarning({
  differences,
}: {
  differences: (ICD10TermDifference & { code: string })[];
}) {
  return (
    <div className="alert alert-danger warning-banner" role="alert">
      <div className="warning-banner__header">
        <div className="warning-banner__icon" aria-hidden="true">
          !
        </div>
        <div>
          <h2 className="warning-banner__title">
            Conflicting definitions detected
          </h2>
          <p className="warning-banner__lead mb-0">
            This codelist includes{" "}
            <strong>
              {differences.length === 1
                ? "1 code"
                : `${differences.length} codes`}
            </strong>{" "}
            with multiple definitions that require review before use.
          </p>
        </div>
      </div>

      <details className="warning-banner__details">
        <summary>More details</summary>
        <div className="warning-banner__expanded">
          <section className="warning-section">
            <h3 className="warning-section__title">What does this mean?</h3>
            <p>
              OpenCodelists supports both the 2016 and 2019 WHO editions of
              ICD-10 because different datasets use different editions:
            </p>
            <ul>
              <li>
                HES/APCS uses an NHS-modified version of the 2016 edition.
              </li>
              <li>ONS deaths uses the 2019 edition.</li>
            </ul>
            <p className="mb-0">
              Most ICD-10 codes have the same meaning in both editions. However,
              a small number have different meanings between editions.
            </p>
          </section>

          <section className="warning-section">
            <h3 className="warning-section__title">
              Codes that need your attention
            </h3>

            <div className="table-responsive">
              <table className="table table-sm warning-table">
                <thead>
                  <tr>
                    <th scope="col">Code</th>
                    <th scope="col">NHS 2016 definition</th>
                    <th scope="col">WHO 2019 definition</th>
                  </tr>
                </thead>
                <tbody>
                  {differences.map((difference) => (
                    <tr key={difference.code}>
                      <td>
                        <strong>{difference.code}</strong>
                      </td>
                      <td>{difference.combined_2016}</td>
                      <td>{difference.who_2019}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="warning-section mb-0">
            <h3 className="warning-section__title">What should I do?</h3>
            <p>
              <strong>
                If you're using this codelist with a single dataset
              </strong>
              , check that the code has the intended definition in the ICD-10
              edition used by that dataset. If the definition shown above
              doesn't match the condition you intended to include, you should
              create a new version of this codelist that excludes the code.
            </p>
            <p className="mb-0">
              <strong>
                If you're using this codelist with multiple datasets
              </strong>{" "}
              that use different ICD-10 editions, you need to review the
              definitions for each edition. If the code has different meanings,
              you may need separate codelists for each dataset.
            </p>
          </section>
        </div>
      </details>
    </div>
  );
}

function MovedCodesWarning({
  codeIsIncluded,
  movedCodes,
}: {
  codeIsIncluded: (code: string) => boolean;
  movedCodes: ICD10MovedCode[];
}) {
  const missingMovedCodes = (movedCode: ICD10MovedCode) =>
    codesForMovedCode(movedCode).filter((code) => !codeIsIncluded(code));
  const totalNhs2016Codes = movedCodes
    .map((set) => set.nhs2016.length)
    .reduce((a, b) => a + b, 0);
  const totalWho2019Codes = movedCodes
    .map((set) => set.who2019.length)
    .reduce((a, b) => a + b, 0);

  return (
    <div className="alert alert-danger warning-banner" role="alert">
      <div className="warning-banner__header">
        <div className="warning-banner__icon" aria-hidden="true">
          !
        </div>
        <div>
          <h2 className="warning-banner__title">
            This ICD-10 codelist may be incomplete
          </h2>
          <p className="warning-banner__lead mb-0">
            This codelist may be missing codes for concepts that have changed in
            the latest edition of ICD-10.
          </p>
        </div>
      </div>

      <details className="warning-banner__details">
        <summary>More details</summary>

        <section className="warning-section">
          <h3 className="warning-section__title">What does this mean?</h3>

          <p>
            OpenCodelists supports both the 2016 and 2019 WHO editions of ICD-10
            because different datasets use different editions:
          </p>
          <ul>
            <li>HES/APCS uses an NHS-modified version of the 2016 edition.</li>
            <li>ONS deaths uses the 2019 edition.</li>
          </ul>
          <p className="mb-0">
            Some concepts have different codes in each edition. Including only
            one code may cause records to be missed in datasets that use the
            other edition.
          </p>
        </section>

        <div className="warning-banner__expanded">
          <section className="warning-section">
            <h3 className="warning-section__title">
              Potentially missing codes
            </h3>
            <p>
              These concepts have equivalent codes that are not currently
              included in your codelist.
            </p>
            <div className="table-responsive">
              <table className="table table-sm warning-table">
                <thead>
                  <tr>
                    <th scope="col">Concept</th>
                    <th scope="col">
                      NHS 2016 code{totalNhs2016Codes > 1 ? "s" : ""}
                    </th>
                    <th scope="col">
                      WHO 2019 code{totalWho2019Codes > 1 ? "s" : ""}
                    </th>
                    <th scope="col">This codelist</th>
                  </tr>
                </thead>
                <tbody>
                  {movedCodes.map((movedCode) => (
                    <tr key={movedCodeKey(codesForMovedCode(movedCode))}>
                      <td>{movedCode.title}</td>
                      <td>
                        <MovedCodeList codes={movedCode.nhs2016} />
                      </td>
                      <td>
                        <MovedCodeList codes={movedCode.who2019} />
                      </td>
                      <td>
                        Missing{" "}
                        <MovedCodeList
                          codes={missingMovedCodes(movedCode)}
                          status="missing"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <section className="warning-section mb-0">
            <h3 className="warning-section__title">What should I do?</h3>
            <p>
              We recommend using a codelist that includes all ICD-10 codes where
              a concept has different codes in the 2016 and 2019 editions. Codes
              that moved between editions aren't reused for different
              conditions, so using both is the safest way to ensure your
              codelist works across datasets. However, you must check the codes
              carefully as there may be situations where you only need some of
              the codes.
            </p>
            <p className="mb-0">
              If you choose to use this codelist without the missing codes,
              please ensure you have considered the implications.
            </p>
          </section>
        </div>
      </details>
    </div>
  );
}

export default function CodelistWarnings({
  icd10TermDifferences = {},
  icd10MovedCodes = [],
  includedCodes,
}: CodelistWarningsProps) {
  const includedInCurrentCodelist = (code: string) =>
    codeIsIncluded(includedCodes, code);
  const incompleteTermDifferences = activeTermDifferences(
    icd10TermDifferences,
    includedCodes,
  );
  const incompleteMovedCodes = activeMovedCodes(icd10MovedCodes, includedCodes);

  if (
    incompleteTermDifferences.length === 0 &&
    incompleteMovedCodes.length === 0
  ) {
    return null;
  }

  return (
    <>
      {incompleteTermDifferences.length > 0 && (
        <TermDifferencesWarning differences={incompleteTermDifferences} />
      )}
      {incompleteMovedCodes.length > 0 && (
        <MovedCodesWarning
          codeIsIncluded={includedInCurrentCodelist}
          movedCodes={incompleteMovedCodes}
        />
      )}
    </>
  );
}
