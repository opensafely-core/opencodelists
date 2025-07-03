# OpenCodelists Project Structure

This is a Django project for managing medical codelists. It follows functional programming principles where possible and has a distinct architectural style.

## High-Level Overview

-   **Framework**: Django
-   **Frontend**: React/TypeScript, built with Vite.
-   **Database**: SQLite. A main database for application state, and separate, versioned, read-only SQLite databases for each release of a coding system.
-   **Key Pattern**: Business logic is encapsulated in `actions.py` modules within apps, separating it from views and models.

## Backend Directory Structure

-   `opencodelists/`: The main Django project configuration. Contains core models like `User` and `Organisation`.
-   `codelists/`: The primary application for managing codelists.
    -   `models.py`: Defines `Codelist`, `CodelistVersion`, `CodelistVersionSimilarity`, etc.
    -   `views/`: A package containing view modules (e.g., `index.py`, `version.py`).
    -   `actions.py`: Contains business logic for creating/updating codelists.
    -   `hierarchy.py`, `codeset.py`: Core domain logic for handling code relationships and status (+, -, ?, etc.).
-   `builder/`: App for the interactive, web-based codelist builder SPA.
-   `coding_systems/`: A directory containing a Django app for each supported coding system (e.g., `snomedct`, `bnf`, `icd10`).
    -   Each app has a `coding_system.py` that implements a common interface defined in `coding_systems/base/coding_system_base.py`.
    -   `coding_systems/versioning/`: A special app that manages metadata about coding system releases. A `CodingSystemReleaseRouter` in `opencodelists/db_utils.py` directs queries to the correct versioned SQLite database.
-   `mappings/`: Contains apps for defining and applying mappings between different coding systems.
-   `scripts/`: Location for scripts to be run via `manage.py runscript`.

## Frontend Directory Structure

-   `assets/`: Contains all frontend source code (TypeScript, React `.tsx` files, CSS).
-   `templates/`: Contains all Django HTML templates.
-   `static/`: Destination for compiled frontend assets.

## Analysis

-   `analyse.py`: A standalone command-line script in the root for downloading all published codelists and performing analysis, such as hierarchical clustering based on Jaccard distance. It can output cluster data to `clusters.json`.
