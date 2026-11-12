# Requirements

- Total: 41 (35 actionable, 6 context only)
- Cited by at least one ticket: 35 / 35 actionable

| Kind | Count |
|---|---|
| functional | 14 |
| data_model | 9 |
| validation_rule | 2 |
| frontend | 3 |
| backend | 4 |
| non_functional | 1 |
| constraint | 1 |
| decision_open | 1 |
| context_only | 6 |

## functional

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-22f28530` | Page 1: To-Do Management > Required Features | Users can create a new task. | Create a new task. | `US-create-and-view-tasks`, `BE-create-task-endpoint`, `FE-create-task-form` |
| `R-4bed9064` | Page 1: To-Do Management > Required Features | Users can view the task list. | View the task list. | `US-create-and-view-tasks`, `BE-list-tasks-endpoint`, `FE-task-list-view` |
| `R-bc3213df` | Page 1: To-Do Management > Required Features | Users can update an existing task. | Update an existing task. | `US-update-task-details`, `BE-task-update-endpoint`, `FE-task-edit-form` |
| `R-8523b9ec` | Page 1: To-Do Management > Required Features | Users can delete a task. | Delete a task. | `US-delete-task-with-confirmation`, `BE-delete-task-endpoint`, `FE-delete-task-confirmation-prompt`, `FE-delete-task-result-feedback`, `QA-delete-task-test-suite` |
| `R-2304218f` | Page 1: To-Do Management > Required Features | Users can mark a task as 'Completed'. | Mark a task as 'Completed'. | `US-complete-and-reopen-task`, `BE-task-status-change-endpoint`, `FE-task-status-toggle-ui`, `QA-task-status-test-suite` |
| `R-959e2960` | Page 1: To-Do Management > Required Features | Users can revert a 'Completed' task back to 'Open'. | Revert a 'Completed' task back to 'Open'. | `US-complete-and-reopen-task`, `BE-task-status-change-endpoint`, `FE-task-status-toggle-ui`, `QA-task-status-test-suite` |
| `R-8ef41ba1` | Page 1: To-Do Management > Validation Rules & Edge Cases | Deleting a task requires the user to confirm the deletion through a prompt before it is applied. | Deleting a task requires a prompt confirmation. | `US-delete-task-with-confirmation`, `FE-delete-task-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-5f4ef76c` | Page 2: Task Reporting > Required Features | The task report can be filtered by Status, Priority, and Date Range. | Filters: Status, Priority, Date Range. | `US-filter-search-sort-task-report`, `BE-task-report-query-api`, `FE-report-filter-search-sort-controls`, `QA-task-report-filter-search-sort` |
| `R-48e39a9d` | Page 2: Task Reporting > Required Features | The task report can be searched by task title. | Search: By Title. | `US-filter-search-sort-task-report`, `BE-task-report-query-api`, `FE-report-filter-search-sort-controls`, `QA-task-report-filter-search-sort` |
| `R-f214002a` | Page 2: Task Reporting > Required Features | The task report can be sorted by Creation Date, Due Date, Status, or Priority. | Sort: By Creation Date, Due Date, Status, or Priority. | `US-filter-search-sort-task-report`, `BE-task-report-query-api`, `FE-report-filter-search-sort-controls`, `QA-task-report-filter-search-sort` |
| `R-4ffbfafa` | Page 2: Task Reporting > Required Features | The task report shows the counts of Total Tasks, Open Tasks, and Completed Tasks. | Metrics: Total Tasks, Open Tasks, Completed Tasks. | `US-review-task-report`, `BE-task-report-api-with-counts`, `FE-task-report-count-metrics`, `QA-task-report-test-suite` |
| `R-52360b76` | Page 2: Task Reporting > Required Features | The user can download task report data as an Excel file. | Export: Download data to Excel. | `US-export-task-report-to-excel`, `BE-excel-file-generation`, `FE-export-button-and-empty-message` |
| `R-09e9d163` | Page 2: Task Reporting > Excel Export Requirements | The exported Excel file must contain only the rows matching the currently applied filters, in the currently applied sort order. | The file must reflect the currently applied filters and sorting. | `US-export-task-report-to-excel`, `BE-export-excel-data-query` |
| `R-d22b9b6a` | Page 2: Task Reporting > Excel Export Requirements | The exported Excel file name must include the timestamp of when the file was generated. | Filename must include the generation timestamp. | `US-export-task-report-to-excel`, `BE-excel-file-generation` |

## data_model

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-9675bb49` | Page 1: To-Do Management > Task Data Model | Each task has a unique ID field. | Unique ID | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-aaf23206` | Page 1: To-Do Management > Task Data Model | Each task has a Title field. | Title | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-c9046f7a` | Page 1: To-Do Management > Task Data Model | Each task has a Description field. | Description | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-576b7e59` | Page 1: To-Do Management > Task Data Model | Each task has a Status field whose allowed values are Open, In Progress and Completed. | Status (Open, In Progress, Completed) | `US-create-and-view-tasks`, `US-complete-and-reopen-task`, `BE-tasks-table-migration`, `FE-task-list-view`, `BE-task-status-fields-migration`, `QA-task-status-test-suite` |
| `R-9fb58566` | Page 1: To-Do Management > Task Data Model | Each task has a Priority field whose allowed values are Low, Medium and High. | Priority (Low, Medium, High) | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-1c2262bc` | Page 1: To-Do Management > Task Data Model | Each task has a Creation Date field. | Creation Date | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-71bdd372` | Page 1: To-Do Management > Task Data Model | Each task has a Due Date field. | Due Date | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-31569dba` | Page 1: To-Do Management > Task Data Model | Each task has a Last Updated Date field. | Last Updated Date | `US-update-task-details`, `US-complete-and-reopen-task`, `BE-task-last-updated-field`, `BE-task-status-fields-migration`, `QA-task-status-test-suite` |
| `R-34e41747` | Page 1: To-Do Management > Task Data Model | Each task has a Completion Date field, populated when the task is completed. | Completion Date (if completed) | `US-complete-and-reopen-task`, `BE-task-status-fields-migration`, `QA-task-status-test-suite` |

## validation_rule

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-03df7815` | Page 1: To-Do Management > Validation Rules & Edge Cases | A task must not be saved unless its title is non-empty. | Task titles are mandatory; cannot be empty. | `US-create-and-view-tasks`, `US-update-task-details`, `BE-create-task-endpoint`, `FE-create-task-form`, `BE-task-update-endpoint` |
| `R-efe1e5d4` | Page 1: To-Do Management > Validation Rules & Edge Cases | A task's Due Date must not be earlier than its Creation Date. | Due Date cannot be earlier than the Creation Date. | `US-create-and-view-tasks`, `US-update-task-details`, `BE-create-task-endpoint`, `FE-create-task-form`, `BE-task-update-endpoint` |

## frontend

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-d57336f7` | Page 1: To-Do Management > Validation Rules & Edge Cases | A success or error message must be displayed after each create, update, or delete task action. | Success or error messages must be displayed after create/update/delete actions. | `US-create-and-view-tasks`, `US-update-task-details`, `US-delete-task-with-confirmation`, `US-complete-and-reopen-task`, `FE-create-task-form`, `FE-task-update-messages`, `FE-delete-task-result-feedback`, `QA-delete-task-test-suite`, `FE-task-status-toggle-ui`, `QA-task-status-test-suite` |
| `R-a1b267a3` | Page 2: Task Reporting > Required Features | The reporting page displays all tasks in a table. | Tabular display of all tasks. | `US-review-task-report`, `US-filter-search-sort-task-report`, `FE-task-report-table`, `QA-task-report-test-suite`, `FE-report-tasks-table`, `QA-task-report-filter-search-sort` |
| `R-437992f1` | Page 2: Task Reporting > Excel Export Requirements | When there is no data to export, the system must show a message to the user instead of producing an export file; the message text is not specified in the PRD. | User-friendly message if there is no data to export. | `US-export-task-report-to-excel`, `FE-export-button-and-empty-message` |

## backend

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-c55a77b3` | Page 1: To-Do Management > Backend Requirements (API) | Todos are persisted in the existing database in a new table created for them. | The Todos should be saved in persistence DB – assume the DB already exits but there will be a need for a new table | `US-create-and-view-tasks`, `BE-tasks-table-migration` |
| `R-244669c0` | Page 1: To-Do Management > Backend Requirements (API) | The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo. | Endpoints for Create, Read (All & By ID), Update, Delete, and Status Change. | `US-create-and-view-tasks`, `US-update-task-details`, `US-delete-task-with-confirmation`, `US-complete-and-reopen-task`, `BE-list-tasks-endpoint`, `BE-task-update-endpoint`, `BE-delete-task-endpoint`, `QA-delete-task-test-suite`, `BE-task-status-change-endpoint`, `QA-task-status-test-suite` |
| `R-9dc414dc` | Page 1: To-Do Management > Backend Requirements (API) | The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors. | Error handling for: Task Not Found, Invalid Input, Missing Mandatory Fields, Deleting/Updating Non-Existent Tasks, and Internal Server/Database Errors. For error handling - Keep it simple | `US-create-and-view-tasks`, `US-update-task-details`, `US-delete-task-with-confirmation`, `US-complete-and-reopen-task`, `BE-create-task-endpoint`, `BE-task-update-endpoint`, `BE-delete-task-error-responses`, `QA-delete-task-test-suite`, `BE-task-status-change-endpoint`, `QA-task-status-test-suite` |
| `R-8007d6b5` | Page 2: Task Reporting > Backend & Data Requirements for Reporting | The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting. | APIs to support filtering, searching, sorting, and metric aggregation. | `US-review-task-report`, `US-filter-search-sort-task-report`, `US-export-task-report-to-excel`, `BE-task-report-api-with-counts`, `QA-task-report-test-suite`, `BE-task-report-query-api`, `QA-task-report-filter-search-sort`, `BE-export-excel-data-query` |

## non_functional

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-fad183b1` | Page 2: Task Reporting > Excel Export Requirements | The exported Excel file must have clear column headers and use one consistent date format across all date columns. | Clear column headers and consistent date formatting. | `US-export-task-report-to-excel`, `BE-excel-file-generation` |

## constraint

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-ab9e9cb0` | Page 1: To-Do Management > Validation Rules & Edge Cases | The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails. (applies to: R-22f28530, R-bc3213df, R-8523b9ec, R-2304218f, R-959e2960) | Optimistic UI updates are not allowed: if a Backend action fails, the Frontend must not reflect a successful state. | `US-create-and-view-tasks`, `US-update-task-details`, `US-delete-task-with-confirmation`, `US-complete-and-reopen-task`, `FE-create-task-form`, `FE-task-edit-form`, `FE-task-update-messages`, `FE-delete-task-result-feedback`, `QA-delete-task-test-suite`, `FE-task-status-toggle-ui`, `QA-task-status-test-suite` |

## decision_open

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-3a63e0ce` | Page 2: Task Reporting > Backend & Data Requirements for Reporting | The development team decides whether the Excel file is generated on the frontend or the backend. | The architectural decision of whether to generate the Excel file on the Frontend or Backend is left to the development team. | `US-export-task-report-to-excel`, `BE-excel-generation-decision` |

## context_only

| ID | Section | Statement | Source quote | Cited by |
|---|---|---|---|---|
| `R-a62b5beb` | Product Overview | Describes the product as a personal task management system for tracking daily tasks and generating status reports. — Introductory product description; it states the product purpose but no testable requirement. | A personal task management system that allows users to track daily tasks and generate status reports. | — |
| `R-f7f96b9a` | Product Overview | The system is composed of two main pages. — Descriptive statement about system structure; the pages themselves are not specified in this section. | The system consists of two main pages. | — |
| `R-eed06908` | Page 1: To-Do Management | Not a requirement; describes the purpose of the To-Do Management page. — Introductory text that states the page's purpose but no testable requirement. | This page allows the user to manage their personal task list. | — |
| `R-82fe7dda` | Page 1: To-Do Management > Task Data Model | Lead-in sentence listing the fields each task must contain; the listed items are the requirements. — Lead-in sentence for the list of task fields; the individual fields are captured as separate requirements. | Each task must contain: | — |
| `R-60e02b8e` | Page 1: To-Do Management > Frontend Requirements | Task list view. — Heading-like label without a testable requirement. | Task list view. | — |
| `R-d0e0fe7a` | Page 2: Task Reporting | This page presents an aggregated view of the user's tasks. — Introductory text that describes the page's purpose but states no testable requirement. | This page presents an aggregated view of the user's tasks. | — |
