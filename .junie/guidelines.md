# Teamwork Challenge Platform Developer Guidelines

## Project Structure

The project is organized into several key components:

- **Backend API** (`/back`): FastAPI-based REST API for managing challenges, rounds, teams, tasks, and submissions
- **Command Line Interface** (`/cli`): Python-based CLI for interacting with the platform
- **Task Generators** (`/tasks`): REST APIs that generate tasks and validate solutions
- **API Models** (`/api_models`): Shared data models used across components
- **Documentation** (`/docs`): Detailed project documentation

## Tech Stack

- **Language**: Python 3.11
- **Backend**: FastAPI, SQLAlchemy ORM, Mangum (for AWS Lambda)
- **Database**: AWS Aurora Serverless PostgreSQL
- **CLI**: Typer for command handling
- **Testing**: pytest
- **Deployment**: AWS Lambda, API Gateway, SAM CLI

## Setting Up Development Environment

1. Install Python 3.11../
2. Create a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements-dev.txt
   ```
4. For AWS access:
   - Install AWS CLI
   - Configure with `aws configure` (get credentials from AWS admin)
   - Verify with `aws sts get-caller-identity`

## Running Components

### Backend API

1. Navigate to `/back` directory
2. Run locally:
   ```
   python main.py
   ```
3. Access at:
   - API: http://localhost:8088
   - Swagger UI: http://localhost:8088/docs
   - ReDoc: http://localhost:8088/redoc

### CLI

1. Navigate to `/cli` directory
2. Run commands:
   ```
   python main.py [COMMAND] [SUBCOMMAND] [OPTIONS]
   ```

### Task Generators

Task generators are organized in separate folders under `/tasks`.

## Running Tests

1. For CLI tests:
   ```
   cd cli
   pytest test_cli.py
   ```
2. For database tests:
   ```
   cd back
   python database_aws_tests.py
   ```

## Deployment

### Backend and Task Generators

1. Install AWS SAM CLI
2. Build:
   ```
   cd back  # or tasks
   sam build
   ```
3. Deploy:
   ```
   sam deploy
   ```

## Best Practices

1. **Code Organization**:
   - Keep components modular and focused
   - Follow the established directory structure
   - Use dependency injection for services

2. **API Development**:
   - Use shared API models from `api_models`
   - Follow RESTful principles
   - Include proper error handling with appropriate HTTP status codes
   - Document endpoints with docstrings

3. **Testing**:
   - Write tests for new functionality
   - Run tests before submitting changes

4. **Git Workflow**:
   - Make focused commits with clear messages
   - Create feature branches for new development
   - Submit pull requests for review