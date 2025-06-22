# Teamwork Challenge Platform

A comprehensive platform for hosting programming teamwork challenges designed to help freshman CS and SE students learn teamwork by doing.

## Overview

The Teamwork Challenge Platform is designed to create an intensive, game-like programming experience that immerses students in real collaboration. The platform hosts challenges that run in 4-hour rounds, feeling like mini-hackathons, where teams must distribute tasks, collaborate using Git, handle uncertainty, and mitigate technical risks.

### Key Features

- **Round-based Challenges**: Challenges run in 4-hour rounds that feel like mini-hackathons
- **Task Distribution**: Each round contains several task types, encouraging teams to split work
- **Dynamic Task Generation**: Tasks are generated on the fly, nudging students to automate repeated steps
- **Intentional Incompleteness**: Task statements are intentionally incomplete to encourage experimentation and knowledge sharing
- **Integration Requirements**: Later tasks require integrating earlier solutions, reinforcing Git workflow
- **Structured Retrospectives**: Teams analyze and improve their process after every round

## Components

The platform consists of several components:

1. **Backend API**: A FastAPI-based REST API that manages challenges, rounds, teams, tasks, and submissions
2. **Command Line Interface**: A Python-based CLI for interacting with the platform
3. **Task Generators**: REST APIs that generate tasks and validate solutions

## Installation

### Backend

1. Navigate to the `back` directory
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn
   ```
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

   Alternatively, from the root directory:
   ```bash
   uvicorn back.main:app --reload
   ```

### CLI Client

1. Navigate to the `cli` directory
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the CLI:
   ```bash
   python main.py [COMMAND] [OPTIONS]
   ```

## Usage

### Backend API

Once the backend is running, you can access:
- API at: `http://localhost:8000`
- Swagger UI documentation at: `http://localhost:8000/docs`
- ReDoc documentation at: `http://localhost:8000/redoc`

The API provides endpoints for:
- Managing challenges and rounds
- Team registration and management
- Task claiming and submission
- Leaderboard and dashboard views

### CLI Client

The CLI provides commands for:
- Authentication and team management
- Challenge and round information
- Task workflow (claiming, viewing, submitting)
- Scores and rankings

Example usage:
```bash
# Login with your API key
python main.py login <API_KEY>

# Claim a new task
python main.py task claim

# Submit a solution
python main.py task submit <TASK_ID> <ANSWER>
```

## Documentation

For more detailed information, see the documentation in the `/docs` directory:

- [Vision & Goals](/docs/1-Vision.md): Project vision and goals
- [Specification](/docs/2-Specification.md): Detailed specifications
- [Backend](/docs/3-Backend.md): Backend API details
- [CLI](/docs/4-CLI.md): Command Line Interface details
- [Task Generators](/docs/5-TaskGenerators.md): Task generator API details

## Component-Specific Documentation

- [Backend README](/back/README.md): Backend setup and usage
- [CLI README](/cli/README.md): CLI setup and usage
- [Tasks README](/tasks/README.md): Task generator information
