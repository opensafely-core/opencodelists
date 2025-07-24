import React from "react";

interface ReferenceFormProps {
  defaultValue?: {
    text: string;
    url: string;
  };
  onReset: React.FormEventHandler<HTMLFormElement>;
  onSubmit: React.FormEventHandler<HTMLFormElement>;
}

export default function ReferenceForm({
  defaultValue,
  onReset,
  onSubmit,
}: ReferenceFormProps) {
  return (
    <form onReset={onReset} onSubmit={onSubmit}>
      <div className="form-group">
        <label className="form-label" htmlFor="addReferenceText">
          Text
        </label>
        <input
          className="form-control"
          defaultValue={defaultValue?.text}
          id="addReferenceText"
          name="text"
          placeholder="Text to display"
          required
          type="text"
        />
      </div>
      <div className="form-group">
        <label className="form-label" htmlFor="addReferenceUrl">
          URL
        </label>
        <input
          className="form-control"
          defaultValue={defaultValue?.url}
          id="addReferenceUrl"
          name="url"
          placeholder="Website to link to"
          required
          type="url"
        />
      </div>
      <div className="btn-group-sm">
        <button type="submit" className="btn btn-primary">
          Save
        </button>
        <button type="reset" className="btn btn-secondary ml-1">
          Cancel
        </button>
      </div>
    </form>
  );
}
