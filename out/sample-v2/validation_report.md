# Validation report

**Final status:** PASS

## Remaining findings

Every finding still open in the final round of each stage, with the reason it remains.

| Stage | Check | Severity | Item | Finding | Why it remains |
|---|---|---|---|---|---|
| check_plan | P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. | Advisory dependency hint (SPEC §8 lists it as a warning); confirm the ordering at review. |
| check_plan | P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. | Advisory dependency hint (SPEC §8 lists it as a warning); confirm the ordering at review. |
| reference_normalization | REF-CHURN | warning | US-delete-task | Story changed without a requirement change or reviewer decision; code restored the previous version. | Code already applied the stated correction; listed for traceability. |

## Findings per round

### check_requirements — round 1: pass (0 blocking, 0 warnings)

### check_plan — round 1: fail (3 blocking, 5 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-UNREQUESTED | blocking | US-filter-search-sort-report | FE-report-filter-controls (part of this story) limits the Status filter to 'Open and Completed' (DoD 1). The PRD says Status is Open, In Progress, Completed, so In Progress would not be filterable. This misstates the PRD filter. AC1 and the story only mention Open, so the gap is not covered. | Change the Status filter options to Open, In Progress and Completed. |
| CRIT-MISSING | blocking | US-change-task-status | The PRD requires a Status Change endpoint and the data model has Status Open/In Progress/Completed. The endpoint and story only cover setting Completed, yet the plan's own AC5 and task DoD3 need validation of other status values; the QA task also claims 'missing mandatory fields' tests that no AC or endpoint task describes. | Add an AC and endpoint DoD for a missing status value returning a missing mandatory field error, or remove that claim from QA-task-status-tests. |
| CRIT-CONSTRAINT | blocking | US-change-task-status | The story's requirements cite R-d57336f7 (success or error message), but PRD limits that to create/update/delete; fine. However R-9dc414dc 'missing mandatory fields' and 'internal server errors' are cited and no AC covers an internal server or database error from the status endpoint (only the FE edge case). | Add an AC: Given a database error on status change, When the backend processes it, Then it returns an internal error response and the stored status is unchanged. |
| CRIT-PRD-GAP | warning | US-filter-search-sort-report | Story lists open questions about date range target, sort direction and search case, but the AC3 and AC5 are ambiguous without them; the PRD does not say which date the Date Range filter applies to. | Keep it as an open question. |
| CRIT-PRD-GAP | warning | US-create-task | The PRD does not say who sets the Due Date default or whether Due Date and Description are mandatory when creating a task. | List as an open question. |
| CRIT-PRD-GAP | warning | US-change-task-status | The PRD does not say what happens to the Completion Date if a Completed task is moved back to another status, nor whether tasks can be marked back from Completed. | List as an open question. |

### check_plan — round 1: fail (3 blocking, 5 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-UNREQUESTED | blocking | US-filter-search-sort-report | FE-report-filter-controls (part of this story) limits the Status filter to 'Open and Completed' (DoD 1). The PRD says Status is Open, In Progress, Completed, so In Progress would not be filterable. This misstates the PRD filter. AC1 and the story only mention Open, so the gap is not covered. | Change the Status filter options to Open, In Progress and Completed. |
| CRIT-MISSING | blocking | US-change-task-status | The PRD requires a Status Change endpoint and the data model has Status Open/In Progress/Completed. The endpoint and story only cover setting Completed, yet the plan's own AC5 and task DoD3 need validation of other status values; the QA task also claims 'missing mandatory fields' tests that no AC or endpoint task describes. | Add an AC and endpoint DoD for a missing status value returning a missing mandatory field error, or remove that claim from QA-task-status-tests. |
| CRIT-CONSTRAINT | blocking | US-change-task-status | The story's requirements cite R-d57336f7 (success or error message), but PRD limits that to create/update/delete; fine. However R-9dc414dc 'missing mandatory fields' and 'internal server errors' are cited and no AC covers an internal server or database error from the status endpoint (only the FE edge case). | Add an AC: Given a database error on status change, When the backend processes it, Then it returns an internal error response and the stored status is unchanged. |
| CRIT-PRD-GAP | warning | US-filter-search-sort-report | Story lists open questions about date range target, sort direction and search case, but the AC3 and AC5 are ambiguous without them; the PRD does not say which date the Date Range filter applies to. | Keep it as an open question. |
| CRIT-PRD-GAP | warning | US-create-task | The PRD does not say who sets the Due Date default or whether Due Date and Description are mandatory when creating a task. | List as an open question. |
| CRIT-PRD-GAP | warning | US-change-task-status | The PRD does not say what happens to the Completion Date if a Completed task is moved back to another status, nor whether tasks can be marked back from Completed. | List as an open question. |

### check_plan — round 2: pass (0 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |

### check_plan — round 2: pass (0 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |

### reference_normalization — round 0: pass (0 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| REF-CHURN | warning | US-delete-task | Story changed without a requirement change or reviewer decision; code restored the previous version. |  |

## Coverage matrix

| Requirement | Kind | Tickets |
|---|---|---|
| `R-a62b5beb` | context_only | `EPIC-personal-task-management-and-status` |
| `R-f7f96b9a` | context_only | `EPIC-personal-task-management-and-status` |
| `R-eed06908` | functional | `EPIC-personal-task-management-and-status`, `US-view-task-list`, `FE-task-list-view`, `QA-task-list-test-suite` |
| `R-22f28530` | functional | `US-create-task`, `BE-create-task-endpoint`, `FE-task-creation-form`, `QA-create-task-test-suite` |
| `R-4bed9064` | functional | `US-view-task-list`, `BE-tasks-list-endpoint`, `QA-task-list-test-suite` |
| `R-bc3213df` | functional | `US-update-task`, `BE-put-task-endpoint-with-validation`, `FE-task-edit-form-prefill`, `QA-task-update-test-suite` |
| `R-8523b9ec` | functional | `US-delete-task`, `BE-delete-task-endpoint`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-2304218f` | functional | `US-change-task-status`, `BE-task-status-endpoint`, `FE-task-status-toggle`, `QA-task-status-tests` |
| `R-82fe7dda` | context_only | — |
| `R-9675bb49` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-aaf23206` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-c9046f7a` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-576b7e59` | data_model | `US-create-task`, `US-change-task-status`, `BE-tasks-table-migration`, `QA-task-status-tests` |
| `R-9fb58566` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-1c2262bc` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-71bdd372` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-31569dba` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-34e41747` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-03df7815` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `FE-task-creation-form`, `QA-create-task-test-suite`, `BE-put-task-endpoint-with-validation`, `FE-task-update-result-messages`, `QA-task-update-test-suite` |
| `R-efe1e5d4` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `FE-task-creation-form`, `QA-create-task-test-suite`, `BE-put-task-endpoint-with-validation`, `FE-task-update-result-messages`, `QA-task-update-test-suite` |
| `R-0b1853d6` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `BE-put-task-endpoint-with-validation` |
| `R-8ef41ba1` | frontend | `US-delete-task`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-d57336f7` | frontend | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `FE-task-creation-form`, `QA-create-task-test-suite`, `QA-task-list-test-suite`, `FE-task-update-result-messages`, `QA-task-update-test-suite`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite`, `FE-task-status-feedback`, `QA-task-status-tests` |
| `R-ab9e9cb0` | constraint | `US-create-task`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `FE-task-creation-form`, `QA-create-task-test-suite`, `FE-task-update-result-messages`, `QA-task-update-test-suite`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite`, `FE-task-status-toggle`, `FE-task-status-feedback`, `QA-task-status-tests` |
| `R-60e02b8e` | frontend | `US-view-task-list`, `FE-task-list-view`, `QA-task-list-test-suite` |
| `R-9b30a145` | frontend | `US-create-task`, `US-update-task`, `FE-task-creation-form`, `FE-task-edit-form-prefill`, `FE-task-row-edit-action`, `QA-task-update-test-suite` |
| `R-48c89e9e` | frontend | `US-view-task-list`, `FE-task-list-view`, `QA-task-list-test-suite` |
| `R-d7e6667f` | frontend | `US-view-task-list`, `FE-task-list-states`, `QA-task-list-test-suite` |
| `R-6a73fa71` | frontend | `US-view-task-list`, `FE-task-list-auto-refresh`, `QA-task-list-test-suite` |
| `R-c55a77b3` | backend | `US-create-task`, `BE-tasks-table-migration` |
| `R-244669c0` | backend | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-create-task-endpoint`, `BE-tasks-list-endpoint`, `BE-task-by-id-endpoint`, `QA-task-list-test-suite`, `BE-put-task-endpoint-with-validation`, `QA-task-update-test-suite`, `BE-delete-task-endpoint`, `BE-task-status-endpoint`, `QA-task-status-tests` |
| `R-9dc414dc` | backend | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-create-task-endpoint`, `QA-create-task-test-suite`, `BE-tasks-list-endpoint`, `BE-task-by-id-endpoint`, `QA-task-list-test-suite`, `BE-put-task-error-responses`, `QA-task-update-test-suite`, `BE-delete-task-endpoint`, `QA-delete-task-test-suite`, `BE-task-status-endpoint`, `QA-task-status-tests` |
| `R-d0e0fe7a` | frontend | `EPIC-personal-task-management-and-status`, `US-view-task-report`, `FE-report-page-table`, `QA-report-test-suite` |
| `R-a1b267a3` | frontend | `US-view-task-report`, `FE-report-page-table`, `QA-report-test-suite` |
| `R-5f4ef76c` | functional | `US-filter-search-sort-report`, `BE-report-query-filter-search-sort`, `FE-report-filter-controls`, `QA-report-filter-search-sort-tests` |
| `R-48e39a9d` | functional | `US-filter-search-sort-report`, `BE-report-query-filter-search-sort`, `FE-report-search-and-sort-ui`, `QA-report-filter-search-sort-tests` |
| `R-d482bfea` | functional | `US-filter-search-sort-report`, `BE-report-query-filter-search-sort`, `FE-report-search-and-sort-ui`, `QA-report-filter-search-sort-tests` |
| `R-4ffbfafa` | frontend | `US-view-task-report`, `FE-report-metrics-cards`, `QA-report-test-suite` |
| `R-52360b76` | functional | `US-export-report-excel`, `BE-task-report-excel-generator`, `FE-report-excel-download-action`, `QA-excel-export-test-suite` |
| `R-09e9d163` | functional | `US-export-report-excel`, `BE-task-report-excel-generator`, `FE-report-excel-download-action`, `QA-excel-export-test-suite` |
| `R-fad183b1` | constraint | `US-export-report-excel`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |
| `R-d22b9b6a` | functional | `US-export-report-excel`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |
| `R-437992f1` | frontend | `US-export-report-excel`, `FE-report-export-no-data-message`, `QA-excel-export-test-suite` |
| `R-8007d6b5` | backend | `US-view-task-report`, `US-filter-search-sort-report`, `US-export-report-excel`, `BE-report-metrics-endpoint`, `QA-report-test-suite`, `BE-report-query-filter-search-sort`, `QA-report-filter-search-sort-tests`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |
| `R-3a63e0ce` | decision_open | `US-export-report-excel`, `BE-excel-export-generation-decision` |
