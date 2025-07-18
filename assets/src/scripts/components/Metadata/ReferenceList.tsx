import React from "react";
import { PageData, Reference } from "../../types";
import ReferenceForm from "./ReferenceForm";

interface ReferenceListProps {
  isEditable: PageData["isEditable"];
  references: Reference[];
  onSave: (references: Reference[]) => void;
}

interface ReferenceListState {
  editingIndex: number | null;
}
/**
 * Displays and manages a list of reference links in the codelist metadata.
 * Allows adding, editing, and deleting references, with each reference having
 * display text and a URL. Uses ReferenceForm component for editing.
 * @param references - Array of current references
 * @param onSave - Callback when references are modified, receives updated array
 */
export default class ReferenceList extends React.Component<
  ReferenceListProps,
  ReferenceListState
> {
  state: ReferenceListState = {
    editingIndex: null,
  };

  handleDelete = (index: number) => {
    const newReferences = [...this.props.references];
    newReferences.splice(index, 1);
    this.props.onSave(newReferences);
  };

  handleEdit = (index: number) => {
    this.setState({ editingIndex: index });
  };

  handleAdd = () => {
    this.setState({ editingIndex: -1 });
  };

  handleSaveForm = (reference: Reference) => {
    const newReferences = [...this.props.references];
    if (this.state.editingIndex === -1) {
      newReferences.push(reference);
    } else if (this.state.editingIndex !== null) {
      newReferences[this.state.editingIndex] = reference;
    }

    this.props.onSave(newReferences);
    this.setState({ editingIndex: null });
  };

  handleCancel = () => {
    this.setState({ editingIndex: null });
  };

  render() {
    const { references } = this.props;
    const { editingIndex } = this.state;

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
                    onCancel={this.handleCancel}
                    onSave={this.handleSaveForm}
                  />
                ) : (
                  <div className="d-flex align-items-center">
                    <a href={ref.url} target="_blank" rel="noopener noreferrer">
                      {ref.text}
                    </a>
                    <button
                      type="button"
                      className="btn btn-sm btn-warning ml-2"
                      onClick={() => this.handleEdit(index)}
                      title="Edit reference"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-danger ml-2"
                      onClick={() => this.handleDelete(index)}
                      title="Delete reference"
                    >
                      Delete
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
          {this.props.isEditable ? (
            <>
              {editingIndex === -1 ? (
                <ReferenceForm
                  onCancel={this.handleCancel}
                  onSave={this.handleSaveForm}
                />
              ) : (
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={this.handleAdd}
                >
                  {references.length === 0
                    ? "Add a reference"
                    : "Add another reference"}
                </button>
              )}
            </>
          ) : null}
        </div>
      </div>
    );
  }
}
