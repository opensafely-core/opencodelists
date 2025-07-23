import React from "react";
import { Col, Form, Modal, Row, Tab, Tabs } from "react-bootstrap";
import Hierarchy from "../_hierarchy";
import { getCookie } from "../_utils";
import { Code, PageData, Reference, Status } from "../types";
import EmptyState from "./EmptyState";
import CodelistTab from "./Layout/CodelistTab";
import Header from "./Layout/Header";
import MetadataTab from "./Layout/MetadataTab";
import Sidebar from "./Layout/Sidebar";

export type MetadataFieldName = "description" | "methodology";
interface MetadataField {
  text: string;
  html: string;
  isEditing: boolean;
}
interface MetadataProps {
  description: MetadataField;
  methodology: MetadataField;
  references: Reference[];
}
interface CodelistBuilderProps extends PageData {
  hierarchy: Hierarchy;
  metadata: MetadataProps & {
    coding_system_id: string;
    coding_system_name: string;
    coding_system_release: {
      release_name: string;
      valid_from: string;
    };
    organisation_name: string;
    codelist_full_slug: string;
    hash: string;
    codelist_name: string;
  };
}

/**
 * Creates a fetch options object with standard headers including CSRF token
 * @param body - Object to be sent as JSON in the request body
 * @returns Fetch options object configured for POST requests
 */
function getFetchOptions(body: object) {
  const requestHeaders = new Headers();
  requestHeaders.append("Accept", "application/json");
  requestHeaders.append("Content-Type", "application/json");

  const csrfCookie = getCookie("csrftoken");
  if (csrfCookie) {
    requestHeaders.append("X-CSRFToken", csrfCookie);
  }
  const fetchOptions = {
    method: "POST",
    credentials: "include" as RequestCredentials,
    mode: "same-origin" as RequestMode,
    headers: requestHeaders,
    body: JSON.stringify(body),
  };
  return fetchOptions;
}

export default class CodelistBuilder extends React.Component<
  CodelistBuilderProps,
  {
    codeToStatus: PageData["codeToStatus"];
    expandedCompatibleReleases: boolean;
    metadata: MetadataProps;
    updateQueue: string[][];
    updating: boolean;
    editingField: MetadataFieldName | null;
    draftContent: string;
  }
> {
  private modalTextareaRef: React.RefObject<HTMLTextAreaElement>;
  constructor(props: CodelistBuilderProps) {
    super(props);

    this.state = {
      codeToStatus: props.codeToStatus,
      expandedCompatibleReleases: false,
      metadata: {
        description: {
          text: props.metadata.description.text,
          html: props.metadata.description.html,
          isEditing: false,
        },
        methodology: {
          text: props.metadata.methodology.text,
          html: props.metadata.methodology.html,
          isEditing: false,
        },
        references: props.metadata.references || [],
      },
      updateQueue: [],
      updating: false,
      editingField: null,
      draftContent: "",
    };

    this.updateStatus = props.isEditable
      ? this.updateStatus.bind(this)
      : () => null;
    this.toggleExpandedCompatibleReleases =
      this.toggleExpandedCompatibleReleases.bind(this);
    this.modalTextareaRef = React.createRef();
  }

  toggleExpandedCompatibleReleases() {
    this.setState({
      expandedCompatibleReleases: !this.state.expandedCompatibleReleases,
    });
  }

  updateStatus(code: Code, status: Status) {
    this.setState(({ codeToStatus, updateQueue }, { hierarchy }) => {
      const newCodeToStatus = hierarchy.updateCodeToStatus(
        codeToStatus,
        code,
        status,
      );

      return {
        codeToStatus: newCodeToStatus,
        updateQueue: updateQueue.concat([[code, newCodeToStatus[code]]]),
      };
    }, this.maybePostUpdates);
  }

  maybePostUpdates() {
    if (this.state.updating || !this.state.updateQueue.length) {
      return;
    }
    this.setState({ updating: true }, this.postUpdates);
  }

  postUpdates() {
    const fetchOptions = getFetchOptions({ updates: this.state.updateQueue });

    fetch(this.props.updateURL, fetchOptions)
      .then((response) => response.json())
      .then((data) => {
        const lastUpdates = data.updates;

        this.setState(
          (state) => {
            const newUpdateQueue = state.updateQueue.slice(lastUpdates.length);
            return { updating: false, updateQueue: newUpdateQueue };
          },

          this.maybePostUpdates,
        );
      });
  }

  counts() {
    // Define the list of valid status values that we want to count
    const validStatuses = ["?", "!", "+", "(+)", "-", "(-)"];

    // Initialize counts object with 0 for each status and total
    const counts = {
      "?": 0,
      "!": 0,
      "+": 0,
      "(+)": 0,
      "-": 0,
      "(-)": 0,
      total: 0,
    };

    // Iterate through all codes and count occurrences of each valid status
    return this.props.allCodes.reduce((acc, code) => {
      const status = this.state.codeToStatus[code];
      if (validStatuses.includes(status)) {
        acc[status]++; // Increment count for this status
        acc.total++; // Increment total count
      }
      return acc;
    }, counts);
  }

  handleEdit = (field: MetadataFieldName) => {
    this.setState({
      editingField: field,
      draftContent: this.state.metadata[field].text,
    });
  };

  handleCancel = () => {
    this.setState({
      editingField: null,
      draftContent: "",
    });
  };

  handleSave = async () => {
    const field = this.state.editingField;
    if (!field) return;

    const updateBody = {
      description:
        field === "description"
          ? this.state.draftContent
          : this.state.metadata.description.text,
      methodology:
        field === "methodology"
          ? this.state.draftContent
          : this.state.metadata.methodology.text,
    };

    const fetchOptions = getFetchOptions(updateBody);

    try {
      fetch(this.props.updateURL, fetchOptions)
        .then((response) => response.json())
        .then((data) => {
          // We rely on the backend rendering the html from the updated markdown
          // so we need to update the state here with the response from the server
          this.setState({
            metadata: data.metadata,
            editingField: null,
            draftContent: "",
          });
        });
    } catch (error) {
      console.error(`Failed to save ${field}:`, error);
    }
  };

  handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    this.setState({
      draftContent: e.target.value,
    });
  };

  // Add save handler:
  handleSaveReferences = async (
    newReferences: Array<{ text: string; url: string }>,
  ) => {
    const fetchOptions = getFetchOptions({ references: newReferences });

    try {
      await fetch(this.props.updateURL, fetchOptions);

      this.setState({
        metadata: { ...this.state.metadata, references: newReferences },
      });
    } catch (error) {
      console.error("Failed to save references:", error);
    }
  };

  renderMetadataField = (field: MetadataFieldName) => {
    const label = field.charAt(0).toUpperCase() + field.slice(1);
    const htmlContent = this.state.metadata[field].html;

    return (
      <Form.Group className={`card ${field}`} controlId={field}>
        <div className="card-body">
          {this.props.isEditable ? (
            <>
              <div className="card-title d-flex flex-row justify-content-between align-items-center">
                <Form.Label className="h5" as="h3">
                  {label}
                </Form.Label>
                <button
                  type="button"
                  className="btn btn-sm btn-warning"
                  onClick={() => this.handleEdit(field)}
                  title={`Edit ${field}`}
                >
                  Edit
                </button>
              </div>
              <hr />
              <div
                className="builder__markdown"
                dangerouslySetInnerHTML={{
                  __html:
                    htmlContent ||
                    `<em class="text-muted">No ${field} provided yet</em>`,
                }}
              />
            </>
          ) : (
            <>
              <div className="card-title d-flex flex-row justify-content-between align-items-center">
                <Form.Label className="h5" as="h3">
                  {label}
                </Form.Label>
              </div>
              <hr />
              <div
                className="builder__markdown"
                dangerouslySetInnerHTML={{
                  __html:
                    htmlContent ||
                    `<em class="text-muted">No ${field} provided yet</em>`,
                }}
              />
            </>
          )}
        </div>
      </Form.Group>
    );
  };

  render() {
    const {
      allCodes,
      codeToTerm,
      draftURL,
      hierarchy,
      isEditable,
      isEmptyCodelist,
      metadata,
      resultsHeading,
      searches,
      treeTables,
      visiblePaths,
    } = this.props;

    const { editingField, draftContent } = this.state;
    const fieldLabel = editingField
      ? editingField.charAt(0).toUpperCase() + editingField.slice(1)
      : "";

    return (
      <>
        <Header
          counts={this.counts()}
          isEditable={isEditable}
          metadata={metadata}
        />

        <Row>
          <Sidebar
            counts={this.counts()}
            draftURL={draftURL}
            isEditable={isEditable}
            isEmptyCodelist={isEmptyCodelist}
            searches={searches}
          />

          {isEmptyCodelist ? (
            <Col md="9">
              <EmptyState />
            </Col>
          ) : (
            <Col md="9">
              <Tabs defaultActiveKey="codelist" className="mb-3">
                <Tab eventKey="codelist" title="Codelist">
                  <CodelistTab
                    allCodes={allCodes}
                    codeToStatus={this.state.codeToStatus}
                    codeToTerm={codeToTerm}
                    hierarchy={hierarchy}
                    isEditable={isEditable}
                    resultsHeading={resultsHeading}
                    treeTables={treeTables}
                    updateStatus={this.updateStatus}
                    visiblePaths={visiblePaths}
                  />
                </Tab>
                <Tab
                  eventKey="metadata"
                  title="Metadata"
                  className="max-w-80ch"
                >
                  <MetadataTab
                    handleSaveReferences={this.handleSaveReferences}
                    isEditable={isEditable}
                    references={this.state.metadata.references}
                    renderMetadataField={this.renderMetadataField}
                  />
                </Tab>
              </Tabs>
            </Col>
          )}
        </Row>

        {/* Edit Metadata Modal */}
        <Modal
          animation={false}
          show={editingField !== null}
          onHide={this.handleCancel}
          backdrop="static"
          size="lg"
          aria-labelledby="metadata-edit-modal"
          centered
        >
          <Modal.Header closeButton>
            <Modal.Title id="metadata-edit-modal">
              Edit {fieldLabel}
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Control
              id={`${editingField}`}
              ref={this.modalTextareaRef}
              as="textarea"
              rows={10}
              value={draftContent}
              onChange={this.handleContentChange}
              autoFocus
              onKeyDown={(e) => {
                // Handle Ctrl+Enter for Save
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  this.handleSave();
                }
                // Handle Escape for Cancel
                if (e.key === "Escape") {
                  e.preventDefault();
                  this.handleCancel();
                }
              }}
            />
            <Form.Text className="text-muted mt-2">
              Keyboard shortcuts: Save (CTRL-ENTER) / Cancel (ESC)
            </Form.Text>
          </Modal.Body>
          <Modal.Footer>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={this.handleCancel}
              title={`Cancel ${editingField} edit`}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={this.handleSave}
              title={`Save ${editingField}`}
            >
              Save
            </button>
          </Modal.Footer>
        </Modal>
      </>
    );
  }
}
