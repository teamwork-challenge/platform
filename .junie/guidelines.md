Teamwork Challenge Platform — Developer Quick Guidelines

Audience: new contributors. Keep this handy. Commands are shown for Windows PowerShell.

1) Tech stack at a glance
- Language: Python 3.11 (strict typing via mypy)
- Backend: FastAPI + Uvicorn, SQLAlchemy ORM, Pydantic models (api_models package), Mangum (AWS Lambda adapter)
- CLI: Typer + Rich + Requests
- Tasks (generators): FastAPI-based microservices
- Tests: pytest (CLI tests spin up the API locally)

2) Repository layout (platform\)
- back\ — FastAPI backend (routers, services, db models, entry point back.main)
- cli\ — CLI client (Typer apps grouped by domain, entry point cli.main)
- api_models\ — Shared Pydantic models (import as from api_models import ...)
- tasks\ — Task generator services (optional for local dev)
- docs\ — Project documentation

3) Local setup
- Create venv and install deps:
  - py -3.11 -m venv .venv
  - .\.venv\Scripts\Activate.ps1
  - pip install -r back\requirements-dev.txt
  - pip install -r cli\requirements-dev.txt
  - (optional) pip install -r tasks\requirements-dev.txt
- Type checking: mypy back cli (strict mode set in mypy.ini)

4) Running the backend locally
- Option A (module): python -m back.main
  - Default port in back.main when run as __main__: 8089 (Swagger at http://127.0.0.1:8089/docs)
- Option B (uvicorn): uvicorn back.main:app --reload --port 8088
- Set the CLI to talk to your backend:
  - $env:CHALLENGE_API_URL = "http://127.0.0.1:8088"  # or 8089, to match your server

5) Using the CLI
- From repository root:
  - python -m cli.main --help
  - python -m cli.main login <API_KEY>
  - Commands are grouped by domain: team, round, task, task-type, board
  - Every command supports --json for machine-friendly output
- Config location: %USERPROFILE%\.challenge\config.json (stores API key)

6) Running tests
- Tests currently live under cli\ (pytest). They self-start a backend via uvicorn.
- Important: run pytest from the cli\ directory so relative paths work:
  - cd cli
  - pytest -q
- The test fixture sets $env:CHALLENGE_API_URL to the test server port automatically.

7) How to add features
- Backend (back\):
  - Add or extend a router under back\api_*.py and wire it in back\main.py via app.include_router(...)
  - Put business logic in services (e.g., player_service.py), keep routers thin
  - Reuse shared models from api_models; do not duplicate schemas
- CLI (cli\):
  - Create a new <domain>_app.py with typer.Typer(...)
  - Add API calls in cli\api_client.py
  - Register your app in cli\main.py with app.add_typer(..., name="<domain>")
  - Support --json via cli.formatter.print_as_json and json_output_option

8) Conventions and best practices
- Type hints everywhere; keep mypy green (strict mode)
- Separate layers: API (routers) -> service (business logic) -> data (SQLAlchemy models)
- Keep CLI commands thin: fetch with ApiClient, print either JSON or Rich-formatted table
- Use environment variables for config (e.g., CHALLENGE_API_URL), avoid hardcoding
- Handle errors explicitly and return helpful messages to users
- Small PRs, meaningful commit messages, and add/adjust tests for new behavior

9) Useful commands (PowerShell)
- Activate venv: .\.venv\Scripts\Activate.ps1
- Start API: uvicorn back.main:app --reload --port 8088
- Run CLI sample: python -m cli.main round list --json
- Run mypy: mypy back cli
- Run tests: cd cli; pytest -q

10) Troubleshooting
- CLI says “Not logged in”: run python -m cli.main login <API_KEY>
- CLI can’t reach API: ensure CHALLENGE_API_URL matches your running port and API is up
- Pydantic version issues: api_models uses Pydantic v2-style APIs; ensure editable install from requirements-dev is applied
