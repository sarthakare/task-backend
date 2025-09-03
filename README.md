# Task Manager Backend API

A FastAPI-based backend for the Task Manager application with user management capabilities.

## Features

- User authentication and authorization
- User management (CRUD operations)
- Role-based access control
- Department and role management
- Supervisor assignment system
- Password hashing and security

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file with:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/taskmanager
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. **Run database migrations:**
   ```bash
   python create_tables.py
   ```

4. **Start the server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration

### Users
- `GET /users/` - Get all users
- `GET /users/active` - Get active users only
- `GET /users/{user_id}` - Get specific user
- `POST /users/` - Create new user
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Soft delete user

### User Management
- `GET /users/supervisors/` - Get available supervisors
- `GET /users/departments/` - Get available departments
- `GET /users/roles/` - Get available roles
- `GET /users/stats/` - Get user statistics

## User Creation

To create a new user, send a POST request to `/users/` with:

```json
{
  "name": "John Doe",
  "email": "john.doe@company.com",
  "mobile": "+1234567890",
  "password": "securepassword123",
  "department": "engineering",
  "role": "member",
  "supervisor_id": 1
}
```

## Available Departments
- engineering
- marketing
- sales
- hr
- finance
- operations
- it

## Available Roles
- admin
- manager
- supervisor
- team_lead
- member
- intern

## Supervisor System

Only users with roles `admin`, `manager`, `supervisor`, or `team_lead` can be assigned as supervisors to other users.

## Testing

Run the test script to verify all endpoints:
```bash
python test_api.py
```

## Database Schema

The main `users` table includes:
- id (Primary Key)
- name
- email (Unique)
- mobile
- hashed_password
- department
- role
- supervisor_id (Foreign Key to users.id)
- is_active
- created_at
- updated_at

## Security Features

- Password hashing using bcrypt
- JWT token-based authentication
- CORS configuration for frontend integration
- Input validation using Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
