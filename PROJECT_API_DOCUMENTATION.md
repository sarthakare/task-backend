# Project Management API Documentation

## Overview
The Project Management API provides endpoints for creating, reading, updating, and deleting projects, as well as managing project team assignments.

## Base URL
`http://localhost:8000` (development)

## Endpoints

### 1. Get All Projects
- **URL**: `GET /projects/`
- **Description**: Retrieve all projects with their managers and assigned teams
- **Response**: Array of project objects with full details

### 2. Get Project by ID
- **URL**: `GET /projects/{project_id}`
- **Description**: Retrieve a specific project by its ID
- **Response**: Project object with full details

### 3. Create Project
- **URL**: `POST /projects/`
- **Description**: Create a new project
- **Request Body**:
```json
{
  "name": "E-commerce Platform",
  "description": "Modern e-commerce platform with advanced features",
  "manager_id": 1,
  "assigned_teams": [1, 2, 3],
  "start_date": "2024-01-15T00:00:00Z",
  "end_date": "2024-06-15T00:00:00Z",
  "status": "active"
}
```
- **Response**: Created project object with ID

### 4. Update Project
- **URL**: `PUT /projects/{project_id}`
- **Description**: Update an existing project
- **Request Body**: Same as create, but all fields are optional

### 5. Delete Project
- **URL**: `DELETE /projects/{project_id}`
- **Description**: Delete a project
- **Response**: 204 No Content

### 6. Get Project Teams
- **URL**: `GET /projects/{project_id}/teams`
- **Description**: Get all teams assigned to a specific project
- **Response**: Array of team objects with project role information

### 7. Add Team to Project
- **URL**: `POST /projects/{project_id}/teams`
- **Description**: Add a team to a project
- **Request Body**:
```json
{
  "team_id": 4
}
```

### 8. Remove Team from Project
- **URL**: `DELETE /projects/{project_id}/teams/{team_id}`
- **Description**: Remove a team from a project
- **Response**: 204 No Content

### 9. Get Project Statistics
- **URL**: `GET /projects/stats/`
- **Description**: Get project statistics
- **Response**:
```json
{
  "total_projects": 10,
  "active_projects": 6,
  "completed_projects": 3,
  "on_hold_projects": 1,
  "cancelled_projects": 0,
  "manager_counts": {
    "John Doe": 3,
    "Jane Smith": 2,
    "Bob Johnson": 1
  }
}
```

## Data Models

### Project Object
```json
{
  "id": 1,
  "name": "E-commerce Platform",
  "description": "Modern e-commerce platform with advanced features",
  "manager_id": 1,
  "start_date": "2024-01-15T00:00:00Z",
  "end_date": "2024-06-15T00:00:00Z",
  "status": "active",
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "manager": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "manager",
    "department": "engineering"
  },
  "assigned_teams": [
    {
      "id": 1,
      "name": "Frontend Team",
      "department": "engineering",
      "leader": {
        "id": 2,
        "name": "Alice Smith"
      },
      "members": [...]
    }
  ]
}
```

## Project Status Values

- **active**: Project is currently running
- **on_hold**: Project is temporarily paused
- **completed**: Project has been successfully finished
- **cancelled**: Project has been terminated

## Business Rules

1. **Project Name**: Must be unique across all projects
2. **Project Manager**: Must be an active user
3. **Assigned Teams**: All teams must be active
4. **Date Range**: End date must be after start date
5. **Status**: Must be one of the valid status values
6. **Team Assignment**: Teams can be assigned to multiple projects

## Validation Rules

### Create/Update Project
- **name**: Required, must be unique
- **description**: Required
- **manager_id**: Required, must be valid active user
- **assigned_teams**: Optional, must be array of valid active team IDs
- **start_date**: Required, must be valid ISO datetime
- **end_date**: Required, must be after start_date
- **status**: Optional, defaults to "active"

### Date Validation
- Start date cannot be in the past (for new projects)
- End date must be after start date
- Both dates must be valid ISO datetime strings

## Error Responses

- **400 Bad Request**: Invalid data (duplicate name, invalid dates, inactive teams, etc.)
- **404 Not Found**: Project or team not found
- **422 Unprocessable Entity**: Validation errors

## Testing

Run the test script to validate all endpoints:
```bash
cd task-backend
python test_project_api.py
```

Make sure the FastAPI server is running before testing:
```bash
cd task-backend
python -m uvicorn main:app --reload
```

## Dependencies

Projects depend on:
- **Users** (for project managers)
- **Teams** (for team assignments)

Make sure users and teams exist before creating projects.

## API Integration

The frontend Project Management page integrates with these endpoints:
- Creates projects via `POST /projects/`
- Displays projects via `GET /projects/`
- Shows statistics via `GET /projects/stats/`
- Updates projects via `PUT /projects/{id}`

All endpoints return consistent JSON responses and proper HTTP status codes for easy frontend integration.
