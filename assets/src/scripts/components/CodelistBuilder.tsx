import React, { useState } from "react";
import { Col, Form, Row, Tab, Tabs } from "react-bootstrap";
import Hierarchy from "../_hierarchy";
import { getCookie } from "../_utils";
import { Code, PageData, Status } from "../types";
import EmptySearch from "./EmptySearch";
import EmptyState from "./EmptyState";
import ManagementForm from "./ManagementForm";
import Metadata from "./Metadata";
import Search from "./Search";
import SearchForm from "./SearchForm";
import Summary from "./Summary";
import Title from "./Title";
import TreeTables from "./TreeTables";
import Versions from "./Versions";

// The metadata contains a list of "references" which consist of a
// text display value, and an underlying link url
interface Reference {
  text: string;
  url: string;
}

interface ReferenceFormProps {
  reference?: Reference;
  onCancel: () => void;
  onSave: (reference: Reference) => void;
}

/**
 * Form component for adding or editing reference links in a codelist's metadata.
 * @param reference - Optional existing reference to edit, or blank if creating a new one
 * @param onCancel - Callback when user cancels editing
 * @param onSave - Callback when user saves changes, receives updated reference object
 */
function ReferenceForm({
  reference = { text: "", url: "" },
  onCancel,
  onSave,
}: ReferenceFormProps) {
  const textInputRef = React.useRef<HTMLInputElement>(null);
  const urlInputRef = React.useRef<HTMLInputElement>(null);

  const handleSave = () => {
    onSave({
      text: textInputRef.current?.value || "",
      url: urlInputRef.current?.value || "",
    });
  };

  return (
    <div className="card p-3">
      <Form.Group className="mb-2">
        <Form.Label>Text</Form.Label>
        <Form.Control
          ref={textInputRef}
          type="text"
          defaultValue={reference.text}
          placeholder="Text to display"
        />
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>URL</Form.Label>
        <Form.Control
          ref={urlInputRef}
          type="url"
          defaultValue={reference.url}
          placeholder="URL to link to"
        />
      </Form.Group>
      <div className="mt-2 d-flex flex-row justify-content-end">
        <button
          type="button"
          className="btn btn-secondary btn-sm m-1"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          type="button"
          className="btn btn-primary btn-sm m-1"
          onClick={handleSave}
        >
          Save
        </button>
      </div>
    </div>
  );
}
interface ReferenceListProps {
  references: Reference[];
  onSave: (references: Reference[]) => void;
}

/**
 * Displays and manages a list of reference links in the codelist metadata.
 * Allows adding, editing, and deleting references, with each reference having
 * display text and a URL. Uses ReferenceForm component for editing.
 * @param references - Array of current references
 * @param onSave - Callback when references are modified, receives updated array
 */
function ReferenceList({ references, onSave }: ReferenceListProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const handleDelete = (index: number) => {
    const newReferences = [...references];
    newReferences.splice(index, 1);
    onSave(newReferences);
  };

  const handleEdit = (index: number) => {
    setEditingIndex(index);
  };

  const handleAdd = () => {
    setEditingIndex(-1);
  };

  const handleSaveForm = (reference: Reference) => {
    const newReferences = [...references];
    if (editingIndex === -1) {
      newReferences.push(reference);
    } else if (editingIndex !== null) {
      newReferences[editingIndex] = reference;
    }

    onSave(newReferences);
    setEditingIndex(null);
  };

  const handleCancel = () => {
    setEditingIndex(null);
  };

  return (
    <div className="card">
      <div className="card-body">
        <h3 className="h5 card-title">References</h3>
        <hr />
        <p className="font-italic">
          Sometimes it's useful to provide links, for example links to
          algorithms, methodologies or papers that are relevant to this
          codelist. They can be added here:
        </p>
        <ul>
          {references.map((ref, index) => (
            <li key={index} className="mb-2">
              {editingIndex === index ? (
                <ReferenceForm
                  reference={ref}
                  onCancel={handleCancel}
                  onSave={handleSaveForm}
                />
              ) : (
                <div className="d-flex align-items-center">
                  <a href={ref.url} target="_blank" rel="noopener noreferrer">
                    {ref.text}
                  </a>
                  <button
                    type="button"
                    className="btn btn-sm btn-warning ml-2"
                    onClick={() => handleEdit(index)}
                    title="Edit reference"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-danger ml-2"
                    onClick={() => handleDelete(index)}
                    title="Delete reference"
                  >
                    Delete
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
        {editingIndex === -1 ? (
          <ReferenceForm onCancel={handleCancel} onSave={handleSaveForm} />
        ) : (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={handleAdd}
          >
            {references.length === 0
              ? "Add a reference"
              : "Add another reference"}
          </button>
        )}
      </div>
    </div>
  );
}

type MetadataFieldName = "description" | "methodology";
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
  }
> {
  private textareaRefs: {
    description: React.RefObject<HTMLTextAreaElement>;
    methodology: React.RefObject<HTMLTextAreaElement>;
  };
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
    };

    this.updateStatus = props.isEditable
      ? this.updateStatus.bind(this)
      : () => null;
    this.toggleExpandedCompatibleReleases =
      this.toggleExpandedCompatibleReleases.bind(this);
    this.textareaRefs = {
      description: React.createRef(),
      methodology: React.createRef(),
    };
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
    this.setState(
      (prevState) => ({
        metadata: {
          ...prevState.metadata,
          [field]: {
            ...prevState.metadata[field],
            isEditing: true,
          },
        },
      }),
      () => {
        // Auto-focus the textarea after clicking edit
        setTimeout(() => {
          this.textareaRefs[field].current?.focus();
        }, 0);
      },
    );
  };

  handleCancel = (field: MetadataFieldName) => {
    this.setState((prevState) => ({
      metadata: {
        ...prevState.metadata,
        [field]: {
          ...prevState.metadata[field],
          isEditing: false,
        },
      },
    }));
  };

  handleSave = async (field: MetadataFieldName) => {
    const updateBody = {
      description:
        field === "description"
          ? this.textareaRefs[field].current?.value
          : this.state.metadata.description.text,
      methodology:
        field === "methodology"
          ? this.textareaRefs[field].current?.value
          : this.state.metadata.methodology.text,
    };

    const fetchOptions = getFetchOptions(updateBody);

    try {
      fetch(this.props.updateURL, fetchOptions)
        .then((response) => response.json())
        .then((data) => {
          // We rely on the backend rendering the html from the updated markdown
          // so we need to update the state here with the response from the server
          this.setState(() => ({ metadata: data.metadata }));
        });
    } catch (error) {
      console.error(`Failed to save ${field}:`, error);
    }
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
    const isEditing = this.state.metadata[field].isEditing;
    const draftContent = this.state.metadata[field].text;

    return (
      <Form.Group className={`card ${field}`} controlId={field}>
        <div className="card-body">
          <div className="card-title d-flex flex-row justify-content-between align-items-center">
            <Form.Label className="h5" as="h3">
              {label}
            </Form.Label>
            {isEditing ? (
              <div>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => this.handleSave(field)}
                  title={`Save ${field}`}
                >
                  Save
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm ml-2"
                  onClick={() => this.handleCancel(field)}
                  title={`Cancel ${field} edit`}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="btn btn-sm btn-warning"
                onClick={() => this.handleEdit(field)}
                title={`Edit ${field}`}
              >
                Edit
              </button>
            )}
          </div>
          <hr />
          {isEditing ? (
            <>
              <Form.Control
                ref={this.textareaRefs[field]}
                as="textarea"
                rows={5}
                defaultValue={draftContent}
                onFocus={() => this.textareaRefs[field].current?.focus()}
                onKeyDown={(e) => {
                  // Handle Ctrl+Enter for Save
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    this.handleSave(field);
                  }
                  // Handle Escape for Cancel
                  if (e.key === "Escape") {
                    e.preventDefault();
                    this.handleCancel(field);
                  }
                }}
              />
              <Form.Text className="text-muted">
                If you make changes, please remember to click Save (shortcut:
                CTRL-ENTER) to keep them or Cancel (shortcut: ESC) to discard.
              </Form.Text>
            </>
          ) : (
            <>
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
      searchURL,
      treeTables,
      visiblePaths,
    } = this.props;

    return (
      <>
        <div className="border-bottom mb-3 pb-3">
          <div className="d-flex flex-row justify-content-between gap-2 mb-2">
            <Title name={metadata.codelist_name} />
            {isEditable && <ManagementForm counts={this.counts()} />}
          </div>
          <Metadata data={metadata} />
        </div>
        <Row>
          <Col className="builder__sidebar" md="3">
            {!isEmptyCodelist && (
              <Summary counts={this.counts()} draftURL={draftURL} />
            )}

            {searches.length > 0 && (
              <Search
                draftURL={draftURL}
                isEditable={isEditable}
                searches={searches}
              />
            )}

            {isEditable && (
              <SearchForm
                codingSystemName={metadata.coding_system_name}
                searchURL={searchURL}
              />
            )}

            <Versions versions={this.props.versions} />
          </Col>

          {isEmptyCodelist ? (
            <Col md="9">
              <EmptyState />
            </Col>
          ) : (
            <Col md="9">
              <Tabs defaultActiveKey="codelist" className="mb-3">
                <Tab eventKey="codelist" title="Codelist">
                  <h3 className="h4">{resultsHeading}</h3>
                  <hr />
                  {treeTables.length > 0 ? (
                    <TreeTables
                      allCodes={allCodes}
                      codeToStatus={this.state.codeToStatus}
                      codeToTerm={codeToTerm}
                      hierarchy={hierarchy}
                      isEditable={isEditable}
                      toggleVisibility={() => null}
                      treeTables={treeTables}
                      updateStatus={this.updateStatus}
                      visiblePaths={visiblePaths}
                    />
                  ) : (
                    <EmptySearch />
                  )}
                </Tab>
                <Tab
                  eventKey="metadata"
                  title="Metadata"
                  style={{ maxWidth: "80ch" }}
                >
                  <p className="font-italic">
                    Users have found it helpful to record their decision
                    strategy as they build their codelist. Text added here will
                    be ready for you to edit before you publish the codelist.
                  </p>
                  <Form noValidate>
                    {this.renderMetadataField("description")}
                    {this.renderMetadataField("methodology")}
                    <ReferenceList
                      references={this.state.metadata.references}
                      onSave={this.handleSaveReferences}
                    />
                  </Form>
                </Tab>
              </Tabs>
            </Col>
          )}
        </Row>
      </>
    );
  }
}
