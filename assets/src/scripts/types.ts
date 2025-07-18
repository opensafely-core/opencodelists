import { SearchesProps } from "./components/Cards/Searches";

export type AncestorCode = string;
export type AncestorCodes = AncestorCode[];
export type Code = string;
export type IsExpanded = boolean;
export type Path = string;
export type Pipe = "└" | "├" | " " | "│";
export type Status = "+" | "(+)" | "-" | "(-)" | "!" | "?";
export type Term = string;
export type ToggleVisibility = (path: Path) => void;

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

// {{ is_editable|json_script:"is-editable" }}
export type IS_EDITABLE = boolean;

// {{ metadata|json_script:"metadata" }}
export type METADATA = {
  description: {
    text: string;
    html: string;
    isEditing: boolean;
  };
  methodology: {
    text: string;
    html: string;
    isEditing: boolean;
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

// {{ versions|json_script:"versions" }}
export type VERSIONS = {
  created_at: string;
  current: boolean;
  status: string;
  tag_or_hash: string;
  url: string;
}[];

// {{ is_empty_codelist|json_script:"is-empty-codelist" }}
export type IS_EMPTY_CODELIST = boolean;
