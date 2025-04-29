export type AncestorCode = string;
export type AncestorCodes = AncestorCode[];
export type Code = string;
export type IsExpanded = boolean;
export type Path = string;
export type Pipe = "└" | "├" | " " | "│";
export type Status = "+" | "(+)" | "-" | "(-)" | "!" | "?";
export type Term = string;
export type ToggleVisibility = (path: Path) => void;
export type VersionT = {
  current: boolean;
  status: string;
  tag_or_hash: string;
  url: string;
};

type AllCodes = Code[];
type VisiblePaths = Set<string>;

export interface PageData {
  allCodes: AllCodes;
  codeToStatus: { [key: string]: Status };
  codeToTerm: { [key: string]: string };
  draftURL: string;
  filter: string;
  isEditable: boolean;
  metadata: {
    codelist_full_slug: string;
    codelist_name: string;
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
  treeTables: [string, string[]][];
  updateURL: string;
  versions: VersionT[];
  visiblePaths: VisiblePaths;
}
