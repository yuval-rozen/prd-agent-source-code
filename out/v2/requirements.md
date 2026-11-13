# Requirements

- Total: 45 (42 actionable, 3 context only)
- Cited by at least one ticket: 42 / 42 actionable

| Kind | Count |
|---|---|
| functional | 12 |
| data_model | 9 |
| validation_rule | 3 |
| frontend | 11 |
| backend | 4 |
| non_functional | 1 |
| constraint | 1 |
| decision_open | 1 |
| context_only | 3 |

## Requirement diff (update run)

1 added · 1 changed · 1 removed

| Change | Old | New |
|---|---|---|
| added | — | `R-0b1853d6` Task titles cannot be longer than 100 characters. |
| changed | `R-f214002a` Sort: By Creation Date, Due Date, Status, or Priority. | `R-d482bfea` Sort: By Creation Date, Due Date, Status, Priority, or Title. |
| removed | `R-959e2960` Revert a 'Completed' task back to 'Open'. | — |

## functional

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-eed06908` | Page 1: To-Do Management | The to-do management page lets the user manage their personal task list. | This page allows the user to manage their personal task list. | `US-view-task-list`, `FE-task-list-view` |
| `R-22f28530` | Page 1: To-Do Management > Required Features | The user can create a new task. | Create a new task. | `US-create-task`, `BE-create-task-endpoint`, `QA-create-task-test-suite` |
| `R-4bed9064` | Page 1: To-Do Management > Required Features | The user can view the task list. | View the task list. | `US-view-task-list`, `BE-tasks-read-endpoints`, `QA-task-list-qa` |
| `R-bc3213df` | Page 1: To-Do Management > Required Features | The user can update an existing task. | Update an existing task. | `US-update-task`, `BE-task-update-endpoint`, `FE-task-edit-form`, `QA-task-update-tests` |
| `R-8523b9ec` | Page 1: To-Do Management > Required Features | The user can delete a task. | Delete a task. | `US-delete-task`, `BE-delete-task-endpoint`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-2304218f` | Page 1: To-Do Management > Required Features | The user can mark a task as 'Completed'. | Mark a task as 'Completed'. | `US-change-task-status`, `BE-status-change-endpoint`, `FE-status-toggle-control`, `QA-status-change-test-suite` |
| `R-5f4ef76c` | Page 2: Task Reporting > Required Features | The report lets the user filter tasks by Status, Priority, and Date Range. | Filters: Status, Priority, Date Range. | `US-filter-report-tasks`, `FE-report-filter-controls`, `QA-report-filter-tests` |
| `R-48e39a9d` | Page 2: Task Reporting > Required Features | The report lets the user search tasks by title. | Search: By Title. | `US-search-report-tasks`, `FE-report-title-search-input`, `QA-report-title-search-tests` |
| `R-d482bfea` | Page 2: Task Reporting > Required Features | The report lets the user sort tasks by Creation Date, Due Date, Status, Priority, or Title. | Sort: By Creation Date, Due Date, Status, Priority, or Title. | `US-sort-report-tasks`, `FE-report-table-sort-control`, `QA-report-sort-test-suite` |
| `R-52360b76` | Page 2: Task Reporting > Required Features | The report lets the user download its data to an Excel file. | Export: Download data to Excel. | `US-export-report-excel`, `BE-export-report-tasks-endpoint`, `FE-export-to-excel-button` |
| `R-09e9d163` | Page 2: Task Reporting > Excel Export Requirements | The exported Excel file must reflect the filters and sorting currently applied to the task view. | The file must reflect the currently applied filters and sorting. | `US-export-report-excel`, `BE-export-report-tasks-endpoint`, `FE-export-to-excel-button` |
| `R-d22b9b6a` | Page 2: Task Reporting > Excel Export Requirements | The filename of the exported Excel file must include the timestamp of when the file was generated. | Filename must include the generation timestamp. | `US-export-report-excel`, `FE-excel-file-build-and-naming` |

## data_model

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-9675bb49` | Page 1: To-Do Management > Task Data Model | Each task has a unique ID field. | Unique ID | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-aaf23206` | Page 1: To-Do Management > Task Data Model | Each task has a Title field. | Title | `US-create-task`, `BE-tasks-table-migration` |
| `R-c9046f7a` | Page 1: To-Do Management > Task Data Model | Each task has a Description field. | Description | `US-create-task`, `BE-tasks-table-migration` |
| `R-576b7e59` | Page 1: To-Do Management > Task Data Model | Each task has a Status field whose allowed values are Open, In Progress and Completed. | Status (Open, In Progress, Completed) | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-9fb58566` | Page 1: To-Do Management > Task Data Model | Each task has a Priority field whose allowed values are Low, Medium and High. | Priority (Low, Medium, High) | `US-create-task`, `BE-tasks-table-migration` |
| `R-1c2262bc` | Page 1: To-Do Management > Task Data Model | Each task has a Creation Date field. | Creation Date | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-71bdd372` | Page 1: To-Do Management > Task Data Model | Each task has a Due Date field. | Due Date | `US-create-task`, `BE-tasks-table-migration` |
| `R-31569dba` | Page 1: To-Do Management > Task Data Model | Each task has a Last Updated Date field. | Last Updated Date | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-34e41747` | Page 1: To-Do Management > Task Data Model | Each task has a Completion Date field, populated when the task is completed. | Completion Date (if completed) | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |

## validation_rule

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-03df7815` | Page 1: To-Do Management > Validation Rules & Edge Cases | A task cannot be saved unless its title is non-empty. | Task titles are mandatory; cannot be empty. | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `QA-create-task-test-suite`, `BE-task-update-endpoint`, `QA-task-update-tests` |
| `R-efe1e5d4` | Page 1: To-Do Management > Validation Rules & Edge Cases | A task's Due Date must not be earlier than its Creation Date. | Due Date cannot be earlier than the Creation Date. | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `QA-create-task-test-suite`, `BE-task-update-endpoint`, `QA-task-update-tests` |
| `R-0b1853d6` | Page 1: To-Do Management > Validation Rules & Edge Cases | A task title longer than 100 characters is rejected. | Task titles cannot be longer than 100 characters. | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `BE-task-update-endpoint` |

## frontend

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-8ef41ba1` | Page 1: To-Do Management > Validation Rules & Edge Cases | Deleting a task requires the user to confirm the deletion through a prompt before it is performed. | Deleting a task requires a prompt confirmation. | `US-delete-task`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-d57336f7` | Page 1: To-Do Management > Validation Rules & Edge Cases | The UI displays a success or error message after each create, update or delete action on a task. | Success or error messages must be displayed after create/update/delete actions. | `US-create-task`, `US-update-task`, `US-delete-task`, `FE-create-task-form`, `QA-create-task-test-suite`, `FE-task-edit-form`, `QA-task-update-tests`, `FE-delete-result-feedback`, `QA-delete-task-test-suite` |
| `R-60e02b8e` | Page 1: To-Do Management > Frontend Requirements | The system provides a task list view that displays the user's to-do tasks. | Task list view. | `US-view-task-list`, `FE-task-list-view` |
| `R-9b30a145` | Page 1: To-Do Management > Frontend Requirements | The system provides a form for creating and editing tasks. | Task creation/editing form. | `US-create-task`, `US-update-task`, `FE-create-task-form`, `FE-task-edit-form`, `QA-task-update-tests` |
| `R-48c89e9e` | Page 1: To-Do Management > Frontend Requirements | The system displays a status indicator and a priority indicator for each task. | Status and Priority indicators. | `US-view-task-list`, `FE-task-list-view` |
| `R-d7e6667f` | Page 1: To-Do Management > Frontend Requirements | The task list view shows a distinct loading state, empty state, and error state. | Loading, Empty, and Error states. | `US-view-task-list`, `FE-task-list-view`, `QA-task-list-qa` |
| `R-6a73fa71` | Page 1: To-Do Management > Frontend Requirements | The task list refreshes automatically when a task is changed. | List auto-refresh upon task changes. | `US-view-task-list`, `FE-task-list-auto-refresh`, `QA-task-list-qa` |
| `R-d0e0fe7a` | Page 2: Task Reporting | The Task Reporting page presents an aggregated view of the user's tasks. | This page presents an aggregated view of the user's tasks. | `US-view-task-report`, `FE-task-report-page-table`, `QA-task-report-test-suite` |
| `R-a1b267a3` | Page 2: Task Reporting > Required Features | The report shows all tasks in a tabular display. | Tabular display of all tasks. | `US-view-task-report`, `FE-task-report-page-table`, `QA-task-report-test-suite` |
| `R-4ffbfafa` | Page 2: Task Reporting > Required Features | The report displays the metrics Total Tasks, Open Tasks, and Completed Tasks. | Metrics: Total Tasks, Open Tasks, Completed Tasks. | `US-view-task-report`, `FE-report-metric-cards`, `QA-task-report-test-suite` |
| `R-437992f1` | Page 2: Task Reporting > Excel Export Requirements | When there is no data to export, the system must show a message to the user instead of producing an empty file. The exact wording of the message is not specified and is an open question. | User-friendly message if there is no data to export. | `US-export-report-excel`, `FE-export-to-excel-button` |

## backend

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-c55a77b3` | Page 1: To-Do Management > Backend Requirements (API) | To-do items must be saved in the persistence database, which is assumed to already exist, in a new table created for them. | The Todos should be saved in persistence DB – assume the DB already exits but there will be a need for a new table | `US-create-task`, `BE-tasks-table-migration` |
| `R-244669c0` | Page 1: To-Do Management > Backend Requirements (API) | The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items. | Endpoints for Create, Read (All & By ID), Update, Delete, and Status Change. | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-tasks-read-endpoints`, `BE-task-update-endpoint`, `QA-task-update-tests`, `BE-delete-task-endpoint`, `QA-delete-task-test-suite`, `BE-status-change-endpoint`, `QA-status-change-test-suite` |
| `R-9dc414dc` | Page 1: To-Do Management > Backend Requirements (API) | The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach. | Error handling for: Task Not Found, Invalid Input, Missing Mandatory Fields, Deleting/Updating Non-Existent Tasks, and Internal Server/Database Errors. For error handling - Keep it simple | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-tasks-read-endpoints`, `BE-task-update-endpoint`, `QA-task-update-tests`, `BE-delete-task-error-handling`, `QA-delete-task-test-suite`, `BE-status-change-error-handling`, `QA-status-change-test-suite` |
| `R-8007d6b5` | Page 2: Task Reporting > Backend & Data Requirements for Reporting | The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting. | APIs to support filtering, searching, sorting, and metric aggregation. | `US-view-task-report`, `US-filter-report-tasks`, `US-search-report-tasks`, `US-sort-report-tasks`, `BE-report-endpoint-with-metrics`, `QA-task-report-test-suite`, `BE-report-tasks-filter-api`, `QA-report-filter-tests`, `BE-report-title-search-api`, `QA-report-title-search-tests`, `BE-report-api-sort-parameter`, `QA-report-sort-test-suite` |

## non_functional

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-fad183b1` | Page 2: Task Reporting > Excel Export Requirements | The exported Excel file must have clear column headers and use one consistent date format throughout. | Clear column headers and consistent date formatting. | `US-export-report-excel`, `FE-excel-file-build-and-naming` |

## constraint

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-ab9e9cb0` | Page 1: To-Do Management > Validation Rules & Edge Cases | The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed. (applies to: R-22f28530, R-bc3213df, R-8523b9ec, R-2304218f) | Optimistic UI updates are not allowed: if a Backend action fails, the Frontend must not reflect a successful state. | `US-create-task`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `FE-create-task-form`, `QA-create-task-test-suite`, `FE-task-edit-form`, `QA-task-update-tests`, `FE-delete-result-feedback`, `QA-delete-task-test-suite`, `FE-status-toggle-control`, `QA-status-change-test-suite` |

## decision_open

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-3a63e0ce` | Page 2: Task Reporting > Backend & Data Requirements for Reporting | The development team decides whether the Excel file is generated on the frontend or the backend. | The architectural decision of whether to generate the Excel file on the Frontend or Backend is left to the development team. | `US-export-report-excel`, `BE-excel-generation-location-decision` |

## context_only

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-a62b5beb` | Product Overview | The system is a personal task management system for tracking daily tasks and generating status reports. — Introductory product description that states no testable requirement on its own. | A personal task management system that allows users to track daily tasks and generate status reports. | — |
| `R-f7f96b9a` | Product Overview | The system is composed of two main pages. — Descriptive statement that names the page count but does not specify what the pages are or how they behave; the pages themselves are defined elsewhere in the PRD. | The system consists of two main pages. | — |
| `R-82fe7dda` | Page 1: To-Do Management > Task Data Model | Each task must contain the listed fields. — Introductory sentence that lists the fields; the listed items are the requirements. | Each task must contain: | — |
