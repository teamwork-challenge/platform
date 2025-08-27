# Teamwork Challenge Platform: Backend API

## Overview

The Backend API is a core component of the Teamwork Challenge Platform, providing RESTful endpoints for managing challenges, rounds, teams, tasks, and submissions. It serves as the central hub for all platform interactions, enabling both administrative functions and player activities.

## Architecture

The backend is built with FastAPI, a modern, high-performance web framework for building APIs with Python. The architecture follows a layered approach:

- **API Layer**: Handles HTTP requests and responses
- **Service Layer**: Implements business logic
- **Data Layer**: Firebase Firestore (via official Python SDK)

## Installation

1. Install the dependencies to be able to build and run the API:
   ```powershell
   back> pip install -r requirements.txt
   ```

## Running the API locally

Use the Firebase Emulator Suite for local development. The app will auto-connect to the emulator if available.

From repository root:

```powershell
platform> python -m back.main
```

- Default port (when run as module): 8089
- Swagger UI: http://127.0.0.1:8089/docs

Alternatively with uvicorn:

```powershell
platform> uvicorn back.main:app --reload --port 8088
```

Configure CLI or clients to use the chosen port (set CHALLENGE_API_URL accordingly).

## Firebase (local dev)

- Ensure you have the Firebase Emulator installed (see Firebase docs) or use the repo-provided config files (firebase.json, firestore.rules, firestore.indexes.json).
- When the emulator is running, the backend uses it automatically; no real GCP project is required for local dev.

## Type checking

From repository root:

```powershell
platform> mypy -c mypy.ini back
```

## More details

- Backend endpoints and behavior: [Backend Documentation](../docs/3-Backend.md)
- Migration details and Firestore data model: [Migration to Firebase](../docs/6-Migration-to-Firebase.md)
