# Personal task management and status reporting

`EPIC-personal-task-management-and-status` · labels: type:epic, prd-agent

## Scope

A personal task management system where a user manages a personal task list on a To-Do page and views an aggregated, filterable task report with metrics and Excel export on a Task Reporting page. The backend stores tasks in a new table in the existing persistence database.

## Business goals

- Let a user track daily tasks
- Generate status reports from the user's tasks

## User stories

- [ ] `US-create-task` Create a new task with its required fields
- [ ] `US-view-task-list` View all my tasks in a task list
- [ ] `US-update-task` Update an existing task's details
- [ ] `US-delete-task` Delete a task after confirming the deletion
- [ ] `US-change-task-status` Change the status of a task to Completed
- [ ] `US-view-task-report` View all tasks and totals in a report table
- [ ] `US-filter-search-sort-report` Filter, search and sort tasks in the report
- [ ] `US-export-report-excel` Download the filtered task report as an Excel file

## Requirements

- `R-a62b5beb` (context_only) The system is a personal task management system for tracking daily tasks and generating status reports.
- `R-f7f96b9a` (context_only) The system is composed of two main pages.
- `R-eed06908` (functional) The to-do management page lets the user manage their personal task list.
- `R-d0e0fe7a` (frontend) The Task Reporting page presents an aggregated view of the user's tasks.

---

## Create a new task with its required fields

`US-create-task` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-and-status`

### User story

**As a** user managing my to-do list, **I want** to create a new task with a title, description, status, priority and due date, **so that** I can record work I need to do and track it.

### Business description

Users can create a task through a form. The system stores the task with a unique ID, a mandatory title of at most 100 characters, a description, a Status, a Priority, a Due Date, and system-set Creation and Last Updated dates. The user sees a success or error message after the create action.

### Business value

Users can capture work items in one place, and the stored data stays consistent because required fields are validated.

### Acceptance criteria

1. **Given** A user is on the task creation form and enters a non-empty title, **When** The user submits the form, **Then** The task is saved, a unique ID is assigned, and a success message is shown
2. **Given** A user is on the task creation form and leaves the title empty, **When** The user submits the form, **Then** The task is not saved, the title is reported as mandatory, and no success message is shown
3. **Given** A user enters a title longer than 100 characters, **When** The user submits the form, **Then** The task is not saved, an error message states that the title cannot exceed 100 characters, and no success message is shown
4. **Given** A user enters a title of exactly 100 characters, **When** The user submits the form, **Then** The task is saved and a success message is shown
5. **Given** A user enters a Due Date earlier than the Creation Date, **When** The user submits the form, **Then** The task is rejected, an error message is shown, and no task is saved
6. **Given** The backend create request fails because of a server or database error, **When** The frontend receives the failure, **Then** The frontend shows an error message and does not show the task as saved
7. **Given** A task is created with a Status of Open, In Progress or Completed, and a Priority of Low, Medium or High, **When** The task is saved, **Then** The stored Status and Priority values are one of the allowed values
8. **Given** A task is created, **When** The task is saved, **Then** Its Completion Date is empty until the task is completed
9. **Given** A task is created, **When** The backend saves the task, **Then** The backend sets both the Creation Date and the Last Updated Date, and the user does not enter either value

### Edge cases

- A title of exactly 100 characters is accepted; a title of 101 characters is rejected.
- It is not specified whether a title made only of spaces counts as empty.
- The wording of the error messages is not specified.
- The frontend must not show the task as saved before the backend confirms the create action.
- The PRD does not state whether Description and Due Date are required when creating a task.

### Dependencies

- None.

### Definition of Done

- [ ] All acceptance criteria are verified by automated tests.
- [ ] Empty titles, titles over 100 characters and Due Dates earlier than the Creation Date are rejected and nothing is saved.
- [ ] Success and error messages are shown only after the backend responds.

### Tasks

- [ ] `BE-tasks-table-migration` [BE] Create tasks table with all required fields in the persistence database
- [ ] `BE-create-task-endpoint` [BE] Add POST /tasks endpoint with title and due date validation
- [ ] `FE-task-creation-form` [FE] Build task creation form with success and error messages
- [ ] `QA-create-task-test-suite` [QA] Create test suite for task creation

### Requirements

- `R-22f28530` (functional) The system lets a user create a new task.
- `R-9675bb49` (data_model) Each task has a unique ID field.
- `R-aaf23206` (data_model) Each task has a Title field.
- `R-c9046f7a` (data_model) Each task has a Description field.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-9fb58566` (data_model) Each task has a Priority field whose allowed values are Low, Medium and High.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-71bdd372` (data_model) Each task has a Due Date field.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-34e41747` (data_model) Each task has a Completion Date field, populated when the task is completed.
- `R-03df7815` (validation_rule) A task title is required and an empty title must be rejected on task creation or update.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-9b30a145` (frontend) The system provides a form to create a new task and to edit an existing task.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-c55a77b3` (backend) Todo items must be saved in the persistence database in a new table, assuming the database already exists.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.
- `R-0b1853d6` (validation_rule) A task title must not exceed 100 characters.

### Task: [BE] Create tasks table with all required fields in the persistence database

`BE-tasks-table-migration` · labels: type:task, area:db, prd-agent

**Parent:** `US-create-task`

**Track:** backend · **Size:** S · touches DB

#### Description

Add a migration that creates a new tasks table in the existing persistence database with columns for unique ID, Title, Description, Status (Open, In Progress, Completed), Priority (Low, Medium, High), Creation Date, Due Date, Last Updated Date and Completion Date.

#### Blocked by

- Nothing.

#### Definition of Done

- [ ] Migration creates the tasks table with every required field and the allowed values for Status and Priority.
- [ ] The ID column is unique and assigned by the database.
- [ ] Migration runs on the existing database without changing other tables.
- [ ] Migration can be rolled back.

#### Requirements

- `R-9675bb49` (data_model) Each task has a unique ID field.
- `R-aaf23206` (data_model) Each task has a Title field.
- `R-c9046f7a` (data_model) Each task has a Description field.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.
- `R-9fb58566` (data_model) Each task has a Priority field whose allowed values are Low, Medium and High.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-71bdd372` (data_model) Each task has a Due Date field.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-34e41747` (data_model) Each task has a Completion Date field, populated when the task is completed.
- `R-c55a77b3` (backend) Todo items must be saved in the persistence database in a new table, assuming the database already exists.

### Task: [BE] Add POST /tasks endpoint with title and due date validation

`BE-create-task-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-create-task`

**Track:** backend · **Size:** M · touches DB

#### Description

Add the POST /tasks endpoint that creates a task and stores it in the tasks table. The system sets the unique ID, Creation Date and Last Updated Date. Reject a request with an empty title, a title longer than 100 characters, or a Due Date earlier than the Creation Date. Return a simple error response for invalid input, missing mandatory fields and internal server or database errors, and save nothing when validation fails.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] POST /tasks creates a task and returns its unique ID.
- [ ] An empty title is rejected with an error and nothing is saved.
- [ ] A title of 101 or more characters is rejected with an error and nothing is saved.
- [ ] A title of exactly 100 characters is accepted.
- [ ] A Due Date earlier than the Creation Date is rejected and nothing is saved.
- [ ] Server and database errors return an error response.
- [ ] On create, the backend sets both the Creation Date and the Last Updated Date and ignores any values sent for them.

#### Requirements

- `R-22f28530` (functional) The system lets a user create a new task.
- `R-03df7815` (validation_rule) A task title is required and an empty title must be rejected on task creation or update.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-1c2262bc` (data_model) Each task has a Creation Date field.
- `R-31569dba` (data_model) Each task has a Last Updated Date field.
- `R-0b1853d6` (validation_rule) A task title must not exceed 100 characters.

### Task: [FE] Build task creation form with success and error messages

`FE-task-creation-form` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-create-task`

**Track:** frontend · **Size:** M · consumes API

#### Description

Build the form to create a task with Title, Description, Status, Priority and Due Date fields. Show the mandatory title message, the Due Date error and a success or error message after each submit. Do not show the task as saved until the backend confirms the save.

#### Blocked by

- `BE-create-task-endpoint`

#### Definition of Done

- [ ] The form contains Title, Description, Status, Priority and Due Date fields.
- [ ] An empty title is reported as mandatory and no request is sent.
- [ ] A success message is shown only after the backend confirms the save.
- [ ] An error message is shown when the backend rejects or fails the request, and the task is not shown as saved.
- [ ] The form does not show a Creation Date or Completion Date input.

#### Requirements

- `R-22f28530` (functional) The system lets a user create a new task.
- `R-9b30a145` (frontend) The system provides a form to create a new task and to edit an existing task.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-03df7815` (validation_rule) A task title is required and an empty title must be rejected on task creation or update.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.

### Task: [QA] Create test suite for task creation

`QA-create-task-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-create-task`

**Track:** qa_general · **Size:** S · consumes API

#### Description

Create the automated test suite for creating a task, covering the endpoint and the form behaviour for the required fields and validation rules.

#### Blocked by

- `BE-create-task-endpoint`
- `FE-task-creation-form`

#### Definition of Done

- [ ] Tests cover a valid create, an empty title, a Due Date earlier than the Creation Date, a server or database failure, and invalid Status or Priority values.
- [ ] Tests confirm the Creation Date and Last Updated Date are set and the Completion Date is empty on create.
- [ ] Tests confirm the form does not show success when the backend call fails.
- [ ] The test suite runs in the continuous integration pipeline and passes.

#### Requirements

- `R-22f28530` (functional) The system lets a user create a new task.
- `R-03df7815` (validation_rule) A task title is required and an empty title must be rejected on task creation or update.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

---

## View all my tasks in a task list

`US-view-task-list` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-and-status`

### User story

**As a** user, **I want** to view all my saved tasks in a task list on the to-do management page, **so that** I can see every task with its status and priority in one place.

### Business description

The to-do management page shows the task list. The system has a single user and no sign-in, so the list shows all stored tasks. Each task appears as one row with a status indicator and a priority indicator. The list shows a loading state, an empty state and an error state, and it refreshes automatically when a task is created, updated, deleted or has its status changed.

### Business value

The user can see all tasks, their status and their priority without opening each task, and the list stays current after changes.

### Acceptance criteria

1. **Given** I have two or more saved tasks, **When** I open the to-do management page, **Then** the task list shows every saved task, with one row per task
2. **Given** A task has the status Open and the priority High, **When** the task list is displayed, **Then** that task's row shows a status indicator with the value Open and a priority indicator with the value High
3. **Given** The task list is waiting for the task data from the backend, **When** the page is displayed, **Then** a loading state is shown in place of the task list until the data arrives
4. **Given** I have no saved tasks, **When** the task list loads successfully, **Then** an empty state is shown and no task rows are displayed
5. **Given** The backend returns an error when the task list is requested, **When** the task list loads, **Then** an error state is shown, no task rows are displayed, and the page does not show a successful state
6. **Given** The database is unavailable, **When** the backend receives a request for all tasks, **Then** the backend returns an internal server error response and does not return any task data
7. **Given** A saved task with a known ID exists, **When** the backend receives a request for that task by its ID, **Then** the backend returns that one task with its stored values
8. **Given** No saved task has the requested ID, **When** the backend receives a request for that task by its ID, **Then** the backend returns a not-found error and does not return any task data
9. **Given** I am viewing the task list, **When** a task is created, updated, deleted or has its status changed, **Then** the task list refreshes automatically and shows the change without a manual page reload
10. **Given** A create, update or delete action on a task has failed in the backend, **When** the task list is refreshed, **Then** the list shows only the data the backend returns and does not show the failed change as saved

### Edge cases

- A single saved task is shown as one row in the list.
- A task with the status In Progress or the priority Low or Medium is shown with the stored value in its indicator.
- There is no sign-in and no per-user filtering, so the list shows all stored tasks.
- The order of the rows in the list is not specified in the requirements.
- It is not specified what the list shows while a second refresh is still loading after a change.
- The success or error messages after create, update and delete actions are shown by the stories for those actions, not by the task list.

### Dependencies

- `US-create-task`
- `US-update-task`
- `US-delete-task`
- `US-change-task-status`

### Definition of Done

- [ ] GET /tasks returns every stored task with its stored values.
- [ ] GET /tasks returns an internal server error and no task data when the database is unavailable.
- [ ] GET /tasks/{id} returns one task with its stored values when the ID exists.
- [ ] GET /tasks/{id} returns a not-found error and no task data when the ID does not exist.
- [ ] The task list shows one row per task with a status indicator and a priority indicator.
- [ ] The loading, empty and error states are shown as specified and tested.
- [ ] The task list refreshes after a task is created, updated, deleted or has its status changed, without a page reload.
- [ ] The task list displays only data returned by the backend and does not use optimistic updates.
- [ ] The task list test suite passes.

### Tasks

- [ ] `BE-tasks-list-endpoint` [BE] Add GET /tasks endpoint that returns all saved tasks
- [ ] `BE-task-by-id-endpoint` [BE] Add GET /tasks/{id} endpoint returning one task or not-found error
- [ ] `FE-task-list-view` [FE] Build the task list view on the to-do management page
- [ ] `FE-task-list-states` [FE] Show loading, empty and error states in the task list
- [ ] `FE-task-list-auto-refresh` [FE] Refresh the task list automatically after task changes
- [ ] `QA-task-list-test-suite` [QA] Write the test suite for the task list

### Requirements

- `R-eed06908` (functional) The to-do management page lets the user manage their personal task list.
- `R-4bed9064` (functional) The system lets a user view the task list.
- `R-60e02b8e` (frontend) The system provides a task list view that displays the user's tasks.
- `R-48c89e9e` (frontend) The system shows a status indicator and a priority indicator for each task.
- `R-d7e6667f` (frontend) The task list view shows a loading state, an empty state and an error state.
- `R-6a73fa71` (frontend) The task list refreshes automatically when a task is changed.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.

### Task: [BE] Add GET /tasks endpoint that returns all saved tasks

`BE-tasks-list-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-view-task-list`

**Track:** backend · **Size:** S · touches DB

#### Description

Add a GET /tasks endpoint that reads all saved tasks from the tasks table and returns them with their stored values. If the database is unavailable, return an internal server error response with no task data.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] GET /tasks returns every stored task with its stored values.
- [ ] GET /tasks returns an internal server error and no task data when the database is unavailable.
- [ ] Endpoint is covered by unit tests.

#### Requirements

- `R-4bed9064` (functional) The system lets a user view the task list.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [BE] Add GET /tasks/{id} endpoint returning one task or not-found error

`BE-task-by-id-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-view-task-list`

**Track:** backend · **Size:** S · touches DB

#### Description

Add a GET /tasks/{id} endpoint that returns one saved task with its stored values. If no task has the requested ID, return a not-found error with no task data.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] GET /tasks/{id} returns one task with its stored values when the ID exists.
- [ ] GET /tasks/{id} returns a not-found error and no task data when the ID does not exist.
- [ ] Endpoint is covered by unit tests.

#### Requirements

- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [FE] Build the task list view on the to-do management page

`FE-task-list-view` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-list`

**Track:** frontend · **Size:** M · consumes API

#### Description

Build the task list view on the to-do management page. Show one row per task from GET /tasks, with a status indicator and a priority indicator in each row.

#### Blocked by

- `BE-tasks-list-endpoint`

#### Definition of Done

- [ ] The to-do management page shows the task list with one row per task.
- [ ] Each row shows a status indicator and a priority indicator with the stored values.
- [ ] The list shows all stored tasks.

#### Requirements

- `R-eed06908` (functional) The to-do management page lets the user manage their personal task list.
- `R-60e02b8e` (frontend) The system provides a task list view that displays the user's tasks.
- `R-48c89e9e` (frontend) The system shows a status indicator and a priority indicator for each task.

### Task: [FE] Show loading, empty and error states in the task list

`FE-task-list-states` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-list`

**Track:** frontend · **Size:** S · consumes API

#### Description

Show a loading state while the task data is being fetched, an empty state when there are no saved tasks, and an error state when the request fails. The error state shows no task rows and no success state.

#### Blocked by

- `BE-tasks-list-endpoint`

#### Definition of Done

- [ ] The loading state replaces the list until the data arrives.
- [ ] The empty state is shown with no task rows when the list loads successfully with no tasks.
- [ ] The error state is shown with no task rows and no success state when the list request fails.

#### Requirements

- `R-d7e6667f` (frontend) The task list view shows a loading state, an empty state and an error state.

### Task: [FE] Refresh the task list automatically after task changes

`FE-task-list-auto-refresh` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-list`

**Track:** frontend · **Size:** S · consumes API

#### Description

Refresh the task list from the backend after a task is created, updated, deleted or has its status changed, so the change is visible without a page reload.

#### Blocked by

- `BE-tasks-list-endpoint`
- `FE-task-list-view`

#### Definition of Done

- [ ] The list refreshes after a task is created, updated, deleted or has its status changed.
- [ ] The change is visible without a manual page reload.
- [ ] The list shows only data returned by the backend.

#### Requirements

- `R-6a73fa71` (frontend) The task list refreshes automatically when a task is changed.

### Task: [QA] Write the test suite for the task list

`QA-task-list-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-view-task-list`

**Track:** qa_general · **Size:** M · consumes API

#### Description

Write the test suite for the task list covering the list display, the status and priority indicators, the loading, empty and error states, the backend read endpoints and the automatic refresh.

#### Blocked by

- `BE-tasks-list-endpoint`
- `FE-task-list-view`
- `FE-task-list-states`
- `FE-task-list-auto-refresh`

#### Definition of Done

- [ ] Tests cover every acceptance criterion of the task list story.
- [ ] Tests cover the list, the indicators, the loading, empty and error states, and the automatic refresh.
- [ ] The test suite passes in the continuous integration pipeline.

#### Requirements

- `R-eed06908` (functional) The to-do management page lets the user manage their personal task list.
- `R-4bed9064` (functional) The system lets a user view the task list.
- `R-60e02b8e` (frontend) The system provides a task list view that displays the user's tasks.
- `R-48c89e9e` (frontend) The system shows a status indicator and a priority indicator for each task.
- `R-d7e6667f` (frontend) The task list view shows a loading state, an empty state and an error state.
- `R-6a73fa71` (frontend) The task list refreshes automatically when a task is changed.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.

---

## Update an existing task's details

`US-update-task` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-and-status`

### User story

**As a** user managing my to-do list, **I want** to update the details of an existing task, **so that** the task reflects current information.

### Business description

A user opens an existing task in the shared task form, changes its details and saves. The backend validates the change, and the user sees the outcome as a success or error message.

### Business value

Users can keep their tasks accurate without deleting and recreating them.

### Acceptance criteria

1. **Given** An existing task is open in the edit form, **When** The user changes the title to a non-empty value of 100 characters or fewer and clicks save, **Then** The backend stores the new title, the saved title is shown in the task list, and a success message is displayed
2. **Given** An existing task is open in the edit form, **When** The user clears the title field and clicks save, **Then** The task is not saved, the form shows a message that the title is required, and the stored title is unchanged
3. **Given** An existing task is open in the edit form, **When** The user enters a title of 101 characters and clicks save, **Then** The task is not saved, the form shows a message that the title cannot be longer than 100 characters, and the stored title is unchanged
4. **Given** An update request with a title of 101 characters, **When** The backend receives the request, **Then** The backend rejects the request with an invalid input error and stores no changes
5. **Given** An existing task with a creation date of 1 March, **When** The user sets the due date to 28 February and clicks save, **Then** The task is not saved, the form shows a message that the due date cannot be earlier than the creation date, and the stored due date is unchanged
6. **Given** An existing task is open in the edit form and the backend returns an error for the save request, **When** The user clicks save, **Then** The stored task keeps its previous values, an error message is displayed, and no success message is displayed
7. **Given** A task that no longer exists is open in the edit form, **When** The user saves changes to it, **Then** The backend responds with a task not found error, the form shows an error message, and no success message is displayed
8. **Given** A save request that sends a field value the backend does not accept, **When** The backend receives the request, **Then** The backend rejects the request with an invalid input error, stores no changes, and returns the error to the frontend
9. **Given** An update request that omits the title, **When** The backend receives the request, **Then** The backend rejects the request with a missing mandatory field error and stores no changes
10. **Given** A save request that fails because of an internal server or database error, **When** The backend returns the error, **Then** The backend stores no partial changes and the frontend shows an error message
11. **Given** A task with stored values exists, **When** The user opens it for editing, **Then** The edit form shows the stored values of that task
12. **Given** The request to load a task by ID fails, for example because the task does not exist or the server returns an error, **When** The user opens the task for editing, **Then** An error message is shown, the edit form does not open, and no success message is displayed
13. **Given** A task list row for an existing task and a save of that task has failed, **When** The task list is shown after the failed save, **Then** The task list shows the previous values of the task, not the values the user tried to save
14. **Given** A task list row for an existing task, **When** The user selects the edit action on that row, **Then** The edit form opens with the stored values of that task
15. **Given** An existing task is open in the edit form with a stored Last Updated Date, **When** The user changes valid details and clicks save and the backend confirms the save, **Then** The backend sets the task's Last Updated Date to the time of the save and leaves its Creation Date unchanged
16. **Given** An existing task is open in the edit form with a stored Last Updated Date and the save is rejected or fails, **When** The user clicks save, **Then** The stored Last Updated Date is unchanged

### Edge cases

- A title of exactly 100 characters is accepted; a title of 101 characters is rejected.
- The PRD does not specify whether spaces count toward the 100-character limit.
- The wording of the success and error messages is not specified.

### Dependencies

- None.

### Definition of Done

- [ ] All acceptance criteria pass in the test suite
- [ ] Update failures leave stored values unchanged
- [ ] No success message appears before the backend confirms the save
- [ ] Last Updated Date is set on every successful save and unchanged when a save fails

### Tasks

- [ ] `BE-put-task-endpoint-with-validation` [BE] Add PUT /tasks/{id} endpoint that saves edited task fields with validation
- [ ] `BE-put-task-error-responses` [BE] Return not found, invalid input and internal errors from PUT /tasks/{id}
- [ ] `FE-task-edit-form-prefill` [FE] Pre-fill the shared task form with stored values when editing a task
- [ ] `FE-task-update-result-messages` [FE] Show update result messages and keep shown values until save succeeds
- [ ] `FE-task-row-edit-action` [FE] Add edit action to each task row that opens the edit form
- [ ] `QA-task-update-test-suite` [QA] Test suite for updating an existing task

### Requirements

- `R-bc3213df` (functional) The system lets a user update an existing task.
- `R-9b30a145` (frontend) The system provides a form to create a new task and to edit an existing task.
- `R-03df7815` (validation_rule) A task title is required and an empty title must be rejected on task creation or update.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.
- `R-0b1853d6` (validation_rule) A task title must not exceed 100 characters.

### Task: [BE] Add PUT /tasks/{id} endpoint that saves edited task fields with validation

`BE-put-task-endpoint-with-validation` · labels: type:task, area:backend, prd-agent

**Parent:** `US-update-task`

**Track:** backend · **Size:** M · touches DB

#### Description

Add a PUT /tasks/{id} endpoint that saves edited task fields. It sets the Last Updated Date to the time of the save on every successful save and does not change the Creation Date. It rejects an empty title, a due date earlier than the creation date, and a title longer than 100 characters, and stores no changes when it rejects a request.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] PUT /tasks/{id} stores valid edits
- [ ] An empty title is rejected
- [ ] A due date earlier than the creation date is rejected
- [ ] A title of 101 characters is rejected with an invalid input error and nothing is stored
- [ ] A title of exactly 100 characters is accepted
- [ ] Every successful save sets Last Updated Date to the time of the save and leaves Creation Date unchanged
- [ ] A rejected save leaves Last Updated Date unchanged

#### Requirements

- `R-bc3213df` (functional) The system lets a user update an existing task.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-03df7815` (validation_rule) A task title is required and an empty title must be rejected on task creation or update.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-0b1853d6` (validation_rule) A task title must not exceed 100 characters.

### Task: [BE] Return not found, invalid input and internal errors from PUT /tasks/{id}

`BE-put-task-error-responses` · labels: type:task, area:backend, prd-agent

**Parent:** `US-update-task`

**Track:** backend · **Size:** S · touches DB

#### Description

Make PUT /tasks/{id} return a not found error when the task does not exist, an invalid input error when a submitted field value is not accepted, and an error response for internal server or database failures. A failed save must leave no partial changes in the database.

#### Blocked by

- `BE-put-task-endpoint-with-validation`
- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Updating a task that does not exist returns a task not found error and stores nothing
- [ ] A field value the backend does not accept returns an invalid input error and stores nothing
- [ ] An internal server or database error returns an error response and leaves no partial changes, including no change to Last Updated Date
- [ ] Automated tests cover each error response

#### Requirements

- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [FE] Pre-fill the shared task form with stored values when editing a task

`FE-task-edit-form-prefill` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-update-task`

**Track:** frontend · **Size:** M · consumes API

#### Description

Load the stored values of a task by ID and fill the shared task form with them when the user opens a task for editing. If the load fails, show an error message and do not open the edit form.

#### Blocked by

- `BE-task-by-id-endpoint`
- `FE-task-creation-form`

#### Definition of Done

- [ ] The edit form shows the stored values of the selected task
- [ ] A failed load shows an error message and the edit form does not open
- [ ] No success message is shown when the load fails
- [ ] Automated tests cover a successful load and a failed load

#### Requirements

- `R-9b30a145` (frontend) The system provides a form to create a new task and to edit an existing task.
- `R-bc3213df` (functional) The system lets a user update an existing task.

### Task: [FE] Show update result messages and keep shown values until save succeeds

`FE-task-update-result-messages` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-update-task`

**Track:** frontend · **Size:** S · consumes API

#### Description

After a save, show a success message only when the backend confirms the save and an error message when it fails. Show the title-required and due-date messages in the form for the rejected cases. When a save fails, the task list keeps showing the previous values.

#### Blocked by

- `BE-put-task-endpoint-with-validation`
- `FE-task-edit-form-prefill`

#### Definition of Done

- [ ] A success message appears only after the backend confirms the save
- [ ] An error message appears when the backend returns an error and no success message is shown
- [ ] The title-required and due-date messages appear in the form for the rejected cases
- [ ] After a failed save the task list shows the previous values
- [ ] Automated tests cover success, backend error and each validation message

#### Requirements

- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.
- `R-03df7815` (validation_rule) A task title is required and an empty title must be rejected on task creation or update.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.

### Task: [FE] Add edit action to each task row that opens the edit form

`FE-task-row-edit-action` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-update-task`

**Track:** frontend · **Size:** S

#### Description

Add an edit action to each row of the task list. Selecting it opens the edit form for that task.

#### Blocked by

- `FE-task-edit-form-prefill`

#### Definition of Done

- [ ] Each task row has an edit action
- [ ] Selecting the edit action opens the edit form with that task's identifier
- [ ] Automated tests cover the edit action on a row

#### Requirements

- `R-9b30a145` (frontend) The system provides a form to create a new task and to edit an existing task.

### Task: [QA] Test suite for updating an existing task

`QA-task-update-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-update-task`

**Track:** qa_general · **Size:** M · consumes API · touches DB

#### Description

Automated tests for editing an existing task across the form, the update endpoint and the task list, covering all acceptance criteria of this story.

#### Blocked by

- `BE-put-task-endpoint-with-validation`
- `BE-put-task-error-responses`
- `FE-task-edit-form-prefill`
- `FE-task-update-result-messages`
- `FE-task-row-edit-action`

#### Definition of Done

- [ ] Tests cover each acceptance criterion of the story
- [ ] Tests confirm that rejected saves leave stored values unchanged
- [ ] Tests confirm that no success message is shown after a failed save
- [ ] All tests pass in the continuous integration pipeline
- [ ] Tests confirm that a successful save sets Last Updated Date and that a failed save leaves it unchanged

#### Requirements

- `R-bc3213df` (functional) The system lets a user update an existing task.
- `R-9b30a145` (frontend) The system provides a form to create a new task and to edit an existing task.
- `R-03df7815` (validation_rule) A task title is required and an empty title must be rejected on task creation or update.
- `R-efe1e5d4` (validation_rule) A task's Due Date must not be earlier than its Creation Date.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.

---

## Delete a task after confirming the deletion

`US-delete-task` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-and-status`

### User story

**As a** user of the to-do list, **I want** to delete a task after confirming the deletion in a prompt, **so that** I remove tasks I no longer need without deleting one by accident.

### Business description

Users can delete a task. Deleting a task requires the user to confirm the deletion first. The frontend shows a success or error message after the delete action, and it does not show a success state when the backend call fails.

### Business value

Users can clean up their task list, and the confirmation step guards against accidental deletion of tasks.

### Acceptance criteria

1. **Given** A task is shown in the task list, **When** The user chooses the delete action for that task, **Then** A confirmation prompt is shown, the task is still shown in the list, and no delete request has been sent
2. **Given** The confirmation prompt is shown for a task, **When** The user cancels the prompt, **Then** No delete request is sent and the task remains unchanged in the list
3. **Given** The confirmation prompt is shown for an existing task, **When** The user confirms the deletion and the backend returns a success response, **Then** The task is removed from the list and a success message is displayed
4. **Given** The user has confirmed the deletion and the delete request is still in progress, **When** The user views the task list, **Then** The task still appears in the list because the frontend does not remove it before the backend confirms the deletion
5. **Given** The user has confirmed the deletion of a task, **When** The backend returns an error response, **Then** The task remains in the list and an error message is displayed instead of a success message
6. **Given** A delete request is sent for a task ID that does not exist in the database, **When** The backend processes the request, **Then** The backend returns a task not found error and no task data is changed
7. **Given** A delete request fails because of an internal server or database error, **When** The backend processes the request, **Then** The backend returns an error response and the stored task is not removed

### Edge cases

- A delete request is sent for a task that was already deleted, for example from another browser session: the backend returns a task not found error and the frontend shows an error message.
- The wording of the confirmation prompt and of the success and error messages is not specified.
- The PRD does not state whether a deleted task can be restored; this story does not provide restore.

### Dependencies

- `US-create-task`
- `US-view-task-list`

### Definition of Done

- [ ] DELETE /tasks/{id} removes the task with the given ID and returns a success response
- [ ] DELETE /tasks/{id} returns a task not found error for an unknown ID and changes no data
- [ ] DELETE /tasks/{id} returns an error response on internal server or database errors and keeps the stored task
- [ ] The delete action shows a confirmation prompt before any delete request is sent
- [ ] Cancelling the prompt sends no request and leaves the task unchanged
- [ ] The task is removed from the list only after a success response from the backend
- [ ] A success message is shown after a successful delete and an error message after a failed delete
- [ ] The test suite covers confirmation, cancel, success, not-found and server error cases

### Tasks

- [ ] `BE-delete-task-endpoint` [BE] Add DELETE /tasks/{id} endpoint with not-found handling
- [ ] `FE-delete-confirmation-prompt` [FE] Add delete confirmation prompt and result messages to task actions
- [ ] `QA-delete-task-test-suite` [QA] Test suite for task deletion, confirmation and error handling

### Requirements

- `R-8523b9ec` (functional) The system lets a user delete a task.
- `R-8ef41ba1` (frontend) Deleting a task must first show a confirmation prompt that the user must accept before the task is deleted.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.

### Task: [BE] Add DELETE /tasks/{id} endpoint with not-found handling

`BE-delete-task-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-delete-task`

**Track:** backend · **Size:** S · touches DB

#### Description

Add an endpoint that deletes the task with the given ID. Return a task not found error when the ID does not exist, and return an error response on internal server or database errors without removing the stored task.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] DELETE /tasks/{id} deletes the stored task and returns a success response
- [ ] Unknown IDs return a task not found error and change no data
- [ ] Database or server errors return an error response and keep the stored task
- [ ] Endpoint tests cover success, not-found and error cases

#### Requirements

- `R-8523b9ec` (functional) The system lets a user delete a task.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [FE] Add delete confirmation prompt and result messages to task actions

`FE-delete-confirmation-prompt` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-delete-task`

**Track:** frontend · **Size:** S · consumes API

#### Description

Show a confirmation prompt when the user chooses delete on a task. Send the delete request only after the user confirms. Remove the task from the list only after a success response, and show a success or error message with the result.

#### Blocked by

- `BE-delete-task-endpoint`
- `FE-task-list-view`

#### Definition of Done

- [ ] Choosing delete shows a confirmation prompt and sends no request
- [ ] Cancelling the prompt sends no request and leaves the task in the list
- [ ] Confirming sends the delete request for that task
- [ ] The task is removed from the list only after a success response
- [ ] A success message is shown after a successful delete
- [ ] An error message is shown and the task stays in the list after a failed delete

#### Requirements

- `R-8ef41ba1` (frontend) Deleting a task must first show a confirmation prompt that the user must accept before the task is deleted.
- `R-8523b9ec` (functional) The system lets a user delete a task.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.

### Task: [QA] Test suite for task deletion, confirmation and error handling

`QA-delete-task-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-delete-task`

**Track:** qa_general · **Size:** M · consumes API · touches DB

#### Description

Automated tests for the delete flow: the confirmation prompt, cancel, successful delete, not-found and server error responses, and the messages shown to the user.

#### Blocked by

- `BE-delete-task-endpoint`
- `FE-delete-confirmation-prompt`

#### Definition of Done

- [ ] Tests cover the confirmation prompt and the cancel path
- [ ] Tests cover a successful delete and the success message
- [ ] Tests cover a not-found response and confirm that no data changes
- [ ] Tests cover a server or database error and confirm that the task is kept
- [ ] Tests confirm that the task is not removed from the list before a success response

#### Requirements

- `R-8523b9ec` (functional) The system lets a user delete a task.
- `R-8ef41ba1` (frontend) Deleting a task must first show a confirmation prompt that the user must accept before the task is deleted.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.

---

## Change the status of a task to Completed

`US-change-task-status` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-and-status`

### User story

**As a** user managing my to-do list, **I want** to mark a task as Completed, **so that** I can see which work is done.

### Business description

Users can change the status of an existing task to Completed. The backend confirms the change before the screen shows it, and the user sees a success or error message for the outcome.

### Business value

Users can track finished work, and the Completed count is available for reporting.

### Acceptance criteria

1. **Given** an existing task with status Open, **When** the user marks the task as Completed, **Then** the task status is shown as Completed and the Completion Date of the task is populated
2. **Given** a status change request that the backend rejects or cannot complete, **When** the user submits the change, **Then** the task keeps its previous status on screen and an error message is displayed
3. **Given** a status change that the backend confirms as saved, **When** the change completes, **Then** a success message is displayed to the user
4. **Given** a task ID that does not exist in the database, **When** a status change is requested for that ID, **Then** the backend returns a task not found error and no task is changed
5. **Given** a status change request with a status value outside Open, In Progress and Completed, **When** the backend receives the request, **Then** the backend rejects the request with an invalid input error and the stored status is unchanged
6. **Given** A status change request for an existing task where the database or server fails while saving, **When** The backend processes the request, **Then** The backend returns an internal error response and the stored status is unchanged

### Edge cases

- The backend fails while saving the status change: the task keeps its previous status on screen and an error message is shown.
- The status change request is sent for a task that was deleted in the meantime: a task not found error is returned.
- The PRD does not state whether a Completed task can be reopened and what happens to its Completion Date.

### Dependencies

- None.

### Definition of Done

- [ ] Marking a task as Completed is saved and shown after backend confirmation
- [ ] Success and error messages are shown after a status change
- [ ] Error cases for not found and invalid input are covered by tests

### Tasks

- [ ] `BE-task-status-endpoint` [BE] Add status change endpoint that sets a task to Completed
- [ ] `FE-task-status-toggle` [FE] Add Mark as Completed action to each task
- [ ] `FE-task-status-feedback` [FE] Show success or error message after a task status change
- [ ] `QA-task-status-tests` [QA] Test suite for marking tasks Completed

### Requirements

- `R-2304218f` (functional) The system lets a user mark a task as 'Completed'.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.

### Task: [BE] Add status change endpoint that sets a task to Completed

`BE-task-status-endpoint` · labels: type:task, area:db, prd-agent

**Parent:** `US-change-task-status`

**Track:** backend · **Size:** S · touches DB

#### Description

Add an endpoint that changes the status of an existing task to Completed and populates its Completion Date. Return a task not found error for unknown IDs, an invalid input error for status values outside Open, In Progress and Completed, and a simple internal error response for server or database failures. The stored status stays unchanged on any error.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Endpoint sets a task to Completed and populates the Completion Date
- [ ] Unknown task ID returns a task not found error and changes nothing
- [ ] Invalid status value returns an invalid input error and leaves the stored status unchanged
- [ ] Database or server failures return a simple internal error response

#### Requirements

- `R-2304218f` (functional) The system lets a user mark a task as 'Completed'.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.

### Task: [FE] Add Mark as Completed action to each task

`FE-task-status-toggle` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-change-task-status`

**Track:** frontend · **Size:** S · consumes API

#### Description

Add an action to each task that marks it as Completed by calling the status change endpoint. The task shows Completed only after the backend confirms the change. If the backend action fails, the task keeps its previous status on screen.

#### Blocked by

- `BE-task-status-endpoint`
- `FE-task-list-view`

#### Definition of Done

- [ ] Action marks the task as Completed through the backend
- [ ] Completed status is shown only after backend confirmation
- [ ] Failed backend action leaves the previous status on screen

#### Requirements

- `R-2304218f` (functional) The system lets a user mark a task as 'Completed'.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.

### Task: [FE] Show success or error message after a task status change

`FE-task-status-feedback` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-change-task-status`

**Track:** frontend · **Size:** S · consumes API

#### Description

After each status change, show a success message when the backend confirms the change and an error message when the backend call fails.

#### Blocked by

- `BE-task-status-endpoint`

#### Definition of Done

- [ ] A success message is shown after a confirmed status change.
- [ ] An error message is shown after a failed status change.
- [ ] The wording of the messages is confirmed with the product owner, because it is not specified.

#### Requirements

- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.

### Task: [QA] Test suite for marking tasks Completed

`QA-task-status-tests` · labels: type:task, area:qa, prd-agent

**Parent:** `US-change-task-status`

**Track:** qa_general · **Size:** S · consumes API

#### Description

Test the status change to Completed from the screen and the endpoint, including the Completion Date, success and error messages, task not found, invalid input, internal errors, and that no success state is shown before or without backend confirmation.

#### Blocked by

- `BE-task-status-endpoint`
- `FE-task-status-toggle`
- `FE-task-status-feedback`

#### Definition of Done

- [ ] Tests cover marking a task as Completed and the Completion Date
- [ ] Tests cover success and error messages
- [ ] Tests cover task not found and invalid input responses
- [ ] Tests confirm no success state is shown when the backend fails
- [ ] Tests cover an internal error response when the database or server fails during a status change, and the stored status is unchanged

#### Requirements

- `R-2304218f` (functional) The system lets a user mark a task as 'Completed'.
- `R-d57336f7` (frontend) After each create, update or delete action, the UI must display a success or error message reflecting the outcome.
- `R-244669c0` (backend) The backend must expose endpoints to create, read all, read by ID, update, delete, and change the status of todo items.
- `R-9dc414dc` (backend) The backend must handle task not found, invalid input, missing mandatory fields, deleting or updating non-existent tasks, and internal server or database errors, using a simple error handling approach.
- `R-ab9e9cb0` (constraint) The Frontend must not show a successful state for an action before the Backend confirms it, and must not show success when the Backend action fails.
- `R-576b7e59` (data_model) Each task has a Status field whose allowed values are Open, In Progress and Completed.

---

## View all tasks and totals in a report table

`US-view-task-report` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-and-status`

### User story

**As a** a team member who needs an overview of work, **I want** to view all my tasks in a table on the Task Reporting page, with Total, Open and Completed counts, **so that** I can see the full state of my work at a glance.

### Business description

The Task Reporting page gives an aggregated view of the user's tasks. It shows every stored task in a table and summarises the tasks with three metrics: Total Tasks, Open Tasks and Completed Tasks.

### Business value

Users get one place to see all tasks and their overall progress without opening each task.

### Acceptance criteria

1. **Given** The user has at least one task stored in the system, **When** The user opens the Task Reporting page without applying any filter, **Then** The table shows one row for every stored task
2. **Given** Stored tasks with the statuses Open, In Progress and Completed exist, **When** The Task Reporting page loads, **Then** Total Tasks equals the number of all stored tasks, Open Tasks equals the number of tasks with status Open, and Completed Tasks equals the number of tasks with status Completed
3. **Given** No tasks are stored in the system, **When** The Task Reporting page loads, **Then** The table has no task rows and Total Tasks, Open Tasks and Completed Tasks each show 0
4. **Given** The metrics endpoint is called without any filter or search parameters, **When** The endpoint responds successfully, **Then** The response contains the Total, Open and Completed counts of all stored tasks
5. **Given** The metrics endpoint is called and a task has the status In Progress, **When** The endpoint responds successfully, **Then** The In Progress task is included in Total Tasks and is not included in Open Tasks or Completed Tasks

### Edge cases

- A task with the status In Progress counts toward Total Tasks only; it is not counted as Open or Completed.
- When no tasks are stored, the table shows no rows and all three metrics show 0.
- The wording of the empty-table message on the Task Reporting page is not specified.
- The PRD does not state whether In Progress tasks count as Open Tasks.
- The PRD does not state whether the Total, Open and Completed metrics reflect the applied filters or all stored tasks.

### Dependencies

- `US-create-task`
- `US-view-task-list`

### Definition of Done

- [ ] The Task Reporting page loads and shows every stored task as one table row.
- [ ] Total Tasks, Open Tasks and Completed Tasks are shown and match the stored data.
- [ ] The metrics endpoint returns the Total, Open and Completed counts without any filter parameters.
- [ ] The task table reads its rows from the existing task list endpoint and does not add a second endpoint for the same rows.
- [ ] Automated tests for the table, the metrics and the empty state pass.

### Tasks

- [ ] `BE-report-metrics-endpoint` [BE] Add GET endpoint returning Total, Open and Completed task counts
- [ ] `FE-report-page-table` [FE] Build Task Reporting page with a table of all tasks
- [ ] `FE-report-metrics-cards` [FE] Show Total, Open and Completed metrics on the Task Reporting page
- [ ] `QA-report-test-suite` [QA] Add test suite for the task report table and metrics

### Requirements

- `R-d0e0fe7a` (frontend) The Task Reporting page presents an aggregated view of the user's tasks.
- `R-a1b267a3` (frontend) The report displays all tasks in a tabular view.
- `R-4ffbfafa` (frontend) The report displays the metrics Total Tasks, Open Tasks and Completed Tasks.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [BE] Add GET endpoint returning Total, Open and Completed task counts

`BE-report-metrics-endpoint` · labels: type:task, area:backend, prd-agent

**Parent:** `US-view-task-report`

**Track:** backend · **Size:** S · touches DB

#### Description

Add a read-only GET endpoint that counts all stored tasks, tasks with status Open and tasks with status Completed, and returns the three counts. Tasks with status In Progress count only toward Total. The endpoint accepts no filter parameters in this story. The task rows themselves come from the existing task list endpoint.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] GET endpoint returns Total, Open and Completed counts as integers.
- [ ] Counts are computed from the stored tasks and return 0 when no tasks exist.
- [ ] Invalid or unsupported parameters return a clear error response.
- [ ] Unit tests cover zero tasks, mixed statuses and In Progress tasks.

#### Requirements

- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [FE] Build Task Reporting page with a table of all tasks

`FE-report-page-table` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-report`

**Track:** frontend · **Size:** M · consumes API

#### Description

Build the Task Reporting page with a table that lists every task returned by the existing task list endpoint. The table shows one row per task. It shows an empty state when there are no rows. The wording of the empty-state message is not specified.

#### Blocked by

- `BE-tasks-list-endpoint`

#### Definition of Done

- [ ] The Task Reporting page is reachable and shows a table with one row per stored task.
- [ ] The table reads data from the task list endpoint without a second request path for the same rows.
- [ ] An empty state is shown when no tasks are stored.
- [ ] A failed request shows an error state and does not show stale rows as current data.

#### Requirements

- `R-d0e0fe7a` (frontend) The Task Reporting page presents an aggregated view of the user's tasks.
- `R-a1b267a3` (frontend) The report displays all tasks in a tabular view.

### Task: [FE] Show Total, Open and Completed metrics on the Task Reporting page

`FE-report-metrics-cards` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-view-task-report`

**Track:** frontend · **Size:** S · consumes API

#### Description

Show three metric values on the Task Reporting page: Total Tasks, Open Tasks and Completed Tasks. The values come from the metrics endpoint.

#### Blocked by

- `BE-report-metrics-endpoint`

#### Definition of Done

- [ ] Total Tasks, Open Tasks and Completed Tasks are displayed with the values returned by the metrics endpoint.
- [ ] All three values show 0 when no tasks are stored.
- [ ] A failed metrics request shows an error state instead of a value.

#### Requirements

- `R-4ffbfafa` (frontend) The report displays the metrics Total Tasks, Open Tasks and Completed Tasks.

### Task: [QA] Add test suite for the task report table and metrics

`QA-report-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-view-task-report`

**Track:** qa_general · **Size:** M · consumes API

#### Description

Automated test suite covering the Task Reporting page table, the three metrics and the metrics endpoint. It covers all tasks being shown, correct counts for mixed statuses, and the empty case.

#### Blocked by

- `FE-report-page-table`
- `FE-report-metrics-cards`
- `BE-report-metrics-endpoint`

#### Definition of Done

- [ ] Tests verify one table row per stored task.
- [ ] Tests verify Total, Open and Completed counts with Open, In Progress and Completed tasks.
- [ ] Tests verify that all values are 0 and the table has no rows when no tasks are stored.
- [ ] The suite runs in the team's continuous integration pipeline and passes.

#### Requirements

- `R-d0e0fe7a` (frontend) The Task Reporting page presents an aggregated view of the user's tasks.
- `R-a1b267a3` (frontend) The report displays all tasks in a tabular view.
- `R-4ffbfafa` (frontend) The report displays the metrics Total Tasks, Open Tasks and Completed Tasks.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

---

## Filter, search and sort tasks in the report

`US-filter-search-sort-report` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-and-status`

### User story

**As a** report viewer, **I want** to filter, search and sort the tasks in the report, **so that** I can find the tasks I care about and review them in a useful order.

### Business description

The task report lets the user narrow the listed tasks by Status, Priority and Date Range, search them by title, and sort them by Creation Date, Due Date, Status, Priority or Title. The backend supports filtering, searching and sorting for the report.

### Business value

Users find relevant tasks in the report faster without scanning the full list.

### Acceptance criteria

1. **Given** The report contains tasks with Status Open and tasks with Status Completed, **When** The user selects Status Open in the Status filter, **Then** Only tasks with Status Open are listed in the report table
2. **Given** The report contains tasks with Priority Low, Medium and High, **When** The user selects Priority High in the Priority filter, **Then** Only tasks with Priority High are listed in the report table
3. **Given** The report contains tasks with different dates, **When** The user sets a Date Range in the Date Range filter, **Then** Only tasks whose date falls inside the selected range are listed in the report table
4. **Given** The report contains tasks with titles 'Pay invoice' and 'Write report', **When** The user types 'invoice' in the title search, **Then** Only the task titled 'Pay invoice' is listed in the report table
5. **Given** The report table lists several tasks with different Due Dates, **When** The user selects the Due Date column to sort the table, **Then** The tasks are listed in Due Date order
6. **Given** The report table lists several tasks with different Creation Dates, Statuses and Priorities, **When** The user selects Creation Date, Status or Priority as the sort field, **Then** The tasks are listed in the order of the selected field
7. **Given** The report table lists several tasks with different titles, **When** The user selects Title as the sort field, **Then** The tasks are listed in order of their titles
8. **Given** A status filter, a priority filter, a date range, a title search and a sort field are applied on the report page, **When** The report data is requested from the backend, **Then** The backend returns only the tasks matching all applied filters and the search, in the requested sort order

### Edge cases

- The Date Range filter does not state which task date it applies to; this is not specified.
- The sort direction (ascending or descending) is not specified.
- Whether the title search is case-sensitive or matches partial words is not specified beyond the 'invoice' example.

### Dependencies

- None.

### Definition of Done

- [ ] Status, Priority and Date Range filters and the title search narrow the report table
- [ ] The report can be sorted by Creation Date, Due Date, Status, Priority and Title
- [ ] Backend returns filtered, searched and sorted results
- [ ] Test suite covers filters, search and all five sort fields

### Tasks

- [ ] `BE-report-query-filter-search-sort` [BE] Add filter, title search and sort parameters to the report query
- [ ] `FE-report-filter-controls` [FE] Add Status, Priority and Date Range filter controls to the task report page
- [ ] `FE-report-search-and-sort-ui` [FE] Add title search box and sortable column headers to the task report table
- [ ] `QA-report-filter-search-sort-tests` [QA] Add test suite for report filtering, title search and sorting

### Requirements

- `R-5f4ef76c` (functional) The report lets the user filter tasks by Status, Priority and Date Range.
- `R-48e39a9d` (functional) The report lets the user search tasks by title.
- `R-d482bfea` (functional) The report lets the user sort tasks by Creation Date, Due Date, Status, Priority or Title.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [BE] Add filter, title search and sort parameters to the report query

`BE-report-query-filter-search-sort` · labels: type:task, area:backend, prd-agent

**Parent:** `US-filter-search-sort-report`

**Track:** backend · **Size:** M · touches DB

#### Description

Extend the report query so it accepts Status, Priority and Date Range filters, a title search, and a sort field. The sort field may be Creation Date, Due Date, Status, Priority or Title. Results match all applied filters and the search, in the requested order. Sort direction is not specified in the requirements.

#### Blocked by

- `BE-tasks-table-migration`

#### Definition of Done

- [ ] Query filters by Status, Priority and Date Range
- [ ] Query searches tasks by title
- [ ] Query sorts by Creation Date, Due Date, Status, Priority and Title
- [ ] Combined filters, search and sort return only matching tasks in the requested order

#### Requirements

- `R-5f4ef76c` (functional) The report lets the user filter tasks by Status, Priority and Date Range.
- `R-48e39a9d` (functional) The report lets the user search tasks by title.
- `R-d482bfea` (functional) The report lets the user sort tasks by Creation Date, Due Date, Status, Priority or Title.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [FE] Add Status, Priority and Date Range filter controls to the task report page

`FE-report-filter-controls` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-filter-search-sort-report`

**Track:** frontend · **Size:** M · consumes API

#### Description

Add Status, Priority and Date Range filter controls to the task report page. Each control sends its selection to the report data request and updates the table with the response.

#### Blocked by

- `BE-report-query-filter-search-sort`

#### Definition of Done

- [ ] Status filter offers Open, In Progress and Completed
- [ ] Priority filter offers Low, Medium and High
- [ ] Date Range filter accepts a start and end date
- [ ] Selecting a filter updates the report table from the backend response
- [ ] A clear way to remove each filter is available

#### Requirements

- `R-5f4ef76c` (functional) The report lets the user filter tasks by Status, Priority and Date Range.

### Task: [FE] Add title search box and sortable column headers to the task report table

`FE-report-search-and-sort-ui` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-filter-search-sort-report`

**Track:** frontend · **Size:** M · consumes API

#### Description

Add a title search box and make the report table sortable by Creation Date, Due Date, Status, Priority and Title. Selecting a sort field requests the report data in that order.

#### Blocked by

- `BE-report-query-filter-search-sort`

#### Definition of Done

- [ ] Title search box narrows the listed tasks
- [ ] Creation Date, Due Date, Status, Priority and Title can each be selected as the sort field
- [ ] Table shows tasks in the order of the selected field

#### Requirements

- `R-48e39a9d` (functional) The report lets the user search tasks by title.
- `R-d482bfea` (functional) The report lets the user sort tasks by Creation Date, Due Date, Status, Priority or Title.

### Task: [QA] Add test suite for report filtering, title search and sorting

`QA-report-filter-search-sort-tests` · labels: type:task, area:qa, prd-agent

**Parent:** `US-filter-search-sort-report`

**Track:** qa_general · **Size:** M · consumes API

#### Description

Test the report filters, title search and sorting. Sorting tests cover Creation Date, Due Date, Status, Priority and Title, plus combined filters, search and sort through the backend.

#### Blocked by

- `BE-report-query-filter-search-sort`
- `FE-report-filter-controls`
- `FE-report-search-and-sort-ui`

#### Definition of Done

- [ ] Tests cover Status, Priority and Date Range filters
- [ ] Tests cover title search
- [ ] Tests cover sorting by each of the five fields, including Title
- [ ] Tests cover combined filters, search and sort

#### Requirements

- `R-5f4ef76c` (functional) The report lets the user filter tasks by Status, Priority and Date Range.
- `R-48e39a9d` (functional) The report lets the user search tasks by title.
- `R-d482bfea` (functional) The report lets the user sort tasks by Creation Date, Due Date, Status, Priority or Title.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

---

## Download the filtered task report as an Excel file

`US-export-report-excel` · labels: type:story, prd-agent

**Parent:** `EPIC-personal-task-management-and-status`

### User story

**As a** user, **I want** download the filtered, searched and sorted task report as an Excel file, **so that** I can work with the task data in a spreadsheet outside the application.

### Business description

Users can export the task report to Excel. The exported file reflects the rows, order and filters the user has applied on the report page, so the user gets the same view of the data as on screen.

### Business value

Task data can be reviewed and used outside the application in a spreadsheet, using the same filters and sort order the user already set.

### Acceptance criteria

1. **Given** The task report page shows 12 tasks with no filters applied, **When** The user selects the Excel export action, **Then** An Excel file is downloaded that contains 12 data rows, one per task
2. **Given** The report has the Status filter set to Open and is sorted by Due Date ascending, **When** The user selects the Excel export action, **Then** The downloaded file contains only tasks with status Open, in ascending Due Date order
3. **Given** The report has a title search term applied that matches 3 tasks, combined with the Status filter set to Open, **When** The user selects the Excel export action, **Then** The downloaded file contains only the tasks that match both the search term and the Open status, in the same order as on the report page
4. **Given** The user exports the report at a given moment, **When** The file is downloaded, **Then** The file name contains the timestamp of the moment the file was generated
5. **Given** The applied filters match no tasks, **When** The user selects the Excel export action, **Then** No Excel file is downloaded and a message is shown to the user stating that there is no data to export
6. **Given** A report with at least one task is exported, **When** The user opens the downloaded Excel file, **Then** The first row contains clear column headers and every date column uses the same date format

### Edge cases

- The PRD does not define the wording of the no-data message, or whether a file is still produced when there is no data. This is an open question.
- The PRD does not define the timestamp format or time zone used in the file name. This is an open question.
- The PRD does not define the date format for date columns. One format must be chosen and applied to every date column.
- The PRD does not state whether a title search counts as a filter. The export applies the search the same way the report page does.
- A report with exactly one task produces a file with one data row.

### Dependencies

- `US-create-task`
- `US-view-task-report`
- `US-filter-search-sort-report`

### Definition of Done

- [ ] The export action on the task report page downloads a file that matches the filtered, searched and sorted rows shown on the page
- [ ] Exporting a result with no rows shows a message and downloads no file
- [ ] The Excel file generation location is documented with rationale and trade-offs before generator work starts
- [ ] Every exported file has a timestamped name and a header row with clear column headers
- [ ] Every date column in an exported file uses one date format
- [ ] All acceptance criteria are verified by the export test suite

### Tasks

- [ ] `BE-excel-export-generation-decision` [BE] Decide and document where the task report Excel file is generated
- [ ] `BE-task-report-excel-generator` [BE] Add report Excel generator producing a timestamped file
- [ ] `FE-report-excel-download-action` [FE] Add Excel export action that downloads the filtered and sorted report
- [ ] `FE-report-export-no-data-message` [FE] Show a no-data message instead of producing an empty Excel file
- [ ] `QA-excel-export-test-suite` [QA] Add test suite for the task report Excel export

### Requirements

- `R-52360b76` (functional) The report lets the user download its data as an Excel file.
- `R-09e9d163` (functional) The exported Excel file must contain only the rows matching the currently applied filters, in the currently applied sort order.
- `R-fad183b1` (constraint) Every exported Excel file must have clear column headers and use one consistent date format across all date columns.
- `R-d22b9b6a` (functional) The name of each exported Excel file must include the timestamp at which the file was generated.
- `R-437992f1` (frontend) When there is no data to export, the system must show a message to the user instead of producing an empty file. The PRD does not define the message wording or whether a file is still produced; this is an open question.
- `R-3a63e0ce` (decision_open) The development team decides whether the Excel file is generated on the frontend or the backend.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [BE] Decide and document where the task report Excel file is generated

`BE-excel-export-generation-decision` · labels: type:spike, area:backend, prd-agent

**Parent:** `US-export-report-excel`

**Track:** backend · **Size:** S

#### Description

Choose whether the Excel file is generated on the frontend or the backend, and record the rationale and trade-offs. The generator and export action tasks start only after this decision is documented.

#### Blocked by

- Nothing.

#### Definition of Done

- [ ] A decision record states whether the Excel file is generated on the frontend or the backend, with rationale and trade-offs
- [ ] The decision record states which component produces the file and what the frontend receives when a file is produced
- [ ] The decision record is shared with the team before the generator and export action tasks start

#### Requirements

- `R-3a63e0ce` (decision_open) The development team decides whether the Excel file is generated on the frontend or the backend.

### Task: [BE] Add report Excel generator producing a timestamped file

`BE-task-report-excel-generator` · labels: type:task, area:backend, prd-agent

**Parent:** `US-export-report-excel`

**Track:** backend · **Size:** M · touches DB

#### Description

Produce an Excel file from the task report rows, in the applied sort order, using the filter, search and sort parameters of the report query. Column headers are clear and every date column uses one date format. The file name includes the generation timestamp. If the documented decision places generation in the frontend, the scope of this task changes before work starts.

#### Blocked by

- `BE-tasks-table-migration`
- `BE-excel-export-generation-decision`

#### Definition of Done

- [ ] The generator accepts the same filter, search and sort parameters as the report query and adds no new filter parameters
- [ ] Exported rows match the report query result for the same parameters, one row per task, in the same order
- [ ] The file name follows one fixed pattern and includes the timestamp of generation
- [ ] The first row holds column headers and every date column uses the same date format
- [ ] The generator is called only with rows to export; the no-data case is handled by the frontend export action
- [ ] Unit tests cover headers, date format, row order and file name

#### Requirements

- `R-52360b76` (functional) The report lets the user download its data as an Excel file.
- `R-09e9d163` (functional) The exported Excel file must contain only the rows matching the currently applied filters, in the currently applied sort order.
- `R-d22b9b6a` (functional) The name of each exported Excel file must include the timestamp at which the file was generated.
- `R-fad183b1` (constraint) Every exported Excel file must have clear column headers and use one consistent date format across all date columns.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.

### Task: [FE] Add Excel export action that downloads the filtered and sorted report

`FE-report-excel-download-action` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-export-report-excel`

**Track:** frontend · **Size:** M · consumes API

#### Description

Add an Excel export action to the task report page. The action sends the currently applied filters, search term and sort order to the generator and downloads the returned file. Starts after the generator endpoint is available.

#### Blocked by

- `BE-task-report-excel-generator`
- `FE-report-filter-controls`
- `FE-report-search-and-sort-ui`

#### Definition of Done

- [ ] The export action is available on the task report page
- [ ] The request carries the currently applied filters, title search term and sort order
- [ ] The downloaded file uses the file name returned by the generator, including its timestamp
- [ ] The no-data check runs before any file request is made
- [ ] If the generator call fails, an error message is shown and no success state is displayed

#### Requirements

- `R-52360b76` (functional) The report lets the user download its data as an Excel file.
- `R-09e9d163` (functional) The exported Excel file must contain only the rows matching the currently applied filters, in the currently applied sort order.

### Task: [FE] Show a no-data message instead of producing an empty Excel file

`FE-report-export-no-data-message` · labels: type:task, area:frontend, prd-agent

**Parent:** `US-export-report-excel`

**Track:** frontend · **Size:** S

#### Description

Add the no-data check to the export action. When the currently loaded filtered report has no rows, show a message to the user and do not request or download a file. This is the only place where the no-data case is handled. The wording of the message is not specified in the PRD; this is an open question to confirm with the product owner.

#### Blocked by

- `FE-report-excel-download-action`

#### Definition of Done

- [ ] Exporting a report with zero rows after filters are applied shows a message and requests no file
- [ ] The message wording is confirmed with the product owner before release
- [ ] Exporting a report with at least one row does not show the no-data message

#### Requirements

- `R-437992f1` (frontend) When there is no data to export, the system must show a message to the user instead of producing an empty file. The PRD does not define the message wording or whether a file is still produced; this is an open question.

### Task: [QA] Add test suite for the task report Excel export

`QA-excel-export-test-suite` · labels: type:task, area:qa, prd-agent

**Parent:** `US-export-report-excel`

**Track:** qa_general · **Size:** M · consumes API

#### Description

Test suite for the Excel export covering row contents, row order, filters, title search, file name timestamp, column headers, date format and the no-data behaviour. Runs after the export action and the generator are in place.

#### Blocked by

- `BE-task-report-excel-generator`
- `FE-report-excel-download-action`
- `FE-report-export-no-data-message`

#### Definition of Done

- [ ] Tests cover export with no filters, with a status filter, and with a title search
- [ ] Tests check the row count, the row order and that exported rows match the report on screen
- [ ] Tests check the file name timestamp and the header row
- [ ] Tests check that every date column uses the same date format
- [ ] Tests check that no file is downloaded and a message is shown when there are no rows
- [ ] The test suite runs in the project's automated test run and passes

#### Requirements

- `R-52360b76` (functional) The report lets the user download its data as an Excel file.
- `R-09e9d163` (functional) The exported Excel file must contain only the rows matching the currently applied filters, in the currently applied sort order.
- `R-d22b9b6a` (functional) The name of each exported Excel file must include the timestamp at which the file was generated.
- `R-437992f1` (frontend) When there is no data to export, the system must show a message to the user instead of producing an empty file. The PRD does not define the message wording or whether a file is still produced; this is an open question.
- `R-fad183b1` (constraint) Every exported Excel file must have clear column headers and use one consistent date format across all date columns.
- `R-8007d6b5` (backend) The system exposes APIs that support filtering, searching, sorting, and metric aggregation for task reporting.
