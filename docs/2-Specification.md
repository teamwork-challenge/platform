# Specification

## Components

- Platform backend REST API
- Command line client application, working via REST API.
- Optional: web app, working via REST API
- Task generators as REST APIs

## Terms

Challenge – the top-level contest. A Challenge groups one or more Rounds, and have a set of teams - participants. ​
Round – a time-boxed phase inside a Challenge. Every Round starts and ends at scheduled timestamps and defines the set of Task Types, and other settings.​

Task Type – a template that describes how tasks of that kind are generated, what they ask the solver to produce, and how they are scored. A single Round can expose several Task Types so teams can split work. ​

Task – a concrete instance of a Task Type generated for a particular Team during a Round. It contains an input payload, a deadline, current status (PENDING | AC | WA). ​

Submission – one attempt by a Team to solve a Task. A Submission stores the answer payload, timestamp, validation status (AC | WA), and the score awarded by the validator. ​

Claim – the API action that asks the platform to generate and assign a new Task to a Team. If claim-by-type is true, the request must include the desired Task Type.

Team – an identified group of players within a Challenge. Each Team has a unique ID, a name and issued API key. ​

Leaderboard – a Round-specific or Challenge-wide ranking that orders Teams by their total score (ties broken by earliest achievement).

## User Stories

### Players

1. As a player, I want to edit our team name. (optional)
2. As a player, I want to claim a task so my team can solve it.
3. As a player, I want to submit a solution and instantly know if it passed with explanation if not.
4. As a player, I want to view my team’s recent submissions and scores so we can check that everything works fine.
5. As a player, I want to see the round leaderboard to track our ranking and compare with other teams.

### Admin

1. As an admin, I want to set up new challenge.
1. As an admin, I want to configure a round by preparing a task generator and settings.
1. As an admin, I want to create an API key for each team.
1. As an admin, I want to publish a round in the challenge, so that players can start it on time.
1. As an admin, I want to watch a live log of submissions to spot issues early.
1. As an admin, I want to impersonate any team.
1. As an admin, I want to suspend a round to investigate occured incidents.
1. As an admin, I want to find a submission by its ID.
1. As an admin, I want to change status and score of any particular submit as a react on incidents.

## Entities

### Round

- id
- challenge_id
- index — order in challenge
- status
- start time
- end time
- claim-by-type: Boolean — should players specify task-type to claim new task?
- allow-resubmit — can player resubmit an answer after receiving WRONG status. (For test round)
- score-decay: no|linear
- task-types — visible after round started.

### RoundTaskType

- id
- round_id
- type — task-type code
- generator_url — URL of the task generator API
- generator_settings — JSON object with settings for the task generator
- generator_secret — secret key for the task generator API

### Challenge

- id
- title
- description — markdown
- current‑round‑id — id of the round that is currently open, or null

### Team

- id
- challenge‑id
- name
- api‑key
- members
- total‑score

### Task

- id
- round‑id
- team‑id
- type — task‑type code (matches definitions in Round.task‑types)
- input‑payload
- status — PENDING | AC | WA
- possible-score — max scrore that could be achieved
- score — achieved score for AC task
- claimed‑at — timestamp
- expired-at — timestamp when score reaches zero
- list of submission

### Submission

- id
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

# Technological stack and deployment

## Backend

- Python + FastAPI
- OpenAPI and Swagger UI for API documentation.
- Deployment: AWS Lambda (Magnum wrapper for FastAPI) + API Gateway.

## Command Line Interface

- Python + Typer for commands and options handling
- openapi-python-client for http client generation by OpenAPI spec.

## Task generators

- Python + FastAPI + Magnum + AWS Lambda

## Data layer

Serverless PostgreSQL (AWS Aurora Serverless v2) stores all the data.

In case of performance issues, payload, answers and audit logs can be moved into S3.
