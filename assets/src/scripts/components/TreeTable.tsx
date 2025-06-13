import React, { useState } from "react";
import { Button, ButtonGroup, Form, Modal } from "react-bootstrap";
import Hierarchy from "../_hierarchy";
import { AncestorCodes, PageData, ToggleVisibility } from "../types";
import Tree from "./Tree";

interface TreeTableProps {
  allCodes: PageData["allCodes"];
  ancestorCodes: AncestorCodes;
  codeToStatus: PageData["codeToStatus"];
  codeToTerm: PageData["codeToTerm"];
  heading: string;
  hierarchy: Hierarchy;
  isEditable: PageData["isEditable"];
  toggleVisibility: ToggleVisibility;
  updateStatus: Function;
  visiblePaths: PageData["visiblePaths"];
}

export default function TreeTable({
  allCodes,
  ancestorCodes,
  codeToStatus,
  codeToTerm,
  heading,
  hierarchy,
  isEditable,
  toggleVisibility,
  updateStatus,
  visiblePaths,
}: TreeTableProps) {
  const [showExcludeAll, setShowExcludeAll] = useState(false);
  const handleExcludeAllClose = () => setShowExcludeAll(false);
  const handleExcludeAllShow = () => setShowExcludeAll(true);

  const [showExcludeUnresolved, setShowExcludeUnresolved] = useState(false);
  const handleExcludeUnresolvedClose = () => setShowExcludeUnresolved(false);
  const handleExcludeUnresolvedShow = () => setShowExcludeUnresolved(true);

  return (
    <>
      <div className="builder__section">
        <div className="builder__section-header">
          <h3 className="h5">{heading}</h3>
          {heading === "Assessment Scale" ? (
            <ButtonGroup size="sm">
              <Button variant="outline-danger">Exclude all</Button>
              <Button disabled variant="outline-secondary">
                Exclude unresolved
              </Button>
            </ButtonGroup>
          ) : (
            <ButtonGroup size="sm">
              <Button variant="outline-danger" onClick={handleExcludeAllShow}>
                Exclude all
              </Button>
              <Button
                variant="outline-info"
                onClick={handleExcludeUnresolvedShow}
              >
                Exclude unresolved
              </Button>
            </ButtonGroup>
          )}
        </div>
        {heading === "Assessment Scale" ? (
          <dl>
            <div className="text-primary">
              <dt>Included:</dt>
              <dd>1</dd>
            </div>
            <div className="text-info">
              <dt>Excluded:</dt>
              <dd>0</dd>
            </div>
            <div className="text-secondary">
              <dt>Unresolved:</dt>
              <dd>0</dd>
            </div>
            <div className="text-danger">
              <dt>Conflicted:</dt>
              <dd>0</dd>
            </div>
          </dl>
        ) : (
          <dl>
            <div className="text-primary">
              <dt>Included:</dt>
              <dd>2</dd>
            </div>
            <div className="text-info">
              <dt>Excluded:</dt>
              <dd>2</dd>
            </div>
            <div className="text-secondary">
              <dt>Unresolved:</dt>
              <dd>142</dd>
            </div>
            <div className="text-danger">
              <dt>Conflicted:</dt>
              <dd>0</dd>
            </div>
          </dl>
        )}

        <div className="builder__container">
          {ancestorCodes.map((ancestorCode) => (
            <Tree
              allCodes={allCodes}
              ancestorCode={ancestorCode}
              codeToStatus={codeToStatus}
              codeToTerm={codeToTerm}
              hierarchy={hierarchy}
              isEditable={isEditable}
              key={ancestorCode}
              toggleVisibility={toggleVisibility}
              updateStatus={updateStatus}
              visiblePaths={visiblePaths}
            />
          ))}
        </div>
      </div>

      <Modal
        dialogClassName="modal-90w"
        centered
        show={showExcludeAll}
        onHide={handleExcludeAllClose}
      >
        <Modal.Header closeButton>
          <Modal.Title>
            Exclude all in <strong>Body Structure</strong>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <h2 className="h4">Update included codes</h2>
          <p>
            The following 2 codes within <strong>Body Structure</strong> are
            <strong className="text-primary"> included</strong> and will now be{" "}
            <strong className="text-info">excluded</strong> instead:
          </p>
          <ul>
            <li>
              Structure of skin crease of elbow region <code>280388002</code>
            </li>
            <li>
              Entire skin crease of elbow <code>729376007</code>
            </li>
          </ul>
          <hr />
          <h2 className="h4">Already excluded codes</h2>
          <p>
            The following 2 codes within <strong>Body Structure</strong> are
            already <strong className="text-info">excluded</strong> and will not
            be updated:
          </p>
          <ul>
            <li>
              Structure of bone marrow of elbow <code>712957004</code>
            </li>
            <li>
              All bone marrow of elbow <code>731605009</code>
            </li>
          </ul>
          <hr />
          <h2 className="h4">Update unresolved codes</h2>
          <p>
            The following 26 codes are currently unresolved, and will be{" "}
            <strong className="text-info">excluded</strong>:
          </p>
          <ul>
            <li>
              Chinese auricular elbow <code>273193001</code>
            </li>
            <li>
              Elbow region structure <code>127949000</code>
            </li>
            <li>
              Antecubital region structure <code>90837009</code>
            </li>
            <li>
              Bone structure of elbow joint region <code>304678002</code>
            </li>
            <li>
              Elbow joint structure <code>16953009</code>
            </li>
            <li>
              Entire elbow region <code>76248009</code>
            </li>
            <li>
              Left elbow region structure <code>368148009</code>
            </li>
            <li>
              Right elbow region structure <code>368149001</code>
            </li>
            <li>
              Structure of cubital lymph node <code>34775006</code>
            </li>
            <li>
              Structure of cubital tunnel <code>890317009</code>
            </li>
            <li>
              Structure of epitrochlear lymph node <code>28870006</code>
            </li>
            <li>
              Structure of lateral cubital region <code>10484007</code>
            </li>
            <li>
              Structure of medial cubital region <code>54264004</code>
            </li>
            <li>
              Structure of peripheral nerve at elbow <code>310843004</code>
            </li>
            <li>
              Structure of posterior cubital region <code>66498007</code>
            </li>
            <li>
              Structure of soft tissue of elbow region <code>725630005</code>
            </li>
            <li>
              Structure of surface region of elbow <code>243999005</code>
            </li>
            <li>
              Structure of muscle acting on elbow joint <code>303558007</code>
            </li>
            <li>
              Entire muscle acting on elbow joint <code>729645009</code>
            </li>
            <li>
              Structure of extensor of elbow joint <code>303732005</code>
            </li>
            <li>
              Structure of flexor of elbow joint <code>303559004</code>
            </li>
            <li>
              Structure of upper extremity between shoulder and elbow{" "}
              <code>40983000</code>
            </li>
            <li>
              Entire upper arm <code>302538001</code>
            </li>
            <li>
              Left upper arm structure <code>368208006</code>
            </li>
            <li>
              Right upper arm structure <code>368209003</code>
            </li>
            <li>
              Upper arm part <code>709294008</code>
            </li>
          </ul>
        </Modal.Body>
        <Modal.Footer className="modal-foooter">
          <Form.Check
            type="checkbox"
            label="I understand I am updating 2 codes from included to excluded; and excluding 26 unresolved codes"
            required
          />
          <div className="modal-buttons">
            <Button disabled variant="danger" onClick={handleExcludeAllClose}>
              Exclude all Body Structure codes
            </Button>
            <Button variant="secondary" onClick={handleExcludeAllClose}>
              Cancel
            </Button>
          </div>
        </Modal.Footer>
      </Modal>

      <Modal
        dialogClassName="modal-90w"
        centered
        show={showExcludeUnresolved}
        onHide={handleExcludeUnresolvedClose}
      >
        <Modal.Header closeButton>
          <Modal.Title>
            Exclude unresolved in <strong>Body Structure</strong>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>
            The following 26 codes are currently unresolved, and will be{" "}
            <strong className="text-info">excluded</strong>:
          </p>
          <ul>
            <li>
              Chinese auricular elbow <code>273193001</code>
            </li>
            <li>
              Elbow region structure <code>127949000</code>
            </li>
            <li>
              Antecubital region structure <code>90837009</code>
            </li>
            <li>
              Bone structure of elbow joint region <code>304678002</code>
            </li>
            <li>
              Elbow joint structure <code>16953009</code>
            </li>
            <li>
              Entire elbow region <code>76248009</code>
            </li>
            <li>
              Left elbow region structure <code>368148009</code>
            </li>
            <li>
              Right elbow region structure <code>368149001</code>
            </li>
            <li>
              Structure of cubital lymph node <code>34775006</code>
            </li>
            <li>
              Structure of cubital tunnel <code>890317009</code>
            </li>
            <li>
              Structure of epitrochlear lymph node <code>28870006</code>
            </li>
            <li>
              Structure of lateral cubital region <code>10484007</code>
            </li>
            <li>
              Structure of medial cubital region <code>54264004</code>
            </li>
            <li>
              Structure of peripheral nerve at elbow <code>310843004</code>
            </li>
            <li>
              Structure of posterior cubital region <code>66498007</code>
            </li>
            <li>
              Structure of soft tissue of elbow region <code>725630005</code>
            </li>
            <li>
              Structure of surface region of elbow <code>243999005</code>
            </li>
            <li>
              Structure of muscle acting on elbow joint <code>303558007</code>
            </li>
            <li>
              Entire muscle acting on elbow joint <code>729645009</code>
            </li>
            <li>
              Structure of extensor of elbow joint <code>303732005</code>
            </li>
            <li>
              Structure of flexor of elbow joint <code>303559004</code>
            </li>
            <li>
              Structure of upper extremity between shoulder and elbow{" "}
              <code>40983000</code>
            </li>
            <li>
              Entire upper arm <code>302538001</code>
            </li>
            <li>
              Left upper arm structure <code>368208006</code>
            </li>
            <li>
              Right upper arm structure <code>368209003</code>
            </li>
            <li>
              Upper arm part <code>709294008</code>
            </li>
          </ul>
        </Modal.Body>
        <Modal.Footer className="modal-foooter">
          <Form.Check
            type="checkbox"
            label="I understand I am excluding 26 unresolved codes"
            required
          />
          <div className="modal-buttons">
            <Button
              disabled
              variant="danger"
              onClick={handleExcludeUnresolvedClose}
            >
              Exclude unresolved Body Structure codes
            </Button>
            <Button variant="secondary" onClick={handleExcludeUnresolvedClose}>
              Cancel
            </Button>
          </div>
        </Modal.Footer>
      </Modal>
    </>
  );
}
