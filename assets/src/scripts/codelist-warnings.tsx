import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { readValueFromPage } from "./_utils";
import CodelistWarnings from "./components/Codelist/CodelistWarnings";

const container = document.getElementById("codelist-warnings");

if (container) {
  const icd10TermDifferences = readValueFromPage("icd10-term-differences");
  const icd10MovedCodes = readValueFromPage("icd10-moved-codes");
  const includedCodes = readValueFromPage("included-codes");

  createRoot(container).render(
    <StrictMode>
      <CodelistWarnings
        icd10TermDifferences={icd10TermDifferences}
        icd10MovedCodes={icd10MovedCodes}
        includedCodes={new Set(includedCodes)}
      />
    </StrictMode>,
  );
}
