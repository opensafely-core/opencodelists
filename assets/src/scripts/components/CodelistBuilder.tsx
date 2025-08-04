import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import React from "react";
import { Col, Row, Tab, Tabs } from "react-bootstrap";
import type { SelectCallback } from "react-bootstrap/esm/helpers";
import type Hierarchy from "../_hierarchy";
import { getCookie } from "../_utils";
import type { Code, METADATA, PageData, Status } from "../types";
import EmptyState from "./EmptyState";
import CodelistTab from "./Layout/CodelistTab";
import Header from "./Layout/Header";
import MetadataTab from "./Layout/MetadataTab";
import Sidebar from "./Layout/Sidebar";

interface CodelistBuilderProps extends PageData {
  hierarchy: Hierarchy;
  metadata: METADATA;
}
type TabKey = "codelist" | "metadata";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnMount: false,
      refetchOnReconnect: false,
      refetchOnWindowFocus: false,
      staleTime: "static",
    },
  },
});

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

function getTabFromHash(): TabKey {
  const hash = window.location.hash.replace("#", "");
  return hash === "metadata" ? "metadata" : "codelist";
}

export default class CodelistBuilder extends React.Component<
  CodelistBuilderProps,
  {
    codeToStatus: PageData["codeToStatus"];
    expandedCompatibleReleases: boolean;
    updateQueue: string[][];
    updating: boolean;
    activeTab: TabKey;
  }
> {
  constructor(props: CodelistBuilderProps) {
    super(props);

    this.state = {
      codeToStatus: props.codeToStatus,
      expandedCompatibleReleases: false,
      updateQueue: [],
      updating: false,
      activeTab: getTabFromHash(),
    };

    this.updateStatus = props.isEditable
      ? this.updateStatus.bind(this)
      : () => null;
    this.toggleExpandedCompatibleReleases =
      this.toggleExpandedCompatibleReleases.bind(this);
  }

  handleTabSelect: SelectCallback = (key) => {
    if (key === "metadata" || key === "codelist") {
      this.setState({ activeTab: key });
      window.history.pushState(null, "", `#${key}`);
    }
  };

  componentDidMount() {
    window.addEventListener("popstate", this.handlePopState);
  }

  componentWillUnmount() {
    window.removeEventListener("popstate", this.handlePopState);
  }

  handlePopState = () => {
    this.setState({ activeTab: getTabFromHash() });
  };

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

    return (
      <QueryClientProvider client={queryClient}>
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
              <Tabs
                activeKey={this.state.activeTab}
                onSelect={this.handleTabSelect}
                className="mb-3"
              >
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
                  <MetadataTab />
                </Tab>
              </Tabs>
            </Col>
          )}
        </Row>
        <ReactQueryDevtools />
      </QueryClientProvider>
    );
  }
}
