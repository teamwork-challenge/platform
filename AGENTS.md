Teamwork Challenge Platform — Developer Quick Guidelines

Audience: new contributors. Keep this handy. Commands are shown for Windows PowerShell.

## Tech stack at a glance
- Language: Python 3.11 (strict typing via mypy)
- Backend: FastAPI + Uvicorn, Firebase
- CLI: Typer + Rich + Requests
- Tasks (generators): FastAPI-based microservices
- Tests: pytest (CLI tests spin up the API locally)

## Repository layout (platform\)
- back\ — FastAPI backend (routers, services, db models, entry point back.main)
- cli\ — CLI client (Typer apps grouped by domain, entry point cli.main)
- api_models\ — Shared Pydantic models (import as from api_models import ...)
- tasks\ — Task generator services (optional for local dev)
- docs\ — Project documentation

## Local setup
- Create venv and install deps:
  - `py -3.11 -m venv .venv`
  - `platform> .\.venv\Scripts\Activate.ps1`
  - `platform> cd back & pip install -r \requirements-dev.txt`
  - `platform> cd cli & pip install -r \requirements-dev.txt`
  - (optional) `platform> cd tasks & pip install -r \requirements-dev.txt`
- Type checking: `mypy -c mypy.ini back cli`
- Type checking for tasks: `mypy -c mypy.ini back cli tasks`
- Run tests: `platform> cd cli; pytest -q`
- Start API: `platform> python -m back.main`
- Run CLI sample: `platform> python -m cli.main round list --json`



## Running the backend locally
- Option A (module): python -m back.main
  - Default port in back.main when run as __main__: 8089 (Swagger at http://127.0.0.1:8089/docs)
- Option B (uvicorn): uvicorn back.main:app --reload --port 8088
- Set the CLI to talk to your backend:
  - $env:CHALLENGE_API_URL = "http://127.0.0.1:8088"  # or 8089, to match your server

## Using the CLI
- From repository root:
  - python -m cli.main --help
  - python -m cli.main login <API_KEY>
  - Commands are grouped by domain: team, round, task, task-type, board
  - Every command supports --json for machine-friendly output
- Config location: %USERPROFILE%\.challenge\config.json (stores API key)

## Running tests
- Tests currently live under cli\ (pytest). They self-start a backend via uvicorn.
- Important: run pytest from the cli\ directory so relative paths work:
  - cd cli
  - pytest -q
- The test fixture sets $env:CHALLENGE_API_URL to the test server port automatically and run server on this port.

## How to add features
- Backend (back\):
  - Add or extend a router under back\api_*.py and wire it in back\main.py via app.include_router(...)
  - Put business logic in services (e.g., player_service.py), keep routers thin
  - Reuse shared models from api_models; do not duplicate schemas
- CLI (cli\):
  - Create a new <domain>_app.py with typer.Typer(...)
  - Add API calls in cli\api_client.py
  - Register your app in cli\main.py with app.add_typer(..., name="<domain>")
  - Support --json via cli.formatter.print_as_json and json_output_option

## Conventions and best practices
- Type hints everywhere; keep mypy green (strict mode)
- Separate layers: API (routers) -> service (business logic) -> data (SQLAlchemy models)
  - Keep CLI commands thin: fetch with ApiClient, print either JSON or Rich-formatted table
- Use environment variables for config (e.g., CHALLENGE_API_URL), avoid hardcoding
- Handle errors explicitly and return helpful messages to users
  - Do not hide technical details in CLI output: stack traces, errors from API should be visible.
  - Do not catch exceptions in CLI only to hide technical details; let them bubble up.
- Small PRs, meaningful commit messages, and add/adjust tests for new behavior
- Always run mypy and tests when the task is done
- Do not commit changes automatically unless you were asked to do so
