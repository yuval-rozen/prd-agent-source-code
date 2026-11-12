# Personal task management system

`EPIC-personal-task-management-system` · labels: type:epic, prd-agent

## Scope

A personal task management system that lets a user manage a personal task list (create, view, update, delete, complete and reopen tasks) and view an aggregated task report. The report supports filtering, searching, sorting, metric counts and Excel export. The backend stores tasks in a new table in the existing database and exposes API endpoints for task management and reporting.

## Business goals

- Let users track their daily tasks
- Let users generate status reports from their tasks

## User stories

- [ ] `US-create-and-view-tasks` Create a task and view the task list
- [ ] `US-update-task-details` Update the details of an existing task
- [ ] `US-delete-task-with-confirmation` Delete a task after confirming the deletion
- [ ] `US-complete-and-reopen-task` Mark a task as Completed or revert it to Open
- [ ] `US-review-task-report` Review the task report with task counts
- [ ] `US-filter-search-sort-task-report` Filter, search and sort the task report
- [ ] `US-export-task-report-to-excel` Export the current task report view to Excel

---

## Create a task and view the task list

`US-create-and-view-tasks` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

## User story

**As a** user, **I want** to create a new task and view the list of tasks, **so that** I can record the work I need to do and see all tasks in one place.

## Business description

Users can add a task with a title, description, status, priority, creation date and due date, and can view all saved tasks in a list. Each task has a unique ID. A task cannot be saved without a title, and its due date cannot be earlier than its creation date. The frontend shows a success or error message after each create action and never shows a success state before the backend confirms the save.

## Business value

Users can capture tasks and see them in one list, which is the base for the update, delete, status and reporting features.

## Acceptance criteria

1. **Given** a user on the create task form with a non-empty title, a Status of Open, a Priority of Medium and a Due Date equal to or later than today, **When** the user submits the form and the backend confirms the save, **Then** the task is saved with a unique ID, a Creation Date set by the backend, and a success message is shown
2. **Given** a user on the create task form with an empty title, **When** the user submits the form, **Then** the task is not saved, no success message is shown, and an error message stating that the title is mandatory is displayed
3. **Given** a user submits a task whose Due Date is earlier than its Creation Date, **When** the backend receives the request, **Then** the backend rejects it with a simple validation error, the task is not saved, and the frontend shows an error message
4. **Given** the backend fails to save a task because of a database error, **When** the user submits the create task form, **Then** the frontend shows an error message and does not show a success message or add the task to the list
5. **Given** at least one task is saved, **When** the user opens the task list, **Then** every saved task is shown with its ID, Title, Description, Status, Priority, Creation Date and Due Date
6. **Given** no tasks are saved, **When** the user opens the task list, **Then** the list is empty and the response contains an empty collection rather than an error
7. **Given** a create request is submitted with a Status or Priority value outside Open, In Progress, Completed or Low, Medium, High, **When** the backend receives the request, **Then** the backend rejects the request with a simple invalid input error and does not save the task

## Edge cases

- Title containing only whitespace: the PRD requires a non-empty title; it does not state whether whitespace-only titles are allowed. Open question: treat whitespace-only as empty?
- Due Date equal to the Creation Date must be accepted, because the rule only forbids dates earlier than the Creation Date.
- Open question: the PRD does not say whether Due Date is mandatory. It is listed as a field but not in the validation rules.
- Open question: the PRD does not state whether Description is mandatory, optional, or has a maximum length.
- Open question: the PRD does not state the default Status and Priority for a new task. This story assumes the form must send a value.
- Open question: the PRD does not define the order of the task list or whether it is paginated.
- Open question: the PRD requires endpoints for read by ID, update, delete and status change, but this story only covers create and read all. Confirm which story delivers the other endpoints.
- Open question: the PRD does not define the time zone used to compare Due Date with Creation Date.

## Dependencies

- None.

## Definition of Done

- [ ] Migration creates a new tasks table with columns for unique ID, Title, Description, Status (Open, In Progress, Completed), Priority (Low, Medium, High), Creation Date and Due Date, and runs on the existing database.
- [ ] POST endpoint creates a task and returns the saved task with its ID and Creation Date.
- [ ] POST endpoint rejects empty titles and Due Dates earlier than Creation Date, with simple error responses.
- [ ] GET endpoint returns all saved tasks.
- [ ] Error responses cover invalid input, missing mandatory fields and internal or database errors.
- [ ] Create task form shows a success message after the backend confirms the save and an error message after a failure.
- [ ] Task list displays all required fields for each task.
- [ ] Automated tests pass for create, list, validation and error cases.
- [ ] Open questions listed in edge cases are answered or recorded in the story before release.

## Tasks

- [ ] `BE-tasks-table-migration` [BE] Add tasks table migration with ID, Title, Description, Status, Priority and date fields
- [ ] `BE-create-task-endpoint` [BE] Add POST /tasks endpoint with title and due date validation
- [ ] `BE-list-tasks-endpoint` [BE] Add GET /tasks endpoint that returns all saved tasks
- [ ] `FE-create-task-form` [FE] Add create task form with success and error messages
- [ ] `FE-task-list-view` [FE] Add task list view showing all task fields
- [ ] `QA-create-and-list-test-suite` [QA] Add end-to-end test suite for task create and list

## Requirements

- `R-22f28530` (functional) Users can create a new task.
- `R-4bed9064` (functional) Users can view the task list.
- `R-9675bb49` (data_model) Each task has a unique ID field.
- `R-aaf23206` (data_model) Each task has a Title field.
- `R-c9046f7a` (data_model) Each task has a Description field.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-9fb58566` (data_model) Each task has a Priority field whose allowed values are Low, Medium and High.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-71bdd372` (data_model) Each task has a Due Date field.
- `R-03df7815` (validation_rule) A task must not be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.
- `R-c55a77b3` (backend) Todos are persisted in the existing database in a new table created for them.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.

### [BE] Add tasks table migration with ID, Title, Description, Status, Priority and date fields

`BE-tasks-table-migration` · labels: type:task, area:db, prd-agent

**Parent:** `US-create-and-view-tasks`

**Track:** backend · **Size:** M · touches DB
## Description

Create a new table in the existing database with a unique ID, Title, Description, Status (Open, In Progress, Completed), Priority (Low, Medium, High), Creation Date and Due Date. Add a check constraint for the allowed Status and Priority values.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Migration runs on the existing database and creates the tasks table.
- [ ] Unique ID is the primary key.
- [ ] Status and Priority columns reject values outside the allowed sets.
- [ ] Migration has a tested rollback.

## Requirements

- `R-c55a77b3` (backend) Todos are persisted in the existing database in a new table created for them.
- `R-9675bb49` (data_model) Each task has a unique ID field.
- `R-aaf23206` (data_model) Each task has a Title field.
- `R-c9046f7a` (data_model) Each task has a Description field.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-9fb58566` (data_model) Each task has a Priority field whose allowed values are Low, Medium and High.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-71bdd372` (data_model) Each task has a Due Date field.

### [BE] Add POST /tasks endpoint with title and due date validation

`BE-create-task-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-create-and-view-tasks`

**Track:** backend · **Size:** M · touches DB
## Description

Accept a new task, validate that the title is non-empty and that Due Date is not earlier than Creation Date, persist the task and return it. Return simple error responses for invalid input, missing mandatory fields and database errors.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Endpoint saves a valid task and returns the ID and Creation Date.
- [ ] Empty title is rejected and nothing is saved.
- [ ] Due Date earlier than Creation Date is rejected and nothing is saved.
- [ ] Invalid input, missing mandatory fields and database errors return simple error responses.
- [ ] Unit and API tests cover each rule.

## Requirements

- `R-22f28530` (functional) Users can create a new task.
- `R-03df7815` (validation_rule) A task must not be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.

### [BE] Add GET /tasks endpoint that returns all saved tasks

`BE-list-tasks-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-create-and-view-tasks`

**Track:** backend · **Size:** S · touches DB
## Description

Return all saved tasks with all required fields. Return an empty collection when no tasks exist. Return a simple error response on database failure.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Endpoint returns every saved task with ID, Title, Description, Status, Priority, Creation Date and Due Date.
- [ ] Endpoint returns an empty collection when no tasks exist.
- [ ] Database failure returns a simple internal error response.
- [ ] API tests cover these cases.

## Requirements

- `R-4bed9064` (functional) Users can view the task list.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.

### [FE] Add create task form with success and error messages

`FE-create-task-form` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-create-and-view-tasks`

**Track:** frontend · **Size:** M · consumes API
## Description

Provide a form to enter Title, Description, Status, Priority and Due Date and submit it to POST /tasks. Show a success message only after the backend confirms the save and an error message on any failure. Do not update the UI optimistically.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Form submits to POST /tasks.
- [ ] Success message is shown only after a successful backend response.
- [ ] Error message is shown for validation failures and backend errors.
- [ ] No success state is shown before the backend confirms the save.
- [ ] Empty title is blocked in the form with a clear message.

## Requirements

- `R-22f28530` (functional) Users can create a new task.
- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.
- `R-03df7815` (validation_rule) A task must not be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.

### [FE] Add task list view showing all task fields

`FE-task-list-view` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-create-and-view-tasks`

**Track:** frontend · **Size:** M · consumes API
## Description

Show all saved tasks from GET /tasks in a list with ID, Title, Description, Status, Priority, Creation Date and Due Date. Show an empty state when there are no tasks and an error message when loading fails.

## Blocked by

- Nothing.

## Definition of Done

- [ ] List shows all required fields for each task.
- [ ] Empty state is shown when no tasks exist.
- [ ] Error message is shown when the list fails to load.
- [ ] List is refreshed after a successful create.

## Requirements

- `R-4bed9064` (functional) Users can view the task list.
- `R-9675bb49` (data_model) Each task has a unique ID field.
- `R-aaf23206` (data_model) Each task has a Title field.
- `R-c9046f7a` (data_model) Each task has a Description field.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-9fb58566` (data_model) Each task has a Priority field whose allowed values are Low, Medium and High.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-71bdd372` (data_model) Each task has a Due Date field.

### [QA] Add end-to-end test suite for task create and list

`QA-create-and-list-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-create-and-view-tasks`

**Track:** qa_general · **Size:** M · consumes API
## Description

Automated tests covering create, list, validation rules, success and error messages, and the rule that the UI never shows success before the backend confirms.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Tests cover valid create, empty title, Due Date before Creation Date, and database failure.
- [ ] Tests cover list with tasks and empty list.
- [ ] Tests confirm no success message appears when the backend fails.
- [ ] Test suite runs in CI and passes.

## Requirements

- Derived task: testing.

---

## Update the details of an existing task

`US-update-task-details` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

## User story

**As a** task owner, **I want** to update the details of an existing task, **so that** my task information stays accurate and current.

## Business description

Users can change the details of a task after it has been created. Each task keeps a Last Updated Date that reflects the most recent update. Updates must keep the task title non-empty and the Due Date not earlier than the Creation Date. The frontend shows a success or error message after each update and shows success only after the backend confirms the change.

## Business value

Users keep task records accurate over time, so the task list and task report reflect current work.

## Acceptance criteria

1. **Given** an existing task with a non-empty title, **When** the user changes the title to another non-empty value and saves, **Then** the backend confirms the update, the task shows the new title, and the Last Updated Date is set to the time of the save
2. **Given** an existing task, **When** the user clears the title field and saves, **Then** the task is not saved, the backend returns a validation error for the missing title, and the frontend shows an error message and keeps the previous title
3. **Given** an existing task with Creation Date 2024-03-01 and Due Date 2024-03-10, **When** the user sets the Due Date to 2024-02-28 and saves, **Then** the update is rejected with a validation error, the frontend shows an error message, and the stored Due Date remains 2024-03-10
4. **Given** an existing task, **When** the user saves a valid update and the backend confirms it, **Then** the frontend shows a success message and the Last Updated Date is changed
5. **Given** an existing task, **When** the user saves an update and the backend returns an error or cannot be reached, **Then** the frontend shows an error message, does not show a success message, and does not display the unsaved changes as saved
6. **Given** a task ID that does not exist, **When** a client sends an update request for that ID, **Then** the backend returns a simple not-found error and stores nothing

## Edge cases

- Title containing only whitespace: the PRD says the title must be non-empty but does not state whether whitespace-only titles are allowed; this is an open question.
- Due Date equal to Creation Date: the PRD says Due Date must not be earlier than Creation Date, so equal dates are allowed.
- Updating a task that was deleted by another user: the backend returns a not-found error for the update.
- Update request with a Due Date but no change to other fields: the PRD does not state whether Last Updated Date changes when nothing changed; this is an open question.
- Whether the Creation Date itself can be updated is not stated in the PRD; this is an open question.
- Concurrent updates to the same task: the PRD does not define conflict handling; this is an open question.
- The exact field list that is editable on update is not enumerated in the PRD beyond title and Due Date; this is an open question.

## Dependencies

- `US-create-and-view-tasks`

## Definition of Done

- [ ] Backend update endpoint for a task by ID is implemented and returns the updated task on success
- [ ] Backend rejects an empty or missing title with a simple validation error
- [ ] Backend rejects a Due Date earlier than the Creation Date with a simple validation error
- [ ] Backend returns a simple not-found error for a non-existent task ID
- [ ] Last Updated Date is set by the backend on each successful update
- [ ] Frontend shows a success message only after the backend confirms the update
- [ ] Frontend shows an error message on any backend failure and does not show a successful state
- [ ] Automated tests cover valid update, empty title, Due Date before Creation Date, and not-found cases
- [ ] Open questions about whitespace-only titles, no-change updates, and editable fields are documented and resolved with the product owner

## Tasks

- [ ] `BE-task-update-endpoint` [BE] Add PUT /tasks/{id} endpoint to update task details
- [ ] `BE-task-last-updated-field` [BE] Add Last Updated Date column to the task model
- [ ] `FE-task-edit-form` [FE] Add edit task form with title and Due Date fields
- [ ] `FE-task-update-messages` [FE] Show success and error messages after task update
- [ ] `QA-task-update-test-suite` [QA] Test suite for updating task details

## Requirements

- `R-bc3213df` (functional) Users can update an existing task.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-03df7815` (validation_rule) A task must not be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.

### [BE] Add PUT /tasks/{id} endpoint to update task details

`BE-task-update-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-update-task-details`

**Track:** backend · **Size:** M · touches DB
## Description

Add an endpoint that updates an existing task by ID. Validate that the title is non-empty and that Due Date is not earlier than Creation Date. Set Last Updated Date on each successful update. Return a simple not-found error for unknown IDs and simple errors for invalid input.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Endpoint accepts updated task fields and returns the updated task on success
- [ ] Empty or missing title returns a simple validation error and stores nothing
- [ ] Due Date earlier than Creation Date returns a simple validation error and stores nothing
- [ ] Unknown task ID returns a simple not-found error
- [ ] Last Updated Date is set on each successful update
- [ ] Internal or database errors return a simple error response

## Requirements

- `R-bc3213df` (functional) Users can update an existing task.
- `R-03df7815` (validation_rule) A task must not be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.

### [BE] Add Last Updated Date column to the task model

`BE-task-last-updated-field` · labels: type:task, area:db, prd-agent

**Parent:** `US-update-task-details`

**Track:** backend · **Size:** S · touches DB
## Description

Add the Last Updated Date field to the task data model and its storage, with a migration for existing tasks.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Task model includes a Last Updated Date field
- [ ] Migration adds the column to existing task records
- [ ] Existing tasks have a defined Last Updated Date value after migration

## Requirements

- `R-31569dba` (data_model) Each task has a Last Updated Date field.

### [FE] Add edit task form with title and Due Date fields

`FE-task-edit-form` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-update-task-details`

**Track:** frontend · **Size:** M · consumes API
## Description

Provide an edit form for an existing task that shows the current title and Due Date and submits changes to the update endpoint. The form must not show a saved state until the backend confirms the update.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Form loads the current task values
- [ ] Submit calls the update endpoint and waits for the response
- [ ] Form does not display success before a successful backend response
- [ ] Backend errors are shown to the user without changing the displayed saved values

## Requirements

- `R-bc3213df` (functional) Users can update an existing task.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.

### [FE] Show success and error messages after task update

`FE-task-update-messages` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-update-task-details`

**Track:** frontend · **Size:** S · consumes API
## Description

Display a success message after a confirmed update and an error message when the update fails, including validation and not-found errors.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Success message is shown only after backend confirmation
- [ ] Error message is shown for validation, not-found, and server errors
- [ ] No success message appears on failure

## Requirements

- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.

### [QA] Test suite for updating task details

`QA-task-update-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-update-task-details`

**Track:** qa_general · **Size:** M · consumes API
## Description

Automated tests covering the update endpoint, validation rules, Last Updated Date behaviour, and frontend messages.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Tests cover valid update, empty title, Due Date before Creation Date, and not-found cases
- [ ] Tests verify Last Updated Date changes on successful update
- [ ] Tests verify no success message is shown on backend failure

## Requirements

- Derived task: testing.

---

## Delete a task after confirming the deletion

`US-delete-task-with-confirmation` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

## User story

**As a** user, **I want** to delete a task after confirming the deletion in a prompt, **so that** tasks I no longer need are removed from my task list and I am not deleted by accident.

## Business description

Users can delete a task. Before the deletion is applied, a confirmation prompt must be accepted. The frontend shows a success or error message after the delete action, and it shows success only after the backend confirms the deletion. The backend exposes a delete endpoint and returns simple error responses for a missing task and for internal or database errors.

## Business value

Users can remove tasks they no longer need. The confirmation prompt prevents accidental data loss, and the success or error message tells the user the actual outcome.

## Acceptance criteria

1. **Given** a task is shown in the task list, **When** the user chooses delete on that task, **Then** a confirmation prompt is shown and the task is still listed until the user confirms
2. **Given** the confirmation prompt is open, **When** the user confirms the deletion, **Then** the frontend sends the delete request and the task is removed from the list only after the backend returns success
3. **Given** the confirmation prompt is open, **When** the user cancels the prompt, **Then** no delete request is sent and the task remains unchanged in the list
4. **Given** a task has been deleted successfully by the backend, **When** the delete response is received, **Then** the frontend shows a success message stating the task was deleted
5. **Given** the user confirmed the deletion and the backend returns an error, **When** the error response is received, **Then** the frontend shows an error message, keeps the task in the list and does not show a success state
6. **Given** a delete request is sent for a task ID that does not exist, **When** the backend receives the request, **Then** the backend returns a simple not-found error response and does not change any stored task
7. **Given** the backend cannot complete the delete because of an internal or database error, **When** the request is processed, **Then** the backend returns a simple internal error response and the task remains stored unchanged

## Edge cases

- User cancels the confirmation prompt: no request is sent and no message about a deletion is shown.
- User confirms twice quickly: the PRD does not state how a repeated delete is handled; the second request is expected to return the not-found error, which needs to be confirmed.
- Delete request for a task that was already deleted by another session: the backend returns the not-found error, and the frontend must show an error message rather than success. How the list refreshes in this case is not stated in the PRD and needs a decision.
- Backend error during delete: the task must remain in the list and no success state may be shown.
- Open question: the PRD does not state whether a deleted task can be restored or whether deletion is permanent; this story assumes permanent deletion until clarified.
- Open question: the PRD does not define the exact wording of the confirmation prompt or the success and error messages.

## Dependencies

- `US-create-and-view-tasks`

## Definition of Done

- [ ] DELETE endpoint for a single task is implemented and documented with its success and error responses
- [ ] Not-found and internal or database error responses return simple error bodies as defined in the PRD
- [ ] Delete action in the UI opens a confirmation prompt that must be accepted before any request is sent
- [ ] Frontend removes the task from the list only after a successful backend response
- [ ] Success or error message is shown after every delete attempt
- [ ] Frontend never shows a success state when the backend returns an error
- [ ] Automated tests cover confirm, cancel, success, not-found and internal error paths
- [ ] Open questions about repeated delete and permanence are recorded and answered by the product owner

## Tasks

- [ ] `BE-delete-task-endpoint` [BE] Add DELETE /tasks/{id} endpoint that removes a stored task
- [ ] `BE-delete-task-error-responses` [BE] Return simple not-found and internal error responses from DELETE /tasks/{id}
- [ ] `FE-delete-task-confirmation-prompt` [FE] Add confirmation prompt to the task delete action
- [ ] `FE-delete-task-result-feedback` [FE] Remove task from list and show delete result message after backend response
- [ ] `QA-delete-task-test-suite` [QA] Add end-to-end test suite for the delete task flow

## Requirements

- `R-8523b9ec` (functional) Users can delete a task.
- `R-8ef41ba1` (functional) Deleting a task requires the user to confirm the deletion through a prompt before it is applied.
- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.

### [BE] Add DELETE /tasks/{id} endpoint that removes a stored task

`BE-delete-task-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-delete-task-with-confirmation`

**Track:** backend · **Size:** S · touches DB
## Description

Add a DELETE endpoint that takes a task ID, removes the stored task and returns a success response. Document the request and response shape.

## Blocked by

- Nothing.

## Definition of Done

- [ ] DELETE /tasks/{id} removes the stored task and returns a success response
- [ ] Endpoint is documented with request and response examples
- [ ] Endpoint is covered by unit tests for success

## Requirements

- `R-8523b9ec` (functional) Users can delete a task.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.

### [BE] Return simple not-found and internal error responses from DELETE /tasks/{id}

`BE-delete-task-error-responses` · labels: type:task, area:backend, prd-agent

**Parent:** `US-delete-task-with-confirmation`

**Track:** backend · **Size:** S · touches DB
## Description

Make the delete endpoint return a simple not-found error when the task does not exist and a simple internal error when the database or server fails. Stored data must stay unchanged on error.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Deleting a non-existent task returns a simple not-found error response
- [ ] Database or server failure returns a simple internal error response
- [ ] No stored task is changed when an error is returned
- [ ] Error responses are covered by tests

## Requirements

- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.

### [FE] Add confirmation prompt to the task delete action

`FE-delete-task-confirmation-prompt` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-delete-task-with-confirmation`

**Track:** frontend · **Size:** S · consumes API
## Description

Add a delete action on each task that opens a confirmation prompt. The delete request is sent only when the user confirms. Cancelling closes the prompt without any request.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Delete action opens a confirmation prompt
- [ ] Confirm sends DELETE request to the backend
- [ ] Cancel closes the prompt and sends no request
- [ ] Prompt component is covered by tests

## Requirements

- `R-8523b9ec` (functional) Users can delete a task.
- `R-8ef41ba1` (functional) Deleting a task requires the user to confirm the deletion through a prompt before it is applied.

### [FE] Remove task from list and show delete result message after backend response

`FE-delete-task-result-feedback` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-delete-task-with-confirmation`

**Track:** frontend · **Size:** M · consumes API
## Description

After the delete request completes, show a success message and remove the task only when the backend confirms. On error, show an error message and keep the task in the list. No success state is shown before the backend responds.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Task is removed from the list only after a success response
- [ ] Success message is shown after a successful delete
- [ ] Error message is shown after a failed delete and the task stays in the list
- [ ] No optimistic removal or success state is shown before backend confirmation

## Requirements

- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.
- `R-8523b9ec` (functional) Users can delete a task.

### [QA] Add end-to-end test suite for the delete task flow

`QA-delete-task-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-delete-task-with-confirmation`

**Track:** qa_general · **Size:** M
## Description

Write the test suite covering confirm, cancel, success, not-found and internal error paths for deleting a task, including the rule that no success state is shown on backend failure.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Tests cover confirm, cancel, success, not-found and internal error paths
- [ ] Tests verify the task remains in the list when the backend returns an error
- [ ] Tests verify no success message is shown when the backend fails
- [ ] Test suite runs in the CI pipeline

## Requirements

- `R-8523b9ec` (functional) Users can delete a task.
- `R-8ef41ba1` (functional) Deleting a task requires the user to confirm the deletion through a prompt before it is applied.
- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.

---

## Mark a task as Completed or revert it to Open

`US-complete-and-reopen-task` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

## User story

**As a** user who manages tasks, **I want** to mark a task as Completed and revert a Completed task back to Open, **so that** I can record which work is finished and reopen work that needs more effort.

## Business description

Users change the Status of a task between Open and Completed. Completing a task records a Completion Date. Reverting a Completed task sets its Status back to Open. Every change updates the Last Updated Date. The frontend shows a success or error message after each change and never shows a success state before the backend confirms it.

## Business value

Users can see which tasks are finished and reopen tasks that were completed too early, so the task list reflects the actual state of the work.

## Acceptance criteria

1. **Given** a task with Status Open exists, **When** the user marks the task as Completed and the backend confirms the change, **Then** the task Status is Completed, the Completion Date is set to the date of the change, and a success message is shown
2. **Given** a task with Status Completed exists, **When** the user reverts the task to Open and the backend confirms the change, **Then** the task Status is Open and a success message is shown
3. **Given** a task with Status Open exists, **When** the user marks the task as Completed and the backend returns an error, **Then** the task Status remains Open, the UI does not show the task as Completed, and an error message is shown
4. **Given** a task with Status Completed exists, **When** the user reverts the task and the backend returns an error, **Then** the task Status remains Completed, the UI does not show the task as Open, and an error message is shown
5. **Given** a task is marked as Completed, **When** the status change is saved, **Then** the Last Updated Date of the task is set to the time of the change
6. **Given** a task ID that does not exist, **When** a status change request is sent for that ID, **Then** the backend returns a Task Not Found error response

## Edge cases

- Completing a task that is already Completed: the PRD does not state the expected result. Open question: reject, ignore, or keep the original Completion Date.
- Reverting a task that is already Open: the PRD does not state the expected result. Open question.
- Completion Date after a revert: the PRD does not say whether it is cleared or kept. Open question.
- The PRD lists In Progress as a valid Status but does not say how a task enters or leaves In Progress. This story covers only Completed and Open.
- Status change request for a task that was deleted by another user: the backend returns a Task Not Found error and the frontend shows an error message.
- Backend unavailable or database error during a status change: the backend returns an internal error and the frontend shows an error message without changing the displayed status.

## Dependencies

- `US-create-and-view-tasks`

## Definition of Done

- [ ] Status field with allowed values Open, In Progress and Completed exists on every task
- [ ] Completion Date and Last Updated Date fields exist on every task
- [ ] Status change endpoint accepts Completed and Open and returns the updated task
- [ ] Error responses for Task Not Found and invalid input are returned in the simple format defined in the PRD
- [ ] Frontend shows a success or error message after each status change
- [ ] Frontend does not show a success state before the backend confirms the change
- [ ] Automated tests pass for all acceptance criteria

## Tasks

- [ ] `BE-task-status-fields-migration` [BE] Add Status, Completion Date and Last Updated Date columns to tasks table
- [ ] `BE-task-status-change-endpoint` [BE] Add PATCH /tasks/{id}/status endpoint to set Completed or Open
- [ ] `FE-task-status-toggle-ui` [FE] Add Complete and Revert controls with success and error messages
- [ ] `QA-task-status-test-suite` [QA] Test suite for completing and reverting tasks

## Requirements

- `R-2304218f` (functional) Users can mark a task as 'Completed'.
- `R-959e2960` (functional) Users can revert a 'Completed' task back to 'Open'.
- `R-34e41747` (data_model) Each task has a Completion Date field, populated when the task is completed.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.

### [BE] Add Status, Completion Date and Last Updated Date columns to tasks table

`BE-task-status-fields-migration` · labels: type:task, area:db, prd-agent

**Parent:** `US-complete-and-reopen-task`

**Track:** backend · **Size:** S · touches DB
## Description

Add a Status column restricted to Open, In Progress and Completed, a nullable Completion Date column and a Last Updated Date column to the tasks table. Existing tasks get Status Open and no Completion Date.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Migration adds the three columns and runs forward and backward without data loss
- [ ] Status column rejects values other than Open, In Progress and Completed
- [ ] Existing tasks have Status Open after the migration
- [ ] Migration is reviewed and merged

## Requirements

- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-34e41747` (data_model) Each task has a Completion Date field, populated when the task is completed.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.

### [BE] Add PATCH /tasks/{id}/status endpoint to set Completed or Open

`BE-task-status-change-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-complete-and-reopen-task`

**Track:** backend · **Size:** M · touches DB
## Description

Add an endpoint that changes the Status of a task to Completed or Open. Completing sets Completion Date to the current time. Every change sets Last Updated Date. Return simple error responses for Task Not Found, invalid input and internal or database errors.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Endpoint sets Status to Completed and sets Completion Date
- [ ] Endpoint sets Status to Open for a Completed task
- [ ] Unknown task ID returns Task Not Found
- [ ] Invalid status value returns an invalid input error
- [ ] Database failure returns an internal error response
- [ ] Last Updated Date is set on every successful change

## Requirements

- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.
- `R-2304218f` (functional) Users can mark a task as 'Completed'.
- `R-959e2960` (functional) Users can revert a 'Completed' task back to 'Open'.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.

### [FE] Add Complete and Revert controls with success and error messages

`FE-task-status-toggle-ui` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-complete-and-reopen-task`

**Track:** frontend · **Size:** M · consumes API
## Description

Add a control on each task to mark it Completed, and a control on each Completed task to revert it to Open. Show the status only after the backend confirms the change. Show a success or error message after each action.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Complete control is shown on Open tasks and Revert control on Completed tasks
- [ ] Displayed status changes only after a successful backend response
- [ ] Success message is shown after a successful change
- [ ] Error message is shown and status is unchanged after a failed change

## Requirements

- `R-2304218f` (functional) Users can mark a task as 'Completed'.
- `R-959e2960` (functional) Users can revert a 'Completed' task back to 'Open'.
- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.

### [QA] Test suite for completing and reverting tasks

`QA-task-status-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-complete-and-reopen-task`

**Track:** qa_general · **Size:** M · consumes API · touches DB
## Description

Automated tests covering the status change endpoint and the UI controls, including success, error, not-found and optimistic-update cases.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Tests cover every acceptance criterion of the story
- [ ] Tests verify Completion Date and Last Updated Date values after each change
- [ ] Tests verify no success state is shown when the backend returns an error
- [ ] Test suite runs in CI and passes

## Requirements

- `R-2304218f` (functional) Users can mark a task as 'Completed'.
- `R-959e2960` (functional) Users can revert a 'Completed' task back to 'Open'.
- `R-34e41747` (data_model) Each task has a Completion Date field, populated when the task is completed.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-244669c0` (backend) The backend exposes endpoints to create, read all, read by ID, update, delete, and change the status of a Todo.
- `R-9dc414dc` (backend) The backend returns simple error responses for task not found, invalid input, missing mandatory fields, updating or deleting non-existent tasks, and internal server or database errors.
- `R-d57336f7` (frontend) A success or error message must be displayed after each create, update, or delete task action.
- `R-ab9e9cb0` (constraint) The frontend must not show a successful state for a task change before the backend confirms it, and must not show success when a backend action fails.

---

## Review the task report with task counts

`US-review-task-report` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

## User story

**As a** project member, **I want** to review all tasks in a table on the reporting page, with Total, Open and Completed task counts, **so that** I can see the overall status of the work at a glance.

## Business description

The task report page lists all tasks in a table and shows counts of Total Tasks, Open Tasks and Completed Tasks. The backend exposes a report API that provides the task data and the metric aggregation used on the page.

## Business value

Reviewers can see how many tasks exist and how many are open or completed without counting rows by hand.

## Acceptance criteria

1. **Given** at least one task exists in the system, **When** a user opens the reporting page, **Then** every task is shown as a row in a table, and each row shows the task's fields as defined in the task list
2. **Given** 5 tasks exist, 2 with status Open and 3 with status Completed, **When** a user opens the reporting page, **Then** the page shows Total Tasks = 5, Open Tasks = 2 and Completed Tasks = 3
3. **Given** no tasks exist, **When** a user opens the reporting page, **Then** the table shows no rows and the page shows Total Tasks = 0, Open Tasks = 0 and Completed Tasks = 0
4. **Given** the task report API is called, **When** the request is answered, **Then** the response contains the task rows and the Total, Open and Completed counts, and the counts equal the number of returned tasks grouped by status

## Edge cases

- No tasks exist: the table is empty and all three counts are 0.
- Total Tasks must equal Open Tasks plus Completed Tasks, provided every task has exactly one of the two statuses. The PRD does not define other statuses; if others exist, this must be clarified.
- Open question: the PRD does not state whether deleted tasks are counted or whether counts respect the filters and search defined in the filter story. This story assumes counts cover all tasks.
- Open question: the PRD does not state whether the report API must accept filter, search and sort parameters in this story or only in the filter story.

## Dependencies

- `US-create-and-view-tasks`
- `US-complete-and-reopen-task`

## Definition of Done

- [ ] The task report table shows every task returned by the report API.
- [ ] Total Tasks, Open Tasks and Completed Tasks are shown on the reporting page and match the API response.
- [ ] The report API returns the task rows and the three counts in one response.
- [ ] Counts are 0 when no tasks exist.
- [ ] Automated tests cover the table, the counts and the empty state.

## Tasks

- [ ] `BE-task-report-api-with-counts` [BE] Add task report API endpoint with Total, Open and Completed aggregation
- [ ] `FE-task-report-table` [FE] Render all tasks in a table on the reporting page
- [ ] `FE-task-report-count-metrics` [FE] Show Total, Open and Completed counts on the reporting page
- [ ] `QA-task-report-test-suite` [QA] Test suite for the task report table and counts

## Requirements

- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.
- `R-4ffbfafa` (functional) The task report shows the counts of Total Tasks, Open Tasks, and Completed Tasks.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### [BE] Add task report API endpoint with Total, Open and Completed aggregation

`BE-task-report-api-with-counts` · labels: type:task, area:backend, prd-agent

**Parent:** `US-review-task-report`

**Track:** backend · **Size:** M · touches DB
## Description

Add a read endpoint that returns all task rows and the Total, Open and Completed counts computed from stored task status. Filter, search and sort parameters are out of scope unless the filter story requires them.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Endpoint returns task rows and the three counts in one response.
- [ ] Counts are computed from stored status values.
- [ ] Endpoint returns zero counts when no tasks exist.
- [ ] Unit and integration tests cover the aggregation.

## Requirements

- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.
- `R-4ffbfafa` (functional) The task report shows the counts of Total Tasks, Open Tasks, and Completed Tasks.

### [FE] Render all tasks in a table on the reporting page

`FE-task-report-table` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-review-task-report`

**Track:** frontend · **Size:** M · consumes API
## Description

Build the table on the reporting page that lists every task returned by the report API.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Every task returned by the API appears as one table row.
- [ ] Empty state is shown when the API returns no tasks.
- [ ] Component tests cover rendering with data and without data.

## Requirements

- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.

### [FE] Show Total, Open and Completed counts on the reporting page

`FE-task-report-count-metrics` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-review-task-report`

**Track:** frontend · **Size:** S · consumes API
## Description

Display the Total Tasks, Open Tasks and Completed Tasks counts from the report API response on the reporting page.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Page shows Total Tasks, Open Tasks and Completed Tasks with values from the API.
- [ ] Counts show 0 when the API returns zero.
- [ ] Component tests verify the displayed values.

## Requirements

- `R-4ffbfafa` (functional) The task report shows the counts of Total Tasks, Open Tasks, and Completed Tasks.

### [QA] Test suite for the task report table and counts

`QA-task-report-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-review-task-report`

**Track:** qa_general · **Size:** M · consumes API
## Description

End-to-end and integration test suite covering the task report table, the three counts and the empty state.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Tests cover a populated report with known counts.
- [ ] Tests cover the empty report with all counts at 0.
- [ ] Tests run in the CI pipeline and pass.

## Requirements

- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.
- `R-4ffbfafa` (functional) The task report shows the counts of Total Tasks, Open Tasks, and Completed Tasks.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

---

## Filter, search and sort the task report

`US-filter-search-sort-task-report` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

## User story

**As a** a team member reviewing the task report, **I want** to filter, search and sort the tasks in the task report, **so that** I can find specific tasks by status, priority, date range or title.

## Business description

The task report shows all tasks in a table. Users can narrow the list by Status, Priority and Date Range, search by task title, and sort by Creation Date, Due Date, Status or Priority. The backend provides the APIs that support filtering, searching, sorting and metric aggregation for the report.

## Business value

Users can locate the tasks they need in the report without scanning every row.

## Acceptance criteria

1. **Given** a task report containing tasks with different statuses, **When** the user selects one Status value in the Status filter, **Then** only tasks with that Status are listed in the table
2. **Given** a task report containing tasks with different priorities, **When** the user selects one Priority value in the Priority filter, **Then** only tasks with that Priority are listed in the table
3. **Given** a task report containing tasks with dates inside and outside a chosen range, **When** the user sets a Date Range filter, **Then** only tasks whose date falls inside the range are listed in the table
4. **Given** tasks titled 'Quarterly report' and 'Budget review' in the task report, **When** the user enters 'report' in the title search, **Then** only the task titled 'Quarterly report' is listed in the table
5. **Given** a task report with several tasks listed, **When** the user sorts by Creation Date, Due Date, Status or Priority, **Then** the table rows are ordered by the selected field
6. **Given** the reporting page is opened and tasks exist, **When** the page finishes loading, **Then** every task is shown as one row in the table
7. **Given** the task report API receives a request with filter, search and sort parameters, **When** the request is processed, **Then** the response contains only the tasks that match all supplied parameters, in the requested sort order

## Edge cases

- The PRD does not state which date Date Range applies to (creation date, due date or both). To be confirmed before build.
- The PRD does not state whether several filters combine with AND logic. To be confirmed.
- The PRD does not state the title search rules (case sensitivity, partial or whole-word match). To be confirmed.
- The PRD does not state the sort direction or the default sort order. To be confirmed.
- The PRD does not define the ranking order of Status or Priority values when sorting. To be confirmed.
- When no task matches the filters or search, the table has no rows. The PRD does not define an empty-state message.
- If a task has no due date, the PRD does not state where it appears when sorting by Due Date.
- The PRD does not state what happens when Date Range start is later than its end. To be confirmed.

## Dependencies

- `US-create-and-view-tasks`
- `US-complete-and-reopen-task`

## Definition of Done

- [ ] Filter by Status, Priority and Date Range returns the expected rows in automated tests
- [ ] Title search returns the expected rows in automated tests
- [ ] Sorting by Creation Date, Due Date, Status and Priority is verified in automated tests
- [ ] Task report API accepts filter, search and sort parameters and is documented
- [ ] Reporting page table shows all tasks and is verified in a manual or automated check
- [ ] Open questions from the edge cases list are answered and recorded in the story

## Tasks

- [ ] `BE-task-report-query-api` [BE] Add task report API with filter, search and sort parameters
- [ ] `FE-report-filter-search-sort-controls` [FE] Add filter, search and sort controls to the task report
- [ ] `FE-report-tasks-table` [FE] Render all tasks in a table on the reporting page
- [ ] `QA-task-report-filter-search-sort` [QA] Add test suite for task report filtering, search and sorting

## Requirements

- `R-5f4ef76c` (functional) The task report can be filtered by Status, Priority, and Date Range.
- `R-48e39a9d` (functional) The task report can be searched by task title.
- `R-f214002a` (functional) The task report can be sorted by Creation Date, Due Date, Status, or Priority.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.
- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.

### [BE] Add task report API with filter, search and sort parameters

`BE-task-report-query-api` · labels: type:task, area:backend, prd-agent

**Parent:** `US-filter-search-sort-task-report`

**Track:** backend · **Size:** M · touches DB
## Description

Expose the API that returns tasks for the report, applying Status, Priority and Date Range filters, title search and sort by Creation Date, Due Date, Status or Priority. Metric aggregation is part of the same API requirement and is covered by its own story.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Endpoint accepts Status, Priority, Date Range, title search and sort parameters
- [ ] Filters, search and sort are applied in the database query, not in the client
- [ ] Invalid parameter values return a documented error response
- [ ] Unit and integration tests cover each parameter and their combination
- [ ] API contract is documented

## Requirements

- `R-5f4ef76c` (functional) The task report can be filtered by Status, Priority, and Date Range.
- `R-48e39a9d` (functional) The task report can be searched by task title.
- `R-f214002a` (functional) The task report can be sorted by Creation Date, Due Date, Status, or Priority.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### [FE] Add filter, search and sort controls to the task report

`FE-report-filter-search-sort-controls` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-filter-search-sort-task-report`

**Track:** frontend · **Size:** M · consumes API
## Description

Add Status, Priority and Date Range filter controls, a title search box and sort controls to the reporting page. Controls call the task report API and update the table.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Status, Priority and Date Range filters are visible and change the table results
- [ ] Title search updates the table results
- [ ] Sort by Creation Date, Due Date, Status and Priority is available and changes row order
- [ ] Controls show the currently applied filter, search and sort state
- [ ] Component tests cover control behaviour

## Requirements

- `R-5f4ef76c` (functional) The task report can be filtered by Status, Priority, and Date Range.
- `R-48e39a9d` (functional) The task report can be searched by task title.
- `R-f214002a` (functional) The task report can be sorted by Creation Date, Due Date, Status, or Priority.

### [FE] Render all tasks in a table on the reporting page

`FE-report-tasks-table` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-filter-search-sort-task-report`

**Track:** frontend · **Size:** S · consumes API
## Description

Display the tasks returned by the task report API as a table on the reporting page, one row per task.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Reporting page shows every task returned by the API as one table row
- [ ] Table columns include the fields needed for filtering, searching and sorting
- [ ] Component test confirms row count matches the API response

## Requirements

- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.

### [QA] Add test suite for task report filtering, search and sorting

`QA-task-report-filter-search-sort` · labels: type:task, area:qa, prd-agent

**Parent:** `US-filter-search-sort-task-report`

**Track:** qa_general · **Size:** M · consumes API
## Description

End-to-end and API tests covering filter, search, sort and table display on the task report, including combined parameters and empty results.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Tests cover each filter, title search and each sort field
- [ ] Tests cover combined filters, search and sort
- [ ] Tests cover the empty result case
- [ ] Test suite runs in the continuous integration pipeline and passes

## Requirements

- `R-5f4ef76c` (functional) The task report can be filtered by Status, Priority, and Date Range.
- `R-48e39a9d` (functional) The task report can be searched by task title.
- `R-f214002a` (functional) The task report can be sorted by Creation Date, Due Date, Status, or Priority.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.
- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.

---

## Export the current task report view to Excel

`US-export-task-report-to-excel` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

## User story

**As a** project member who reviews task reports, **I want** to download the current task report view as an Excel file, **so that** I can share or analyse the filtered and sorted task data outside the application.

## Business description

Users can export the task report data to Excel. The exported file contains only the rows that match the currently applied filters, in the currently applied sort order. The file has clear column headers, one consistent date format, and a file name that includes the generation timestamp. If there is no data to export, the user sees a message and no file is produced.

## Business value

Users can take task report data out of the application for sharing and offline analysis, and the exported data matches what they see on screen.

## Acceptance criteria

1. **Given** a task report with at least one row is displayed, **When** the user selects the Export to Excel action, **Then** an Excel file is downloaded to the user's device
2. **Given** a task report with filters and a sort order applied, **When** the user exports the report to Excel, **Then** the file contains only the rows matching the applied filters, in the same order as the applied sort
3. **Given** an exported Excel file with date columns, **When** the file is opened, **Then** the header row has a label for every column and every date column uses the same date format
4. **Given** a user exports the report at a known generation time, **When** the file is downloaded, **Then** the file name contains the timestamp of the generation time
5. **Given** the current filters return zero rows, **When** the user selects the Export to Excel action, **Then** no file is downloaded and a message informing the user that there is no data to export is shown
6. **Given** the team has recorded its decision on where the Excel file is generated, **When** the user exports the report, **Then** the file content and file name are the same whichever side generates the file

## Edge cases

- Filters return zero rows: no file is produced and a message is shown. The message wording is not specified in the PRD and needs a decision.
- The exact date format for date columns is not specified in the PRD and needs a decision.
- The exact timestamp format used in the file name is not specified in the PRD and needs a decision.
- Export is requested while the filters or sort are changing: the PRD does not define which state is exported.
- Very large result sets: the PRD does not define a maximum number of rows or a size limit for export.

## Dependencies

- `US-filter-search-sort-task-report`
- `US-review-task-report`

## Definition of Done

- [ ] Export action downloads an .xlsx file containing the filtered and sorted rows
- [ ] Exported file has a header row with clear column labels
- [ ] All date columns use one documented date format
- [ ] File name includes the generation timestamp in a documented format
- [ ] Zero-row export shows a user message and produces no file
- [ ] Decision on frontend or backend generation is recorded and implemented
- [ ] Automated tests cover filtering, sorting, headers, date format, file name and empty-data behaviour

## Tasks

- [ ] `BE-export-excel-data-query` [BE] Add export data query that applies current filters and sort
- [ ] `BE-excel-generation-decision` [BE] Decide where the Excel file is generated, frontend or backend
- [ ] `BE-excel-file-generation` [BE] Generate Excel file with headers, date format and timestamped name
- [ ] `FE-export-button-and-empty-message` [FE] Add Export to Excel action and no-data message to task report
- [ ] `QA-export-test-suite` [QA] Add end-to-end test suite for task report Excel export

## Requirements

- `R-52360b76` (functional) The user can download task report data as an Excel file.
- `R-09e9d163` (functional) The exported Excel file must contain only the rows matching the currently applied filters, in the currently applied sort order.
- `R-fad183b1` (non_functional) The exported Excel file must have clear column headers and use one consistent date format across all date columns.
- `R-d22b9b6a` (functional) The exported Excel file name must include the timestamp of when the file was generated.
- `R-437992f1` (frontend) When there is no data to export, the system must show a message to the user instead of producing an export file; the message text is not specified in the PRD.
- `R-3a63e0ce` (decision_open) The development team decides whether the Excel file is generated on the frontend or the backend.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### [BE] Add export data query that applies current filters and sort

`BE-export-excel-data-query` · labels: type:task, area:backend, prd-agent

**Parent:** `US-export-task-report-to-excel`

**Track:** backend · **Size:** M · touches DB
## Description

Provide the server-side data source for the export that applies the same filters, search and sort as the task report view. Returns the rows and columns needed for the Excel file.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Export data source returns only rows matching the applied filters
- [ ] Rows are returned in the applied sort order
- [ ] Returns an empty result when no rows match
- [ ] Unit tests cover filter, search and sort combinations

## Requirements

- `R-09e9d163` (functional) The exported Excel file must contain only the rows matching the currently applied filters, in the currently applied sort order.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### [BE] Decide where the Excel file is generated, frontend or backend

`BE-excel-generation-decision` · labels: type:spike, area:backend, prd-agent

**Parent:** `US-export-task-report-to-excel`

**Track:** backend · **Size:** S
## Description

Decision spike. Compare generating the Excel file in the frontend and in the backend. Consider file size, library support, testability, and dependency on the data query. Record the chosen option.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Decision document records the chosen option and its rationale
- [ ] Trade-offs of frontend and backend generation are documented
- [ ] Open implementation questions from the story are listed with owners

## Requirements

- `R-3a63e0ce` (decision_open) The development team decides whether the Excel file is generated on the frontend or the backend.

### [BE] Generate Excel file with headers, date format and timestamped name

`BE-excel-file-generation` · labels: type:task, area:backend, prd-agent

**Parent:** `US-export-task-report-to-excel`

**Track:** backend · **Size:** M
## Description

Build the .xlsx file from the export data. Use clear column headers, one consistent date format for all date columns, and a file name that includes the generation timestamp. If the generation side is decided as frontend, this task supplies the shared column and format definitions instead.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Generated file is a valid .xlsx file
- [ ] Header row uses clear column labels
- [ ] All date columns use one documented date format
- [ ] File name includes the generation timestamp
- [ ] Generation is covered by automated tests

## Requirements

- `R-52360b76` (functional) The user can download task report data as an Excel file.
- `R-fad183b1` (non_functional) The exported Excel file must have clear column headers and use one consistent date format across all date columns.
- `R-d22b9b6a` (functional) The exported Excel file name must include the timestamp of when the file was generated.

### [FE] Add Export to Excel action and no-data message to task report

`FE-export-button-and-empty-message` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-export-task-report-to-excel`

**Track:** frontend · **Size:** M · consumes API
## Description

Add an Export to Excel action to the task report view. Trigger the download with the current filters and sort. When the result is empty, show a message and do not start a download.

## Blocked by

- Nothing.

## Definition of Done

- [ ] Export action is visible on the task report view
- [ ] Download starts with the current filters and sort applied
- [ ] Zero-row state shows a message and no download starts
- [ ] Component tests cover the download and empty-data states

## Requirements

- `R-52360b76` (functional) The user can download task report data as an Excel file.
- `R-437992f1` (frontend) When there is no data to export, the system must show a message to the user instead of producing an export file; the message text is not specified in the PRD.

### [QA] Add end-to-end test suite for task report Excel export

`QA-export-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-export-task-report-to-excel`

**Track:** qa_general · **Size:** M
## Description

Test suite covering the export flow end to end: filters, sort, headers, date format, file name timestamp and empty-data message.

## Blocked by

- Nothing.

## Definition of Done

- [ ] End-to-end tests verify the exported rows match the applied filters and sort
- [ ] End-to-end tests verify headers, date format and file name pattern
- [ ] End-to-end tests verify the zero-row message and absence of a file
- [ ] Test suite runs in the CI pipeline

## Requirements

- Derived task: testing.
