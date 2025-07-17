export type AncestorCode = string;
export type AncestorCodes = AncestorCode[];
export type Code = string;
export type IsExpanded = boolean;
export type Path = string;
export type Pipe = "└" | "├" | " " | "│";
export type Status = "+" | "(+)" | "-" | "(-)" | "!" | "?";
export type Term = string;
export type ToggleVisibility = (path: Path) => void;
export type Version = {
  created_at: string;
  current: boolean;
  status: string;
  tag_or_hash: string;
  url: string;
};

type AllCodes = Code[];

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
  searches: {
    active: boolean;
    delete_url: string;
    term_or_code: string;
    url: string;
  }[];
  searchURL: string;
  sortByTerm: boolean;
  treeTables: [string, string[]][];
  updateURL: string;
  versions: Version[];
  visiblePaths: VisiblePathsType;
}

// The metadata contains a list of "references" which consist of a
// text display value, and an underlying link url
export interface Reference {
  text: string;
  url: string;
}

// {{ results_heading|json_script:"results-heading" }}
export type RESULTS_HEADING = string;

// {{ searches|json_script:"searches" }}
export type SEARCHES = {
  active: boolean;
  delete_url: string;
  term_or_code: string;
  url: string;
}[];

// {{ tree_tables|json_script:"tree-tables" }}
export type TREE_TABLES = [string, Code[]][];

// {{ code_to_term|json_script:"code-to-term" }}
export type CODE_TO_TERM = { [key: Code]: string };

// {{ code_to_status|json_script:"code-to-status" }}
export type CODE_TO_STATUS = { [key: Code]: Status };

// {{ all_codes|json_script:"all-codes" }}
export type ALL_CODES = Code[];

// {{ parent_map|json_script:"parent-map" }}
export type PARENT_MAP = Record<Code, Code[]>;

// {{ child_map|json_script:"child-map" }}
export type CHILD_MAP = Record<Code, Code[]>;

// {{ is_editable|json_script:"is-editable" }}
export type IS_EDITABLE = boolean;

// {{ draft_url|json_script:"draft-url" }}
export type DRAFT_URL = string;

// {{ update_url|json_script:"update-url" }}
export type UPDATE_URL = string;

// {{ search_url|json_script:"search-url" }}
export type SEARCH_URL = string;

// {{ sort_by_term|json_script:"sort-by-term" }}
export type SORT_BY_TERM = boolean;

// {{ versions|json_script:"versions" }}
export type VERSIONS = {
  created_at: string;
  current: boolean;
  status: string;
  tag_or_hash: string;
  url: string;
}[];

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

// {{ is_empty_codelist|json_script:"is-empty-codelist" }}
export type IS_EMPTY_CODELIST = boolean;

export type VisiblePathsType = Set<Code>;
export type UpdateStatusType = Function;
