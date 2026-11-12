# PRD: To-Do Management System

## Product Overview

A personal task management system that allows users to track daily tasks and generate status reports. The system consists of two main pages.

## Page 1: To-Do Management

This page allows the user to manage their personal task list.

### Required Features

- Create a new task.

- View the task list.

- Update an existing task.

- Delete a task.

- Mark a task as 'Completed'.

### Task Data Model

Each task must contain:

- Unique ID

- Title

- Description

- Status (Open, In Progress, Completed)

- Priority (Low, Medium, High)

- Creation Date

- Due Date

- Last Updated Date

- Completion Date (if completed)

### Validation Rules & Edge Cases

- Task titles are mandatory; cannot be empty.

- Due Date cannot be earlier than the Creation Date.

- Task titles cannot be longer than 100 characters.

- Deleting a task requires a prompt confirmation.

- Success or error messages must be displayed after create/update/delete actions.

- Optimistic UI updates are not allowed: if a Backend action fails, the Frontend must not reflect a successful state.

### Frontend Requirements

- Task list view.

- Task creation/editing form.

- Status and Priority indicators.

- Loading, Empty, and Error states.

- List auto-refresh upon task changes.

### Backend Requirements (API)

- The Todos should be saved in persistence DB – assume the DB already exits but there will be a need for a new table

- Endpoints for Create, Read (All & By ID), Update, Delete, and Status Change.

- Error handling for: Task Not Found, Invalid Input, Missing Mandatory Fields, Deleting/Updating Non-Existent Tasks, and Internal Server/Database Errors. For error handling - Keep it simple

## Page 2: Task Reporting

This page presents an aggregated view of the user's tasks.

### Required Features

- Tabular display of all tasks.

- Filters: Status, Priority, Date Range.

- Search: By Title.

- Sort: By Creation Date, Due Date, Status, Priority, or Title.

- Metrics: Total Tasks, Open Tasks, Completed Tasks.

- Export: Download data to Excel.

### Excel Export Requirements

- The file must reflect the currently applied filters and sorting.

- Clear column headers and consistent date formatting.

- Filename must include the generation timestamp.

- User-friendly message if there is no data to export.

### Backend & Data Requirements for Reporting

- APIs to support filtering, searching, sorting, and metric aggregation.

- The architectural decision of whether to generate the Excel file on the Frontend or Backend is left to the development team.
