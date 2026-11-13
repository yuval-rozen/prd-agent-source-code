# Validation report

**Final status:** PASS

## Remaining findings

Every finding still open in the final round of each stage, with the reason it remains.

| Stage | Check | Severity | Item | Finding | Why it remains |
|---|---|---|---|---|---|
| check_plan | CRIT-PRD-GAP | warning | US-update-task | The story lists open questions on space-only titles, Status/Priority editing and concurrent saves, but not on whether a changed Due Date is compared to the original Creation Date or whether the user can change the Completion Date through the form. The PRD does not say whether the edit form can change the Completion Date. Suggested fix: Add an open question to the story for the Completion Date. | Non-blocking critic suggestion; it does not stop the pipeline. |
| check_plan | P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. | Advisory dependency hint (SPEC §8 lists it as a warning); confirm the ordering at review. |
| check_plan | P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. | Advisory dependency hint (SPEC §8 lists it as a warning); confirm the ordering at review. |

## Findings per round

### check_requirements — round 1: pass (0 blocking, 0 warnings)

### check_plan — round 1: fail (9 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P2 | blocking | QA-create-task-tests | Task cites no requirement and has no derived_reason. | Cite the requirement it implements, or set derived_reason. |
| P11 | blocking | BE-report-query-filter-search-sort | Title is 83 characters (max 80): '[BE] Add filter, title search and sort parameters to the task report query endpoint' | Shorten it while keeping the object it names. |
| P11 | blocking | FE-task-update-feedback | Title is 92 characters (max 80): '[FE] Show success or error message after a task update and keep failed edits out of the list' | Shorten it while keeping the object it names. |
| CRIT-UNREQUESTED | blocking | US-view-task-list | The PRD describes a personal task list and never mentions a signed-in user or sign-in. The story DoD 1, AC and task BE-tasks-list-endpoint ('returns every task belonging to the signed-in user') add a user identification rule the PRD does not ask for. | Remove 'signed-in user' wording from DoD 1 and the BE-tasks-list-endpoint title, description and DoD. Return all tasks, or list the user identity as an open question. |
| CRIT-UNREQUESTED | blocking | US-update-task | AC5 and Edge case 1 refer to 'another user session' and the story says 'registered user'. The PRD has no registered users or multiple sessions. | Reword AC5 to 'a task that no longer exists' and change the story to 'a user'. |
| CRIT-OVERLAP | blocking | BE-report-all-tasks-endpoint | Returns all tasks via a GET endpoint, which duplicates BE-tasks-list-endpoint (GET /tasks). BE-report-query-filter-search-sort later extends the report endpoint, making the same data served twice. | Remove BE-report-all-tasks-endpoint, or reuse GET /tasks with query parameters for the report. Depend on BE-tasks-list-endpoint. |
| CRIT-MISSING | blocking | US-delete-task | The PRD requires a read-by-ID endpoint. No task builds a read-by-ID endpoint; BE-tasks-list-endpoint explicitly says it belongs to other stories, and FE-task-edit-form-mode loads values by task ID. | Add a [BE] GET /tasks/{id} endpoint task, for example in US-update-task, that the edit form depends on. |
| CRIT-MISSING | blocking | US-export-report-excel | The export story depends on a generation-location decision, and no task builds the actual Excel file generation (backend or frontend). FE-report-excel-download-action is blocked by the decision, and its data source is undefined. | Add a task that generates the Excel file after the decision, or give FE-report-excel-download-action explicit generation scope. |
| CRIT-CONSTRAINT | blocking | US-create-task | The story AC and tasks leave out the 'Last Updated Date' set on create, and the story cites R-31569dba, but no AC checks the Creation Date and Last Updated Date being set. Also there is no AC for the success of created-task refresh. | Add an AC: Given a task is created, When it is saved, Then Creation Date and Last Updated Date are set by the system. |
| CRIT-PRD-GAP | warning | US-view-task-report | The PRD does not say whether In Progress tasks count in Open Tasks. The story assumes they do not (an invented answer) though also lists it as open. | Remove the assumption and keep it as an open question. |
| CRIT-PRD-GAP | warning | US-update-task | The PRD does not define how a Due Date is set when none is entered. | List this as an open question in the story. |

### check_plan — round 1: fail (9 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P2 | blocking | QA-create-task-tests | Task cites no requirement and has no derived_reason. | Cite the requirement it implements, or set derived_reason. |
| P11 | blocking | BE-report-query-filter-search-sort | Title is 83 characters (max 80): '[BE] Add filter, title search and sort parameters to the task report query endpoint' | Shorten it while keeping the object it names. |
| P11 | blocking | FE-task-update-feedback | Title is 92 characters (max 80): '[FE] Show success or error message after a task update and keep failed edits out of the list' | Shorten it while keeping the object it names. |
| CRIT-UNREQUESTED | blocking | US-view-task-list | The PRD describes a personal task list and never mentions a signed-in user or sign-in. The story DoD 1, AC and task BE-tasks-list-endpoint ('returns every task belonging to the signed-in user') add a user identification rule the PRD does not ask for. | Remove 'signed-in user' wording from DoD 1 and the BE-tasks-list-endpoint title, description and DoD. Return all tasks, or list the user identity as an open question. |
| CRIT-UNREQUESTED | blocking | US-update-task | AC5 and Edge case 1 refer to 'another user session' and the story says 'registered user'. The PRD has no registered users or multiple sessions. | Reword AC5 to 'a task that no longer exists' and change the story to 'a user'. |
| CRIT-OVERLAP | blocking | BE-report-all-tasks-endpoint | Returns all tasks via a GET endpoint, which duplicates BE-tasks-list-endpoint (GET /tasks). BE-report-query-filter-search-sort later extends the report endpoint, making the same data served twice. | Remove BE-report-all-tasks-endpoint, or reuse GET /tasks with query parameters for the report. Depend on BE-tasks-list-endpoint. |
| CRIT-MISSING | blocking | US-delete-task | The PRD requires a read-by-ID endpoint. No task builds a read-by-ID endpoint; BE-tasks-list-endpoint explicitly says it belongs to other stories, and FE-task-edit-form-mode loads values by task ID. | Add a [BE] GET /tasks/{id} endpoint task, for example in US-update-task, that the edit form depends on. |
| CRIT-MISSING | blocking | US-export-report-excel | The export story depends on a generation-location decision, and no task builds the actual Excel file generation (backend or frontend). FE-report-excel-download-action is blocked by the decision, and its data source is undefined. | Add a task that generates the Excel file after the decision, or give FE-report-excel-download-action explicit generation scope. |
| CRIT-CONSTRAINT | blocking | US-create-task | The story AC and tasks leave out the 'Last Updated Date' set on create, and the story cites R-31569dba, but no AC checks the Creation Date and Last Updated Date being set. Also there is no AC for the success of created-task refresh. | Add an AC: Given a task is created, When it is saved, Then Creation Date and Last Updated Date are set by the system. |
| CRIT-PRD-GAP | warning | US-view-task-report | The PRD does not say whether In Progress tasks count in Open Tasks. The story assumes they do not (an invented answer) though also lists it as open. | Remove the assumption and keep it as an open question. |
| CRIT-PRD-GAP | warning | US-update-task | The PRD does not define how a Due Date is set when none is entered. | List this as an open question in the story. |

### check_plan — round 2: fail (5 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P2 | blocking | QA-delete-task-test-suite | Task cites no requirement and has no derived_reason. | Cite the requirement it implements, or set derived_reason. |
| CRIT-MISSING | blocking | US-update-task | US-update-task is not planned to include the FE edit form's trigger, but more importantly FE-task-edit-form-prefill and update tasks never deliver the 'Status Change' via the update path; however the clearest gap is that the status change story is in separate story, so this is fine. Real gap: the update story's AC1 says the task list shows the new title, but FE-task-update-result-messages DoD 4 only covers refresh; no task builds an entry point (edit action) on the task list to open the edit form. | Add an edit action on each task row in FE-task-edit-form-prefill that opens the form in edit mode. |
| CRIT-OVERLAP | blocking | FE-task-update-result-messages | DoD 4 'task list refreshes to the new values after a successful save' duplicates FE-task-list-auto-refresh, which already reloads the list after update. | Remove DoD 4 and rely on FE-task-list-auto-refresh. |
| CRIT-MISSING | blocking | US-delete-task | QA-delete-task-test-suite lists no requirements, and no delete task covers the GET /tasks/{id} AC8 in tests; also US-delete-task owns GET /tasks/{id} although the story is about deletion, while the edit story needs it. | Move BE-get-task-by-id-endpoint to the update story (or the view story) and move AC8 there; set QA requirements on the delete test suite. |
| CRIT-CONSTRAINT | blocking | US-export-report-excel | FE-report-excel-download-action and BE-task-report-excel-generator assume backend generation before the decision task is made, and the generator says it would be replaced if the decision is frontend. FE-report-export-no-data-message has no dependency on the generator or action and BE generator DoD 4 returns an error for no data, duplicating the FE no-data handling. | Keep the no-data check in one place: remove BE generator DoD 4 or make the FE message task react to that response, and add a dependency. |
| CRIT-PRD-GAP | warning | US-create-task | Edge case 2 and its wording is confusing; the PRD does not say whether the Due Date is mandatory or who sets the Creation Date default. | List as open question. |
| CRIT-PRD-GAP | warning | US-view-task-report | The PRD does not say whether the report metrics change when filters are applied. | Add as open question. |

### check_plan — round 2: fail (5 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P2 | blocking | QA-delete-task-test-suite | Task cites no requirement and has no derived_reason. | Cite the requirement it implements, or set derived_reason. |
| CRIT-MISSING | blocking | US-update-task | US-update-task is not planned to include the FE edit form's trigger, but more importantly FE-task-edit-form-prefill and update tasks never deliver the 'Status Change' via the update path; however the clearest gap is that the status change story is in separate story, so this is fine. Real gap: the update story's AC1 says the task list shows the new title, but FE-task-update-result-messages DoD 4 only covers refresh; no task builds an entry point (edit action) on the task list to open the edit form. | Add an edit action on each task row in FE-task-edit-form-prefill that opens the form in edit mode. |
| CRIT-OVERLAP | blocking | FE-task-update-result-messages | DoD 4 'task list refreshes to the new values after a successful save' duplicates FE-task-list-auto-refresh, which already reloads the list after update. | Remove DoD 4 and rely on FE-task-list-auto-refresh. |
| CRIT-MISSING | blocking | US-delete-task | QA-delete-task-test-suite lists no requirements, and no delete task covers the GET /tasks/{id} AC8 in tests; also US-delete-task owns GET /tasks/{id} although the story is about deletion, while the edit story needs it. | Move BE-get-task-by-id-endpoint to the update story (or the view story) and move AC8 there; set QA requirements on the delete test suite. |
| CRIT-CONSTRAINT | blocking | US-export-report-excel | FE-report-excel-download-action and BE-task-report-excel-generator assume backend generation before the decision task is made, and the generator says it would be replaced if the decision is frontend. FE-report-export-no-data-message has no dependency on the generator or action and BE generator DoD 4 returns an error for no data, duplicating the FE no-data handling. | Keep the no-data check in one place: remove BE generator DoD 4 or make the FE message task react to that response, and add a dependency. |
| CRIT-PRD-GAP | warning | US-create-task | Edge case 2 and its wording is confusing; the PRD does not say whether the Due Date is mandatory or who sets the Creation Date default. | List as open question. |
| CRIT-PRD-GAP | warning | US-view-task-report | The PRD does not say whether the report metrics change when filters are applied. | Add as open question. |

### check_plan — round 3: fail (4 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P11 | blocking | BE-delete-task-endpoint | Title is 86 characters (max 80): '[BE] Add DELETE /tasks/{id} endpoint that removes a task by ID with not-found handling' | Shorten it while keeping the object it names. |
| CRIT-MISSING | blocking | US-view-task-list | PRD requires endpoints for 'Read (All & By ID)'. GET /tasks is planned, but no task delivers a read-by-ID endpoint. FE-task-edit-form-prefill loads the stored values of a task from the backend, and nothing provides that endpoint. | Add a [BE] GET /tasks/{id} task to US-view-task-list (or narrow the edit prefill to use data from GET /tasks), with not-found handling and tests. |
| CRIT-OVERLAP | blocking | BE-task-update-error-handling | Duplicates BE-task-update-endpoint: both implement the update endpoint's validation and storing nothing on failure (empty title rejected, invalid input, nothing stored), and the endpoint task already rejects an empty title. | Narrow BE-task-update-error-handling to not-found, invalid input, missing-field and server error responses only, and remove the empty-title/due-date rejection from BE-task-update-endpoint or leave it there and drop it here. |
| CRIT-PRD-GAP | warning | US-update-task | The PRD does not say whether a title of only spaces counts as empty; the story lists this already but the update AC2 treats an empty title only. | Keep the open question recorded. |
| CRIT-MISSING | blocking | US-delete-task | QA-delete-task-test-suite lists no requirements, and no delete task covers the GET /tasks/{id} AC8 in tests; also US-delete-task owns GET /tasks/{id} although the story is about deletion, while the edit story needs it. | Move BE-get-task-by-id-endpoint to the update story (or the view story) and move AC8 there; set QA requirements on the delete test suite. |

### check_plan — round 3: fail (4 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P11 | blocking | BE-delete-task-endpoint | Title is 86 characters (max 80): '[BE] Add DELETE /tasks/{id} endpoint that removes a task by ID with not-found handling' | Shorten it while keeping the object it names. |
| CRIT-MISSING | blocking | US-view-task-list | PRD requires endpoints for 'Read (All & By ID)'. GET /tasks is planned, but no task delivers a read-by-ID endpoint. FE-task-edit-form-prefill loads the stored values of a task from the backend, and nothing provides that endpoint. | Add a [BE] GET /tasks/{id} task to US-view-task-list (or narrow the edit prefill to use data from GET /tasks), with not-found handling and tests. |
| CRIT-OVERLAP | blocking | BE-task-update-error-handling | Duplicates BE-task-update-endpoint: both implement the update endpoint's validation and storing nothing on failure (empty title rejected, invalid input, nothing stored), and the endpoint task already rejects an empty title. | Narrow BE-task-update-error-handling to not-found, invalid input, missing-field and server error responses only, and remove the empty-title/due-date rejection from BE-task-update-endpoint or leave it there and drop it here. |
| CRIT-PRD-GAP | warning | US-update-task | The PRD does not say whether a title of only spaces counts as empty; the story lists this already but the update AC2 treats an empty title only. | Keep the open question recorded. |
| CRIT-MISSING | blocking | US-delete-task | QA-delete-task-test-suite lists no requirements, and no delete task covers the GET /tasks/{id} AC8 in tests; also US-delete-task owns GET /tasks/{id} although the story is about deletion, while the edit story needs it. | Move BE-get-task-by-id-endpoint to the update story (or the view story) and move AC8 there; set QA requirements on the delete test suite. |

### check_plan — round 4: fail (3 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | BE-task-update-error-responses | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-UNREQUESTED | blocking | US-view-task-list | The business description says 'the signed-in user's saved tasks'. The PRD mentions no sign-in or user accounts, so this adds an unrequested sign-in concept. The same unrequested user scoping appears in BE-tasks-list-endpoint ('all saved tasks of the user') and in DoD 1 of the story ('every saved task of the user'). | Remove the 'signed-in' wording and the per-user filtering from the story and from BE-tasks-list-endpoint. Say 'all saved tasks'. |
| CRIT-UNREQUESTED | blocking | US-update-task | AC9 and DoD 4 add a per-row edit action. The PRD asks for a task creation/editing form but never mentions a row action. Also, AC4 requires 'the task list shows the previous values', which is a UI behaviour the PRD does not describe in this form. | Describe opening the edit form in neutral terms, for example 'the user opens an existing task for editing'. Drop the row-specific edit action wording. |
| CRIT-CONSTRAINT | blocking | US-view-task-list | The story's AC9 and DoD 6 cover the optimistic update rule only for the list. There is no AC for the read-by-ID endpoint serving the edit form, and FE-task-edit-form-prefill has no AC for the failure case when loading the task by ID (error shown, no prefilled success state). | Add an AC to US-update-task, and a matching DoD to FE-task-edit-form-prefill: when GET /tasks/{id} fails, the edit form shows an error message and no prefilled values. |

### check_plan — round 4: fail (3 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | BE-task-update-error-responses | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-UNREQUESTED | blocking | US-view-task-list | The business description says 'the signed-in user's saved tasks'. The PRD mentions no sign-in or user accounts, so this adds an unrequested sign-in concept. The same unrequested user scoping appears in BE-tasks-list-endpoint ('all saved tasks of the user') and in DoD 1 of the story ('every saved task of the user'). | Remove the 'signed-in' wording and the per-user filtering from the story and from BE-tasks-list-endpoint. Say 'all saved tasks'. |
| CRIT-UNREQUESTED | blocking | US-update-task | AC9 and DoD 4 add a per-row edit action. The PRD asks for a task creation/editing form but never mentions a row action. Also, AC4 requires 'the task list shows the previous values', which is a UI behaviour the PRD does not describe in this form. | Describe opening the edit form in neutral terms, for example 'the user opens an existing task for editing'. Drop the row-specific edit action wording. |
| CRIT-CONSTRAINT | blocking | US-view-task-list | The story's AC9 and DoD 6 cover the optimistic update rule only for the list. There is no AC for the read-by-ID endpoint serving the edit form, and FE-task-edit-form-prefill has no AC for the failure case when loading the task by ID (error shown, no prefilled success state). | Add an AC to US-update-task, and a matching DoD to FE-task-edit-form-prefill: when GET /tasks/{id} fails, the edit form shows an error message and no prefilled values. |

### check_plan — round 2: fail (4 blocking, 3 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P11 | blocking | BE-task-update-endpoint | Title is 89 characters (max 80): '[BE] Add PUT /tasks/{id} endpoint that updates the task fields submitted by the edit form' | Shorten it while keeping the object it names. |
| P11 | blocking | FE-task-update-result-messages | Title is 88 characters (max 80): '[FE] Show update result messages and keep displayed values unchanged until save succeeds' | Shorten it while keeping the object it names. |
| CRIT-CONSTRAINT | blocking | FE-task-edit-form-prefill | The PRD forbids showing a successful state when a backend call has failed. FE-task-edit-form-prefill loads the stored task from GET /tasks/{id}, but neither it nor US-update-task has a criterion for a failed load (for example not found or server error). The form could show a prefilled or success state in that case. | Add a DoD to FE-task-edit-form-prefill and an AC to US-update-task: Given the by-ID request fails, When the user opens the task for editing, Then an error message is shown and the form shows no prefilled values. |
| CRIT-PRD-GAP | warning | US-update-task | The story does not say how the user opens a task for editing. The PRD only asks for a creation/editing form, so the entry point is undefined (AC9 is phrased neutrally). | List the entry point as an open question. |
| CRIT-CONSTRAINT | blocking | US-view-task-list | The story's AC9 and DoD 6 cover the optimistic update rule only for the list. There is no AC for the read-by-ID endpoint serving the edit form, and FE-task-edit-form-prefill has no AC for the failure case when loading the task by ID (error shown, no prefilled success state). | Add an AC to US-update-task, and a matching DoD to FE-task-edit-form-prefill: when GET /tasks/{id} fails, the edit form shows an error message and no prefilled values. |

### check_plan — round 2: fail (4 blocking, 3 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P11 | blocking | BE-task-update-endpoint | Title is 89 characters (max 80): '[BE] Add PUT /tasks/{id} endpoint that updates the task fields submitted by the edit form' | Shorten it while keeping the object it names. |
| P11 | blocking | FE-task-update-result-messages | Title is 88 characters (max 80): '[FE] Show update result messages and keep displayed values unchanged until save succeeds' | Shorten it while keeping the object it names. |
| CRIT-CONSTRAINT | blocking | FE-task-edit-form-prefill | The PRD forbids showing a successful state when a backend call has failed. FE-task-edit-form-prefill loads the stored task from GET /tasks/{id}, but neither it nor US-update-task has a criterion for a failed load (for example not found or server error). The form could show a prefilled or success state in that case. | Add a DoD to FE-task-edit-form-prefill and an AC to US-update-task: Given the by-ID request fails, When the user opens the task for editing, Then an error message is shown and the form shows no prefilled values. |
| CRIT-PRD-GAP | warning | US-update-task | The story does not say how the user opens a task for editing. The PRD only asks for a creation/editing form, so the entry point is undefined (AC9 is phrased neutrally). | List the entry point as an open question. |
| CRIT-CONSTRAINT | blocking | US-view-task-list | The story's AC9 and DoD 6 cover the optimistic update rule only for the list. There is no AC for the read-by-ID endpoint serving the edit form, and FE-task-edit-form-prefill has no AC for the failure case when loading the task by ID (error shown, no prefilled success state). | Add an AC to US-update-task, and a matching DoD to FE-task-edit-form-prefill: when GET /tasks/{id} fails, the edit form shows an error message and no prefilled values. |

### check_plan — round 3: pass (0 blocking, 4 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | BE-task-update-error-responses | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | BE-task-update-validation | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |

### check_plan — round 3: pass (0 blocking, 4 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | BE-task-update-error-responses | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | BE-task-update-validation | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |

### check_plan — round 2: fail (2 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-UNREQUESTED | blocking | US-update-task | Edge case 4 says 'If the task is deleted by another user while the edit form is open'. The PRD and the reviewer decision describe a single user with no sign-in, so another user is an actor the PRD never mentions. | Reword edge case 4 to 'If the task is deleted (for example in another browser session) while the edit form is open, the save returns a task not found error and the form shows an error message.' |
| CRIT-OVERLAP | blocking | BE-task-update-validation | Applies the same empty-title and Due Date rules to updates. BE-task-update-endpoint and BE-task-update-error-responses already cover updates on PUT /tasks/{id}, including the missing-title error, so the work is split across three tasks. The missing-title error is also delivered twice: BE-task-update-validation DoD 1 rejects an empty title, and BE-task-update-error-responses DoD 3 returns a missing-field error for a missing title. | Narrow BE-task-update-error-responses to not-found, invalid-input and server errors, and leave title and due date rules to BE-task-update-validation. Alternatively merge the validation into BE-task-update-endpoint. |
| CRIT-PRD-GAP | warning | US-update-task | The PRD does not say whether Status, Priority and Completion Date can be changed in the update form or only through the status change. The story and BE-task-update-endpoint DoD 2 refer to 'the fields the edit form allows' without naming them. | List this as an open question on the story. |

### check_plan — round 2: fail (2 blocking, 2 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-UNREQUESTED | blocking | US-update-task | Edge case 4 says 'If the task is deleted by another user while the edit form is open'. The PRD and the reviewer decision describe a single user with no sign-in, so another user is an actor the PRD never mentions. | Reword edge case 4 to 'If the task is deleted (for example in another browser session) while the edit form is open, the save returns a task not found error and the form shows an error message.' |
| CRIT-OVERLAP | blocking | BE-task-update-validation | Applies the same empty-title and Due Date rules to updates. BE-task-update-endpoint and BE-task-update-error-responses already cover updates on PUT /tasks/{id}, including the missing-title error, so the work is split across three tasks. The missing-title error is also delivered twice: BE-task-update-validation DoD 1 rejects an empty title, and BE-task-update-error-responses DoD 3 returns a missing-field error for a missing title. | Narrow BE-task-update-error-responses to not-found, invalid-input and server errors, and leave title and due date rules to BE-task-update-validation. Alternatively merge the validation into BE-task-update-endpoint. |
| CRIT-PRD-GAP | warning | US-update-task | The PRD does not say whether Status, Priority and Completion Date can be changed in the update form or only through the status change. The story and BE-task-update-endpoint DoD 2 refer to 'the fields the edit form allows' without naming them. | List this as an open question on the story. |

### check_plan — round 3: fail (2 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-OVERLAP | blocking | BE-task-update-validation | Still splits PUT /tasks/{id} work across three tasks. BE-task-update-endpoint already says it validates the submitted fields, and BE-task-update-validation applies title and due date rules on the same endpoint. BE-task-update-error-responses also covers invalid input on the same update path. The missing-title error is still delivered twice: BE-task-update-validation DoD 2 returns a missing mandatory field error for a missing title, and BE-task-update-error-responses DoD 2 returns an invalid input error for field values the backend does not accept. | Merge BE-task-update-validation into BE-task-update-endpoint (or narrow the endpoint task to saving only). Keep not-found, invalid-input and server errors in BE-task-update-error-responses and drop the duplicated missing-title DoD. |
| CRIT-OVERLAP | blocking | BE-task-update-validation | Applies the same empty-title and Due Date rules to updates. BE-task-update-endpoint and BE-task-update-error-responses already cover updates on PUT /tasks/{id}, including the missing-title error, so the work is split across three tasks. The missing-title error is also delivered twice: BE-task-update-validation DoD 1 rejects an empty title, and BE-task-update-error-responses DoD 3 returns a missing-field error for a missing title. | Narrow BE-task-update-error-responses to not-found, invalid-input and server errors, and leave title and due date rules to BE-task-update-validation. Alternatively merge the validation into BE-task-update-endpoint. |

### check_plan — round 3: fail (2 blocking, 1 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-OVERLAP | blocking | BE-task-update-validation | Still splits PUT /tasks/{id} work across three tasks. BE-task-update-endpoint already says it validates the submitted fields, and BE-task-update-validation applies title and due date rules on the same endpoint. BE-task-update-error-responses also covers invalid input on the same update path. The missing-title error is still delivered twice: BE-task-update-validation DoD 2 returns a missing mandatory field error for a missing title, and BE-task-update-error-responses DoD 2 returns an invalid input error for field values the backend does not accept. | Merge BE-task-update-validation into BE-task-update-endpoint (or narrow the endpoint task to saving only). Keep not-found, invalid-input and server errors in BE-task-update-error-responses and drop the duplicated missing-title DoD. |
| CRIT-OVERLAP | blocking | BE-task-update-validation | Applies the same empty-title and Due Date rules to updates. BE-task-update-endpoint and BE-task-update-error-responses already cover updates on PUT /tasks/{id}, including the missing-title error, so the work is split across three tasks. The missing-title error is also delivered twice: BE-task-update-validation DoD 1 rejects an empty title, and BE-task-update-error-responses DoD 3 returns a missing-field error for a missing title. | Narrow BE-task-update-error-responses to not-found, invalid-input and server errors, and leave title and due date rules to BE-task-update-validation. Alternatively merge the validation into BE-task-update-endpoint. |

### check_plan — round 2: pass (0 blocking, 3 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-PRD-GAP | warning | US-update-task | The story lists open questions on space-only titles, Status/Priority editing and concurrent saves, but not on whether a changed Due Date is compared to the original Creation Date or whether the user can change the Completion Date through the form. The PRD does not say whether the edit form can change the Completion Date. | Add an open question to the story for the Completion Date. |

### check_plan — round 2: pass (0 blocking, 3 warnings)

| Check | Severity | Item | Message | Suggested fix |
|---|---|---|---|---|
| P7 | warning | QA-delete-task-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| P7 | warning | QA-task-update-test-suite | Task touches the database but is not blocked by an area:db task. |  |
| CRIT-PRD-GAP | warning | US-update-task | The story lists open questions on space-only titles, Status/Priority editing and concurrent saves, but not on whether a changed Due Date is compared to the original Creation Date or whether the user can change the Completion Date through the form. The PRD does not say whether the edit form can change the Completion Date. | Add an open question to the story for the Completion Date. |

### reference_normalization — round 0: pass (0 blocking, 0 warnings)

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
| `R-959e2960` | functional | `US-change-task-status`, `BE-task-status-endpoint`, `FE-task-status-toggle`, `QA-task-status-tests` |
| `R-82fe7dda` | context_only | — |
| `R-9675bb49` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-aaf23206` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-c9046f7a` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-576b7e59` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-9fb58566` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-1c2262bc` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-71bdd372` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-31569dba` | data_model | `US-create-task`, `BE-tasks-table-migration`, `BE-create-task-endpoint` |
| `R-34e41747` | data_model | `US-create-task`, `BE-tasks-table-migration` |
| `R-03df7815` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `FE-task-creation-form`, `QA-create-task-test-suite`, `BE-put-task-endpoint-with-validation`, `FE-task-update-result-messages`, `QA-task-update-test-suite` |
| `R-efe1e5d4` | validation_rule | `US-create-task`, `US-update-task`, `BE-create-task-endpoint`, `FE-task-creation-form`, `QA-create-task-test-suite`, `BE-put-task-endpoint-with-validation`, `FE-task-update-result-messages`, `QA-task-update-test-suite` |
| `R-8ef41ba1` | functional | `US-delete-task`, `FE-delete-confirmation-prompt`, `QA-delete-task-test-suite` |
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
| `R-f214002a` | functional | `US-filter-search-sort-report`, `BE-report-query-filter-search-sort`, `FE-report-search-and-sort-ui`, `QA-report-filter-search-sort-tests` |
| `R-4ffbfafa` | frontend | `US-view-task-report`, `FE-report-metrics-cards`, `QA-report-test-suite` |
| `R-52360b76` | functional | `US-export-report-excel`, `BE-task-report-excel-generator`, `FE-report-excel-download-action`, `QA-excel-export-test-suite` |
| `R-09e9d163` | functional | `US-export-report-excel`, `BE-task-report-excel-generator`, `FE-report-excel-download-action`, `QA-excel-export-test-suite` |
| `R-fad183b1` | constraint | `US-export-report-excel`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |
| `R-d22b9b6a` | functional | `US-export-report-excel`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |
| `R-437992f1` | frontend | `US-export-report-excel`, `FE-report-export-no-data-message`, `QA-excel-export-test-suite` |
| `R-8007d6b5` | backend | `US-view-task-report`, `US-filter-search-sort-report`, `US-export-report-excel`, `BE-report-metrics-endpoint`, `QA-report-test-suite`, `BE-report-query-filter-search-sort`, `QA-report-filter-search-sort-tests`, `BE-task-report-excel-generator`, `QA-excel-export-test-suite` |
| `R-3a63e0ce` | decision_open | `US-export-report-excel`, `BE-excel-export-generation-decision` |
