import PropTypes from "prop-types";
import React, { useRef } from "react";
import {
  Button,
  ButtonGroup,
  Col,
  Form,
  ListGroup,
  OverlayTrigger,
  Row,
  Tooltip,
} from "react-bootstrap";
import Modal from "react-bootstrap/Modal";
import { getCookie } from "../_utils";
import Filter from "./Filter";
import MoreInfoModal from "./MoreInfoModal";
import Search from "./Search";
import SearchForm from "./SearchForm";
import Summary from "./Summary";
import TreeTables from "./TreeTables";
import Version from "./Version";

class CodelistBuilder extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      codeToStatus: props.codeToStatus,
      expandedCompatibleReleases: false,
      moreInfoModalCode: null,
      showConfirmDiscardModal: false,
      updateQueue: [],
      updating: false,
    };

    this.updateStatus = props.isEditable ? this.updateStatus.bind(this) : null;
    this.showMoreInfoModal = this.showMoreInfoModal.bind(this);
    this.hideMoreInfoModal = this.hideMoreInfoModal.bind(this);
    this.ManagementForm = this.ManagementForm.bind(this);
    this.setShowConfirmDiscardModal =
      this.setShowConfirmDiscardModal.bind(this);
    this.renderConfirmDiscardModal = this.renderConfirmDiscardModal.bind(this);
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

  updateStatus(code, status) {
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
    fetch(this.props.updateURL, {
      method: "POST",
      credentials: "include",
      mode: "same-origin",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
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

  showMoreInfoModal(code) {
    this.setState({ moreInfoModalCode: code });
  }

  hideMoreInfoModal() {
    this.setState({ moreInfoModalCode: null });
  }

  setShowConfirmDiscardModal(value) {
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
    this.props.allCodes.forEach((code) => {
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
        <Row>
          <Col md="3">
            {this.props.isEditable && (
              <>
                <this.ManagementForm complete={this.complete()} />
                <hr />
              </>
            )}

            <h3 className="h6">Summary</h3>
            <Filter filter={this.props.filter} />
            <Summary counts={this.counts()} />
            <hr />

            {this.props.searches.length > 0 && (
              <>
                <h3 className="h6">Searches</h3>
                <ListGroup>
                  {this.props.searches.map((search) => (
                    <Search key={search.url} search={search} />
                  ))}
                  {this.props.searches.some((search) => search.active) ? (
                    <ListGroup.Item
                      action
                      className="py-1 px-2 font-italic"
                      href={encodeURI(this.props.draftURL)}
                    >
                      show all
                    </ListGroup.Item>
                  ) : null}
                </ListGroup>
                <hr />
              </>
            )}

            {this.props.isEditable && (
              <>
                <h3 className="h6">New search</h3>
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

            <h3 className="h6">Versions</h3>
            <ul className="pl-3">
              {this.props.versions.map((version) => (
                <Version key={version.tag_or_hash} version={version} />
              ))}
            </ul>
          </Col>

          <Col md="9" className="overflow-auto">
            <h3 className="h4">{this.props.resultsHeading}</h3>
            <hr />
            <TreeTables
              codeToStatus={this.state.codeToStatus}
              codeToTerm={this.props.codeToTerm}
              hierarchy={this.props.hierarchy}
              showMoreInfoModal={this.showMoreInfoModal}
              treeTables={this.props.treeTables}
              updateStatus={this.updateStatus}
              visiblePaths={this.props.visiblePaths}
            />
          </Col>
        </Row>

        {moreInfoModal}
      </>
    );
  }

  ManagementForm(props) {
    const { complete } = props;

    const management_form = useRef();
    const confirmDiscardModal =
      this.state.showConfirmDiscardModal &&
      this.renderConfirmDiscardModal(management_form);

    const handleConfirmMsg = (e) => {
      e.preventDefault();
      this.setShowConfirmDiscardModal(true);
    };

    return (
      <>
        <Form method="POST" ref={management_form}>
          <Form.Control
            id="csrfmiddlewaretoken"
            name="csrfmiddlewaretoken"
            type="hidden"
            value={getCookie("csrftoken")}
          />
          <Form.Control id="action" name="action" type="hidden" value="" />
          <ButtonGroup
            aria-label="Codelist actions"
            className="d-block"
            vertical
          >
            {complete ? (
              <Button
                block
                name="action"
                type="submit"
                value="save-for-review"
                variant="outline-primary"
              >
                Save for review
              </Button>
            ) : (
              <>
                <OverlayTrigger
                  placement="right"
                  overlay={
                    <Tooltip id="disabled-review">
                      You cannot save for review until all search results are
                      included or excluded
                    </Tooltip>
                  }
                >
                  <Button block disabled variant="outline-secondary">
                    Save for review
                  </Button>
                </OverlayTrigger>
              </>
            )}
            <Button
              block
              name="action"
              type="submit"
              value="save-draft"
              variant="outline-primary"
            >
              Save draft
            </Button>
            <Button
              block
              type="button"
              variant="outline-primary"
              onClick={handleConfirmMsg}
            >
              Discard
            </Button>
          </ButtonGroup>
        </Form>
        {confirmDiscardModal}
      </>
    );
  }

  renderMoreInfoModal(code) {
    const included = this.props.allCodes.filter(
      (c) => this.state.codeToStatus[c] === "+",
    );
    const excluded = this.props.allCodes.filter(
      (c) => this.state.codeToStatus[c] === "-",
    );
    const significantAncestors = this.props.hierarchy.significantAncestors(
      code,
      included,
      excluded,
    );

    const includedAncestorsText = significantAncestors.includedAncestors
      .map((code) => `${this.props.codeToTerm[code]} (${code})`)
      .join(", ");

    const excludedAncestorsText = significantAncestors.excludedAncestors
      .map((code) => `${this.props.codeToTerm[code]} (${code})`)
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

  renderConfirmDiscardModal(form) {
    const handleConfirm = () => {
      form.current[1].value = "discard";
      form.current.submit();
    };

    const handleCancel = () => {
      this.setShowConfirmDiscardModal(false);
    };

    return (
      <Modal centered show={this.state.showConfirmDiscardModal}>
        <Modal.Header>
          Are you sure you want to discard this draft?
        </Modal.Header>
        <Modal.Body>
          <Button className="mr-2" onClick={handleConfirm} variant="primary">
            Yes
          </Button>
          <Button onClick={handleCancel} variant="secondary">
            No
          </Button>
        </Modal.Body>
      </Modal>
    );
  }
}

export default CodelistBuilder;

CodelistBuilder.propTypes = {
  allCodes: PropTypes.arrayOf(PropTypes.string),
  codeToStatus: PropTypes.objectOf(PropTypes.string),
  codeToTerm: PropTypes.objectOf(PropTypes.string),
  draftURL: PropTypes.string,
  filter: PropTypes.string,
  hierarchy: PropTypes.shape({
    ancestorMap: PropTypes.shape(),
    childMap: PropTypes.objectOf(PropTypes.array),
    nodes: PropTypes.shape(),
    parentMap: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)),
    updateCodeToStatus: PropTypes.func,
    significantAncestors: PropTypes.func,
  }),
  isEditable: PropTypes.bool,
  metadata: PropTypes.shape({
    codelist_full_slug: PropTypes.string,
    coding_system_name: PropTypes.string,
    hash: PropTypes.string,
    organisation_name: PropTypes.string,
    coding_system_release: PropTypes.shape({
      release_name: PropTypes.string,
      valid_from: PropTypes.string,
    }),
  }),
  resultsHeading: PropTypes.string,
  searches: PropTypes.arrayOf(
    PropTypes.shape({
      active: PropTypes.bool,
      delete_url: PropTypes.string,
      term_or_code: PropTypes.string,
      url: PropTypes.string,
    }),
  ),
  searchURL: PropTypes.string,
  treeTables: PropTypes.arrayOf(PropTypes.array),
  updateURL: PropTypes.string,
  versions: PropTypes.arrayOf(
    PropTypes.shape({
      current: PropTypes.bool,
      status: PropTypes.string,
      tag_or_hash: PropTypes.string,
      url: PropTypes.string,
    }),
  ),
  visiblePaths: PropTypes.object,
};
