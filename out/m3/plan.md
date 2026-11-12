# Personal task management system

`EPIC-personal-task-management-system` · labels: type:epic, prd-agent

## Scope

A personal task management system for tracking daily tasks and generating status reports. Page 1 manages the user's to-do list: create, view, update, delete, and change task status, with a defined task data model and validation rules. Page 2 is a task reporting page that shows an aggregated, filterable, searchable, sortable table with metrics and an Excel export. Where the PRD leaves choices open, such as where the Excel file is generated and the wording of the no-data message, these remain open questions.

## Business goals

- Track daily tasks
- Generate status reports

## User stories

- [ ] `US-create-task` Create a new task with required fields
- [ ] `US-view-task-list` View the task list with status and priority indicators
- [ ] `US-update-task` Edit an existing task
- [ ] `US-delete-task` Delete a task after confirmation
- [ ] `US-change-task-status` Mark a task as Completed or revert it to Open
- [ ] `US-view-task-report` View all tasks in a report table with metrics
- [ ] `US-filter-report-tasks` Filter report tasks by status, priority and date range
- [ ] `US-search-report-tasks` Search report tasks by title
- [ ] `US-sort-report-tasks` Sort report tasks by creation date, due date, status or priority
- [ ] `US-export-report-excel` Export the filtered report tasks to an Excel file

---

## Create a new task with required fields

`US-create-task` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user, **I want** create a new task with its required fields, **so that** I can record a piece of work in my personal task list.

### Business description

Users need to add tasks to their personal to-do list. Each new task stores a unique ID, a Title, a Description, a Status, a Priority, a Creation Date, a Due Date, a Last Updated Date and a Completion Date. The task is saved in the persistence database, in a new tasks table.

### Business value

Without task creation, no other to-do capability (viewing, editing, status changes, reporting) has data to work on. Mandatory titles and date validation keep stored tasks complete and consistent.

### Acceptance criteria

1. **Given** A user opens the task creation form, **When** The user submits the form with a non-empty title and all other required inputs valid, **Then** The backend stores exactly one new task with a unique ID, and the form shows a success message
2. **Given** A user opens the task creation form, **When** The user submits the form with an empty title, **Then** The backend rejects the task, no task is stored, and the form shows an error message that names the title field as mandatory
3. **Given** A user opens the task creation form with a Creation Date of 2024-05-10, **When** The user submits a Due Date of 2024-05-09, **Then** The backend rejects the task with an error stating that the Due Date cannot be earlier than the Creation Date, and no task is stored
4. **Given** A user opens the task creation form with a Creation Date of 2024-05-10, **When** The user submits a Due Date of 2024-05-10, **Then** The backend accepts the task because the Due Date is not earlier than the Creation Date
5. **Given** A new task has been stored, **When** The task is read from the database, **Then** The task has the fields ID, Title, Description, Status, Priority, Creation Date, Due Date, Last Updated Date and Completion Date, and Completion Date is empty
6. **Given** The backend create request fails because of a database error, **When** The user submits the task creation form, **Then** The form shows an error message and does not show the task as created
7. **Given** A create request has been sent but the backend has not yet responded, **When** The form is waiting for the response, **Then** The frontend does not show a success message or add the task to any list

### Edge cases

- The PRD does not state the exact wording of the success message; the wording is an open question.
- The PRD does not state whether Due Date is mandatory; if it is left empty, the behaviour is an open question.
- The PRD does not say whether a title containing only spaces counts as empty; this is an open question.
- The PRD does not state the default values of Status and Priority on creation; this is an open question.
- A Due Date equal to the Creation Date is valid.
- Completion Date stays empty on creation because the task is not completed yet.

### Dependencies

- None.

### Definition of Done

- [ ] The tasks table migration creates every task data-model field, including the unique ID and Completion Date.
- [ ] POST /tasks rejects an empty title and a Due Date earlier than the Creation Date, with clear error responses.
- [ ] The form shows a success message only after the backend confirms the save, and an error message on failure.
- [ ] The form does not add the task to any list before the backend responds.
- [ ] Automated tests cover the valid, empty-title and date-order cases.

### Tasks

- [ ] `BE-tasks-table-migration` [BE] Add migration that creates the tasks table with all task data-model fields
- [ ] `BE-create-task-endpoint` [BE] Add POST /tasks endpoint with title and Due Date validation
- [ ] `FE-create-task-form` [FE] Add task creation form with title, description, priority and due date
- [ ] `QA-create-task-test-suite` [QA] Add test suite for task creation across API, database and form

### Requirements

- `R-22f28530` (functional) The user can create a new task.
- `R-9675bb49` (data_model) Each task has a unique ID field.
- `R-aaf23206` (data_model) Each task has a Title field.
- `R-c9046f7a` (data_model) Each task has a Description field.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-9fb58566` (data_model) Each task has a Priority field whose allowed values are Low, Medium and High.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-71bdd372` (data_model) Each task has a Due Date field.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-34e41747` (data_model) Each task has a Completion Date field, populated when the task is completed.
- `R-03df7815` (validation_rule) The system rejects a task whose title is empty, so task titles are mandatory.
- `R-efe1e5d4` (validation_rule) The system rejects a task whose Due Date is earlier than its Creation Date.
- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-d57336f7` (frontend) A success or error message is displayed after each create, update and delete task action.
- `R-c55a77b3` (backend) To-do items must be saved in the persistence database, which is assumed to already exist, in a new table created for them.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

### Task: [BE] Add migration that creates the tasks table with all task data-model fields

`BE-tasks-table-migration` · labels: type:task, area:db, prd-agent

**Parent:** `US-create-task`

**Track:** backend · **Size:** S · touches DB
#### Description

Create the new tasks table in the existing persistence database with the unique ID, Title, Description, Status, Priority, Creation Date, Due Date, Last Updated Date and Completion Date columns.

#### Blocked by

- Nothing.

#### Definition of Done

- [ ] Migration creates the tasks table with all nine data-model fields.
- [ ] Migration runs and rolls back cleanly on the existing database.
- [ ] Status and Priority columns accept only the allowed values.

#### Requirements

- `R-c55a77b3` (backend) To-do items must be saved in the persistence database, which is assumed to already exist, in a new table created for them.
- `R-9675bb49` (data_model) Each task has a unique ID field.
- `R-aaf23206` (data_model) Each task has a Title field.
- `R-c9046f7a` (data_model) Each task has a Description field.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-9fb58566` (data_model) Each task has a Priority field whose allowed values are Low, Medium and High.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-71bdd372` (data_model) Each task has a Due Date field.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-34e41747` (data_model) Each task has a Completion Date field, populated when the task is completed.

### Task: [BE] Add POST /tasks endpoint with title and Due Date validation

`BE-create-task-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-create-task`

**Track:** backend · **Size:** M · touches DB
#### Description

Add the create operation of the tasks endpoint. Reject an empty title, reject a Due Date earlier than the Creation Date, store the task with a unique ID, and return clear errors for invalid input and database failures.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] POST /tasks stores one task with a unique ID when input is valid.
- [ ] An empty title is rejected and no task is stored.
- [ ] A Due Date earlier than the Creation Date is rejected and no task is stored.
- [ ] A database failure returns an internal error response and no task is stored.
- [ ] Error responses use one simple format.

#### Requirements

- `R-22f28530` (functional) The user can create a new task.
- `R-03df7815` (validation_rule) The system rejects a task whose title is empty, so task titles are mandatory.
- `R-efe1e5d4` (validation_rule) The system rejects a task whose Due Date is earlier than its Creation Date.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.

### Task: [FE] Add task creation form with title, description, priority and due date

`FE-create-task-form` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-create-task`

**Track:** frontend · **Size:** M · consumes API
#### Description

Build the create form with title, description, priority and due date inputs. Call POST /tasks on submit. Show a success message only after the backend confirms the save, and an error message naming the failed field or reason otherwise.

#### Blocked by

- `BE-create-task-endpoint`

#### Definition of Done

- [ ] The form shows a success message only after the backend confirms the save.
- [ ] The form shows an error message when the backend rejects the task or fails.
- [ ] The task is not added to any list while the request is pending.
- [ ] The title field is marked as mandatory.

#### Requirements

- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-d57336f7` (frontend) A success or error message is displayed after each create, update and delete task action.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

### Task: [QA] Add test suite for task creation across API, database and form

`QA-create-task-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-create-task`

**Track:** qa_general · **Size:** S · consumes API · touches DB
#### Description

Test task creation end to end: valid create, empty title, Due Date earlier than Creation Date, Due Date equal to Creation Date, database failure, and the pending state of the form.

#### Blocked by

- `BE-create-task-endpoint`
- `FE-create-task-form`
- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Tests cover every acceptance criterion of this story.
- [ ] Tests check the stored fields and that rejected tasks are not stored.
- [ ] Tests pass in the CI pipeline.

#### Requirements

- `R-22f28530` (functional) The user can create a new task.
- `R-03df7815` (validation_rule) The system rejects a task whose title is empty, so task titles are mandatory.
- `R-efe1e5d4` (validation_rule) The system rejects a task whose Due Date is earlier than its Creation Date.

---

## View the task list with status and priority indicators

`US-view-task-list` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user with a personal to-do list, **I want** to view my task list with a status and a priority indicator on each task, **so that** I can see the state and urgency of my tasks at a glance on the to-do management page.

### Business description

The to-do management page lets the user manage their personal task list. This story delivers the read-only task list view: it shows the user's tasks, each with a status indicator and a priority indicator, and shows loading, empty and error states. The list refreshes automatically when a task is changed. Creating, editing, deleting and changing status are handled by other stories.

### Business value

The user can see all their tasks and their state in one place, so they know what is open, in progress or completed and how urgent each task is.

### Acceptance criteria

1. **Given** The user has at least one task in their personal task list, **When** The user opens the to-do management page, **Then** The task list view shows each of the user's tasks, with a status indicator and a priority indicator on every row
2. **Given** A task has status Open, In Progress or Completed, **When** The task list view renders that task, **Then** The status indicator shows the task's current status text and a visually distinct mark for each of the three values
3. **Given** A task has priority Low, Medium or High, **When** The task list view renders that task, **Then** The priority indicator shows the task's priority text and a visually distinct mark for each of the three values
4. **Given** The task list request to the backend has not yet completed, **When** The task list view is displayed, **Then** A loading state is shown and no task rows or empty-state text are shown
5. **Given** The user has no tasks, **When** The backend returns an empty task list, **Then** The empty state is shown and no task rows are shown
6. **Given** The task list request to the backend fails with an error, **When** The task list view is displayed, **Then** The error state is shown with a message, and the loading state is no longer shown
7. **Given** The task list is displayed and the user creates, updates, deletes or changes the status of a task, **When** The backend confirms the change succeeded, **Then** The task list is reloaded from the backend and shows the changed task without a manual page refresh
8. **Given** The backend read endpoint for all tasks is called, **When** The request is received, **Then** The backend returns only the tasks belonging to the requesting user

### Edge cases

- A task whose status or priority value is outside the allowed values cannot be produced by the data model, so the indicators need only handle Open, In Progress, Completed, Low, Medium and High (open question: the PRD does not state how the view should display a value outside these sets)
- The list refresh happens only after the backend confirms a change; the view must not show the changed state before that confirmation
- A read by ID request for a task that does not exist returns a task-not-found error, which this story exposes through the backend read endpoint but does not display in a dedicated screen (open question: the PRD does not say where a single-task view is shown)
- The PRD does not state how many tasks the list shows per page or whether it paginates (open question)
- The PRD does not state how the user is authenticated or how tasks are scoped to a user (open question)

### Dependencies

- `US-create-task`

### Definition of Done

- [ ] Backend exposes a GET endpoint that returns all tasks for the requesting user, with each task's status and priority
- [ ] Backend exposes a GET endpoint that returns one task by ID, returning a task-not-found error when the ID does not exist
- [ ] Backend returns the error responses defined by the shared error handling approach for not-found and internal server or database errors
- [ ] Task list view renders loading, empty and error states as separate, distinguishable views
- [ ] Status indicator and priority indicator render for every task row with all allowed values
- [ ] Task list refetches from the backend after a create, update, delete or status change succeeds, and does not update the list optimistically
- [ ] Automated tests cover the loading, empty, error and populated states of the task list view
- [ ] Automated tests cover the GET all and GET by ID endpoints, including the not-found case
- [ ] Open questions on pagination, authentication scope and single-task display are recorded in the story notes

### Tasks

- [ ] `BE-tasks-read-endpoints` [BE] Add GET /tasks and GET /tasks/{id} read endpoints with not-found handling
- [ ] `FE-task-list-view` [FE] Build the task list view with status and priority indicators
- [ ] `FE-task-list-auto-refresh` [FE] Refresh the task list after a successful task change
- [ ] `QA-task-list-qa` [QA] Test suite for the task list view and read endpoints

### Requirements

- `R-eed06908` (functional) The to-do management page lets the user manage their personal task list.
- `R-4bed9064` (functional) The user can view the task list.
- `R-60e02b8e` (frontend) The system provides a task list view that displays the user's to-do tasks.
- `R-48c89e9e` (frontend) The system displays a status indicator and a priority indicator for each task.
- `R-d7e6667f` (frontend) The task list view shows a distinct loading state, empty state, and error state.
- `R-6a73fa71` (frontend) The task list refreshes automatically when a task is changed.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [BE] Add GET /tasks and GET /tasks/{id} read endpoints with not-found handling

`BE-tasks-read-endpoints` · labels: type:task, area:backend, prd-agent

**Parent:** `US-view-task-list`

**Track:** backend · **Size:** M · touches DB
#### Description

Implement the read-all and read-by-ID endpoints for the user's to-do items. Return only the requesting user's tasks. Return a task-not-found error for an unknown ID, and use the shared simple error response format for internal and database errors. Create and write endpoints belong to other stories.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] GET /tasks returns the requesting user's tasks including status and priority
- [ ] GET /tasks/{id} returns one task or a task-not-found error
- [ ] Internal and database errors return the shared error response format
- [ ] Unit and integration tests cover both endpoints and the not-found case

#### Requirements

- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-4bed9064` (functional) The user can view the task list.

### Task: [FE] Build the task list view with status and priority indicators

`FE-task-list-view` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-list`

**Track:** frontend · **Size:** M · consumes API
#### Description

Build the task list component on the to-do management page. Each row shows the task's status indicator and priority indicator. The component renders distinct loading, empty and error states, and calls the read-all endpoint.

#### Blocked by

- `BE-tasks-read-endpoints`

#### Definition of Done

- [ ] Each row shows a status indicator and a priority indicator for all allowed values
- [ ] Loading, empty and error states are visually distinct from each other and from the populated list
- [ ] Component consumes GET /tasks
- [ ] Component tests cover all four states

#### Requirements

- `R-60e02b8e` (frontend) The system provides a task list view that displays the user's to-do tasks.
- `R-48c89e9e` (frontend) The system displays a status indicator and a priority indicator for each task.
- `R-d7e6667f` (frontend) The task list view shows a distinct loading state, empty state, and error state.
- `R-eed06908` (functional) The to-do management page lets the user manage their personal task list.

### Task: [FE] Refresh the task list after a successful task change

`FE-task-list-auto-refresh` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-list`

**Track:** frontend · **Size:** S · consumes API
#### Description

Make the task list reload from the backend after a create, update, delete or status change is confirmed by the backend. The list must not change before the backend confirms the action.

#### Blocked by

- `BE-tasks-read-endpoints`

#### Definition of Done

- [ ] List refetches after each successful task change event
- [ ] No list update occurs before backend confirmation
- [ ] Test verifies refetch after a mocked successful change and no refetch after a failed change

#### Requirements

- `R-6a73fa71` (frontend) The task list refreshes automatically when a task is changed.

### Task: [QA] Test suite for the task list view and read endpoints

`QA-task-list-qa` · labels: type:task, area:qa, prd-agent

**Parent:** `US-view-task-list`

**Track:** qa_general · **Size:** M · consumes API
#### Description

Write the end-to-end and integration tests for the task list story, covering the populated, loading, empty and error states, the status and priority indicators, the auto-refresh behaviour and the read endpoints.

#### Blocked by

- `BE-tasks-read-endpoints`
- `FE-task-list-view`

#### Definition of Done

- [ ] End-to-end test shows the list with indicators for seeded tasks
- [ ] End-to-end test covers loading, empty and error states
- [ ] End-to-end test confirms the list refreshes after a change
- [ ] Test report is attached to the story

#### Requirements

- `R-4bed9064` (functional) The user can view the task list.
- `R-d7e6667f` (frontend) The task list view shows a distinct loading state, empty state, and error state.
- `R-6a73fa71` (frontend) The task list refreshes automatically when a task is changed.

---

## Edit an existing task

`US-update-task` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user, **I want** to edit an existing task and save my changes, **so that** my task list reflects the current state of my work.

### Business description

The user can change the details of a task that already exists. The same form used to create a task is reused in edit mode. The backend validates the changed values and returns a success or error result, and the frontend shows that result only after the backend confirms the change.

### Business value

Users can correct and maintain their tasks without deleting and recreating them, which keeps the task list accurate.

### Acceptance criteria

1. **Given** an existing task with a valid title and a Due Date not earlier than its Creation Date, **When** the user opens the edit form, changes the title, and submits the form, **Then** the backend stores the new title and the task shows the new title in the list after the backend returns success
2. **Given** an existing task being edited in the form, **When** the user clears the title field and submits the form, **Then** the backend rejects the update, the task keeps its previous title, and an error message stating that the title is mandatory is shown
3. **Given** an existing task with Creation Date 2024-05-10, **When** the user sets the Due Date to 2024-05-09 and submits the update, **Then** the backend rejects the update with a validation error, the stored Due Date is unchanged, and an error message is shown
4. **Given** a task update request where the backend returns an error, **When** the frontend receives the error response, **Then** the frontend does not show the task as updated and displays an error message
5. **Given** a task update request where the backend returns success, **When** the frontend receives the success response, **Then** the frontend displays a success message after the update action
6. **Given** a task ID that does not exist in the database, **When** an update request is sent for that ID, **Then** the backend returns a Task Not Found error and no data is changed

### Edge cases

- Update request for a task that was deleted by another session: the backend returns Task Not Found and the frontend shows an error message.
- Title containing only spaces: the PRD does not say whether whitespace-only titles are empty; this is an open question.
- Due Date equal to Creation Date: the PRD rejects only dates earlier than the Creation Date, so equal dates are accepted.
- Update that fails with an internal server or database error: the frontend shows an error and does not show the task as updated.
- Open question: the PRD does not state which fields are editable; whether Creation Date, Status and Completion Date can be changed through the update is not specified.
- Open question: the PRD lists a Last Updated Date field but does not state that it must change on each update; this needs confirmation.

### Dependencies

- `US-create-task`

### Definition of Done

- [ ] Update endpoint accepts changes to a task by ID and returns the updated task on success.
- [ ] Backend rejects an empty title and a Due Date earlier than the Creation Date with a validation error, and stores nothing in those cases.
- [ ] Backend returns Task Not Found for an unknown ID and an error for invalid input, as defined by the shared error handling.
- [ ] Frontend reuses the create/edit form in edit mode with the existing values pre-filled.
- [ ] Frontend shows a success or error message after every update action.
- [ ] Frontend does not show a task as updated until the backend returns success.
- [ ] Open questions about editable fields and Last Updated Date are recorded and answered before release.

### Tasks

- [ ] `BE-task-update-endpoint` [BE] Add update endpoint for a task by ID with validation and error responses
- [ ] `FE-task-edit-form` [FE] Reuse task form in edit mode with existing values pre-filled
- [ ] `QA-task-update-tests` [QA] Test suite for editing an existing task

### Requirements

- `R-bc3213df` (functional) The user can update an existing task.
- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-03df7815` (validation_rule) The system rejects a task whose title is empty, so task titles are mandatory.
- `R-efe1e5d4` (validation_rule) The system rejects a task whose Due Date is earlier than its Creation Date.
- `R-d57336f7` (frontend) A success or error message is displayed after each create, update and delete task action.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

### Task: [BE] Add update endpoint for a task by ID with validation and error responses

`BE-task-update-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-update-task`

**Track:** backend · **Size:** M · touches DB
#### Description

Implement the update operation of the task endpoints: accept changed fields for an existing task ID, validate that the title is not empty and that the Due Date is not earlier than the Creation Date, store the change, and return the updated task. Return Task Not Found for unknown IDs and the shared error responses for invalid input and internal or database errors. Only the update operation is built here; create, read, delete and status change belong to other stories.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Endpoint updates an existing task and returns the updated task.
- [ ] Empty title is rejected and nothing is stored.
- [ ] Due Date earlier than Creation Date is rejected and nothing is stored.
- [ ] Unknown task ID returns Task Not Found.
- [ ] Invalid input and internal or database errors return the shared error format.
- [ ] Unit tests cover each validation rule and error case.

#### Requirements

- `R-bc3213df` (functional) The user can update an existing task.
- `R-03df7815` (validation_rule) The system rejects a task whose title is empty, so task titles are mandatory.
- `R-efe1e5d4` (validation_rule) The system rejects a task whose Due Date is earlier than its Creation Date.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [FE] Reuse task form in edit mode with existing values pre-filled

`FE-task-edit-form` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-update-task`

**Track:** frontend · **Size:** M · consumes API
#### Description

Extend the existing task creation/editing form so that it opens for an existing task with its current values filled in. On submit, call the update endpoint. Do not show the task as updated until the backend returns success. Show a success or error message after the update action.

#### Blocked by

- `BE-task-update-endpoint`
- `FE-create-task-form`

#### Definition of Done

- [ ] Edit form opens with the current values of the selected task.
- [ ] Submit calls the update endpoint and waits for its response.
- [ ] No success state is shown before the backend returns success.
- [ ] A success message is shown after a successful update.
- [ ] An error message is shown when the backend returns an error, and the displayed task is unchanged.
- [ ] Empty title and past Due Date errors from the backend are shown next to the relevant field or as a message.

#### Requirements

- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-d57336f7` (frontend) A success or error message is displayed after each create, update and delete task action.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.
- `R-bc3213df` (functional) The user can update an existing task.

### Task: [QA] Test suite for editing an existing task

`QA-task-update-tests` · labels: type:task, area:qa, prd-agent

**Parent:** `US-update-task`

**Track:** qa_general · **Size:** S · consumes API
#### Description

Write the test suite for the edit story covering the update endpoint, the edit form and the messages after each update action, including the rule that no optimistic success state is shown.

#### Blocked by

- `BE-task-update-endpoint`
- `FE-task-edit-form`

#### Definition of Done

- [ ] Tests cover a successful update, empty title rejection, Due Date rejection, Task Not Found and internal error cases.
- [ ] Tests verify the success message appears only after backend success.
- [ ] Tests verify the error message appears and the task is not shown as updated when the backend fails.
- [ ] All tests pass in the continuous integration pipeline.

#### Requirements

- `R-bc3213df` (functional) The user can update an existing task.
- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-03df7815` (validation_rule) The system rejects a task whose title is empty, so task titles are mandatory.
- `R-efe1e5d4` (validation_rule) The system rejects a task whose Due Date is earlier than its Creation Date.
- `R-d57336f7` (frontend) A success or error message is displayed after each create, update and delete task action.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

---

## Delete a task after confirmation

`US-delete-task` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user of the to-do list, **I want** to delete a task after confirming the deletion, **so that** tasks I no longer need are removed from my list.

### Business description

The user can delete a task from their list. Deletion requires a confirmation prompt. The frontend shows a success or error message after the delete action, and shows a success state only after the backend confirms the deletion.

### Business value

Users can remove tasks they no longer need, and accidental deletions are reduced by the confirmation prompt.

### Acceptance criteria

1. **Given** a task with a known ID exists in the user's list, **When** the user selects delete on that task and cancels the confirmation prompt, **Then** no delete request is sent to the backend and the task remains in the list
2. **Given** a task with a known ID exists in the user's list, **When** the user selects delete and confirms the prompt, **Then** the frontend sends a delete request for that task ID, the backend responds with success, and the frontend shows a success message and removes the task from the list
3. **Given** a task with a known ID exists in the user's list, **When** the user confirms the delete prompt and the backend returns an error, **Then** the task remains visible in the list and the frontend shows an error message; no success state is shown
4. **Given** a task ID that does not exist in storage, **When** a delete request is sent for that ID, **Then** the backend responds with a task-not-found error and no data is changed
5. **Given** the database is unavailable during a delete request, **When** the backend attempts to delete the task, **Then** the backend responds with an internal server or database error and the task is not reported as deleted

### Edge cases

- A delete request for a task ID that does not exist returns a task-not-found error and changes no data.
- The database is unavailable during a delete request: the backend returns an internal server or database error and the task is not reported as deleted.
- The backend returns an error after the user confirms: the task stays in the list and no success state is shown.
- The PRD does not state whether deletion is permanent or soft. This is an open question for the team.
- The PRD does not state how the frontend should behave if the delete request times out without a response. This is an open question for the team.

### Dependencies

- `US-create-task`
- `US-view-task-list`

### Definition of Done

- [ ] DELETE /tasks/{id} removes the task with the given ID and returns success.
- [ ] A delete request for an unknown ID returns a task-not-found error and changes no data.
- [ ] A database or internal error during delete returns an error response and the task is not reported as deleted.
- [ ] The delete action opens a confirmation prompt; cancelling sends no request.
- [ ] Confirming sends the delete request; the success message is shown and the task is removed only after success.
- [ ] An error response shows an error message and keeps the task visible.
- [ ] No success state is shown before the backend confirms the deletion.
- [ ] Automated tests cover the confirm, cancel, success, not-found and server-error paths.

### Tasks

- [ ] `BE-delete-task-endpoint` [BE] Add DELETE /tasks/{id} endpoint that removes a task by ID
- [ ] `BE-delete-task-error-handling` [BE] Return not-found and server error responses for task deletion
- [ ] `FE-delete-confirmation-prompt` [FE] Add delete action with confirmation prompt on each task
- [ ] `FE-delete-result-feedback` [FE] Show success or error after task deletion, with no optimistic removal
- [ ] `QA-delete-task-test-suite` [QA] Add test suite for task deletion with confirmation and error paths

### Requirements

- `R-8523b9ec` (functional) The user can delete a task.
- `R-8ef41ba1` (frontend) Deleting a task requires the user to confirm the deletion through a prompt before it is performed.
- `R-d57336f7` (frontend) A success or error message is displayed after each create, update and delete task action.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

### Task: [BE] Add DELETE /tasks/{id} endpoint that removes a task by ID

`BE-delete-task-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-delete-task`

**Track:** backend · **Size:** S · touches DB
#### Description

Add the DELETE /tasks/{id} endpoint. It deletes the stored task with the given ID and returns success. It covers only the delete part of the shared task endpoints.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] DELETE /tasks/{id} deletes the stored task and returns a success response.
- [ ] The endpoint does not change any other task.
- [ ] Unit or integration tests cover success for an existing ID.

#### Requirements

- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-8523b9ec` (functional) The user can delete a task.

### Task: [BE] Return not-found and server error responses for task deletion

`BE-delete-task-error-handling` · labels: type:task, area:backend, prd-agent

**Parent:** `US-delete-task`

**Track:** backend · **Size:** S · touches DB
#### Description

Make DELETE /tasks/{id} return a task-not-found error for an unknown ID and an internal or database error when storage fails. Use the simple error handling approach from the PRD.

#### Blocked by

- `BE-delete-task-endpoint`
- `BE-tasks-table-migration`

#### Definition of Done

- [ ] An unknown ID returns the task-not-found error and changes no data.
- [ ] A database failure returns an internal server or database error and the task is not reported as deleted.
- [ ] Error responses follow the simple error format used by the other endpoints.

#### Requirements

- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [FE] Add delete action with confirmation prompt on each task

`FE-delete-confirmation-prompt` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-delete-task`

**Track:** frontend · **Size:** S · consumes API
#### Description

Add a delete action to each task in the list. Selecting it opens a confirmation prompt. Cancelling sends no request. Confirming sends the delete request for that task ID.

#### Blocked by

- `BE-delete-task-endpoint`

#### Definition of Done

- [ ] Each task in the list shows a delete action.
- [ ] Selecting delete opens a confirmation prompt.
- [ ] Cancelling the prompt sends no request and leaves the task in the list.
- [ ] Confirming sends a delete request for the selected task ID.

#### Requirements

- `R-8ef41ba1` (frontend) Deleting a task requires the user to confirm the deletion through a prompt before it is performed.
- `R-8523b9ec` (functional) The user can delete a task.

### Task: [FE] Show success or error after task deletion, with no optimistic removal

`FE-delete-result-feedback` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-delete-task`

**Track:** frontend · **Size:** S · consumes API
#### Description

After the delete request completes, show a success message and remove the task only on backend success. On error, show an error message and keep the task visible. Do not remove the task before the backend responds.

#### Blocked by

- `BE-delete-task-endpoint`
- `BE-delete-task-error-handling`

#### Definition of Done

- [ ] A success message is shown only after the backend confirms the deletion.
- [ ] The task is removed from the list only after a success response.
- [ ] An error response shows an error message and keeps the task visible.
- [ ] No success state is shown when the backend returns an error.

#### Requirements

- `R-d57336f7` (frontend) A success or error message is displayed after each create, update and delete task action.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

### Task: [QA] Add test suite for task deletion with confirmation and error paths

`QA-delete-task-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-delete-task`

**Track:** qa_general · **Size:** S
#### Description

Test suite for the delete story. It covers the confirm and cancel paths, success and error messages, the not-found response, and the server or database error response.

#### Blocked by

- `BE-delete-task-endpoint`
- `BE-delete-task-error-handling`
- `FE-delete-confirmation-prompt`
- `FE-delete-result-feedback`

#### Definition of Done

- [ ] Tests cover cancel, confirm success and confirm error paths.
- [ ] Tests cover the task-not-found and internal or database error responses.
- [ ] Tests check that no success state is shown on error.
- [ ] All tests pass in the CI pipeline.

#### Requirements

- `R-8523b9ec` (functional) The user can delete a task.
- `R-8ef41ba1` (frontend) Deleting a task requires the user to confirm the deletion through a prompt before it is performed.
- `R-d57336f7` (frontend) A success or error message is displayed after each create, update and delete task action.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

---

## Mark a task as Completed or revert it to Open

`US-change-task-status` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user, **I want** mark a task as Completed or revert a Completed task back to Open, **so that** I can track which tasks are done on my to-do list.

### Business description

Users need to record progress on their tasks. A task moves between Open and Completed. The backend stores each change, and the task list reflects only changes the backend has confirmed.

### Business value

Users can see which work is finished and which is still open, and the stored status stays accurate.

### Acceptance criteria

1. **Given** a task with status Open exists, **When** the user marks the task as Completed, **Then** the backend stores the status Completed and the task list shows the task with status Completed
2. **Given** a task with status Completed exists, **When** the user reverts the task to Open, **Then** the backend stores the status Open and the task list shows the task with status Open
3. **Given** the status change request for an existing task fails in the backend, **When** the frontend receives the failure, **Then** the task list still shows the previous status and an error message is displayed
4. **Given** a status change request is pending and the backend has not responded yet, **When** the task list is displayed, **Then** the row still shows the previous status and no success message is displayed
5. **Given** a status change request is sent for a task ID that does not exist, **When** the backend processes the request, **Then** the backend returns a task not found error and no stored task changes
6. **Given** a status change request is sent with a status value other than Open or Completed, **When** the backend validates the request, **Then** the backend rejects the request with an invalid input error and the stored status does not change
7. **Given** a task is marked as Completed, **When** the backend saves the change, **Then** the Completion Date field of the task is populated with the time of the change

### Edge cases

- A task is marked Completed while it is already Completed, or reverted to Open while it is already Open: the PRD does not say whether this is rejected or accepted as a no-op; this is an open question.
- A task is reverted to Open: the PRD does not state whether the Completion Date is cleared or kept; this is an open question.
- The status change request fails with an internal server or database error: the stored status stays unchanged and the frontend shows an error message.
- The status change request is still pending when the user views the task list: the row keeps the previous status until the backend confirms the change.

### Dependencies

- `US-create-task`
- `US-view-task-list`

### Definition of Done

- [ ] A status change endpoint accepts only Open and Completed and stores the new status.
- [ ] Marking a task Completed populates its Completion Date with the time of the change.
- [ ] Task not found and invalid status responses are returned as specified by the error handling rules.
- [ ] The frontend shows the new status only after the backend confirms the change and never before.
- [ ] A pending status change leaves the row at its previous status.
- [ ] A failed status change leaves the previous status displayed and shows an error message.
- [ ] The QA test suite passes for all acceptance criteria.

### Tasks

- [ ] `BE-status-change-endpoint` [BE] Add status change endpoint to set a task to Completed or Open
- [ ] `BE-status-change-error-handling` [BE] Return errors for status change on missing task and invalid status
- [ ] `FE-status-toggle-control` [FE] Add Completed toggle to task list rows with backend-confirmed update
- [ ] `QA-status-change-test-suite` [QA] Add test suite for task status change endpoint and toggle

### Requirements

- `R-2304218f` (functional) The user can mark a task as 'Completed'.
- `R-959e2960` (functional) The user can revert a 'Completed' task back to 'Open'.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

### Task: [BE] Add status change endpoint to set a task to Completed or Open

`BE-status-change-endpoint` · labels: type:task, area:db, prd-agent

**Parent:** `US-change-task-status`

**Track:** backend · **Size:** S · touches DB
#### Description

Add an endpoint that sets the status of an existing task to Completed or Open. Set the Completion Date when the status becomes Completed. Store the change in the tasks table created by the create task story.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Endpoint sets status to Completed or Open and persists it.
- [ ] Completion Date is populated when the status becomes Completed.
- [ ] Endpoint returns the updated task on success.

#### Requirements

- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-2304218f` (functional) The user can mark a task as 'Completed'.
- `R-959e2960` (functional) The user can revert a 'Completed' task back to 'Open'.

### Task: [BE] Return errors for status change on missing task and invalid status

`BE-status-change-error-handling` · labels: type:task, area:backend, prd-agent

**Parent:** `US-change-task-status`

**Track:** backend · **Size:** S
#### Description

Return a task not found error when the task ID does not exist and an invalid input error when the status is not Open or Completed. Use the simple error handling approach. Leave stored data unchanged on both errors.

#### Blocked by

- `BE-status-change-endpoint`

#### Definition of Done

- [ ] Unknown task ID returns a task not found error.
- [ ] Status values other than Open or Completed return an invalid input error.
- [ ] Stored status is unchanged after either error.
- [ ] Internal and database errors return the standard error response.

#### Requirements

- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [FE] Add Completed toggle to task list rows with backend-confirmed update

`FE-status-toggle-control` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-change-task-status`

**Track:** frontend · **Size:** M · consumes API
#### Description

Add a control on each task list row that marks the task Completed or reverts it to Open. Show the row at its previous status while the request is pending. Update the row only after the backend confirms success. On failure, keep the previous status and show an error message.

#### Blocked by

- `BE-status-change-endpoint`
- `FE-task-list-view`

#### Definition of Done

- [ ] The toggle sends the status change request to the backend.
- [ ] The row keeps the previous status while the request is pending.
- [ ] The row shows the new status only after the backend confirms the change.
- [ ] A failed request keeps the previous status and shows an error message.
- [ ] No success message is shown before backend confirmation.

#### Requirements

- `R-2304218f` (functional) The user can mark a task as 'Completed'.
- `R-959e2960` (functional) The user can revert a 'Completed' task back to 'Open'.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

### Task: [QA] Add test suite for task status change endpoint and toggle

`QA-status-change-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-change-task-status`

**Track:** qa_general · **Size:** M · consumes API
#### Description

Test the status change endpoint, its error responses, the Completion Date behaviour, and the toggle behaviour, including pending and failed states.

#### Blocked by

- `BE-status-change-endpoint`
- `BE-status-change-error-handling`
- `FE-status-toggle-control`

#### Definition of Done

- [ ] Tests cover all acceptance criteria of this story.
- [ ] Tests cover task not found and invalid status responses.
- [ ] Tests confirm the row does not change before backend confirmation.
- [ ] Tests confirm the stored status is unchanged after a failed request.

#### Requirements

- `R-2304218f` (functional) The user can mark a task as 'Completed'.
- `R-959e2960` (functional) The user can revert a 'Completed' task back to 'Open'.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The frontend does not show a successful state for a task action unless the backend action has succeeded; optimistic UI updates are not allowed.

---

## View all tasks in a report table with metrics

`US-view-task-report` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user, **I want** see all of my tasks in a table on the Task Reporting page, with Total Tasks, Open Tasks and Completed Tasks metrics, **so that** I can review the status of my whole task list at a glance.

### Business description

The Task Reporting page gives the user an aggregated view of their own tasks. It shows every task in a table and three metrics computed from those tasks: Total Tasks, Open Tasks and Completed Tasks.

### Business value

The user can see how much work is open and how much is completed without opening each task.

### Acceptance criteria

1. **Given** The user has 5 tasks, 2 with status Open and 3 with status Completed, **When** The user opens the Task Reporting page, **Then** The table shows 5 rows, one per task, and the metrics show Total Tasks 5, Open Tasks 2 and Completed Tasks 3
2. **Given** The user has no tasks, **When** The user opens the Task Reporting page, **Then** The table shows no task rows and the metrics show Total Tasks 0, Open Tasks 0 and Completed Tasks 0
3. **Given** The report endpoint returns tasks with their Status, Priority and Due Date values, **When** The Task Reporting page loads, **Then** Each table row shows the task Title, Status, Priority and Due Date from the endpoint response, with no values added or changed by the page
4. **Given** A user changes the status of a task from Open to Completed, **When** The user reloads the Task Reporting page, **Then** The Open Tasks metric decreases by 1 and the Completed Tasks metric increases by 1, while Total Tasks stays the same
5. **Given** The report endpoint is called without any filter, search or sort parameters, **When** The request is processed, **Then** The response contains all of the user's tasks and the three metric values Total, Open and Completed computed from those tasks

### Edge cases

- The user has no tasks: the table is empty and all three metrics show 0.
- Metric values are computed from the same set of tasks as the table rows, so they always agree with the rows shown.
- The PRD does not state the table column order or the date display format; this is an open question for the team.

### Dependencies

- `US-create-task`
- `US-change-task-status`

### Definition of Done

- [ ] The report endpoint returns all of the user's tasks with Title, Status, Priority and Due Date.
- [ ] The report endpoint returns Total, Open and Completed counts for the user's tasks in the same response.
- [ ] The Task Reporting page renders one table row per task returned by the endpoint.
- [ ] The Task Reporting page shows Total Tasks, Open Tasks and Completed Tasks from the endpoint response.
- [ ] The page shows no task values that differ from the endpoint response.
- [ ] Automated tests for the table and metrics pass.

### Tasks

- [ ] `BE-report-endpoint-with-metrics` [BE] Add GET report endpoint with all tasks and Total, Open, Completed counts
- [ ] `FE-task-report-page-table` [FE] Build Task Reporting page with a table of all tasks
- [ ] `FE-report-metric-cards` [FE] Show Total, Open and Completed metrics on Task Reporting page
- [ ] `QA-task-report-test-suite` [QA] Add test suite for the task report table and metrics

### Requirements

- `R-d0e0fe7a` (frontend) The Task Reporting page presents an aggregated view of the user's tasks.
- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.
- `R-4ffbfafa` (frontend) The reporting page shows the metrics Total Tasks, Open Tasks, and Completed Tasks.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [BE] Add GET report endpoint with all tasks and Total, Open, Completed counts

`BE-report-endpoint-with-metrics` · labels: type:task, area:backend, prd-agent

**Parent:** `US-view-task-report`

**Track:** backend · **Size:** M · touches DB
#### Description

Add a GET report endpoint that returns all tasks of the current user with Title, Status, Priority and Due Date, plus the Total, Open and Completed counts computed from those tasks. Filtering, search and sorting are out of scope for this story.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] GET report endpoint returns all of the user's tasks when no parameters are given.
- [ ] Response includes Total, Open and Completed counts computed from the returned tasks.
- [ ] Endpoint returns a clear error response on internal or database failure.
- [ ] Unit tests cover the count calculation and the empty-task case.

#### Requirements

- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [FE] Build Task Reporting page with a table of all tasks

`FE-task-report-page-table` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-report`

**Track:** frontend · **Size:** M · consumes API
#### Description

Build the Task Reporting page that calls the report endpoint and shows every returned task as one row in a table with Title, Status, Priority and Due Date.

#### Blocked by

- `BE-report-endpoint-with-metrics`

#### Definition of Done

- [ ] Page loads data from the report endpoint.
- [ ] Table shows one row per task with Title, Status, Priority and Due Date from the response.
- [ ] Table shows an empty state when the user has no tasks.
- [ ] Page shows no values that were not returned by the endpoint.

#### Requirements

- `R-d0e0fe7a` (frontend) The Task Reporting page presents an aggregated view of the user's tasks.
- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.

### Task: [FE] Show Total, Open and Completed metrics on Task Reporting page

`FE-report-metric-cards` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-report`

**Track:** frontend · **Size:** S · consumes API
#### Description

Show the Total Tasks, Open Tasks and Completed Tasks metrics on the Task Reporting page using the counts returned by the report endpoint.

#### Blocked by

- `BE-report-endpoint-with-metrics`
- `FE-task-report-page-table`

#### Definition of Done

- [ ] Page shows Total Tasks, Open Tasks and Completed Tasks.
- [ ] Displayed values equal the counts in the endpoint response.
- [ ] Metrics show 0 when the user has no tasks.

#### Requirements

- `R-4ffbfafa` (frontend) The reporting page shows the metrics Total Tasks, Open Tasks, and Completed Tasks.

### Task: [QA] Add test suite for the task report table and metrics

`QA-task-report-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-view-task-report`

**Track:** qa_general · **Size:** S
#### Description

Add the automated test suite for the Task Reporting page table and metrics, covering the report endpoint and page behaviour.

#### Blocked by

- `BE-report-endpoint-with-metrics`
- `FE-task-report-page-table`
- `FE-report-metric-cards`

#### Definition of Done

- [ ] Tests cover 5 tasks (2 Open, 3 Completed) and 0 tasks.
- [ ] Tests check that table values match the endpoint response.
- [ ] Tests check the metric changes after a status change.
- [ ] All tests pass in the CI pipeline.

#### Requirements

- `R-d0e0fe7a` (frontend) The Task Reporting page presents an aggregated view of the user's tasks.
- `R-a1b267a3` (frontend) The reporting page displays all tasks in a table.
- `R-4ffbfafa` (frontend) The reporting page shows the metrics Total Tasks, Open Tasks, and Completed Tasks.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

---

## Filter report tasks by status, priority and date range

`US-filter-report-tasks` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user who reviews my tasks on the task reporting page, **I want** to filter the report tasks by Status, Priority and Date Range, **so that** I can see only the tasks that match the part of my workload I am reviewing.

### Business description

The reporting page offers Status, Priority and Date Range filters. The backend report API must support filtering so that the page can show only the matching tasks. Searching, sorting and metric aggregation are covered by other stories.

### Business value

Users can narrow a long task list to the subset they need to review, without scanning every task on the page.

### Acceptance criteria

1. **Given** The report contains tasks with Open, In Progress and Completed status, **When** The user selects the status filter value Open on the reporting page, **Then** The report table lists only tasks whose status is Open and no other tasks
2. **Given** The report contains tasks with Low, Medium and High priority, **When** The user selects the priority filter value High on the reporting page, **Then** The report table lists only tasks whose priority is High and no other tasks
3. **Given** The report contains tasks with dates both inside and outside a chosen range, **When** The user sets a Date Range on the reporting page, **Then** The report table lists only tasks whose date value falls inside the range; the date field used is the open question listed in the edge cases
4. **Given** The report API is called with a status, a priority or a date range filter, **When** The request is sent with one or more filter values, **Then** The response contains only the tasks that match the filter values sent, and the count in the response equals the number of returned tasks

### Edge cases

- The PRD does not state which date field the Date Range filter applies to (Creation Date, Due Date, Completion Date or Last Updated Date). This is an open question and must be decided before the date filter is built.
- The PRD does not state whether the range bounds are inclusive. This is an open question.
- The PRD does not state whether several filters combine with AND or OR. This is an open question; the API and the page must follow the same rule.
- A Date Range where the start date is later than the end date is not defined by the PRD. This is an open question: the API or the page must reject it, and the wording of the message is not specified.
- When no task matches the selected filters, the report table has no rows. The PRD does not specify the message or empty state for this case on the report page.
- A filter value outside the allowed values (Open, In Progress, Completed for status; Low, Medium, High for priority) is invalid input and must be rejected with the error handling defined in the create task story.
- Clearing a filter returns the report to the unfiltered list for that filter.

### Dependencies

- `US-create-task`
- `US-view-task-report`

### Definition of Done

- [ ] The report API accepts status, priority and date range filter parameters and returns only matching tasks.
- [ ] The API rejects invalid filter values with the standard invalid input error.
- [ ] The reporting page shows Status, Priority and Date Range filter controls that call the API and update the table.
- [ ] The date field and combination rule for the Date Range filter are documented and implemented as decided.
- [ ] Automated tests cover each filter alone, combined filters, an empty result and an invalid filter value.
- [ ] No optimistic UI is used: the table updates only after the API returns the filtered result.

### Tasks

- [ ] `BE-report-tasks-filter-api` [BE] Add status, priority and date range filters to the report tasks endpoint
- [ ] `FE-report-filter-controls` [FE] Add Status, Priority and Date Range filter controls to the report page
- [ ] `QA-report-filter-tests` [QA] Test suite for report task filters

### Requirements

- `R-5f4ef76c` (functional) The reporting page lets the user filter tasks by Status, Priority, and Date Range.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [BE] Add status, priority and date range filters to the report tasks endpoint

`BE-report-tasks-filter-api` · labels: type:task, area:backend, prd-agent

**Parent:** `US-filter-report-tasks`

**Track:** backend · **Size:** M · touches DB
#### Description

Extend the task report GET endpoint so it accepts optional status, priority and date range query parameters and returns only matching tasks. Validate values against the allowed Status and Priority values and reject invalid input. Searching, sorting and metric aggregation are implemented in other stories and are not part of this task.

#### Blocked by

- `BE-tasks-table-migration`
- `BE-report-endpoint-with-metrics`

#### Definition of Done

- [ ] Endpoint accepts status, priority and date range parameters, each optional.
- [ ] Only tasks matching all supplied filter values are returned, following the combination rule documented in the open question.
- [ ] Invalid status, priority or date values return the standard invalid input error.
- [ ] Filter queries read the stored tasks table created by the create task story.

#### Requirements

- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [FE] Add Status, Priority and Date Range filter controls to the report page

`FE-report-filter-controls` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-filter-report-tasks`

**Track:** frontend · **Size:** M · consumes API
#### Description

Add Status and Priority selectors and a Date Range control to the task reporting page. Changing a filter calls the report endpoint with the filter values and renders the returned tasks in the report table. Show the loading and error states while the request runs.

#### Blocked by

- `BE-report-tasks-filter-api`
- `FE-task-report-page-table`

#### Definition of Done

- [ ] Status, Priority and Date Range controls are visible on the reporting page.
- [ ] Each filter change calls the filtered report endpoint and updates the table only after the response arrives.
- [ ] Clearing a filter restores the unfiltered results for that filter.
- [ ] Loading and error states are shown while the filtered request runs or fails.

#### Requirements

- `R-5f4ef76c` (functional) The reporting page lets the user filter tasks by Status, Priority, and Date Range.

### Task: [QA] Test suite for report task filters

`QA-report-filter-tests` · labels: type:task, area:qa, prd-agent

**Parent:** `US-filter-report-tasks`

**Track:** qa_general · **Size:** M · consumes API
#### Description

Write the automated tests for the report filters: API tests for each filter, combined filters, empty results and invalid values, and UI tests for the filter controls and the resulting table rows.

#### Blocked by

- `BE-report-tasks-filter-api`
- `FE-report-filter-controls`

#### Definition of Done

- [ ] API tests cover status, priority and date range filters, combined filters, empty results and invalid values.
- [ ] UI tests cover selecting each filter and checking the visible table rows.
- [ ] All tests pass in the continuous integration pipeline.

#### Requirements

- `R-5f4ef76c` (functional) The reporting page lets the user filter tasks by Status, Priority, and Date Range.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

---

## Search report tasks by title

`US-search-report-tasks` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user, **I want** search my tasks by title on the reporting page, **so that** I can find a specific task in my report without scanning the full table.

### Business description

The Task Reporting page lets the user type text to search tasks by their title. The backend report API accepts a title search value and returns only the matching tasks.

### Business value

Users can locate a single task quickly in a larger report by matching its title, as required by the 'Search: By Title' reporting requirement.

### Acceptance criteria

1. **Given** the reporting page shows tasks and a title search input is visible, **When** the user enters a search text that exactly matches the title of one task and submits the search, **Then** the backend report API is called with that search text and the table shows only the task(s) whose title contains it
2. **Given** the reporting page shows tasks, **When** the user enters a search text that matches no task title, **Then** the table shows no rows and a message stating that no tasks match the search is displayed
3. **Given** a search text is entered on the reporting page, **When** the user clears the search input, **Then** the backend report API is called without a title search value and the table shows all tasks again
4. **Given** the report API is running and the database holds tasks with titles, **When** a client calls the report API with a title search parameter, **Then** the response contains only tasks whose Title matches the parameter and the response status is 200

### Edge cases

- Open question: whether the match is exact or partial (contains) is not stated in the PRD; this story assumes a partial match only if the team confirms it.
- Open question: whether the match is case-sensitive is not stated in the PRD.
- An empty search text is treated as no search; the PRD does not state this explicitly.
- Search text containing only spaces: the PRD does not state whether it is trimmed or rejected.
- Search combined with status, priority, date range, sorting or export filters: combined behaviour is owned by those stories and must be consistent with this search.
- Search text containing special characters must be treated as plain text and must not change the query result (no injection).

### Dependencies

- `US-create-task`
- `US-view-task-report`

### Definition of Done

- [ ] Report API accepts an optional title search parameter and returns only tasks whose Title matches it.
- [ ] Reporting page has a title search input that calls the API and shows the filtered table.
- [ ] Empty result state for a search with no matches is shown on the page.
- [ ] Automated tests cover exact match, partial match behaviour as decided, no match, and cleared search.
- [ ] Open questions on exact versus partial match and case sensitivity are answered and recorded in the story notes.
- [ ] Code reviewed and merged into the main branch.

### Tasks

- [ ] `BE-report-title-search-api` [BE] Add title search parameter to the task report query
- [ ] `FE-report-title-search-input` [FE] Add title search input to the task reporting page
- [ ] `QA-report-title-search-tests` [QA] Add test suite for report title search end to end

### Requirements

- `R-48e39a9d` (functional) The reporting page lets the user search tasks by title.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [BE] Add title search parameter to the task report query

`BE-report-title-search-api` · labels: type:task, area:backend, prd-agent

**Parent:** `US-search-report-tasks`

**Track:** backend · **Size:** S · touches DB
#### Description

Extend the task report API so it accepts an optional title search value and filters the returned tasks by their Title field. Other report parameters (filtering, sorting, aggregation) belong to other stories and are not implemented here.

#### Blocked by

- `BE-tasks-table-migration`
- `BE-report-endpoint-with-metrics`

#### Definition of Done

- [ ] Report API accepts an optional title search parameter.
- [ ] Query matches on the Title field of stored tasks.
- [ ] Requests without the parameter return the same results as before.
- [ ] Invalid parameter input returns the error response defined by the error handling approach.
- [ ] Unit tests cover matching, empty value and no match.

#### Requirements

- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [FE] Add title search input to the task reporting page

`FE-report-title-search-input` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-search-report-tasks`

**Track:** frontend · **Size:** S · consumes API
#### Description

Add a search input labelled By Title to the Task Reporting page. The input sends the search text to the report API and displays the returned rows in the report table.

#### Blocked by

- `BE-report-title-search-api`
- `FE-task-report-page-table`

#### Definition of Done

- [ ] Search input labelled By Title is visible on the reporting page.
- [ ] Submitting text calls the report API with the title search value.
- [ ] Clearing the input shows all tasks again.
- [ ] No-match state shows a message in the table area.
- [ ] Component tests cover submit, clear and no-match.

#### Requirements

- `R-48e39a9d` (functional) The reporting page lets the user search tasks by title.

### Task: [QA] Add test suite for report title search end to end

`QA-report-title-search-tests` · labels: type:task, area:qa, prd-agent

**Parent:** `US-search-report-tasks`

**Track:** qa_general · **Size:** S · consumes API
#### Description

Write the end-to-end and API tests that verify title search on the reporting page and in the report API.

#### Blocked by

- `BE-report-title-search-api`
- `FE-report-title-search-input`

#### Definition of Done

- [ ] Tests cover a matching search, a non-matching search and a cleared search.
- [ ] Tests run in the continuous integration pipeline and pass.
- [ ] Test data is seeded and reset for each run.

#### Requirements

- `R-48e39a9d` (functional) The reporting page lets the user search tasks by title.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

---

## Sort report tasks by creation date, due date, status or priority

`US-sort-report-tasks` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user viewing the task report, **I want** to sort the report tasks by Creation Date, Due Date, Status or Priority, **so that** I can review my tasks in the order I need.

### Business description

The Task Reporting page lets the user sort the task table by Creation Date, Due Date, Status or Priority. The report API accepts a sort field and returns tasks ordered by it.

### Business value

Users can find the most urgent or oldest tasks quickly and review the report in a consistent order.

### Acceptance criteria

1. **Given** The Task Reporting page displays at least two tasks with different Creation Dates, **When** The user selects the sort option Creation Date, **Then** The table rows are reordered so that the Creation Date values are in a single consistent order (ascending or descending, as defined by the sort control) and the sort option shown as selected is Creation Date
2. **Given** The Task Reporting page displays tasks with different Due Dates, **When** The user selects the sort option Due Date, **Then** The table rows are reordered by the Due Date field and the sort option shown as selected is Due Date
3. **Given** The Task Reporting page displays tasks with different Status values, **When** The user selects the sort option Status, **Then** The table rows are reordered by the Status field and the sort option shown as selected is Status
4. **Given** The Task Reporting page displays tasks with different Priority values, **When** The user selects the sort option Priority, **Then** The table rows are reordered by the Priority field and the sort option shown as selected is Priority
5. **Given** The report API is called with a sort field of creation_date, due_date, status or priority, **When** The request is processed by the backend, **Then** The response contains the matching tasks ordered by that field
6. **Given** The report API is called with a sort field that is not one of creation_date, due_date, status or priority, **When** The request is processed by the backend, **Then** The backend returns an invalid input error and no task data is returned

### Edge cases

- The PRD does not state the sort direction (ascending or descending) for each option or the default sort order; this is an open question for the sort control.
- The PRD does not define the order of Status values (Open, In Progress, Completed) or Priority values (Low, Medium, High) when sorting; this is an open question.
- The PRD does not define the order of tasks that share the same sort value; this is an open question.
- A sort field outside the four allowed values is rejected with an invalid input error.

### Dependencies

- `US-create-task`
- `US-view-task-report`

### Definition of Done

- [ ] The report API accepts a sort parameter with the values creation_date, due_date, status and priority.
- [ ] The report API rejects any other sort value with an invalid input error and returns no task data.
- [ ] The report table offers exactly four sort options: Creation Date, Due Date, Status and Priority.
- [ ] The selected sort option is shown in the UI and matches the sort applied to the table.
- [ ] Sort direction and the order of Status and Priority values are documented or confirmed with the product owner.

### Tasks

- [ ] `BE-report-api-sort-parameter` [BE] Add sort parameter to the task report endpoint
- [ ] `FE-report-table-sort-control` [FE] Add sort control with four options to the report table
- [ ] `QA-report-sort-test-suite` [QA] Test suite for report task sorting

### Requirements

- `R-f214002a` (functional) The reporting page lets the user sort tasks by Creation Date, Due Date, Status, or Priority.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [BE] Add sort parameter to the task report endpoint

`BE-report-api-sort-parameter` · labels: type:task, area:backend, prd-agent

**Parent:** `US-sort-report-tasks`

**Track:** backend · **Size:** M · touches DB
#### Description

Add a sort parameter to the report tasks endpoint that accepts creation_date, due_date, status or priority and returns matching tasks ordered by that field. Reject other values with an invalid input error.

#### Blocked by

- `BE-tasks-table-migration`
- `BE-report-endpoint-with-metrics`

#### Definition of Done

- [ ] Endpoint accepts sort values creation_date, due_date, status and priority.
- [ ] Response is ordered by the requested field.
- [ ] Any other sort value returns an invalid input error with no task data.
- [ ] Unit tests cover each valid value and an invalid value.

#### Requirements

- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [FE] Add sort control with four options to the report table

`FE-report-table-sort-control` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-sort-report-tasks`

**Track:** frontend · **Size:** M · consumes API
#### Description

Add a sort control to the Task Reporting page with the options Creation Date, Due Date, Status and Priority. Selecting an option calls the report API with the matching sort value and shows the selected option.

#### Blocked by

- `BE-report-api-sort-parameter`
- `FE-task-report-page-table`

#### Definition of Done

- [ ] Sort control shows exactly four options: Creation Date, Due Date, Status, Priority.
- [ ] Selecting an option reorders the table rows using the API sort parameter.
- [ ] The selected option stays visible after the table reloads.
- [ ] Error state is shown if the sort request fails.

#### Requirements

- `R-f214002a` (functional) The reporting page lets the user sort tasks by Creation Date, Due Date, Status, or Priority.

### Task: [QA] Test suite for report task sorting

`QA-report-sort-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-sort-report-tasks`

**Track:** qa_general · **Size:** S · consumes API
#### Description

Test suite covering the report sort control and the sort parameter of the report endpoint, including the invalid sort value case.

#### Blocked by

- `BE-report-api-sort-parameter`
- `FE-report-table-sort-control`

#### Definition of Done

- [ ] Tests cover sorting by each of the four fields.
- [ ] Tests cover an invalid sort value and confirm the invalid input error.
- [ ] Tests confirm the selected sort option is shown in the UI.
- [ ] Test suite runs in the CI pipeline and passes.

#### Requirements

- `R-f214002a` (functional) The reporting page lets the user sort tasks by Creation Date, Due Date, Status, or Priority.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

---

## Export the filtered report tasks to an Excel file

`US-export-report-excel` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** report user, **I want** to download the tasks currently shown in the report as an Excel file, **so that** I can use the filtered and sorted task data outside the application.

### Business description

The Task Reporting page lets the user download task data to an Excel file. The exported file must match the filters and sorting currently applied to the task view. It must have clear column headers, one consistent date format, and a filename that includes the time the file was generated. If there is no data to export, the user sees a message and no file is produced.

### Business value

Users can share and analyse the exact task view they are working with, without re-entering filters or manually copying data from the report table.

### Acceptance criteria

1. **Given** The Task Reporting page is open and at least one task is shown in the report table, **When** The user clicks the Export to Excel control, **Then** An Excel file is downloaded containing the tasks shown in the report
2. **Given** The report has Status = Open, Priority = High and a sort by Due Date ascending applied, **When** The user exports the report to Excel, **Then** The file contains only tasks with Status Open and Priority High, in Due Date ascending order, and no other tasks
3. **Given** The report is filtered so that no tasks match, **When** The user clicks the Export to Excel control, **Then** No file is downloaded and the message 'No tasks to export' is shown on the page (exact wording is an open question)
4. **Given** An Excel file is exported, **When** The file is opened, **Then** The first row contains a column header for every exported field and every date cell uses the same date format
5. **Given** A file is exported at a given time, **When** The browser saves the file, **Then** The filename contains the timestamp of the moment the export was generated
6. **Given** The team has completed the decision spike on where the Excel file is generated, **When** The export is implemented, **Then** The generation location matches the documented decision and the decision record is linked from the story

### Edge cases

- The filtered result is empty: no file is produced and the no-data message is shown.
- The report contains a single task: the file still has the header row and one data row.
- Sorting is applied with equal values in the sort column: the exported order of tied rows is not specified in the PRD (open question).
- Tasks with no Completion Date: the value shown in the exported cell is not specified in the PRD (open question).
- The exact wording of the no-data message is not specified (open question).
- The timestamp format in the filename and the time zone used for it are not specified (open question).
- The list of exported columns is not specified beyond 'task data' (open question; assumed to match the columns of the report table).
- Very large result sets: maximum export size and any limit are not specified (open question).

### Dependencies

- `US-view-task-report`
- `US-filter-report-tasks`
- `US-sort-report-tasks`

### Definition of Done

- [ ] Export control is visible on the Task Reporting page and downloads a file when clicked.
- [ ] Exported rows match the filters and sort applied to the report at the time of export, verified by automated tests.
- [ ] Column headers are present in the first row and are human-readable.
- [ ] All date cells in the file use one date format.
- [ ] Filename contains a generation timestamp and is unique for each export.
- [ ] No file is produced when the filtered result is empty, and the no-data message is shown.
- [ ] The decision on frontend or backend generation is documented with rationale and trade-offs.
- [ ] Error responses from the export endpoint are handled and shown to the user.

### Tasks

- [ ] `BE-excel-generation-location-decision` [BE] Decide and document where the Excel file is generated
- [ ] `BE-export-report-tasks-endpoint` [BE] Add export endpoint returning filtered and sorted report tasks
- [ ] `FE-export-to-excel-button` [FE] Add Export to Excel control to the report page
- [ ] `FE-excel-file-build-and-naming` [FE] Build the Excel file with headers, date format and timestamped filename
- [ ] `QA-export-excel-test-suite` [QA] Add test suite for the Excel export

### Requirements

- `R-52360b76` (functional) The reporting page lets the user download task data to an Excel file.
- `R-09e9d163` (functional) The exported Excel file must reflect the filters and sorting currently applied to the task view.
- `R-fad183b1` (non_functional) The exported Excel file must have clear column headers and use one consistent date format throughout.
- `R-d22b9b6a` (functional) The filename of the exported Excel file must include the timestamp of when the file was generated.
- `R-437992f1` (frontend) When there is no data to export, the system must show a message to the user instead of producing an empty file. The exact wording of the message is not specified and is an open question.
- `R-3a63e0ce` (decision_open) The development team decides whether the Excel file is generated on the frontend or the backend.

### Task: [BE] Decide and document where the Excel file is generated

`BE-excel-generation-location-decision` · labels: type:spike, area:backend, prd-agent

**Parent:** `US-export-report-excel`

**Track:** backend · **Size:** S
#### Description

Resolve the open decision whether the Excel file is generated on the frontend or the backend. Document the choice, rationale and trade-offs. The implementation tasks of this story follow the outcome.

#### Blocked by

- Nothing.

#### Definition of Done

- [ ] Decision record states whether generation is on the frontend or the backend.
- [ ] Decision record includes rationale and trade-offs for the chosen option.
- [ ] Decision record lists the effects on the export endpoint, the file library and the test approach.
- [ ] Decision record is linked from this story.

#### Requirements

- `R-3a63e0ce` (decision_open) The development team decides whether the Excel file is generated on the frontend or the backend.

### Task: [BE] Add export endpoint returning filtered and sorted report tasks

`BE-export-report-tasks-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-export-report-excel`

**Track:** backend · **Size:** M · touches DB
#### Description

Add an endpoint that returns the report tasks for the export using the same filter and sort parameters as the report API. The endpoint returns the rows and column values needed for the Excel file. Its exact role depends on the outcome of the generation location decision.

#### Blocked by

- `BE-tasks-table-migration`
- `BE-excel-generation-location-decision`
- `BE-report-tasks-filter-api`
- `BE-report-api-sort-parameter`

#### Definition of Done

- [ ] Endpoint accepts the same filter and sort parameters as the report task API.
- [ ] Response contains the same tasks, in the same order, as the report table for the same parameters.
- [ ] Endpoint returns an empty result when no tasks match, without an error.
- [ ] Endpoint returns a clear error response for invalid filter or sort parameters.
- [ ] Unit and API tests cover filtering, sorting and the empty result.

#### Requirements

- `R-52360b76` (functional) The reporting page lets the user download task data to an Excel file.
- `R-09e9d163` (functional) The exported Excel file must reflect the filters and sorting currently applied to the task view.

### Task: [FE] Add Export to Excel control to the report page

`FE-export-to-excel-button` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-export-report-excel`

**Track:** frontend · **Size:** S · consumes API
#### Description

Add an export control to the Task Reporting page. The control sends the currently applied filters and sort to the export endpoint, downloads the result and shows the no-data message when there is nothing to export.

#### Blocked by

- `BE-export-report-tasks-endpoint`
- `FE-task-report-page-table`

#### Definition of Done

- [ ] Export control is shown on the Task Reporting page.
- [ ] Clicking the control sends the current filter and sort values to the export endpoint.
- [ ] When the result is empty, no file is downloaded and the no-data message is shown.
- [ ] Export errors are shown to the user as an error message.

#### Requirements

- `R-52360b76` (functional) The reporting page lets the user download task data to an Excel file.
- `R-09e9d163` (functional) The exported Excel file must reflect the filters and sorting currently applied to the task view.
- `R-437992f1` (frontend) When there is no data to export, the system must show a message to the user instead of producing an empty file. The exact wording of the message is not specified and is an open question.

### Task: [FE] Build the Excel file with headers, date format and timestamped filename

`FE-excel-file-build-and-naming` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-export-report-excel`

**Track:** frontend · **Size:** M · consumes API
#### Description

Build the Excel file from the export data with clear column headers, one consistent date format for all date cells, and a filename that includes the generation timestamp. Scope may change if the decision spike places file generation on the backend.

#### Blocked by

- `BE-export-report-tasks-endpoint`
- `BE-excel-generation-location-decision`

#### Definition of Done

- [ ] First row of the file contains clear column headers for every exported field.
- [ ] All date cells use one date format, verified by tests.
- [ ] Filename includes the generation timestamp in the format agreed in the story.
- [ ] Each export produces a different filename when generated at different times.

#### Requirements

- `R-fad183b1` (non_functional) The exported Excel file must have clear column headers and use one consistent date format throughout.
- `R-d22b9b6a` (functional) The filename of the exported Excel file must include the timestamp of when the file was generated.

### Task: [QA] Add test suite for the Excel export

`QA-export-excel-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-export-report-excel`

**Track:** qa_general · **Size:** M · consumes API
#### Description

Test suite covering the export endpoint, the export control, the file content and the filename, as well as the no-data case and the filter and sort behaviour of the export.

#### Blocked by

- `BE-export-report-tasks-endpoint`
- `FE-export-to-excel-button`
- `FE-excel-file-build-and-naming`

#### Definition of Done

- [ ] Tests verify that the exported rows match the applied filters and sort.
- [ ] Tests verify headers, date format and filename timestamp in the generated file.
- [ ] Tests verify that no file is produced and the message is shown when there is no data.
- [ ] Tests verify error handling for failed export requests.
- [ ] Test suite runs in the continuous integration pipeline and passes.

#### Requirements

- Derived task: testing.
