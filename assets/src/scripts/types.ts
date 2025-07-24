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
