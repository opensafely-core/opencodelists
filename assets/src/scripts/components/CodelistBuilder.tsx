import React from "react";
import { Col, Row } from "react-bootstrap";
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
import Version from "./Version";

interface CodelistBuilderProps extends PageData {
  hierarchy: Hierarchy;
}

export default class CodelistBuilder extends React.Component<
  CodelistBuilderProps,
  {
    codeToStatus: PageData["codeToStatus"];
    expandedCompatibleReleases: boolean;
    updateQueue: string[][];
    updating: boolean;
  }
> {
  constructor(props: CodelistBuilderProps) {
    super(props);

    this.state = {
      codeToStatus: props.codeToStatus,
      expandedCompatibleReleases: false,
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

            <Version versions={this.props.versions} />
          </Col>

          {isEmptyCodelist ? (
            <Col md="9">
              <EmptyState />
            </Col>
          ) : (
            <Col md="9" className="overflow-auto">
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
            </Col>
          )}
        </Row>
      </>
    );
  }
}
