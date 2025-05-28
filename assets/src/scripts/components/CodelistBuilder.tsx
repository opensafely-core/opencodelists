import React from "react";
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

type MetadataFieldName = "description" | "methodology";
interface MetadataField {
  text: string;
  html: string;
}
interface MetadataProps {
  description: MetadataField;
  methodology: MetadataField;
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
  constructor(props: CodelistBuilderProps) {
    super(props);

    this.state = {
      codeToStatus: props.codeToStatus,
      expandedCompatibleReleases: false,
      metadata: {
        description: {
          text: props.metadata.description.text,
          html: props.metadata.description.html,
        },
        methodology: {
          text: props.metadata.methodology.text,
          html: props.metadata.methodology.html,
        },
      },
      updateQueue: [],
      updating: false,
    };

    this.updateStatus = props.isEditable
      ? this.updateStatus.bind(this)
      : () => null;
    this.toggleExpandedCompatibleReleases =
      this.toggleExpandedCompatibleReleases.bind(this);
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
    const requestHeaders = new Headers();
    requestHeaders.append("Accept", "application/json");
    requestHeaders.append("Content-Type", "application/json");

    const csrfCookie = getCookie("csrftoken");
    if (csrfCookie) {
      requestHeaders.append("X-CSRFToken", csrfCookie);
    }

    fetch(this.props.updateURL, {
      method: "POST",
      credentials: "include",
      mode: "same-origin",
      headers: requestHeaders,
      body: JSON.stringify({ updates: this.state.updateQueue }),
    })
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

  renderMetadataField = (field: MetadataFieldName) => {
    const label = field.charAt(0).toUpperCase() + field.slice(1);
    const htmlContent = this.state.metadata[field].html;

    return (
      <Form.Group className="card" controlId={field}>
        <div className="card-body">
          <div className="card-title">
            <Form.Label className="h5" as="h3">
              {label}
            </Form.Label>
          </div>
          <hr />

          <style>{` .markdown p:last-child { margin-bottom: 0; } `}</style>
          <div
            className="markdown"
            dangerouslySetInnerHTML={{
              __html:
                htmlContent ||
                `<em class="text-muted">No ${field} provided yet</em>`,
            }}
          />
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
                  <p style={{ fontStyle: "italic" }}>
                    Users have found it helpful to record their decision
                    strategy as they build their codelist. Text added here will
                    be ready for you to edit before you publish the codelist.
                  </p>
                  <Form noValidate>
                    {this.renderMetadataField("description")}
                    {this.renderMetadataField("methodology")}
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
