import type { SearchesProps } from "./components/Cards/Searches";

export type AncestorCode = string;
export type AncestorCodes = AncestorCode[];
export type Code = string;
export type IsExpanded = boolean;
export type Path = string;
export type Pipe = "└" | "├" | " " | "│";
export type Status = "+" | "(+)" | "-" | "(-)" | "!" | "?";
export type Term = string;
export type ToggleVisibility = (path: Path) => void;
export type UpdateStatus = (code: Code, status: Status) => void;

type AllCodes = Code[];
type VisiblePaths = Set<string>;

export interface PageData {
  allCodes: AllCodes;
  codeToStatus: { [key: string]: Status };
  codeToTerm: { [key: string]: string };
  draftURL: string;
  isEditable: boolean;
  isEmptyCodelist: boolean;
  metadata: {
    codelist_full_slug: string;
    codelist_name: string;
    coding_system_id: string;
    coding_system_name: string;
    coding_system_release: {
      release_name: string;
      valid_from: string;
    };
    hash: string;
    organisation_name: string;
  };
  resultsHeading: string;
  searches: SearchesProps["searches"];
  sortByTerm: boolean;
  treeTables: [string, string[]][];
  updateURL: string;
  visiblePaths: VisiblePaths;
}

// The metadata contains a list of "references" which consist of a
// text display value, and an underlying link url
export interface Reference {
  text: string;
  url: string;
}

/**
 * Set up types for data passed from Django
 */

// {{ is_editable|json_script:"is-editable" }}
export type IS_EDITABLE = boolean;

// {{ metadata|json_script:"metadata" }}
export type METADATA = {
  description: {
    text: string;
    html: string;
  };
  methodology: {
    text: string;
    html: string;
  };
  references: {
    text: string;
    url: string;
  }[];
  coding_system_id: string;
  coding_system_name: string;
  coding_system_release: {
    release_name: string;
    valid_from: string;
  };
  organisation_name: string;
  codelist_full_slug: string;
  hash: string;
  codelist_name: string;
};

// {{ search_url|json_script:"update-url" }}
export type UPDATE_URL = string;

// {{ search_url|json_script:"draft-url" }}
export type DRAFT_URL = string;
