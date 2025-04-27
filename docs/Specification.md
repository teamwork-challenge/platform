# Specification

## Terms
Challenge – the top-level contest. A Challenge groups one or more Rounds, and have a set of teams - participants. ​
Round – a time-boxed phase inside a Challenge. Every Round starts and ends at scheduled timestamps and defines the set of Task Types, and other settings.​

Task Type – a template that describes how tasks of that kind are generated, what they ask the solver to produce, and how they are scored. A single Round can expose several Task Types so teams can split work. ​

Task – a concrete instance of a Task Type generated for a particular Team during a Round. It contains an input payload, a deadline, current status (CLAIMED | AC | WA). ​

Submission – one attempt by a Team to solve a Task. A Submission stores the answer payload, timestamp, validation status (AC | WA), and the score awarded by the validator. ​

Claim – the API action that asks the platform to generate and assign a new Task to a Team. If claim-by-type is true, the request must include the desired Task Type.

Team – an identified group of students within a Challenge. Each Team has a unique ID, a name and issued API key. ​

Leaderboard – a Round-specific or Challenge-wide ranking that orders Teams by their total score (ties broken by earliest achievement).


## Student User Stories

- S-P1 As a student, I want to edit our team name.
- S-T1 As a student, I want to claim a task so my team can solve it.
- S-T2 As a student, I want to submit a solution and instantly know if it passed with explanation if not.
- S-D1 As a student, I want to view my team’s recent submissions and scores so we can check that everything works fine.
- S-D2 As a student, I want to see the round leaderboard to track our ranking and compare with other teams.

## Admin User Stories

- A-S1 As an admin, I want to set up new challenge.
- A-S2 As an admin, I want to configure a round by preparing a task generator and settings.
- A-S3 As an admin, I want to create API keys for each team.
- A-S4 As an admin, I want to publish a round in the challenge, so that students can start it on time.
- A-M1 As an admin, I want to watch a live log of submissions to spot issues early.
- A-S1 As an admin, I want to impersonate any team.
- A-M2 As an admin, I want to suspend a round to investigate occured incidents.
- A-M3 As an admin, I want to find a submission by its ID.
- A-M4 As an admin, I want to change status and score of any particular submit as a react on incidents.

# Requirements

## UI

- Web application for humans.
- REST API for automated solvers.
- Starter Kits for automated solvers:
  - in Python
  - in Kotlin

## Entities

### Round

- id
- challengeId
- index — order in challenge
- start time
- end time
- claim-by-type: Boolean — should players specify task-type to claim new task?
- allow-resubmit — can player resubmit an answer after receiving WRONG status. (For test round)
- score-decay: no|linear
- max-score-decay: no|linear
- task-types — visible after round started.

### Challenge

- id — unique identifier of the challenge
- title — short human‑readable name
- description — markdown text shown on the lobby screen
- current‑round‑id — id of the round that is currently open, or null

### Team

- id (UUID) — unique identifier of the team
- challenge‑id — foreign key to Challenge
- name — team‑selected display name (editable until the first submission)
- api‑key — key issued to the team for authentication
- members — free‑form string with GitHub handles / names (optional)
- total‑score — sum of best‑per‑task scores within the active challenge

### Task

- id (UUID)
- round‑id — foreign key to Round
- team‑id — foreign key to Team
- type — task‑type code (matches definitions in Round.task‑types)
- input‑payload — JSON or binary blob provided to the solver
- status — CLAIMED | AC | WA
- last‑answer‑id — id of the most recent Submission
- max-score — score achieved so far (null until evaluated)
- score
- claimed‑at — timestamps
- expired-at — timestamp when score reaches zero
- list of submission

### Submission
- id (UUID)
- task-id
- answer
- submitted-at
- status — AC | WA
- score

## Behaviour

### Claiming task

1. Generates a task instance. 
2. Stores the generated task.
3. Returns id, statement, input data, scoring formula, and deadline.
4. Returns HTTP 400 if incompatible claim-mode was used.

Teams may hold several open tasks at once.

The task generators should attempt to supply each team with a unique instance; 
identical tasks may occur only by statistical coincidence.

### Answer Validation 

- Validate payload format; malformed → 400 Bad Request (attempt not counted, not stored, but logged).
- Run sandboxed validator; produce status OK or WRONG and, if wrong, an explanation.
- Calculate score from correctness and time remaining before the task deadline.
- Persist submission record.
- Respond with JSON {status, score, explanation} and 200 OK.

## Authentication

All API calls must include a valid API_KEY header.

Missing or invalid keys return 401 Unauthorized.
Authentication determines roles: admin or player and a challenge.

## REST API Endpoints

### For Player

GET|PUT /teams/me
GET /rounds
GET /tasks?round={id}[&type={type}&status={status}] - dashboard
POST /tasks?round={id}[&type={task-type}] - claim task
GET  /tasks/{id}
POST /tasks/{id}/answer - submit solution
GET /rounds/{id}/leaderboard

Note: teamId and challengeId is defined by authentication and filters and validators applied when it make sense.

### For Admin

GET|POST|DELETE /challenges
GET|PUT /challenges/{id}
GET /rounds?challenge={id}
GET|POST|PUT|DELETE /rounds/{id}
GET|PUT /teams?challenge={id}
GET /round/{id}/logs
PUT /tasks/{id}/answer - override answer verdict, for incidents.

Note: challengeId should be specidfied 

## Deadline handling

Submissions after a task-specific deadline score 0 but are still evaluated for status. Claiming and submitting before round start or after round end returns 403 Forbidden.

## Logging

Every task-related action — claim, submit, status update — is written to an immutable audit log with timestamp, team id, task id, status, and score.

## Rate limits

The API must sustain at least 20 concurrent submissions and throttle a team to 10 task claims per minute; excess requests return 429 Too Many Requests.

## Performance

Any API request must return within 1 s at the 95-th percentile.

6 task types ✕ 1000 tasks ✕ 20 teams ✕ 2 answers = 240_000 records per round in answers DB table.

The platform must handle at least 20 concurrently active students who may poll, claim, and submit in a tight loop (≈50 req/s aggregate) without breaching the latency target.

- Probably cache leaderboard parts.
- Indexes for dashboard should be used.

# Technological stack and deployment

## Frontend

React + TypeScript built with Vite.
Static assets live in an object S3-bucket behind the provider’s CDN. 

## Backend

Python 3.12 + FastAPI, packaged as a single Docker image and run in a serverless runtime (AWS Lambda via API Gateway or Google Cloud Run).

## Data layer

PostgreSQL in its serverless flavour (Aurora Serverless v2 / Cloud SQL auto-scale) stores rounds, tasks, teams, and submissions.

S3 buckets keep task input payloads, answers, and nightly-exported audit logs.

## Security & limits

API Gateway checks API-Key headers and enforces the “10 task claims per minute” rule. All task-related actions are inserted into an append-only audit table for later analysis.

## Observability

Cloud-native metrics and traces (CloudWatch + X-Ray or Cloud Monitoring + Cloud Trace) with alerts on p95 latency and error spikes.

## CI/CD & IaC

GitHub Actions builds, tests, and pushes the image; Terraform provisions the runtime, database, cache, and bucket, so a full environment spins up—or down—with a single command.

# Web App UI/UX Design

TODO

# OpenAPI spec

TODO

# Task generators and validator API

TODO

