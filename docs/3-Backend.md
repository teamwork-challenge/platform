# Backend

## Authentication

All API calls must include a valid API_KEY header.

Missing or invalid keys return 401 Unauthorized.
Authentication determines roles: admin or player and a challenge.

## Endpoints for Players

```
GET | PUT /teams/me
GET /rounds
GET /tasks/{id} – Get full details of a specific task (Task)
GET /tasks?round={id}[&type={type}&status={status}] – Get tasks filtered by type and status (Task List)
GET /tasks?round={id} – Get all team tasks for a round (Dashboard)
GET /rounds/{id}/leaderboard – Get leaderboard for a specific round (Leaderboard)
POST /tasks?round={id}[&type={task-type}] – Claim Task
POST /tasks/{id}/answer – Submit Solution
```

Note: teamId and challengeId is defined by authentication and filters and validators applied when it make sense.

## Endpoints for Admin

```
GET|POST|DELETE /challenges
GET|PUT /challenges/{id}
GET|POST /rounds
GET|PUT|DELETE /rounds/{id}
GET|POST /task-types
GET|PUT|DELETE /task-types/{id}
POST /teams
GET|PUT /teams
GET /round/{id}/logs
PUT /tasks/{id}/answer - override answer verdict, for incidents.
```

## Deadline handling

Submissions after a task-specific deadline score 0 but are still evaluated for status. Claiming and submitting before round start or after round end returns 403 Forbidden.

## Logging

Every task-related action — claim, submit, status update — is written to an immutable audit log with timestamp, team id, task id, status, and score.

## Rate limits

The API must sustain at least 20 concurrent submissions and throttle a team to 30 requests per minute; excess requests return 429 Too Many Requests.

## Performance requirements

Any API request must return within 1 s at the 95-th percentile.

6 task types ✕ 1000 tasks ✕ 20 teams ✕ 2 answers = 240_000 records per round in answers DB table.

The platform must handle at least 20 concurrently active players who may poll, claim, and submit in a tight loop (≈50 req/s aggregate) without breaching the latency target.

### Important!

Dashboard and Leaderboard require optimizations: e.g. separate tables for dashboard and leaderboard entries with incremental updates on every claim / submit.
