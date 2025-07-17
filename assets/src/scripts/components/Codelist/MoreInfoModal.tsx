import React, { useEffect, useState } from "react";
import { Modal } from "react-bootstrap";
import Hierarchy from "../../_hierarchy";
import { getCookie, readValueFromPage } from "../../_utils";
import { useCodelistContext } from "../../context/codelist-context";
import { Code, PageData, Status } from "../../types";

function createModalText({
  allCodes,
  code,
  codeToStatus,
  codeToTerm,
  hierarchy,
  status,
}: {
  allCodes: PageData["allCodes"];
  code: Code;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  hierarchy: Hierarchy;
  status: Status;
}) {
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

function MoreInfoModal({
  code,
  status,
  term,
}: { code: string; status: Status; term: string }) {
  const { allCodes, codeToStatus, codeToTerm, hierarchy } =
    useCodelistContext();
  const codingSystemId = readValueFromPage("metadata")?.coding_system_id;

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
          code,
          status,
          allCodes,
          codeToStatus,
          codeToTerm,
          hierarchy,
        }),
      );
    }
  }, [
    showMoreInfoModal,
    synonyms,
    code,
    status,
    allCodes,
    codeToStatus,
    codeToTerm,
    hierarchy,
  ]);

  return (
    <>
      <button
        className="btn btn-outline-dark builder__more-info-btn"
        onClick={handleShow}
      >
        More info
      </button>

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
