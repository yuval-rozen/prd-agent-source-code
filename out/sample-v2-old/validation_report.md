# Validation report

**Final status:** PASS

## Remaining findings

None.

## Findings per round

### check_requirements — round 1: pass (0 blocking, 0 warnings)

### check_plan — round 1: fail (2 blocking, 0 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P12 | blocking | US-change-task-status | edge case 3 contains a requirement ID, 'requirement ID', 'the PRD text' (internal note, not product language): 'The PRD text for this story does not include the requirement ID for success and error messages (R-d57336f7); the success message wording is not specified.' | Rewrite it in plain product language; state an open question plainly (for example 'The wording of the confirmation message is not specified.'). |
| P12 | blocking | US-update-task | edge case 2 contains 'reviewer decision' (internal note, not product language): 'Editing a task that is already Completed: the PRD and reviewer decision do not state whether its Status can be changed back by the edit form. This is an open qu' | Rewrite it in plain product language; state an open question plainly (for example 'The wording of the confirmation message is not specified.'). |

### check_plan — round 2: pass (0 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-MISSING | warning | US-change-task-status | The US-create-task edge case says Last Updated Date on status change is covered by the status change story. None of the status change ACs or tasks say Last Updated Date is set when a task is marked Completed. The PRD data model requires a Last Updated Date field. | Add an AC to US-change-task-status: Given a task is marked Completed, When the backend saves the change, Then its Last Updated Date is set to the time of the change. Add the same behaviour to the description of BE-status-change-endpoint. |

### check_plan — round 2: pass (0 blocking, 0 warnings)

### reference_normalization — round 0: pass (0 blocking, 0 warnings)

## Coverage matrix

| Requirement | Kind | Tickets |
|---|---|---|
| `R-a62b5beb` | context_only | — |
| `R-f7f96b9a` | context_only | — |
| `R-eed06908` | functional | `US-view-task-list`, `FE-task-list-view` |
| `R-22f28530` | functional | `US-create-task`, `BE-create-task-endpoint`, `QA-create-task-test-suite` |
| `R-4bed9064` | functional | `US-view-task-list`, `BE-tasks-read-endpoints`, `QA-task-list-qa` |
| `R-bc3213df` | functional | `US-update-task`, `BE-task-update-endpoint`, `FE-task-edit-form`, `QA-task-update-tests` |
| `R-8523b9ec` | functional | `US-delete-task`, `BE-delete-task-endpoint`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-2304218f` | functional | `US-change-task-status`, `BE-status-change-endpoint`, `FE-status-toggle-control`, `QA-status-change-test-suite` |
| `R-82fe7dda` | context_only | — |
| `R-9675bb49` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-aaf23206` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-c9046f7a` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-576b7e59` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-9fb58566` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-1c2262bc` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-71bdd372` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-31569dba` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-34e41747` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-03df7815` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `QA-create-task-test-suite`, `BE-task-update-endpoint`, `QA-task-update-tests` |
| `R-efe1e5d4` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `QA-create-task-test-suite`, `BE-task-update-endpoint`, `QA-task-update-tests` |
| `R-0b1853d6` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `BE-task-update-endpoint` |
| `R-8ef41ba1` | frontend | `US-delete-task`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-d57336f7` | frontend | `US-create-task`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `FE-create-task-form`, `QA-create-task-test-suite`, `FE-task-edit-form`, `QA-task-update-tests`, `FE-delete-result-feedback`, `QA-delete-task-test-suite` |
| `R-ab9e9cb0` | constraint | `US-create-task`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `FE-create-task-form`, `QA-create-task-test-suite`, `FE-task-edit-form`, `QA-task-update-tests`, `FE-delete-result-feedback`, `QA-delete-task-test-suite`, `FE-status-toggle-control`, `QA-status-change-test-suite` |
| `R-60e02b8e` | frontend | `US-view-task-list`, `FE-task-list-view` |
| `R-9b30a145` | frontend | `US-create-task`, `US-update-task`, `FE-create-task-form`, `FE-task-edit-form`, `QA-task-update-tests` |
| `R-48c89e9e` | frontend | `US-view-task-list`, `FE-task-list-view` |
| `R-d7e6667f` | frontend | `US-view-task-list`, `FE-task-list-view`, `QA-task-list-qa` |
| `R-6a73fa71` | frontend | `US-view-task-list`, `FE-task-list-auto-refresh`, `QA-task-list-qa` |
| `R-c55a77b3` | backend | `US-create-task`, `BE-tasks-table-migration` |
| `R-244669c0` | backend | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-tasks-read-endpoints`, `BE-task-update-endpoint`, `QA-task-update-tests`, `BE-delete-task-endpoint`, `QA-delete-task-test-suite`, `BE-status-change-endpoint`, `QA-status-change-test-suite` |
| `R-9dc414dc` | backend | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-tasks-read-endpoints`, `BE-task-update-endpoint`, `QA-task-update-tests`, `BE-delete-task-error-handling`, `QA-delete-task-test-suite`, `BE-status-change-error-handling`, `QA-status-change-test-suite` |
| `R-d0e0fe7a` | frontend | `US-view-task-report`, `FE-task-report-page-table`, `QA-task-report-test-suite` |
| `R-a1b267a3` | frontend | `US-view-task-report`, `FE-task-report-page-table`, `QA-task-report-test-suite` |
| `R-5f4ef76c` | functional | `US-filter-report-tasks`, `FE-report-filter-controls`, `QA-report-filter-tests` |
| `R-48e39a9d` | functional | `US-search-report-tasks`, `FE-report-title-search-input`, `QA-report-title-search-tests` |
| `R-d482bfea` | functional | `US-sort-report-tasks`, `FE-report-table-sort-control`, `QA-report-sort-test-suite` |
| `R-4ffbfafa` | frontend | `US-view-task-report`, `FE-report-metric-cards`, `QA-task-report-test-suite` |
| `R-52360b76` | functional | `US-export-report-excel`, `BE-export-report-tasks-endpoint`, `FE-export-to-excel-button` |
| `R-09e9d163` | functional | `US-export-report-excel`, `BE-export-report-tasks-endpoint`, `FE-export-to-excel-button` |
| `R-fad183b1` | non_functional | `US-export-report-excel`, `FE-excel-file-build-and-naming` |
| `R-d22b9b6a` | functional | `US-export-report-excel`, `FE-excel-file-build-and-naming` |
| `R-437992f1` | frontend | `US-export-report-excel`, `FE-export-to-excel-button` |
| `R-8007d6b5` | backend | `US-view-task-report`, `US-filter-report-tasks`, `US-search-report-tasks`, `US-sort-report-tasks`, `BE-report-endpoint-with-metrics`, `QA-task-report-test-suite`, `BE-report-tasks-filter-api`, `QA-report-filter-tests`, `BE-report-title-search-api`, `QA-report-title-search-tests`, `BE-report-api-sort-parameter`, `QA-report-sort-test-suite` |
| `R-3a63e0ce` | decision_open | `US-export-report-excel`, `BE-excel-generation-location-decision` |
