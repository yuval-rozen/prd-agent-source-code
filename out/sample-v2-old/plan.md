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
- [ ] `US-change-task-status` Mark a task as Completed
- [ ] `US-view-task-report` View all tasks in a report table with metrics
- [ ] `US-filter-report-tasks` Filter report tasks by status, priority and date range
- [ ] `US-search-report-tasks` Search report tasks by title
- [ ] `US-sort-report-tasks` Sort report tasks by creation date, due date, status, priority or title
- [ ] `US-export-report-excel` Export the filtered report tasks to an Excel file

---

## Create a new task with required fields

`US-create-task` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user managing my to-do list, **I want** to create a new task with a title and optional details, **so that** I can record work I need to do and track it later.

### Business description

The user fills in a task creation form. The backend validates the input, stores the task in the tasks table and returns a result. The form shows a success or error message based on the backend response only.

### Business value

Users can capture tasks with validated data, and the stored data model is complete from the moment a task is created.

### Acceptance criteria

1. **Given** A user opens the task creation form and enters a non-empty title and other valid inputs, **When** The user submits the form, **Then** The backend stores exactly one new task with a unique ID and the status Open, and the form shows a success message
2. **Given** A user opens the task creation form and leaves the title empty, **When** The user submits the form, **Then** The backend rejects the task, no task is stored, and the form shows an error message that names the Title field as mandatory
3. **Given** A user enters a title of 101 characters on the task creation form, **When** The user submits the form, **Then** The backend rejects the task with an error stating that the title cannot be longer than 100 characters, no task is stored, and the form shows that error message
4. **Given** A user enters a title of exactly 100 characters and other valid inputs, **When** The user submits the form, **Then** The backend accepts the task and stores it with the full 100-character title
5. **Given** The backend sets the Creation Date of a new task to 2024-05-10, **When** The user submits a Due Date of 2024-05-09 for that task, **Then** The backend rejects the task with an error stating that the Due Date cannot be earlier than the Creation Date, and no task is stored
6. **Given** The backend sets the Creation Date of a new task to 2024-05-10, **When** The user submits a Due Date of 2024-05-10 for that task, **Then** The backend accepts the task because the Due Date is not earlier than the Creation Date
7. **Given** A create request is received with valid inputs, **When** The backend stores the new task, **Then** The backend sets the Creation Date and the Last Updated Date of the task, sets the Status to Open, and the Completion Date is empty
8. **Given** A new task has been stored, **When** The task is read from the database, **Then** The task has the fields ID, Title, Description, Status, Priority, Creation Date, Due Date, Last Updated Date and Completion Date, the Status is Open, and Completion Date is empty
9. **Given** The backend create request fails because of a database error, **When** The user submits the task creation form, **Then** The form shows an error message and does not show the task as created
10. **Given** A create request has been sent but the backend has not yet responded, **When** The form is waiting for the response, **Then** The frontend does not show a success message or add the task to any list

### Edge cases

- Updating Last Updated Date on edit and on status change is covered by the update and status change stories, not by this story.
- The PRD does not state a default Priority for a new task when the user does not choose one; this is an open question.

### Dependencies

- None.

### Definition of Done

- [ ] All acceptance criteria pass in the QA test suite
- [ ] Tasks are stored in the new tasks table
- [ ] Success and error messages are shown only after the backend response

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
- `R-03df7815` (validation_rule) A task cannot be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-c55a77b3` (backend) To-do items must be saved in the persistence database, which is assumed to already exist, in a new table created for them.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.
- `R-0b1853d6` (validation_rule) A task title longer than 100 characters is rejected.

### Task: [BE] Add migration that creates the tasks table with all task data-model fields

`BE-tasks-table-migration` · labels: type:task, area:db, prd-agent

**Parent:** `US-create-task`

**Track:** backend · **Size:** S · touches DB

#### Description

Create the new tasks table in the existing persistence database with columns for ID (unique), Title, Description, Status (Open, In Progress, Completed), Priority (Low, Medium, High), Creation Date, Due Date, Last Updated Date and Completion Date (nullable).

#### Blocked by

- Nothing.

#### Definition of Done

- [ ] Migration creates the tasks table with every data-model field listed in the PRD.
- [ ] ID is unique and Completion Date is nullable.
- [ ] Migration runs on the existing database and can be reverted.

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

Add POST /tasks. Validate that the title is non-empty and at most 100 characters, and that the Due Date is not earlier than the Creation Date. On success, store the task with a unique ID, set Status to Open, set Creation Date and Last Updated Date, leave Completion Date empty, and return the stored task. Return simple errors for missing mandatory fields, invalid input and database errors. Updating Last Updated Date on edit and status change belongs to the update and status change stories.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Empty title and title over 100 characters are rejected and nothing is stored
- [ ] Due Date earlier than Creation Date is rejected and nothing is stored
- [ ] A stored task has Status Open, Creation Date and Last Updated Date set, and empty Completion Date
- [ ] Database errors return an error response

#### Requirements

- `R-22f28530` (functional) The user can create a new task.
- `R-03df7815` (validation_rule) A task cannot be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-9675bb49` (data_model) Each task has a unique ID field.
- `R-0b1853d6` (validation_rule) A task title longer than 100 characters is rejected.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-34e41747` (data_model) Each task has a Completion Date field, populated when the task is completed.

### Task: [FE] Add task creation form with title, description, priority and due date

`FE-create-task-form` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-create-task`

**Track:** frontend · **Size:** M · consumes API

#### Description

Add the create mode of the task form with inputs for Title, Description, Priority and Due Date. The form does not collect Creation Date or Last Updated Date, because the backend sets them. The form calls POST /tasks and shows a success or error message only after the backend responds. It does not add the task to any list before the backend confirms the create.

#### Blocked by

- `BE-create-task-endpoint`

#### Definition of Done

- [ ] Form has Title, Description, Priority and Due Date inputs.
- [ ] Success message is shown only after the backend confirms the create.
- [ ] Validation errors from the backend are shown next to the relevant input or as a clear message.
- [ ] No task is shown as created while the request is pending or after it fails.

#### Requirements

- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.

### Task: [QA] Add test suite for task creation across API, database and form

`QA-create-task-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-create-task`

**Track:** qa_general · **Size:** S · consumes API · touches DB

#### Description

Automated tests for task creation covering the POST /tasks endpoint, the stored database row and the creation form.

#### Blocked by

- `BE-create-task-endpoint`
- `FE-create-task-form`
- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Tests cover a valid create, an empty title, a Due Date earlier than the Creation Date, and a Due Date equal to the Creation Date.
- [ ] Tests check that Creation Date and Last Updated Date are set by the backend and Completion Date is empty.
- [ ] Tests check that a database failure shows an error and no task is shown as created.
- [ ] Tests check that no success message is shown while the request is pending.
- [ ] All tests pass in the CI pipeline.

#### Requirements

- `R-22f28530` (functional) The user can create a new task.
- `R-03df7815` (validation_rule) A task cannot be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.

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

**As a** user managing my tasks, **I want** to edit an existing task, including its title, Due Date and Status, **so that** my task details stay current.

### Business description

Users update an existing task through the shared task form. The backend validates the input, stores the change, sets Last Updated Date, and the UI reports success or failure without showing an unconfirmed change.

### Business value

Keeps task data accurate and gives users clear feedback on every update.

### Acceptance criteria

1. **Given** an existing task with a valid title and a Due Date not earlier than its Creation Date, **When** the user opens the edit form, changes the title, and submits the form, **Then** the backend stores the new title and the task shows the new title in the list after the backend returns success
2. **Given** an existing task being edited in the form, **When** the user clears the title field and submits the form, **Then** the backend rejects the update, the task keeps its previous title, and an error message stating that the title is mandatory is shown
3. **Given** an existing task being edited in the form, **When** the user enters a title of 101 characters and submits the form, **Then** the backend rejects the update, the task keeps its previous title, and an error message stating that the title cannot be longer than 100 characters is shown
4. **Given** an existing task being edited in the form, **When** the user enters a title of exactly 100 characters and submits the form, **Then** the backend stores the new title and returns success
5. **Given** an existing task with Creation Date 2024-05-10, **When** the user sets the Due Date to 2024-05-09 and submits the update, **Then** the backend rejects the update with a validation error, the stored Due Date is unchanged, and an error message is shown
6. **Given** a task update request where the backend returns an error, **When** the frontend receives the error response, **Then** the frontend does not show the task as updated and displays an error message
7. **Given** a task update request where the backend returns success, **When** the frontend receives the success response, **Then** the frontend displays a success message after the update action
8. **Given** a task ID that does not exist in the database, **When** an update request is sent for that ID, **Then** the backend returns a Task Not Found error and no data is changed
9. **Given** an existing task with Last Updated Date 2024-05-10, **When** the backend successfully stores an update to that task, **Then** the task's Last Updated Date is set to the date and time of that update
10. **Given** an existing task being edited in the form, **When** the user selects Status In Progress (or Open) and submits the form, **Then** the backend stores the selected Status and the task shows that Status in the list after the backend returns success
11. **Given** an existing task being edited, **When** an update request sets Status to Completed, **Then** the backend rejects the update with a validation error and the stored Status is unchanged

### Edge cases

- Completed is set only by Mark as Completed (which also sets Completion Date), not by the edit form.
- Editing a task that is already Completed: it is not stated whether its Status can be changed back by the edit form. This is an open question.

### Dependencies

- None.

### Definition of Done

- [ ] All acceptance criteria pass in automated tests
- [ ] Update endpoint returns documented error responses
- [ ] Success and error messages are shown after each update
- [ ] Last Updated Date is set on every successful update

### Tasks

- [ ] `BE-task-update-endpoint` [BE] Add update endpoint for a task by ID with validation and error responses
- [ ] `FE-task-edit-form` [FE] Reuse task form in edit mode with existing values pre-filled
- [ ] `QA-task-update-tests` [QA] Test suite for editing an existing task

### Requirements

- `R-bc3213df` (functional) The user can update an existing task.
- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-03df7815` (validation_rule) A task cannot be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.
- `R-0b1853d6` (validation_rule) A task title longer than 100 characters is rejected.

### Task: [BE] Add update endpoint for a task by ID with validation and error responses

`BE-task-update-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-update-task`

**Track:** backend · **Size:** M · touches DB

#### Description

Add the update endpoint for a task by ID. Validate title (mandatory, max 100 characters) and Due Date (not earlier than Creation Date). Accept Status values Open or In Progress and reject Completed with a validation error (Completed is set only by Mark as Completed). On every successful update the backend sets Last Updated Date. Return errors for task not found, invalid input, missing mandatory fields and internal/database errors in a simple approach.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Endpoint updates the task by ID and returns success
- [ ] Title and Due Date validation reject invalid input
- [ ] Last Updated Date is set on every successful update
- [ ] Status Open or In Progress is accepted; Completed is rejected
- [ ] Not-found and server errors return error responses

#### Requirements

- `R-bc3213df` (functional) The user can update an existing task.
- `R-03df7815` (validation_rule) A task cannot be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-0b1853d6` (validation_rule) A task title longer than 100 characters is rejected.

### Task: [FE] Reuse task form in edit mode with existing values pre-filled

`FE-task-edit-form` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-update-task`

**Track:** frontend · **Size:** M · consumes API

#### Description

Reuse the task form in edit mode with existing values pre-filled, including a Status field that offers only Open and In Progress. Show a success message only after the backend confirms the update and an error message when it fails; do not update the UI optimistically.

#### Blocked by

- `BE-task-update-endpoint`
- `FE-create-task-form`

#### Definition of Done

- [ ] Form pre-fills existing values including Status
- [ ] Status field offers only Open and In Progress
- [ ] Success message shown only after backend success
- [ ] Error message shown and no updated state on backend failure

#### Requirements

- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.
- `R-bc3213df` (functional) The user can update an existing task.

### Task: [QA] Test suite for editing an existing task

`QA-task-update-tests` · labels: type:task, area:qa, prd-agent

**Parent:** `US-update-task`

**Track:** qa_general · **Size:** S · consumes API

#### Description

Test suite covering the update acceptance criteria: title validation, Due Date validation, not-found, success and error messages with no optimistic UI, Last Updated Date set on update, Status set to Open or In Progress from the edit form, and Completed rejected by the update endpoint.

#### Blocked by

- `BE-task-update-endpoint`
- `FE-task-edit-form`

#### Definition of Done

- [ ] All update acceptance criteria are covered by tests
- [ ] Last Updated Date and Status cases are tested
- [ ] Tests pass in CI

#### Requirements

- `R-bc3213df` (functional) The user can update an existing task.
- `R-9b30a145` (frontend) The system provides a form for creating and editing tasks.
- `R-03df7815` (validation_rule) A task cannot be saved unless its title is non-empty.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.

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
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.

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

- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.

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
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.

---

## Mark a task as Completed

`US-change-task-status` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user managing my to-do list, **I want** to mark a task as Completed, **so that** I can record that the work on the task is done.

### Business description

The user marks an existing task as Completed from the task list. The backend stores the status Completed and the Completion Date. The frontend shows the new status and a success message only after the backend confirms the change. Open and In Progress are set through the edit form, not through this action.

### Business value

The task list and reports reflect which tasks are done, and the user gets confirmation of each change.

### Acceptance criteria

1. **Given** a task with status Open or In Progress exists, **When** the user marks the task as Completed, **Then** the backend stores the status Completed and the task list shows the task with status Completed
2. **Given** a task with status Open or In Progress exists, **When** the user marks it as Completed and the backend returns success, **Then** a success message is displayed and the row shows the status Completed
3. **Given** the status change request for an existing task fails in the backend, **When** the frontend receives the failure, **Then** the task list still shows the previous status and an error message is displayed
4. **Given** a status change request is pending and the backend has not responded yet, **When** the task list is displayed, **Then** the row still shows the previous status and no success message is displayed
5. **Given** a status change request is sent for a task ID that does not exist, **When** the backend processes the request, **Then** the backend returns a task not found error and no stored task changes
6. **Given** a status change request is sent with a status value other than Completed, including Open or In Progress, **When** the backend validates the request, **Then** the backend rejects the request with an invalid input error and the stored status does not change
7. **Given** A task is marked as Completed, **When** the backend saves the change, **Then** the Completion Date field and the Last Updated Date field of the task are populated with the time of the change

### Edge cases

- The status endpoint accepts only Completed; Open and In Progress are set through the edit form.
- A task that is already Completed and is marked Completed again: PRD does not state the behavior; open question.
- The wording of the success and error messages is not specified. Marking a task Completed also sets its Last Updated Date.

### Dependencies

- None.

### Definition of Done

- [ ] All acceptance criteria are covered by passing tests
- [ ] Status change endpoint accepts only Completed and sets Completion Date and Last Updated Date
- [ ] Frontend shows success or error messages only after the backend responds and has no optimistic updates

### Tasks

- [ ] `BE-status-change-endpoint` [BE] Add status change endpoint that accepts only Completed
- [ ] `BE-status-change-error-handling` [BE] Return errors for status change on missing task and non-Completed value
- [ ] `FE-status-toggle-control` [FE] Add Mark as Completed control with confirmed update and success message
- [ ] `QA-status-change-test-suite` [QA] Add test suite for task status change endpoint and Completed control

### Requirements

- `R-2304218f` (functional) The user can mark a task as 'Completed'.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.
- `R-d57336f7` (frontend) The UI displays a success or error message after each create, update or delete action on a task.

### Task: [BE] Add status change endpoint that accepts only Completed

`BE-status-change-endpoint` · labels: type:task, area:db, prd-agent

**Parent:** `US-change-task-status`

**Track:** backend · **Size:** S · touches DB

#### Description

Add an endpoint that sets an existing task to Completed and populates the Completion Date and the Last Updated Date with the time of the change. The endpoint accepts only the value Completed. Open and In Progress are set through the edit form, not this endpoint.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Endpoint sets status to Completed and stores Completion Date and Last Updated Date
- [ ] Endpoint accepts no status value other than Completed
- [ ] Task in Open or In Progress can be completed

#### Requirements

- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-2304218f` (functional) The user can mark a task as 'Completed'.

### Task: [BE] Return errors for status change on missing task and non-Completed value

`BE-status-change-error-handling` · labels: type:task, area:backend, prd-agent

**Parent:** `US-change-task-status`

**Track:** backend · **Size:** S

#### Description

Return a task not found error when the task ID does not exist. Return an invalid input error for any status value other than Completed, including Open and In Progress. Stored data is unchanged in both cases.

#### Blocked by

- `BE-status-change-endpoint`

#### Definition of Done

- [ ] Unknown task ID returns a not found error
- [ ] Any value other than Completed returns an invalid input error
- [ ] Stored task is unchanged after an error

#### Requirements

- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [FE] Add Mark as Completed control with confirmed update and success message

`FE-status-toggle-control` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-change-task-status`

**Track:** frontend · **Size:** M · consumes API

#### Description

Add a Mark as Completed control on each task that is not Completed. Send the status change request and update the row to Completed only after the backend returns success. After a successful response, show a success message. On failure, keep the previous status and show an error message. While the request is pending, show the previous status and no success message. No optimistic updates.

#### Blocked by

- `BE-status-change-endpoint`
- `FE-task-list-view`

#### Definition of Done

- [ ] Row shows Completed and a success message only after the backend confirms
- [ ] Failure keeps the previous status and shows an error message
- [ ] Pending request shows the previous status and no success message
- [ ] No optimistic UI update

#### Requirements

- `R-2304218f` (functional) The user can mark a task as 'Completed'.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.

### Task: [QA] Add test suite for task status change endpoint and Completed control

`QA-status-change-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-change-task-status`

**Track:** qa_general · **Size:** M · consumes API

#### Description

Test the status change endpoint and the Mark as Completed control: Completed accepted and Completion Date and Last Updated Date set, non-Completed values rejected, unknown ID returns not found, success message shown after a successful change, error message and unchanged status on failure, previous status and no success message while pending.

#### Blocked by

- `BE-status-change-endpoint`
- `BE-status-change-error-handling`
- `FE-status-toggle-control`

#### Definition of Done

- [ ] Test asserts a success message is shown after a successful Mark as Completed
- [ ] Test asserts no success message on failure or while pending
- [ ] Endpoint tests cover Completed with Completion Date and Last Updated Date set, invalid value and not-found cases

#### Requirements

- `R-2304218f` (functional) The user can mark a task as 'Completed'.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of to-do items.
- `R-9dc414dc` (backend) The backend must handle errors for task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action whose Backend request has failed; optimistic UI updates are not allowed.

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
- `R-a1b267a3` (frontend) The report shows all tasks in a tabular display.
- `R-4ffbfafa` (frontend) The report displays the metrics Total Tasks, Open Tasks, and Completed Tasks.
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
- `R-a1b267a3` (frontend) The report shows all tasks in a tabular display.

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

- `R-4ffbfafa` (frontend) The report displays the metrics Total Tasks, Open Tasks, and Completed Tasks.

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
- `R-a1b267a3` (frontend) The report shows all tasks in a tabular display.
- `R-4ffbfafa` (frontend) The report displays the metrics Total Tasks, Open Tasks, and Completed Tasks.
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

- `R-5f4ef76c` (functional) The report lets the user filter tasks by Status, Priority, and Date Range.
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

- `R-5f4ef76c` (functional) The report lets the user filter tasks by Status, Priority, and Date Range.

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

- `R-5f4ef76c` (functional) The report lets the user filter tasks by Status, Priority, and Date Range.
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

- `R-48e39a9d` (functional) The report lets the user search tasks by title.
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

- `R-48e39a9d` (functional) The report lets the user search tasks by title.

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

- `R-48e39a9d` (functional) The report lets the user search tasks by title.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

---

## Sort report tasks by creation date, due date, status, priority or title

`US-sort-report-tasks` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-system`

### User story

**As a** user of the Task Reporting page, **I want** to sort the report tasks by Creation Date, Due Date, Status, Priority or Title, **so that** I can view the tasks in the order that matters to me.

### Business description

The Task Reporting page lets the user sort the listed tasks by one of five fields. Each field has a fixed ascending order. The backend report API supports the same five sort fields.

### Business value

Users find and review tasks faster in reports, and the report API serves sorted data to the UI.

### Acceptance criteria

1. **Given** The Task Reporting page displays at least two tasks with different Creation Dates, **When** The user selects the sort option Creation Date, **Then** The table rows are ordered ascending by Creation Date (oldest first) and the sort option shown as selected is Creation Date
2. **Given** The Task Reporting page displays at least two tasks with different Due Dates, **When** The user selects the sort option Due Date, **Then** The table rows are ordered ascending by Due Date (earliest first) and the sort option shown as selected is Due Date
3. **Given** The Task Reporting page displays tasks with the Status values Open, In Progress and Completed, **When** The user selects the sort option Status, **Then** The table rows are ordered Open first, then In Progress, then Completed, and the sort option shown as selected is Status
4. **Given** The Task Reporting page displays tasks with the Priority values Low, Medium and High, **When** The user selects the sort option Priority, **Then** The table rows are ordered Low first, then Medium, then High, and the sort option shown as selected is Priority
5. **Given** The Task Reporting page displays at least two tasks with different Titles, **When** The user selects the sort option Title, **Then** The table rows are ordered ascending alphabetically by Title (A to Z, ignoring letter case) and the sort option shown as selected is Title
6. **Given** The report API is called with a sort field of creation_date, due_date, status, priority or title, **When** The request is processed by the backend, **Then** The response contains the matching tasks in the ascending order defined for that field: oldest Creation Date first, earliest Due Date first, Open then In Progress then Completed, Low then Medium then High, Title A to Z
7. **Given** The report API is called with a sort field that is not one of creation_date, due_date, status, priority or title, **When** The request is processed by the backend, **Then** The backend returns an invalid input error and no task data is returned

### Edge cases

- The PRD does not state a sort direction; ascending is used for every field and a direction control is not part of this story. Reviewer to confirm.
- Tasks without a Due Date: the PRD does not say where they appear when sorting by Due Date. Open question.
- Tasks with equal values in the sort field: the PRD does not define a secondary order. Open question.
- Status values are Open, In Progress and Completed. Completed is set only by Mark as Completed.

### Dependencies

- None.

### Definition of Done

- [ ] All five sort options reorder the table in the defined ascending order
- [ ] The report API accepts the five sort fields and rejects any other value with an invalid input error
- [ ] Automated tests cover every sort field and the invalid sort value

### Tasks

- [ ] `BE-report-api-sort-parameter` [BE] Add sort parameter to the task report endpoint
- [ ] `FE-report-table-sort-control` [FE] Add sort control with five options to the report table
- [ ] `QA-report-sort-test-suite` [QA] Test suite for report task sorting

### Requirements

- `R-d482bfea` (functional) The report lets the user sort tasks by Creation Date, Due Date, Status, Priority, or Title.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [BE] Add sort parameter to the task report endpoint

`BE-report-api-sort-parameter` · labels: type:task, area:backend, prd-agent

**Parent:** `US-sort-report-tasks`

**Track:** backend · **Size:** M · touches DB

#### Description

Add a sort parameter to the task report endpoint accepting creation_date, due_date, status, priority or title. Order ascending: creation_date oldest first, due_date earliest first, status Open then In Progress then Completed, priority Low then Medium then High, title A to Z ignoring letter case. Any other value returns an invalid input error and no task data.

#### Blocked by

- `BE-tasks-table-migration`
- `BE-report-endpoint-with-metrics`

#### Definition of Done

- [ ] All five sort values return tasks in the defined ascending order
- [ ] Status and Priority use the explicit rank order, not alphabetical order
- [ ] An unsupported sort value returns an invalid input error with no task data
- [ ] Unit tests cover each sort value and the invalid value

#### Requirements

- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [FE] Add sort control with five options to the report table

`FE-report-table-sort-control` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-sort-report-tasks`

**Track:** frontend · **Size:** M · consumes API

#### Description

Add a sort control with the options Creation Date, Due Date, Status, Priority and Title. Selecting an option requests the report with the matching sort field (creation_date, due_date, status, priority, title) and shows the rows in ascending order: oldest Creation Date first, earliest Due Date first, Open then In Progress then Completed, Low then Medium then High, Title A to Z. The selected option is shown as selected.

#### Blocked by

- `BE-report-api-sort-parameter`
- `FE-task-report-page-table`

#### Definition of Done

- [ ] Control lists exactly the five options
- [ ] Each option sends the matching sort field and renders rows in the defined order
- [ ] The selected option is shown as selected

#### Requirements

- `R-d482bfea` (functional) The report lets the user sort tasks by Creation Date, Due Date, Status, Priority, or Title.

### Task: [QA] Test suite for report task sorting

`QA-report-sort-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-sort-report-tasks`

**Track:** qa_general · **Size:** S · consumes API

#### Description

Test sorting through the UI and the API. For each of the five fields, verify the ascending order: oldest Creation Date first, earliest Due Date first, Open then In Progress then Completed, Low then Medium then High, Title A to Z ignoring case. Verify that an unsupported sort value returns an invalid input error with no task data.

#### Blocked by

- `BE-report-api-sort-parameter`
- `FE-report-table-sort-control`

#### Definition of Done

- [ ] Each of the five sort fields is verified in the UI and in the API
- [ ] Status and Priority rank orders are verified with all three values present
- [ ] The invalid sort value case is verified

#### Requirements

- `R-d482bfea` (functional) The report lets the user sort tasks by Creation Date, Due Date, Status, Priority, or Title.
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

- `R-52360b76` (functional) The report lets the user download its data to an Excel file.
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

- `R-52360b76` (functional) The report lets the user download its data to an Excel file.
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

- `R-52360b76` (functional) The report lets the user download its data to an Excel file.
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
