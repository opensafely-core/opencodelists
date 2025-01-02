import React, { useRef } from "react";
import { Button } from "react-bootstrap";
import Modal from "react-bootstrap/Modal";
import Hierarchy from "../_hierarchy";
import { getCookie } from "../_utils";
import Filter, { FilterProps } from "./Filter";
import MoreInfoModal from "./MoreInfoModal";
import Search, { SearchProps } from "./Search";
import SearchForm, { SearchFormProps } from "./SearchForm";
import Summary from "./Summary";
import { TreeProps } from "./Tree";
import TreeTables, { TreeTableProps } from "./TreeTables";
import Version, { VersionProps } from "./Version";

interface CodingSystemReleaseProps {
  release_name: string;
  valid_from: string;
}

interface MetadataProps {
  codelist_full_slug: string;
  coding_system_name: string;
  hash: string;
  organisation_name: string;
  coding_system_release: CodingSystemReleaseProps;
}

interface CodelistBuilderProps {
  allCodes: string[];
  codeToStatus: TreeProps["codeToStatus"];
  codeToTerm: TreeProps["codeToTerm"];
  draftURL: string;
  filter: FilterProps["filter"];
  hierarchy: Hierarchy;
  isEditable: boolean;
  metadata: MetadataProps;
  resultsHeading: string;
  searches: SearchProps["search"][];
  searchURL: SearchFormProps["searchURL"];
  treeTables: TreeTableProps["treeTables"];
  updateURL: string;
  versions: VersionProps["version"][];
  visiblePaths: TreeProps["visiblePaths"];
}

class CodelistBuilder extends React.Component<
  CodelistBuilderProps,
  {
    codeToStatus: CodelistBuilderProps["codeToStatus"];
    expandedCompatibleReleases: boolean;
    moreInfoModalCode: string | null;
    showConfirmDiscardModal: boolean;
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
      moreInfoModalCode: null,
      showConfirmDiscardModal: false,
      updateQueue: [],
      updating: false,
    };

    this.updateStatus = props.isEditable
      ? this.updateStatus.bind(this)
      : () => null;
    this.showMoreInfoModal = this.showMoreInfoModal.bind(this);
    this.hideMoreInfoModal = this.hideMoreInfoModal.bind(this);
    this.ManagementForm = this.ManagementForm.bind(this);
    this.setShowConfirmDiscardModal =
      this.setShowConfirmDiscardModal.bind(this);
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

  updateStatus(code: string, status: string) {
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
    const requestHeaders: HeadersInit = new Headers();
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

  showMoreInfoModal(code: string) {
    this.setState({ moreInfoModalCode: code });
  }

  hideMoreInfoModal() {
    this.setState({ moreInfoModalCode: null });
  }

  setShowConfirmDiscardModal(value: boolean) {
    this.setState({ showConfirmDiscardModal: value });
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
    this.props.allCodes.forEach((code: string) => {
      const status = this.state.codeToStatus[code];
      if (["?", "!", "+", "(+)", "-", "(-)"].includes(status)) {
        counts[status] += 1;
        counts["total"] += 1;
      }
    });
    return counts;
  }

  complete() {
    const counts = this.counts();
    return counts["!"] === 0 && counts["?"] === 0;
  }

  render() {
    const moreInfoModal =
      this.state.moreInfoModalCode &&
      this.renderMoreInfoModal(this.state.moreInfoModalCode);

    return (
      <>
        <div className="row">
          <div className="col-md-3">
            {this.props.isEditable && (
              <>
                <this.ManagementForm complete={this.complete()} />
                <hr />
              </>
            )}

            <h6>Summary</h6>
            <Filter filter={this.props.filter} />
            <Summary counts={this.counts()} />
            <hr />

            {this.props.searches.length > 0 && (
              <>
                <h6>Searches</h6>
                <div className="list-group">
                  {this.props.searches.map((search) => (
                    <Search key={search.url} search={search} />
                  ))}
                  {this.props.searches.some((search) => search.active) ? (
                    <a
                      className="list-group-item list-group-item-action py-1 font-italic"
                      href={encodeURI(this.props.draftURL)}
                    >
                      show all
                    </a>
                  ) : null}
                </div>
                <hr />
              </>
            )}

            {this.props.isEditable && (
              <>
                <h6>New search</h6>
                <SearchForm
                  codingSystemName={this.props.metadata.coding_system_name}
                  searchURL={this.props.searchURL}
                />
                <hr />
              </>
            )}

            <dl>
              <dt>Coding system</dt>
              <dd>{this.props.metadata.coding_system_name}</dd>

              <dt>Coding system release</dt>
              <dd>
                {this.props.metadata.coding_system_release.release_name}
                {this.props.metadata.coding_system_release.valid_from ? (
                  <>({this.props.metadata.coding_system_release.valid_from})</>
                ) : null}
              </dd>

              {this.props.metadata.organisation_name ? (
                <>
                  <dt>Organisation</dt>
                  <dd>{this.props.metadata.organisation_name}</dd>
                </>
              ) : null}

              <dt>Codelist ID</dt>
              <dd className="text-break">
                {this.props.metadata.codelist_full_slug}
              </dd>

              <dt>ID</dt>
              <dd>{this.props.metadata.hash}</dd>
            </dl>
            <hr />

            <h6>Versions</h6>
            <ul className="pl-3">
              {this.props.versions.map((version) => (
                <Version key={version.tag_or_hash} version={version} />
              ))}
            </ul>
          </div>

          <div className="col-md-9 overflow-auto">
            <h4>{this.props.resultsHeading}</h4>
            <hr />
            <TreeTables
              codeToStatus={this.state.codeToStatus}
              codeToTerm={this.props.codeToTerm}
              hierarchy={this.props.hierarchy}
              showMoreInfoModal={this.showMoreInfoModal}
              toggleVisibility={() => null}
              treeTables={this.props.treeTables}
              updateStatus={this.updateStatus}
              visiblePaths={this.props.visiblePaths}
            />
          </div>
        </div>

        {moreInfoModal}
      </>
    );
  }

  ManagementForm(props: { complete: boolean }) {
    const { complete } = props;
    return (
      <>
        <form method="POST">
          <input
            id="csrfmiddlewaretoken"
            name="csrfmiddlewaretoken"
            type="hidden"
            value={getCookie("csrftoken")}
          />
          <input id="action" name="action" type="hidden" value="" />
          <div className="btn-group-vertical btn-block" role="group">
            {complete ? (
              <button
                className="btn btn-outline-primary btn-block"
                name="action"
                type="submit"
                value="save-for-review"
              >
                Save for review
              </button>
            ) : (
              <button
                aria-disabled="true"
                className="disabled btn btn-outline-secondary btn-block"
                data-toggle="tooltip"
                title="You cannot save for review until all search results are included or excluded"
                type="button"
              >
                Save for review
              </button>
            )}
            <button
              className="btn btn-outline-primary btn-block"
              name="action"
              type="submit"
              value="save-draft"
            >
              Save draft
            </button>
            <Button
              block
              type="button"
              variant="outline-primary"
              onClick={() => this.setShowConfirmDiscardModal(true)}
            >
              Discard
            </Button>
          </div>
        </form>
        <DiscardModal
          show={this.state.showConfirmDiscardModal}
          handleCancel={() => this.setShowConfirmDiscardModal(false)}
        />
      </>
    );
  }

  renderMoreInfoModal(code: string) {
    const included = this.props.allCodes.filter(
      (c: string) => this.state.codeToStatus[c] === "+",
    );
    const excluded = this.props.allCodes.filter(
      (c: string) => this.state.codeToStatus[c] === "-",
    );
    const significantAncestors = this.props.hierarchy.significantAncestors(
      code,
      included,
      excluded,
    );

    const includedAncestorsText = significantAncestors.includedAncestors
      .map((code: string) => `${this.props.codeToTerm[code]} (${code})`)
      .join(", ");

    const excludedAncestorsText = significantAncestors.excludedAncestors
      .map((code: string) => `${this.props.codeToTerm[code]} (${code})`)
      .join(", ");

    return (
      <MoreInfoModal
        code={code}
        excludedAncestorsText={excludedAncestorsText}
        hideModal={this.hideMoreInfoModal}
        includedAncestorsText={includedAncestorsText}
        status={this.state.codeToStatus[code]}
        term={this.props.codeToTerm[code]}
      />
    );
  }
}

function DiscardModal({
  show,
  handleCancel,
}: { show: boolean; handleCancel: () => void }) {
  return (
    <Modal centered show={show}>
      <Modal.Header>Are you sure you want to discard this draft?</Modal.Header>
      <Modal.Body>
        <form className="mb-2" method="POST">
          <input
            id="csrfmiddlewaretoken"
            name="csrfmiddlewaretoken"
            type="hidden"
            value={getCookie("csrftoken")}
          />
          <input id="action" name="action" type="hidden" value="discard" />
          <Button
            className="mr-2"
            type="submit"
            value="discard"
            variant="primary"
          >
            Yes
          </Button>
        </form>
        <Button variant="secondary" onClick={handleCancel}>
          No
        </Button>
      </Modal.Body>
    </Modal>
  );
}

export default CodelistBuilder;
