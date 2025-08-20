# Teamwork Challenge Platform: Backend API

## Overview

The Backend API is a core component of the Teamwork Challenge Platform, providing RESTful endpoints for managing challenges, rounds, teams, tasks, and submissions. It serves as the central hub for all platform interactions, enabling both administrative functions and player activities.

## Architecture

The backend is built with FastAPI, a modern, high-performance web framework for building APIs with Python. The architecture follows a layered approach:

- **API Layer**: Handles HTTP requests and responses
- **Service Layer**: Implements business logic
- **Alchemy ORM** as data layer

## Installation

1. Install the dependencies to be able to build and run the API:
   ```bash
   back> pip install -r requirements-dev.txt
   ```

## Running the API locally

In the root directory:

   ```bash
   platform> cd back & python -m main
   ```
## Type checking

In the root directory:

   ```bash
   platform> mypy back
   ```

Once running, you can access:
- API at: `http://localhost:8000`
- Swagger UI documentation at: `http://localhost:8000/docs`
- ReDoc documentation at: `http://localhost:8000/redoc`

## More details

See [Backend Documentation](../docs/2-Backend.md) in the docs directory.
