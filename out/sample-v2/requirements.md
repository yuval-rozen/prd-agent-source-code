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
| constraint | 2 |
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
| `R-eed06908` | Page 1: To-Do Management | The to-do management page lets the user manage their personal task list. | This page allows the user to manage their personal task list. | `EPIC-personal-task-management-and-status`, `US-view-task-list`, `FE-task-list-view`, `QA-task-list-test-suite` |
| `R-22f28530` | Page 1: To-Do Management > Required Features | The system lets a user create a new task. | Create a new task. | `US-create-task`, `BE-create-task-endpoint`, `FE-task-creation-form`, `QA-create-task-test-suite` |
| `R-4bed9064` | Page 1: To-Do Management > Required Features | The system lets a user view the task list. | View the task list. | `US-view-task-list`, `BE-tasks-list-endpoint`, `QA-task-list-test-suite` |
| `R-bc3213df` | Page 1: To-Do Management > Required Features | The system lets a user update an existing task. | Update an existing task. | `US-update-task`, `BE-put-task-endpoint-with-validation`, `FE-task-edit-form-prefill`, `QA-task-update-test-suite` |
| `R-8523b9ec` | Page 1: To-Do Management > Required Features | The system lets a user delete a task. | Delete a task. | `US-delete-task`, `BE-delete-task-endpoint`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-2304218f` | Page 1: To-Do Management > Required Features | The system lets a user mark a task as 'Completed'. | Mark a task as 'Completed'. | `US-change-task-status`, `BE-task-status-endpoint`, `FE-task-status-toggle`, `QA-task-status-tests` |
| `R-5f4ef76c` | Page 2: Task Reporting > Required Features | The report lets the user filter tasks by Status, Priority and Date Range. | Filters: Status, Priority, Date Range. | `US-filter-search-sort-report`, `BE-report-query-filter-search-sort`, `FE-report-filter-controls`, `QA-report-filter-search-sort-tests` |
| `R-48e39a9d` | Page 2: Task Reporting > Required Features | The report lets the user search tasks by title. | Search: By Title. | `US-filter-search-sort-report`, `BE-report-query-filter-search-sort`, `FE-report-search-and-sort-ui`, `QA-report-filter-search-sort-tests` |
| `R-d482bfea` | Page 2: Task Reporting > Required Features | The report lets the user sort tasks by Creation Date, Due Date, Status, Priority or Title. | Sort: By Creation Date, Due Date, Status, Priority, or Title. | `US-filter-search-sort-report`, `BE-report-query-filter-search-sort`, `FE-report-search-and-sort-ui`, `QA-report-filter-search-sort-tests` |
| `R-52360b76` | Page 2: Task Reporting > Required Features | The report lets the user download its data as an Excel file. | Export: Download data to Excel. | `US-export-report-excel`, `BE-task-report-excel-generator`, `FE-report-excel-download-action`, `QA-excel-export-test-suite` |
| `R-09e9d163` | Page 2: Task Reporting > Excel Export Requirements | The exported Excel file must contain only the rows matching the currently applied filters, in the currently applied sort order. | The file must reflect the currently applied filters and sorting. | `US-export-report-excel`, `BE-task-report-excel-generator`, `FE-report-excel-download-action`, `QA-excel-export-test-suite` |
| `R-d22b9b6a` | Page 2: Task Reporting > Excel Export Requirements | The name of each exported Excel file must include the timestamp at which the file was generated. | Filename must include the generation timestamp. | `US-export-report-excel`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |

## data_model

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-9675bb49` | Page 1: To-Do Management > Task Data Model | Each task has a unique ID field. | Unique ID | `US-create-task`, `BE-tasks-table-migration` |
| `R-aaf23206` | Page 1: To-Do Management > Task Data Model | Each task has a Title field. | Title | `US-create-task`, `BE-tasks-table-migration` |
| `R-c9046f7a` | Page 1: To-Do Management > Task Data Model | Each task has a Description field. | Description | `US-create-task`, `BE-tasks-table-migration` |
| `R-576b7e59` | Page 1: To-Do Management > Task Data Model | Each task has a Status field whose allowed values are Open, In Progress and Completed. | Status (Open, In Progress, Completed) | `US-create-task`, `US-change-task-status`, `BE-tasks-table-migration`, `QA-task-status-tests` |
| `R-9fb58566` | Page 1: To-Do Management > Task Data Model | Each task has a Priority field whose allowed values are Low, Medium and High. | Priority (Low, Medium, High) | `US-create-task`, `BE-tasks-table-migration` |
| `R-1c2262bc` | Page 1: To-Do Management > Task Data Model | Each task has a Creation Date field. | Creation Date | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-71bdd372` | Page 1: To-Do Management > Task Data Model | Each task has a Due Date field. | Due Date | `US-create-task`, `BE-tasks-table-migration` |
| `R-31569dba` | Page 1: To-Do Management > Task Data Model | Each task has a Last Updated Date field. | Last Updated Date | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-34e41747` | Page 1: To-Do Management > Task Data Model | Each task has a Completion Date field, populated when the task is completed. | Completion Date (if completed) | `US-create-task`, `BE-tasks-table-migration` |

## validation_rule

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-03df7815` | Page 1: To-Do Management > Validation Rules & Edge Cases | A task title is required and an empty title must be rejected on task creation or update. | Task titles are mandatory; cannot be empty. | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `FE-task-creation-form`, `QA-create-task-test-suite`, `BE-put-task-endpoint-with-validation`, `FE-task-update-result-messages`, `QA-task-update-test-suite` |
| `R-efe1e5d4` | Page 1: To-Do Management > Validation Rules & Edge Cases | A task's Due Date must not be earlier than its Creation Date. | Due Date cannot be earlier than the Creation Date. | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `FE-task-creation-form`, `QA-create-task-test-suite`, `BE-put-task-endpoint-with-validation`, `FE-task-update-result-messages`, `QA-task-update-test-suite` |
| `R-0b1853d6` | Page 1: To-Do Management > Validation Rules & Edge Cases | A task title must not exceed 100 characters. | Task titles cannot be longer than 100 characters. | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `BE-put-task-endpoint-with-validation` |

## frontend

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-8ef41ba1` | Page 1: To-Do Management > Validation Rules & Edge Cases | Deleting a task must first show a confirmation prompt that the user must accept before the task is deleted. | Deleting a task requires a prompt confirmation. | `US-delete-task`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-d57336f7` | Page 1: To-Do Management > Validation Rules & Edge Cases | After each create, update or delete action, the UI must display a success or error message reflecting the outcome. | Success or error messages must be displayed after create/update/delete actions. | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `FE-task-creation-form`, `QA-create-task-test-suite`, `QA-task-list-test-suite`, `FE-task-update-result-messages`, `QA-task-update-test-suite`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite`, `FE-task-status-feedback`, `QA-task-status-tests` |
| `R-60e02b8e` | Page 1: To-Do Management > Frontend Requirements | The system provides a task list view that displays the user's tasks. | Task list view. | `US-view-task-list`, `FE-task-list-view`, `QA-task-list-test-suite` |
| `R-9b30a145` | Page 1: To-Do Management > Frontend Requirements | The system provides a form to create a new task and to edit an existing task. | Task creation/editing form. | `US-create-task`, `US-update-task`, `FE-task-creation-form`, `FE-task-edit-form-prefill`, `FE-task-row-edit-action`, `QA-task-update-test-suite` |
| `R-48c89e9e` | Page 1: To-Do Management > Frontend Requirements | The system shows a status indicator and a priority indicator for each task. | Status and Priority indicators. | `US-view-task-list`, `FE-task-list-view`, `QA-task-list-test-suite` |
| `R-d7e6667f` | Page 1: To-Do Management > Frontend Requirements | The task list view shows a loading state, an empty state and an error state. | Loading, Empty, and Error states. | `US-view-task-list`, `FE-task-list-states`, `QA-task-list-test-suite` |
| `R-6a73fa71` | Page 1: To-Do Management > Frontend Requirements | The task list refreshes automatically when a task is changed. | List auto-refresh upon task changes. | `US-view-task-list`, `FE-task-list-auto-refresh`, `QA-task-list-test-suite` |
| `R-d0e0fe7a` | Page 2: Task Reporting | The Task Reporting page presents an aggregated view of the user's tasks. | This page presents an aggregated view of the user's tasks. | `EPIC-personal-task-management-and-status`, `US-view-task-report`, `FE-report-page-table`, `QA-report-test-suite` |
| `R-a1b267a3` | Page 2: Task Reporting > Required Features | The report displays all tasks in a tabular view. | Tabular display of all tasks. | `US-view-task-report`, `FE-report-page-table`, `QA-report-test-suite` |
| `R-4ffbfafa` | Page 2: Task Reporting > Required Features | The report displays the metrics Total Tasks, Open Tasks and Completed Tasks. | Metrics: Total Tasks, Open Tasks, Completed Tasks. | `US-view-task-report`, `FE-report-metrics-cards`, `QA-report-test-suite` |
| `R-437992f1` | Page 2: Task Reporting > Excel Export Requirements | When there is no data to export, the system must show a message to the user instead of producing an empty file. The PRD does not define the message wording or whether a file is still produced; this is an open question. | User-friendly message if there is no data to export. | `US-export-report-excel`, `FE-report-export-no-data-message`, `QA-excel-export-test-suite` |

## backend

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-c55a77b3` | Page 1: To-Do Management > Backend Requirements (API) | Todo items must be saved in the persistence database in a new table, assuming the database already exists. | The Todos should be saved in persistence DB – assume the DB already exits but there will be a need for a new table | `US-create-task`, `BE-tasks-table-migration` |
| `R-244669c0` | Page 1: To-Do Management > Backend Requirements (API) | The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items. | Endpoints for Create, Read (All & By ID), Update, Delete, and Status Change. | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-create-task-endpoint`, `BE-tasks-list-endpoint`, `BE-task-by-id-endpoint`, `QA-task-list-test-suite`, `BE-put-task-endpoint-with-validation`, `QA-task-update-test-suite`, `BE-delete-task-endpoint`, `BE-task-status-endpoint`, `QA-task-status-tests` |
| `R-9dc414dc` | Page 1: To-Do Management > Backend Requirements (API) | The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach. | Error handling for: Task Not Found, Invalid Input, Missing Mandatory Fields, Deleting/Updating Non-Existent Tasks, and Internal Server/Database Errors. For error handling - Keep it simple | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-create-task-endpoint`, `QA-create-task-test-suite`, `BE-tasks-list-endpoint`, `BE-task-by-id-endpoint`, `QA-task-list-test-suite`, `BE-put-task-error-responses`, `QA-task-update-test-suite`, `BE-delete-task-endpoint`, `QA-delete-task-test-suite`, `BE-task-status-endpoint`, `QA-task-status-tests` |
| `R-8007d6b5` | Page 2: Task Reporting > Backend & Data Requirements for Reporting | The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting. | APIs to support filtering, searching, sorting, and metric aggregation. | `US-view-task-report`, `US-filter-search-sort-report`, `US-export-report-excel`, `BE-report-metrics-endpoint`, `QA-report-test-suite`, `BE-report-query-filter-search-sort`, `QA-report-filter-search-sort-tests`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |

## constraint

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-ab9e9cb0` | Page 1: To-Do Management > Validation Rules & Edge Cases | The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails. (applies to: R-22f28530, R-bc3213df, R-8523b9ec, R-2304218f) | Optimistic UI updates are not allowed: if a Backend action fails, the Frontend must not reflect a successful state. | `US-create-task`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `FE-task-creation-form`, `QA-create-task-test-suite`, `FE-task-update-result-messages`, `QA-task-update-test-suite`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite`, `FE-task-status-toggle`, `FE-task-status-feedback`, `QA-task-status-tests` |
| `R-fad183b1` | Page 2: Task Reporting > Excel Export Requirements | Every exported Excel file must have clear column headers and use one consistent date format across all date columns. (applies to: R-52360b76) | Clear column headers and consistent date formatting. | `US-export-report-excel`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |

## decision_open

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-3a63e0ce` | Page 2: Task Reporting > Backend & Data Requirements for Reporting | The development team decides whether the Excel file is generated on the frontend or the backend. | The architectural decision of whether to generate the Excel file on the Frontend or Backend is left to the development team. | `US-export-report-excel`, `BE-excel-export-generation-decision` |

## context_only

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-a62b5beb` | Product Overview | The system is a personal task management system for tracking daily tasks and generating status reports. — Introductory product description that states no testable requirement on its own. | A personal task management system that allows users to track daily tasks and generate status reports. | `EPIC-personal-task-management-and-status` |
| `R-f7f96b9a` | Product Overview | The system is composed of two main pages. — Descriptive statement that names the page count but does not define the pages; their content is specified elsewhere in the PRD. | The system consists of two main pages. | `EPIC-personal-task-management-and-status` |
| `R-82fe7dda` | Page 1: To-Do Management > Task Data Model | Each task must contain the listed fields. — Introductory sentence that lists the fields; the listed items are the requirements. | Each task must contain: | — |
