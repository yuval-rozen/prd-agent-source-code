# Validation report

**Final status:** NOT CHECKED

## reference_normalization — round 0: pass (0 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| REF-UNIT | warning | PRD: To-Do Management System > Page 1: To-Do Management > Frontend Requirements | Unknown unit ID(s) ['U-b46f2e-b46f2e-60e02b8e'] for quote 'Task list view.'; attached to best-matching unit U-b46f2e-60e02b8e. |  |

## Coverage matrix

| Requirement | Kind | Tickets |
|---|---|---|
| `R-a62b5beb` | context_only | — |
| `R-f7f96b9a` | context_only | — |
| `R-eed06908` | context_only | — |
| `R-22f28530` | functional | `US-create-and-view-tasks`, `BE-create-task-endpoint`, `FE-create-task-form` |
| `R-4bed9064` | functional | `US-create-and-view-tasks`, `BE-list-tasks-endpoint`, `FE-task-list-view` |
| `R-bc3213df` | functional | `US-update-task-details`, `BE-task-update-endpoint`, `FE-task-edit-form` |
| `R-8523b9ec` | functional | `US-delete-task-with-confirmation`, `BE-delete-task-endpoint`, `FE-delete-task-confirmation-prompt`, `FE-delete-task-result-feedback`, `QA-delete-task-test-suite` |
| `R-2304218f` | functional | `US-complete-and-reopen-task`, `BE-task-status-change-endpoint`, `FE-task-status-toggle-ui`, `QA-task-status-test-suite` |
| `R-959e2960` | functional | `US-complete-and-reopen-task`, `BE-task-status-change-endpoint`, `FE-task-status-toggle-ui`, `QA-task-status-test-suite` |
| `R-82fe7dda` | context_only | — |
| `R-9675bb49` | data_model | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-aaf23206` | data_model | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-c9046f7a` | data_model | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-576b7e59` | data_model | `US-create-and-view-tasks`, `US-complete-and-reopen-task`, `BE-tasks-table-migration`, `FE-task-list-view`, `BE-task-status-fields-migration`, `QA-task-status-test-suite` |
| `R-9fb58566` | data_model | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-1c2262bc` | data_model | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-71bdd372` | data_model | `US-create-and-view-tasks`, `BE-tasks-table-migration`, `FE-task-list-view` |
| `R-31569dba` | data_model | `US-update-task-details`, `US-complete-and-reopen-task`, `BE-task-last-updated-field`, `BE-task-status-fields-migration`, `QA-task-status-test-suite` |
| `R-34e41747` | data_model | `US-complete-and-reopen-task`, `BE-task-status-fields-migration`, `QA-task-status-test-suite` |
| `R-03df7815` | validation_rule | `US-create-and-view-tasks`, `US-update-task-details`, `BE-create-task-endpoint`, `FE-create-task-form`, `BE-task-update-endpoint` |
| `R-efe1e5d4` | validation_rule | `US-create-and-view-tasks`, `US-update-task-details`, `BE-create-task-endpoint`, `FE-create-task-form`, `BE-task-update-endpoint` |
| `R-8ef41ba1` | functional | `US-delete-task-with-confirmation`, `FE-delete-task-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-d57336f7` | frontend | `US-create-and-view-tasks`, `US-update-task-details`, `US-delete-task-with-confirmation`, `US-complete-and-reopen-task`, `FE-create-task-form`, `FE-task-update-messages`, `FE-delete-task-result-feedback`, `QA-delete-task-test-suite`, `FE-task-status-toggle-ui`, `QA-task-status-test-suite` |
| `R-ab9e9cb0` | constraint | `US-create-and-view-tasks`, `US-update-task-details`, `US-delete-task-with-confirmation`, `US-complete-and-reopen-task`, `FE-create-task-form`, `FE-task-edit-form`, `FE-task-update-messages`, `FE-delete-task-result-feedback`, `QA-delete-task-test-suite`, `FE-task-status-toggle-ui`, `QA-task-status-test-suite` |
| `R-60e02b8e` | context_only | — |
| `R-c55a77b3` | backend | `US-create-and-view-tasks`, `BE-tasks-table-migration` |
| `R-244669c0` | backend | `US-create-and-view-tasks`, `US-update-task-details`, `US-delete-task-with-confirmation`, `US-complete-and-reopen-task`, `BE-list-tasks-endpoint`, `BE-task-update-endpoint`, `BE-delete-task-endpoint`, `QA-delete-task-test-suite`, `BE-task-status-change-endpoint`, `QA-task-status-test-suite` |
| `R-9dc414dc` | backend | `US-create-and-view-tasks`, `US-update-task-details`, `US-delete-task-with-confirmation`, `US-complete-and-reopen-task`, `BE-create-task-endpoint`, `BE-task-update-endpoint`, `BE-delete-task-error-responses`, `QA-delete-task-test-suite`, `BE-task-status-change-endpoint`, `QA-task-status-test-suite` |
| `R-d0e0fe7a` | context_only | — |
| `R-a1b267a3` | frontend | `US-review-task-report`, `US-filter-search-sort-task-report`, `FE-task-report-table`, `QA-task-report-test-suite`, `FE-report-tasks-table`, `QA-task-report-filter-search-sort` |
| `R-5f4ef76c` | functional | `US-filter-search-sort-task-report`, `BE-task-report-query-api`, `FE-report-filter-search-sort-controls`, `QA-task-report-filter-search-sort` |
| `R-48e39a9d` | functional | `US-filter-search-sort-task-report`, `BE-task-report-query-api`, `FE-report-filter-search-sort-controls`, `QA-task-report-filter-search-sort` |
| `R-f214002a` | functional | `US-filter-search-sort-task-report`, `BE-task-report-query-api`, `FE-report-filter-search-sort-controls`, `QA-task-report-filter-search-sort` |
| `R-4ffbfafa` | functional | `US-review-task-report`, `BE-task-report-api-with-counts`, `FE-task-report-count-metrics`, `QA-task-report-test-suite` |
| `R-52360b76` | functional | `US-export-task-report-to-excel`, `BE-excel-file-generation`, `FE-export-button-and-empty-message` |
| `R-09e9d163` | functional | `US-export-task-report-to-excel`, `BE-export-excel-data-query` |
| `R-fad183b1` | non_functional | `US-export-task-report-to-excel`, `BE-excel-file-generation` |
| `R-d22b9b6a` | functional | `US-export-task-report-to-excel`, `BE-excel-file-generation` |
| `R-437992f1` | frontend | `US-export-task-report-to-excel`, `FE-export-button-and-empty-message` |
| `R-8007d6b5` | backend | `US-review-task-report`, `US-filter-search-sort-task-report`, `US-export-task-report-to-excel`, `BE-task-report-api-with-counts`, `QA-task-report-test-suite`, `BE-task-report-query-api`, `QA-task-report-filter-search-sort`, `BE-export-excel-data-query` |
| `R-3a63e0ce` | decision_open | `US-export-task-report-to-excel`, `BE-excel-generation-decision` |
