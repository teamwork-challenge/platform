# Teamwork Challenge Platform: Backend API

## Overview

The Backend API is a core component of the Teamwork Challenge Platform, providing RESTful endpoints for managing challenges, rounds, teams, tasks, and submissions. It serves as the central hub for all platform interactions, enabling both administrative functions and player activities.

## Architecture

The backend is built with FastAPI, a modern, high-performance web framework for building APIs with Python. The architecture follows a layered approach:

- **API Layer**: Handles HTTP requests and responses
- **Service Layer**: Implements business logic
- **Repository Layer**: Manages data access and storage


## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:
   ```bash
   pip install fastapi uvicorn
   ```

## Running the API

To run the API locally:

1. Navigate to the 'back' directory:
   ```bash
   cd back
   ```

2. Start the Uvicorn server:
   ```bash
   uvicorn main:app --reload
   ```

Alternatively, you can run the API from the root directory:

```bash
uvicorn back.main:app --reload
```

Once running, you can access:
- API at: `http://localhost:8000`
- Swagger UI documentation at: `http://localhost:8000/docs`
- ReDoc documentation at: `http://localhost:8000/redoc`

## API Endpoints

### Admin Endpoints
- `GET /challenges` - Get all challenges
- `POST /challenges` - Create a new challenge
- `GET /challenges/{challenge_id}` - Get a specific challenge by ID
- `PUT /challenges/{challenge_id}` - Update a specific challenge
- `DELETE /challenges` - Delete all challenges

### Player Endpoints
- `GET /tasks/{task_id}` - Get a specific task by ID
- `POST /tasks` - Create a new task


## Example Usage

### Get all challenges
```bash
curl -X GET "http://localhost:8000/challenges"
```

### Create a new challenge
```bash
curl -X POST "http://localhost:8000/challenges" \
  -H "Content-Type: application/json" \
  -d '{"title": "New Challenge 2025"}'
```

### Get a specific task
```bash
curl -X GET "http://localhost:8000/tasks/1"
```

### Create a new task
```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "New task", "status": "PENDING"}'
```

## Development

For more detailed information about the backend architecture, data models, and API design, please refer to the [Backend Documentation](/docs/3-Backend.md) in the docs directory.
