# Validation report

**Final status:** NEEDS_REVIEW

- check_plan: stopped: blocking findings did not decrease (1 -> 2); kept the plan of round 2 (1 blocking) instead of round 3 (2 blocking)

## Remaining findings

Every finding still open in the final round of each stage, with the reason it remains.

| Stage | Check | Severity | Item | Finding | Why it remains |
|---|---|---|---|---|---|
| check_plan | CRIT-MISSING | blocking | US-create-task | The PRD requires a Last Updated Date on each task, but no create AC or task sets it on creation. The Creation Date is also never set by the backend; ACs assume it is supplied by the form. The PRD does not say how it is populated. Suggested fix: In BE-create-task-endpoint, state that Creation Date and Last Updated Date are set by the backend on create. Add an AC for both. | Not resolved: stopped: blocking findings did not decrease (1 -> 2); kept the plan of round 2 (1 blocking) instead of round 3 (2 blocking). Needs a human decision at G1 (approve, feedback or abort). |

## Findings per round

### check_requirements — round 1: pass (0 blocking, 0 warnings)

### check_plan — round 1: fail (6 blocking, 0 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P2 | blocking | QA-create-task-test-suite | Task cites no requirement and has no derived_reason. | Cite the requirement it implements, or set derived_reason. |
| P2 | blocking | QA-report-sort-test-suite | Task cites no requirement and has no derived_reason. | Cite the requirement it implements, or set derived_reason. |
| P11 | blocking | BE-report-endpoint-with-metrics | Title is 86 characters (max 80): '[BE] Add GET report endpoint returning all tasks with Total, Open and Completed counts' | Shorten it while keeping the object it names. |
| P11 | blocking | FE-create-task-form | Title is 81 characters (max 80): '[FE] Add task creation form with title, description, priority and due date fields' | Shorten it while keeping the object it names. |
| P11 | blocking | FE-delete-result-feedback | Title is 81 characters (max 80): '[FE] Show success or error message after task deletion without optimistic removal' | Shorten it while keeping the object it names. |
| CRIT-MISSING | blocking | US-change-task-status | The PRD requires success or error messages after create/update/delete actions; the story's AC3 only shows an error. This is minor, but the status change story AC1/AC2 do not state a success state. More importantly, the story has no AC for the optimistic-UI constraint (R-ab9e9cb0) on success. | Add an AC: Given a status change request is pending, When the backend has not responded, Then the row still shows the previous status. |

### check_plan — round 2: fail (1 blocking, 0 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-MISSING | blocking | US-create-task | The PRD requires a Last Updated Date on each task, but no create AC or task sets it on creation. The Creation Date is also never set by the backend; ACs assume it is supplied by the form. The PRD does not say how it is populated. | In BE-create-task-endpoint, state that Creation Date and Last Updated Date are set by the backend on create. Add an AC for both. |

### check_plan — round 3: fail (2 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-UNREQUESTED | warning | US-create-task | AC5 and the story state that Last Updated Date equals Creation Date and that the backend sets both at creation. The PRD does not say how these fields are populated. The edge cases flag this as an open question, yet the AC states it as fact and makes it testable. | Remove the 'Last Updated Date equals the Creation Date' clause from AC5, or keep it only as a documented assumption confirmed with the team. |
| CRIT-UNTESTABLE-AC | blocking | US-create-task | AC1 says 'all other required inputs valid', but the PRD names only the title as mandatory. Which other inputs are required is undefined, so the AC cannot be verified as written. | Rewrite AC1 with concrete values, for example Title 'Buy milk', Priority 'Medium' and Due Date 2024-05-12, and state the expected stored values. |
| CRIT-MISSING | blocking | FE-create-task-form | The PRD requires a task creation/editing form with Status and Priority. The create form task covers only Title, Description, Priority and Due Date. Status cannot be set on create, and the PRD does not state a default. The task also does not mention Status. Neither the AC nor the task resolves this. | State in the form task and AC1 whether Status is selectable on create or defaulted, for example to Open, and mark the default as an open question if the team has not confirmed it. |
| CRIT-OVERLAP | warning | QA-create-task-test-suite | The task has no requirement IDs and its scope ('API, database and form') is broad. It overlaps with the QA coverage of the same endpoint and form in the update test suite, which reuses the same form. | Link the QA task to R-22f28530, R-03df7815, R-efe1e5d4, R-d57336f7 and R-ab9e9cb0, and limit it to create-only behaviour. |

### check_plan — round 2: fail (1 blocking, 0 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| CRIT-MISSING | blocking | US-create-task | The PRD requires a Last Updated Date on each task, but no create AC or task sets it on creation. The Creation Date is also never set by the backend; ACs assume it is supplied by the form. The PRD does not say how it is populated. | In BE-create-task-endpoint, state that Creation Date and Last Updated Date are set by the backend on create. Add an AC for both. |

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
| `R-959e2960` | functional | `US-change-task-status`, `BE-status-change-endpoint`, `FE-status-toggle-control`, `QA-status-change-test-suite` |
| `R-82fe7dda` | context_only | — |
| `R-9675bb49` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-aaf23206` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-c9046f7a` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-576b7e59` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-9fb58566` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-1c2262bc` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-71bdd372` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-31569dba` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-34e41747` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-03df7815` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `QA-create-task-test-suite`, `BE-task-update-endpoint`, `QA-task-update-tests` |
| `R-efe1e5d4` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `QA-create-task-test-suite`, `BE-task-update-endpoint`, `QA-task-update-tests` |
| `R-8ef41ba1` | frontend | `US-delete-task`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
| `R-d57336f7` | frontend | `US-create-task`, `US-update-task`, `US-delete-task`, `FE-create-task-form`, `FE-task-edit-form`, `QA-task-update-tests`, `FE-delete-result-feedback`, `QA-delete-task-test-suite` |
| `R-ab9e9cb0` | constraint | `US-create-task`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `FE-create-task-form`, `FE-task-edit-form`, `QA-task-update-tests`, `FE-delete-result-feedback`, `QA-delete-task-test-suite`, `FE-status-toggle-control`, `QA-status-change-test-suite` |
| `R-60e02b8e` | frontend | `US-view-task-list`, `FE-task-list-view` |
| `R-9b30a145` | frontend | `US-create-task`, `US-update-task`, `FE-create-task-form`, `FE-task-edit-form`, `QA-task-update-tests` |
| `R-48c89e9e` | frontend | `US-view-task-list`, `FE-task-list-view` |
| `R-d7e6667f` | frontend | `US-view-task-list`, `FE-task-list-view`, `QA-task-list-qa` |
| `R-6a73fa71` | frontend | `US-view-task-list`, `FE-task-list-auto-refresh`, `QA-task-list-qa` |
| `R-c55a77b3` | backend | `US-create-task`, `BE-tasks-table-migration` |
| `R-244669c0` | backend | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-create-task-endpoint`, `BE-tasks-read-endpoints`, `BE-task-update-endpoint`, `QA-task-update-tests`, `BE-delete-task-endpoint`, `QA-delete-task-test-suite`, `BE-status-change-endpoint`, `QA-status-change-test-suite` |
| `R-9dc414dc` | backend | `US-create-task`, `US-view-task-list`, `US-update-task`, `US-delete-task`, `US-change-task-status`, `BE-create-task-endpoint`, `BE-tasks-read-endpoints`, `BE-task-update-endpoint`, `QA-task-update-tests`, `BE-delete-task-error-handling`, `QA-delete-task-test-suite`, `BE-status-change-error-handling`, `QA-status-change-test-suite` |
| `R-d0e0fe7a` | frontend | `US-view-task-report`, `FE-task-report-page-table`, `QA-task-report-test-suite` |
| `R-a1b267a3` | frontend | `US-view-task-report`, `FE-task-report-page-table`, `QA-task-report-test-suite` |
| `R-5f4ef76c` | functional | `US-filter-report-tasks`, `FE-report-filter-controls`, `QA-report-filter-tests` |
| `R-48e39a9d` | functional | `US-search-report-tasks`, `FE-report-title-search-input`, `QA-report-title-search-tests` |
| `R-f214002a` | functional | `US-sort-report-tasks`, `FE-report-table-sort-control`, `QA-report-sort-test-suite` |
| `R-4ffbfafa` | frontend | `US-view-task-report`, `FE-report-metric-cards`, `QA-task-report-test-suite` |
| `R-52360b76` | functional | `US-export-report-excel`, `BE-export-report-tasks-endpoint`, `FE-export-to-excel-button` |
| `R-09e9d163` | functional | `US-export-report-excel`, `BE-export-report-tasks-endpoint`, `FE-export-to-excel-button` |
| `R-fad183b1` | non_functional | `US-export-report-excel`, `FE-excel-file-build-and-naming` |
| `R-d22b9b6a` | functional | `US-export-report-excel`, `FE-excel-file-build-and-naming` |
| `R-437992f1` | frontend | `US-export-report-excel`, `FE-export-to-excel-button` |
| `R-8007d6b5` | backend | `US-view-task-report`, `US-filter-report-tasks`, `US-search-report-tasks`, `US-sort-report-tasks`, `BE-report-endpoint-with-metrics`, `QA-task-report-test-suite`, `BE-report-tasks-filter-api`, `QA-report-filter-tests`, `BE-report-title-search-api`, `QA-report-title-search-tests`, `BE-report-api-sort-parameter`, `QA-report-sort-test-suite` |
| `R-3a63e0ce` | decision_open | `US-export-report-excel`, `BE-excel-generation-location-decision` |
