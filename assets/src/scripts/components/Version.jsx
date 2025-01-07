import PropTypes from "prop-types";
import React from "react";
import { Badge } from "react-bootstrap";

function Version({ version }) {
  return (
    <li>
      {version.current ? (
        version.tag_or_hash
      ) : (
        <a href={encodeURI(version.url)}>{version.tag_or_hash}</a>
      )}

      {version.status === "draft" ? (
        <Badge className="ml-1" variant="primary">
          Draft
        </Badge>
      ) : null}

      {version.status === "under review" ? (
        <Badge className="ml-1" variant="primary">
          Review
        </Badge>
      ) : null}
    </li>
  );
}

export default Version;

Version.propTypes = {
  version: PropTypes.shape({
    current: PropTypes.bool,
    status: PropTypes.string,
    tag_or_hash: PropTypes.string,
    url: PropTypes.string,
  }),
};
