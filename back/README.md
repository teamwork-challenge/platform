# FastAPI Demo Application for Teamwork Challenge Platform

## Overview

This is a simple FastAPI demo application that provides basic endpoints for managing challenges and tasks. It serves as a starting point for the Teamwork Challenge Platform backend.

## Features

- Simple in-memory database for challenges and tasks
- RESTful API endpoints for retrieving and creating data
- Data validation using Pydantic models

## Installation

1. Make sure you have Python 3.7+ installed
2. Install FastAPI and Uvicorn:
   ```bash
   pip install fastapi uvicorn
   ```

## Running the API

To run the API locally:

```bash
uvicorn main:app --reload
```

Once running, you can access:
- API at: `http://localhost:8000`
- Swagger UI documentation at: `http://localhost:8000/docs`
- ReDoc documentation at: `http://localhost:8000/redoc`

## API Endpoints

### Test Endpoint
- `GET /` - Test endpoint that returns a simple message

### Admin Endpoints
- `GET /challenges` - Get all challenges
- `GET /challenges/{challenge_id}` - Get a specific challenge by ID

### Player Endpoints
- `GET /tasks/{task_id}` - Get a specific task by ID
- `POST /tasks` - Create a new task

## Data Models

### Challenge (In-memory)
- id: int
- title: string

### Task (In-memory)
- id: int
- title: string
- status: string

### Task (Request Model)
- title: string
- status: string (defaults to "PENDING")

## Example Usage

### Get all challenges
```bash
curl -X GET "http://localhost:8000/challenges"
```

### Get a specific challenge
```bash
curl -X GET "http://localhost:8000/challenges/1"
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
