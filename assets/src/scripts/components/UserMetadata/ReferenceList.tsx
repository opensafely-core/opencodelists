import React, { useState } from "react";
import { Reference } from "../../types";
import ReferenceForm from "./ReferenceForm";

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
export default function ReferenceList({
  references,
  onSave,
}: ReferenceListProps) {
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
        <p style={{ fontStyle: "italic" }}>
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
