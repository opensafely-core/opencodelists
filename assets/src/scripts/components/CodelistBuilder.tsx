import React from "react";
import { Col, Row } from "react-bootstrap";
import Hierarchy from "../_hierarchy";
import { getCookie } from "../_utils";
import { Code, PageData, Status } from "../types";
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
  private _isMounted: boolean = false;
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

  componentDidMount() {
    // This is required for testing.  See other uses for _isMounted for explanation.
    this._isMounted = true;
  }

  componentWillUnmount() {
    this._isMounted = false;
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
        if (!this._isMounted) {
          // In tests the compenent is unmounted, and this may happen before
          // the promise is resolved.  Calling setState on an unmounted
          // component is a no-op and may indicate a memory leak, so it triggers
          // a warning.  Exiting early here prevents that warning.
          return;
        }

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
    let counts = {
      "?": 0,
      "!": 0,
      "+": 0,
      "(+)": 0,
      "-": 0,
      "(-)": 0,
      total: 0,
    };
    this.props.allCodes.forEach((code) => {
      const status = this.state.codeToStatus[code];
      if (["?", "!", "+", "(+)", "-", "(-)"].includes(status)) {
        counts[status] += 1;
        counts["total"] += 1;
      }
    });
    return counts;
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

    return (
      <>
        <Row>
          <Col md="3">
            {isEditable && <ManagementForm counts={this.counts()} />}

            <h3 className="h6">Summary</h3>
            <Filter filter={filter} />
            <Summary counts={this.counts()} />
            <hr />

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
        </Row>
      </>
    );
  }
}
