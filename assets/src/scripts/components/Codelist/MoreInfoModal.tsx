import React, { useEffect, useState } from "react";
import { Button, Modal } from "react-bootstrap";
import type Hierarchy from "../../_hierarchy";
import { getCookie, readValueFromPage } from "../../_utils";
import type { Code, PageData, Status, Term } from "../../types";

interface CreateModalTextProps {
  allCodes: PageData["allCodes"];
  code: Code;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  status: Status;
}

type RubricValues = Record<string, string[]>;

interface CodeRubrics {
  concept_rubrics?: RubricValues;
  modifier_rubrics?: Record<string, RubricValues>;
  ancestor_rubrics?: AncestorRubrics[];
}

interface AncestorRubrics extends CodeRubrics {
  code: string;
  term: string;
}

const rubricDisplayNames: Record<string, string> = {
  exclusion: "Excludes:",
  inclusion: "Includes:",
  "coding-hint": "Coding hint:",
};

const rubricOrder = ["definition", "text", "note", "inclusion", "exclusion"];
const italicRubricKinds = ["footnote", "text", "note", "definition"];
const inlineHeaderRubricKinds = ["coding-hint"];

function emptyRubrics(): CodeRubrics {
  return {
    concept_rubrics: {},
    modifier_rubrics: {},
    ancestor_rubrics: [],
  };
}

function formatRubricKind(kind: string) {
  return rubricDisplayNames[kind] || kind.replaceAll("_", "-");
}

function sortAndFilterRubricEntries(rubrics: RubricValues) {
  return Object.entries(rubrics)
    .filter(([kind]) => kind !== "modifierlink")
    .sort(([left], [right]) => {
      const leftIndex = rubricOrder.indexOf(left);
      const rightIndex = rubricOrder.indexOf(right);

      if (leftIndex !== -1 || rightIndex !== -1) {
        return (
          (leftIndex === -1 ? rubricOrder.length : leftIndex) -
          (rightIndex === -1 ? rubricOrder.length : rightIndex)
        );
      }

      return left.localeCompare(right);
    });
}

function hasRubricValues(rubricValues?: RubricValues) {
  return Object.values(rubricValues || {}).some((values) => values.length > 0);
}

function hasRubrics(rubrics: CodeRubrics | null) {
  if (!rubrics) {
    return false;
  }

  return (
    hasRubricValues(rubrics.concept_rubrics) ||
    Object.values(rubrics.modifier_rubrics || {}).some(hasRubricValues) ||
    (rubrics.ancestor_rubrics || []).some(hasRubrics)
  );
}

function hasOwnRubrics(rubrics: CodeRubrics) {
  return (
    hasRubricValues(rubrics.concept_rubrics) ||
    Object.values(rubrics.modifier_rubrics || {}).some(hasRubricValues)
  );
}

function rubricMultipleWithHeader(kind: string, values: string[]) {
  return (
    <>
      <h3 className="h6 font-weight-bold">{formatRubricKind(kind)}</h3>
      <ul>
        {values.map((value, idx) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: item won't be re-rendered based on key
          <li key={idx}>{value}</li>
        ))}
      </ul>
    </>
  );
}

function rubricWithHeaderInline(kind: string, values: string[]) {
  return (
    <p>
      <span className="h6 font-weight-bold">{formatRubricKind(kind)} </span>
      {values.join(" ")}
    </p>
  );
}

function rubricItalicWithoutHeader(value: string) {
  return <p className="font-italic">{value}</p>;
}

function rubricFormat(kind: string, values: string[]) {
  if (italicRubricKinds.includes(kind)) {
    return rubricItalicWithoutHeader(values.join(" "));
  } else if (inlineHeaderRubricKinds.includes(kind)) {
    return rubricWithHeaderInline(kind, values);
  } else {
    return rubricMultipleWithHeader(kind, values);
  }
}

function RubricList({ rubrics }: { rubrics: RubricValues }) {
  return sortAndFilterRubricEntries(rubrics).map(([kind, values]) => (
    <React.Fragment key={kind}>{rubricFormat(kind, values)}</React.Fragment>
  ));
}

function RubricBlock({ rubrics }: { rubrics: CodeRubrics }) {
  return (
    <>
      {rubrics.concept_rubrics && (
        <RubricList rubrics={rubrics.concept_rubrics} />
      )}

      {Object.entries(rubrics.modifier_rubrics || {}).map(
        ([termModifier, modifierRubrics]) => (
          <section
            key={termModifier}
            className="mb-3 px-3 pt-3 rounded border border-primary bg-light shadow-sm"
          >
            <h3 className="h6 font-weight-bold mb-3">
              Modifier: "{termModifier}"
            </h3>

            <RubricList rubrics={modifierRubrics} />
          </section>
        ),
      )}
    </>
  );
}

function RubricSections({ rubrics }: { rubrics: CodeRubrics }) {
  const ancestorRubrics = rubrics.ancestor_rubrics || [];

  return (
    <>
      {hasOwnRubrics(rubrics) && (
        <section className={ancestorRubrics.length > 0 ? "mb-4" : undefined}>
          {ancestorRubrics.length > 0 && (
            <h3 className="h6 font-weight-bold mb-3">For this code</h3>
          )}
          <RubricBlock rubrics={rubrics} />
        </section>
      )}

      {ancestorRubrics.length > 0 && (
        <section>
          <h3 className="h6 font-weight-bold mb-3">
            From higher up the ICD-10 tree
          </h3>

          {ancestorRubrics.map((ancestor) => (
            <section
              key={ancestor.code}
              className="mb-3 px-3 pt-3 rounded border border-secondary bg-light"
            >
              <h4 className="h6 font-weight-bold mb-3">
                {ancestor.term} (
                {ancestor.code.match(/^[IVX]+$/)
                  ? `Chapter ${ancestor.code}`
                  : ancestor.code}
                )
              </h4>
              <RubricBlock rubrics={ancestor} />
            </section>
          ))}
        </section>
      )}
    </>
  );
}

function createModalText({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  hierarchy,
  status,
}: CreateModalTextProps) {
  const included = allCodes.filter((c) => codeToStatus[c] === "+");
  const excluded = allCodes.filter((c) => codeToStatus[c] === "-");
  const significantAncestors = hierarchy.significantAncestors(
    code,
    included,
    excluded,
  );

  const includedAncestorsText = significantAncestors.includedAncestors
    .map((code: Code) => `${codeToTerm[code]} [${code}]`)
    .join(", ");

  const excludedAncestorsText = significantAncestors.excludedAncestors
    .map((code: Code) => `${codeToTerm[code]} [${code}]`)
    .join(", ");

  let text = "";

  switch (status) {
    case "+":
      text = "Included";
      break;
    case "(+)":
      text = `Included because you included its ancestor: "${includedAncestorsText}"`;
      break;
    case "-":
      text = "Excluded";
      break;
    case "(-)":
      text = `Excluded because you excluded its ancestor: "${excludedAncestorsText}"`;
      break;
    case "?":
      text = "Unresolved";
      break;
    case "!":
      text = `In conflict!  Included by "${includedAncestorsText}", and excluded by "${excludedAncestorsText}"`;
      break;
  }

  return text;
}

interface MoreInfoModalProps {
  allCodes: PageData["allCodes"];
  code: Code;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  status: Status;
  term: Term;
}

function MoreInfoModal({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  hierarchy,
  status,
  term,
}: MoreInfoModalProps) {
  const codingSystemId = readValueFromPage("metadata")?.coding_system_id;
  const showSynonymsAndReferences = codingSystemId !== "icd10";

  const [showMoreInfoModal, setShowMoreInfoModal] = useState(false);
  const [references, setReferences] = useState<Array<[string, string]> | null>(
    null,
  );
  const [rubrics, setRubrics] = useState<CodeRubrics | null>(null);
  const [synonyms, setSynonyms] = useState<string[] | null>(null);
  const [modalText, setModalText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleShow = () => {
    setShowMoreInfoModal(true);
    if (synonyms === null || references === null || rubrics === null) {
      setLoading(true);
      const requestHeaders = new Headers();
      requestHeaders.append("Accept", "application/json");
      requestHeaders.append("Content-Type", "application/json");
      const csrfCookie = getCookie("csrftoken");
      if (csrfCookie) {
        requestHeaders.append("X-CSRFToken", csrfCookie);
      }
      fetch(`/coding-systems/more-info/${codingSystemId}`, {
        method: "POST",
        credentials: "include" as RequestCredentials,
        mode: "same-origin" as RequestMode,
        headers: requestHeaders,
        body: JSON.stringify({ codes: [code] }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.error) {
            throw new Error(data.error);
          }
          // data.synonyms[code] can contain synonyms that are an exact match
          // for the main term. We filter these out.
          setSynonyms(
            data.synonyms?.[code]?.filter(
              (synonym: string) => synonym !== term,
            ) || [],
          );
          setReferences(data.references?.[code] || []);
          setRubrics(data.rubrics?.[code] || emptyRubrics());
        })
        .catch(() => {
          setSynonyms([]);
          setReferences([]);
          setRubrics(emptyRubrics());
        })
        .finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    if (showMoreInfoModal && synonyms !== null) {
      setModalText(
        createModalText({
          allCodes,
          code,
          codeToStatus,
          codeToTerm,
          hierarchy,
          status,
        }),
      );
    }
  }, [showMoreInfoModal, synonyms]);

  return (
    <>
      <Button
        className="builder__more-info-btn plausible-event-name=More+info+click"
        onClick={handleShow}
        variant="outline-dark"
      >
        More info
      </Button>

      <Modal
        centered
        onHide={() => setShowMoreInfoModal(false)}
        size="lg"
        show={showMoreInfoModal}
      >
        <Modal.Header closeButton>
          <Modal.Title>
            {term} ({code})
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {showSynonymsAndReferences && (
            <>
              <h2 className="h6 font-weight-bold">Synonyms</h2>
              {loading ? (
                <p>Loading synonyms...</p>
              ) : (
                <ul>
                  {!synonyms || synonyms?.length === 0 ? (
                    <li>No synonyms</li>
                  ) : (
                    // biome-ignore lint/suspicious/noArrayIndexKey: item won't be re-rendered based on key
                    synonyms.map((synonym, idx) => <li key={idx}>{synonym}</li>)
                  )}
                </ul>
              )}
            </>
          )}
          {hasRubrics(rubrics) && (
            <section className="border border-info rounded overflow-hidden mb-4">
              {/* WHO header */}
              <div className="bg-info text-white px-4 py-3">
                <div className="font-weight-bold">
                  WHO ICD-10 Additional Info
                </div>
                <small className="opacity-75">
                  This information is primarily targeted at clinical coders, but
                  may be useful and so included for completeness.
                </small>
              </div>

              {/* WHO body */}
              <div className="bg-white pt-3 px-4">
                {rubrics && <RubricSections rubrics={rubrics} />}
              </div>
            </section>
          )}
          {showSynonymsAndReferences && (
            <>
              <h2 className="h6 font-weight-bold">References</h2>
              {loading ? (
                <p>Loading references...</p>
              ) : (
                <ul>
                  {!references?.length ? (
                    <li>No references</li>
                  ) : (
                    references.map((reference, idx) => (
                      // biome-ignore lint/suspicious/noArrayIndexKey: item won't be re-rendered based on key
                      <li key={idx}>
                        <a href={reference[1]}>{reference[0]}</a>
                      </li>
                    ))
                  )}
                </ul>
              )}
            </>
          )}
          <h2 className="h6 font-weight-bold">Status</h2>
          <p>{modalText}</p>
        </Modal.Body>
      </Modal>
    </>
  );
}

export default MoreInfoModal;
