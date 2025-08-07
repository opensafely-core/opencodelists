import React, { useEffect, useState } from "react";
import { Button, Modal } from "react-bootstrap";
import type Hierarchy from "../../_hierarchy";
import { getCookie, readValueFromPage } from "../../_utils";
import type { BUILDER_CONFIG, Code, PageData, Status, Term } from "../../types";

interface CreateModalTextProps {
  allCodes: PageData["allCodes"];
  code: Code;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  status: Status;
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
  const {
    coding_system: { id: codingSystemId },
  }: BUILDER_CONFIG = readValueFromPage("builder-config");

  const [showMoreInfoModal, setShowMoreInfoModal] = useState(false);
  const [references, setReferences] = useState<string[] | null>(null);
  const [synonyms, setSynonyms] = useState<string[] | null>(null);
  const [modalText, setModalText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleShow = () => {
    setShowMoreInfoModal(true);
    if (synonyms === null || references === null) {
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
        })
        .catch(() => {
          setSynonyms([]);
          setReferences([]);
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
          <h2 className="h6 font-weight-bold">Status</h2>
          <p>{modalText}</p>
        </Modal.Body>
      </Modal>
    </>
  );
}

export default MoreInfoModal;
