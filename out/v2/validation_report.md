# Validation report

**Final status:** PASS

## Remaining findings

Every finding still open in the final round of each stage, with the reason it remains.

| Stage | Check | Severity | Item | Finding | Why it remains |
|---|---|---|---|---|---|
| reference_normalization | REF-CHURN | warning | US-delete-task | Story changed without a requirement change or reviewer decision; code restored the previous version. | Code already applied the stated correction; listed for traceability. |
| reference_normalization | REF-CHURN | warning | BE-status-change-error-handling | Task changed without a requirement change or reviewer decision; code restored the previous version. | Code already applied the stated correction; listed for traceability. |
| reference_normalization | REF-CHURN | warning | BE-report-api-sort-parameter | Task changed without a requirement change or reviewer decision; code restored the previous version. | Code already applied the stated correction; listed for traceability. |
| reference_normalization | REF-STORY | warning | US-sort-report-tasks | Dropped unknown story dependency key(s): US-task-report-page. | Code already applied the stated correction; listed for traceability. |

## Findings per round

### check_requirements — round 1: pass (0 blocking, 0 warnings)

### check_plan — round 1: fail (3 blocking, 3 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-MISREPRESENTED | blocking | US-change-task-status | AC5 and BE-status-change-error-handling treat a status value 'other than Open or Completed' as invalid, yet the endpoint is described as only setting Completed. The PRD only requires marking a task as Completed. Accepting Open and rejecting In Progress is an invented rule that also conflicts with the plan's statement that reverting to Open is not required. | Make AC5 consistent with the endpoint: accept only Completed, reject any other value with an invalid input error. Align the error-handling task accordingly. |
| CRIT-UNREQUESTED | warning | US-change-task-status | Edge cases mention that the Completion Date is kept or cleared if status is changed by another path, and a revert to Open. The PRD defines no such path, which only creates confusion. | Remove these edge cases or leave only the open question about re-marking Completed. |
| CRIT-UNTESTABLE-AC | blocking | US-sort-report-tasks | AC1-AC5 do not define a sort direction ('ascending or descending, as defined by the sort control') or Status/Priority ordering ('reordered by the Status field'). A tester cannot verify the resulting order. | State a concrete order in each AC, for example ascending by default and a rank for Status and Priority, or add a direction control and test both directions. |
| CRIT-MISSING | blocking | US-create-task | The US-create-task ACs and tasks do not cover the Last Updated Date being updated on update. Separately, the update story (US-update-task) has no AC or task stating that Last Updated Date is set on update, and the status change story does not update it either, so the data model field R-31569dba is only set on create. | Add to BE-task-update-endpoint and the update ACs that Last Updated Date is set on every update, and the same for the status change. |
| CRIT-CONSTRAINT | warning | US-update-task | The update story cites R-9dc414dc (missing mandatory fields, invalid input, internal/database errors) but its ACs cover only not-found and validation errors. A database/internal error on update is not reflected in an AC. | Add an AC: Given the database is unavailable, When an update request is sent, Then the backend returns an internal server or database error and the stored task is unchanged. |
| CRIT-MISSING | warning | QA-status-change-test-suite | The QA task omits R-ab9e9cb0 coverage for the pending state only partially, and AC3 (pending request) is hard to test; also the FE task is named 'status-toggle-control' although no toggle exists. | Rename FE-status-toggle-control to a 'Mark as Completed' control and specify the pending-state test in the QA task. |

### check_plan — round 2: fail (4 blocking, 0 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-MISSING | blocking | US-sort-report-tasks | The PRD requires sorting by Title, but the task BE-report-api-sort-parameter accepts only creation_date, due_date, status or priority. AC6 and AC7 and the FE task require title sorting through the API. The backend would reject or not implement the title sort, so the Title sort is only partly delivered. | Add title to the accepted values in BE-report-api-sort-parameter, so that it matches AC6, AC7 and the five FE sort options. |
| CRIT-UNTESTABLE-AC | blocking | US-sort-report-tasks | AC4 orders priority 'from the lowest priority value to the highest'. AC3 says 'Open before Completed' but does not place In Progress. The PRD allows three statuses (Open, In Progress, Completed), so the order of In Progress tasks is undefined and a tester cannot verify the Status order. | State the full Status order explicitly (Open, In Progress, Completed) in AC3, and state Low, Medium, High for Priority in AC4. Update the FE and QA tasks to match. |
| CRIT-MISREPRESENTED | blocking | US-change-task-status | AC5 and BE-status-change-error-handling treat a status value 'other than Open or Completed' as invalid, yet the endpoint is described as only setting Completed. The PRD only requires marking a task as Completed. Accepting Open and rejecting In Progress is an invented rule that also conflicts with the plan's statement that reverting to Open is not required. | Make AC5 consistent with the endpoint: accept only Completed, reject any other value with an invalid input error. Align the error-handling task accordingly. |
| CRIT-MISSING | blocking | US-create-task | The US-create-task ACs and tasks do not cover the Last Updated Date being updated on update. Separately, the update story (US-update-task) has no AC or task stating that Last Updated Date is set on update, and the status change story does not update it either, so the data model field R-31569dba is only set on create. | Add to BE-task-update-endpoint and the update ACs that Last Updated Date is set on every update, and the same for the status change. |

### check_plan — round 1: fail (5 blocking, 0 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-MISREPRESENTED | blocking | US-change-task-status | AC5 and BE-status-change-error-handling treat a status value 'other than Open or Completed' as invalid, yet the endpoint is described as only setting Completed. The PRD only requires marking a task as Completed. Accepting Open and rejecting In Progress is an invented rule that also conflicts with the plan's statement that reverting to Open is not required. | Make AC5 consistent with the endpoint: accept only Completed, reject any other value with an invalid input error. Align the error-handling task accordingly. |
| CRIT-UNTESTABLE-AC | blocking | US-sort-report-tasks | AC1-AC5 do not define a sort direction ('ascending or descending, as defined by the sort control') or Status/Priority ordering ('reordered by the Status field'). A tester cannot verify the resulting order. | State a concrete order in each AC, for example ascending by default and a rank for Status and Priority, or add a direction control and test both directions. |
| CRIT-MISSING | blocking | US-create-task | The US-create-task ACs and tasks do not cover the Last Updated Date being updated on update. Separately, the update story (US-update-task) has no AC or task stating that Last Updated Date is set on update, and the status change story does not update it either, so the data model field R-31569dba is only set on create. | Add to BE-task-update-endpoint and the update ACs that Last Updated Date is set on every update, and the same for the status change. |
| CRIT-MISSING | blocking | US-sort-report-tasks | The PRD requires sorting by Title, but the task BE-report-api-sort-parameter accepts only creation_date, due_date, status or priority. AC6 and AC7 and the FE task require title sorting through the API. The backend would reject or not implement the title sort, so the Title sort is only partly delivered. | Add title to the accepted values in BE-report-api-sort-parameter, so that it matches AC6, AC7 and the five FE sort options. |
| CRIT-UNTESTABLE-AC | blocking | US-sort-report-tasks | AC4 orders priority 'from the lowest priority value to the highest'. AC3 says 'Open before Completed' but does not place In Progress. The PRD allows three statuses (Open, In Progress, Completed), so the order of In Progress tasks is undefined and a tester cannot verify the Status order. | State the full Status order explicitly (Open, In Progress, Completed) in AC3, and state Low, Medium, High for Priority in AC4. Update the FE and QA tasks to match. |

### check_plan — round 1: fail (10 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-MISSING | blocking | US-update-task | Last Updated Date (R-31569dba) is set only on create. No AC or task in US-update-task or US-change-task-status says it is updated when a task is edited or its status changes. | Add an AC and an update-endpoint task statement that the backend sets Last Updated Date on every update and status change. |
| CRIT-MISSING | blocking | US-update-task | Reviewer decision says the edit form can set Status to Open or In Progress, but the edit form task, update endpoint and ACs do not cover Status editing or Status validation. New tasks start as Open is also not in the create ACs. | Add ACs and task text: the edit form sets Status to Open or In Progress, and the update endpoint rejects Completed. Add an AC to the create story that new tasks have status Open. |
| CRIT-MISSING | blocking | US-sort-report-tasks | BE-report-api-sort-parameter accepts only creation_date, due_date, status or priority, but the PRD requires sorting by Title and AC6 and AC7 expect title to work. Title sorting is only partly delivered. | Add title to the accepted sort values in BE-report-api-sort-parameter. |
| CRIT-MISREPRESENTED | blocking | US-change-task-status | AC5 and BE-status-change-error-handling treat 'other than Open or Completed' as the invalid-status rule, but the endpoint only sets Completed and the plan says revert to Open is not required. This is an invented rule. | Make the endpoint accept only Completed and reject any other value with an invalid-input error. Update AC5 and the task text. |
| CRIT-UNTESTABLE-AC | blocking | US-sort-report-tasks | AC1-AC5 do not define a sort direction ('ascending or descending, as defined by the sort control') or the order of Status and Priority values. A tester cannot verify the resulting order. | Fix a direction per field, or add a direction control. State the order Open < In Progress < Completed and Low < Medium < High. |
| CRIT-MISSING | warning | US-export-report-excel | QA-export-excel-test-suite lists no requirements, so no export requirement is traced to its tests. | Add R-52360b76, R-09e9d163, R-fad183b1, R-d22b9b6a and R-437992f1 to the QA task. |
| CRIT-MISREPRESENTED | blocking | US-change-task-status | AC5 and BE-status-change-error-handling treat a status value 'other than Open or Completed' as invalid, yet the endpoint is described as only setting Completed. The PRD only requires marking a task as Completed. Accepting Open and rejecting In Progress is an invented rule that also conflicts with the plan's statement that reverting to Open is not required. | Make AC5 consistent with the endpoint: accept only Completed, reject any other value with an invalid input error. Align the error-handling task accordingly. |
| CRIT-UNTESTABLE-AC | blocking | US-sort-report-tasks | AC1-AC5 do not define a sort direction ('ascending or descending, as defined by the sort control') or Status/Priority ordering ('reordered by the Status field'). A tester cannot verify the resulting order. | State a concrete order in each AC, for example ascending by default and a rank for Status and Priority, or add a direction control and test both directions. |
| CRIT-MISSING | blocking | US-create-task | The US-create-task ACs and tasks do not cover the Last Updated Date being updated on update. Separately, the update story (US-update-task) has no AC or task stating that Last Updated Date is set on update, and the status change story does not update it either, so the data model field R-31569dba is only set on create. | Add to BE-task-update-endpoint and the update ACs that Last Updated Date is set on every update, and the same for the status change. |
| CRIT-MISSING | blocking | US-sort-report-tasks | The PRD requires sorting by Title, but the task BE-report-api-sort-parameter accepts only creation_date, due_date, status or priority. AC6 and AC7 and the FE task require title sorting through the API. The backend would reject or not implement the title sort, so the Title sort is only partly delivered. | Add title to the accepted values in BE-report-api-sort-parameter, so that it matches AC6, AC7 and the five FE sort options. |
| CRIT-UNTESTABLE-AC | blocking | US-sort-report-tasks | AC4 orders priority 'from the lowest priority value to the highest'. AC3 says 'Open before Completed' but does not place In Progress. The PRD allows three statuses (Open, In Progress, Completed), so the order of In Progress tasks is undefined and a tester cannot verify the Status order. | State the full Status order explicitly (Open, In Progress, Completed) in AC3, and state Low, Medium, High for Priority in AC4. Update the FE and QA tasks to match. |

### check_plan — round 2: pass (0 blocking, 0 warnings)

### check_plan — round 2: fail (1 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-CONSTRAINT | blocking | US-change-task-status | The PRD says success or error messages must be displayed after create/update/delete actions, and the story cites R-d57336f7 via the status change. No AC requires a success message after a successful Mark as Completed. AC1 only checks the stored status and the list; AC2 covers the error message, and AC3 requires no success message while pending. | Add an AC: Given a task with status Open or In Progress, When the user marks it Completed and the backend returns success, Then a success message is displayed and the row shows Completed. |
| CRIT-MISSING | warning | US-change-task-status | The story's requirement list lacks R-d57336f7 (success or error messages), and the tasks FE-status-toggle-control and QA-status-change-test-suite do not cover the success message. | Add R-d57336f7 to the story and FE-status-toggle-control. Require showing a success message after backend confirmation, and add the check to the QA suite. |

### check_plan — round 3: pass (0 blocking, 0 warnings)

### check_plan — round 2: pass (0 blocking, 0 warnings)

### reference_normalization — round 0: pass (0 blocking, 4 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| REF-STORY | warning | US-sort-report-tasks | Dropped unknown story dependency key(s): US-task-report-page. |  |
| REF-CHURN | warning | US-delete-task | Story changed without a requirement change or reviewer decision; code restored the previous version. |  |
| REF-CHURN | warning | BE-status-change-error-handling | Task changed without a requirement change or reviewer decision; code restored the previous version. |  |
| REF-CHURN | warning | BE-report-api-sort-parameter | Task changed without a requirement change or reviewer decision; code restored the previous version. |  |

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
| `R-d57336f7` | frontend | `US-create-task`, `US-update-task`, `US-delete-task`, `FE-create-task-form`, `QA-create-task-test-suite`, `FE-task-edit-form`, `QA-task-update-tests`, `FE-delete-result-feedback`, `QA-delete-task-test-suite` |
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
