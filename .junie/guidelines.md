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
  - `py -3.11 -m venv venv`
  - `platform> .\venv\Scripts\Activate.ps1`
  - `platform> pip install -r \requirements.txt`
- Type checking: `mypy .`
- Run tests: `platform> py -m pytest`
- Start API Locally: `platform>  python -m back.main dev`
- Run CLI sample: `platform> python -m cli.main round list`


## Using the CLI
- Config location: %USERPROFILE%\.challenge\config.json (stores API key, backend url, port)


## How to add features
- Backend (back\):
  - Add or extend a router under back\api\*_api.py and wire it in back\main.py via app.include_router(...)
  - Put business logic in services (e.g., *_service.py)
  - Reuse shared models from api_models; do not duplicate schemas
- CLI (cli\):
  - Create a new <domain>_app.py with typer.Typer(...)
  - Add API calls in cli\api_client.py
  - Register your app in cli\main.py with app.add_typer(..., name="<domain>")
  - Support --json via cli.formatter.print_as_json and json_output_option

## Conventions and best practices
- Type hints everywhere; keep mypy green (strict mode)
- Separate layers: API (routers) -> service (business logic)
  - Keep CLI commands thin: fetch with ApiClient, print either JSON or Rich-formatted table
- Use environment variables for config (e.g., CHALLENGE_API_URL), avoid hardcoding
- Handle errors explicitly and return helpful messages to users
  - Do not hide technical details in CLI output: stack traces, errors from API should be visible.
  - Do not catch exceptions in CLI only to hide technical details; let them bubble up.
- Always run mypy and tests when the task is done
- Do not commit changes automatically unless you were asked to do so
- Document all nontrivial decisions made in the docs directory in the appropriate file and section.
- Keep the docs folder up-to-date.
