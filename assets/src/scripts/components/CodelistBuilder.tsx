import React from "react";
import { Col, Row } from "react-bootstrap";
import Hierarchy from "../_hierarchy";
import { getCookie } from "../_utils";
import { Code, PageData, Status } from "../types";
import EmptyState from "./EmptyState";
import Filter from "./Filter";
import ManagementForm from "./ManagementForm";
import Search from "./Search";
import SearchForm from "./SearchForm";
import Summary from "./Summary";
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
      filter,
      hierarchy,
      isEditable,
      metadata,
      resultsHeading,
      searches,
      searchURL,
      treeTables,
      visiblePaths,
    } = this.props;

    const isEmpty =
      searches.length === 0 &&
      treeTables.length === 0 &&
      resultsHeading ===
        "Start building your codelist by searching for a term or a code";

    return (
      <>
        <Row>
          <Col md="3">
            {isEditable && <ManagementForm counts={this.counts()} />}

            {!isEmpty ? (
              <>
                <Filter filter={filter} />
                <h3 className="h6">Summary</h3>
                <Summary counts={this.counts()} />
                <hr />
              </>
            ) : null}

            {searches.length > 0 && (
              <Search draftURL={draftURL} searches={searches} />
            )}

            {isEditable && (
              <>
                <h3 className="h6">New search</h3>
                <SearchForm
                  codingSystemName={metadata.coding_system_name}
                  searchURL={searchURL}
                />
                <hr />
              </>
            )}

            <dl>
              <dt>Coding system</dt>
              <dd>{metadata.coding_system_name}</dd>

              <dt>Coding system release</dt>
              <dd>
                {metadata.coding_system_release.release_name}
                {metadata.coding_system_release.valid_from ? (
                  <>({metadata.coding_system_release.valid_from})</>
                ) : null}
              </dd>

              {metadata.organisation_name ? (
                <>
                  <dt>Organisation</dt>
                  <dd>{metadata.organisation_name}</dd>
                </>
              ) : null}

              <dt>Codelist ID</dt>
              <dd className="text-break">{metadata.codelist_full_slug}</dd>

              <dt>ID</dt>
              <dd>{metadata.hash}</dd>
            </dl>
            <hr />

            <h3 className="h6">Versions</h3>
            <ul className="pl-3">
              {this.props.versions.map((version) => (
                <Version key={version.tag_or_hash} version={version} />
              ))}
            </ul>
          </Col>

          {isEmpty ? (
            <Col md="9">
              <EmptyState />
            </Col>
          ) : (
            <Col md="9" className="overflow-auto">
              <h3 className="h4">{resultsHeading}</h3>
              <hr />
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
            </Col>
          )}
        </Row>
      </>
    );
  }
}
