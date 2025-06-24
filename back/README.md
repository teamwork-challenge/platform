# Teamwork Challenge Platform: Backend API

## Overview

The Backend API is a core component of the Teamwork Challenge Platform, providing RESTful endpoints for managing challenges, rounds, teams, tasks, and submissions. It serves as the central hub for all platform interactions, enabling both administrative functions and player activities.

## Architecture

The backend is built with FastAPI, a modern, high-performance web framework for building APIs with Python. The architecture follows a layered approach:

- **API Layer**: Handles HTTP requests and responses
- **Service Layer**: Implements business logic
- **Repository Layer**: Manages data access and storage

## Installation

1. Install the dependencies to be able to build and run the API:
   ```bash
   pip install -r requirements.txt
   ```
2. Install AWS CLI. https://aws.amazon.com/cli/
3. Ask AWS admin for Access Key Name, Access Key Secret and Region Name. Use them to configure AWS CLI:
   ```bash
   aws configure
   ```
4. Run test in database_aws_tests.py to check the connection to the could database:
 

## Running the API

   ```bash
   cd back
   uvicorn main:app --reload
   ```

Once running, you can access:
- API at: `http://localhost:8000`
- Swagger UI documentation at: `http://localhost:8000/docs`
- ReDoc documentation at: `http://localhost:8000/redoc`

## More details

See [Backend Documentation](../docs/2-Backend.md) in the docs directory.
