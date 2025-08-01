import type {
  DRAFT_URL,
  IS_EDITABLE,
  METADATA,
  SEARCHES,
  VERSIONS,
} from "../types";
import version_from_scratch from "./fixtures/version_from_scratch.json";

export const mockMetadata = {
  ...version_from_scratch.metadata,
};

// biome-ignore lint/suspicious/noExplicitAny: we can pass in any data in this test
export function setScript(id: string, value: any) {
  const el = document.createElement("script");
  el.id = id;
  el.type = "application/json";
  el.textContent = JSON.stringify(value);
  document.body.appendChild(el);
}

export function scriptTagSetup({
  draftURL,
  isEditable,
  metadata,
  searches,
  versions,
}: {
  draftURL?: DRAFT_URL;
  isEditable?: IS_EDITABLE;
  metadata?: METADATA;
  searches?: SEARCHES;
  versions?: VERSIONS;
}) {
  setScript("draft-url", draftURL);
  setScript("is-editable", isEditable);
  setScript("metadata", metadata);
  setScript("searches", searches);
  setScript("versions", versions);
}

export function cleanupScriptTags(scriptNames: string[]) {
  scriptNames.forEach((id) => document.getElementById(id)?.remove());
}
