# Backend

## Authentication

All API calls must include a valid API_KEY header.

Missing or invalid keys return 401 Unauthorized.
Authentication determines roles: admin or player and a challenge.

## Endpoints for Players

GET|PUT /teams/me
GET /rounds
GET /tasks?round={id}[&type={type}&status={status}] - dashboard
POST /tasks?round={id}[&type={task-type}] - claim task
GET  /tasks/{id}
POST /tasks/{id}/answer - submit solution
GET /rounds/{id}/leaderboard

Note: teamId and challengeId is defined by authentication and filters and validators applied when it make sense.

## Endpoints for Admin

GET|POST|DELETE /challenges
GET|PUT /challenges/{id}
GET /rounds?challenge={id}
GET|POST|PUT|DELETE /rounds/{id}
GET|PUT /teams?challenge={id}
GET /round/{id}/logs
PUT /tasks/{id}/answer - override answer verdict, for incidents.

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

# Command Line Client UI/UX

All commands respect the API key in `~/.challenge/config.json`; 
`-r/--round` defaults to the current round reported by the server.

`--json` outputs in json format instead of human readable plain text.

## Login

```
challenge login <API_KEY>            # store key into config file after successful login
challenge logout
challenge whoami                     # show team id, name
```

## As Player

### Team Settings

```
challenge team show
challenge team rename <NEW_NAME>     # allowed until first submission
```

### Challenge and Round Information

```
challenge show
challenge round show        [-r ID]
challenge round list
```

### Task Workflow

```
challenge task claim        [-t TYPE]
challenge task show <TASK_ID>					# shows task and it's submissions
challenge task show-input <TASK_ID>				# shows raw task input payload
challenge task submit <TASK_ID> <ANSWER|--file PATH>
challenge task show-answer <SUBMIT_ID>			# shows raw submitted answer
```

```
challenge task list         [-s STATUS] [-t TYPE] [-r ID] [--since TIME] [--watch]
```
shows list of  tasks with columns:

- task-type
- task-id
- score - for WA and PENDING shows possible score according to score decay rule
- time-remaining - for PENDING and WA
- claimed-at
- last-attempt-at - for WA
- solved-at - for AC

Ordered by `claimed-at` by descending, starting with `time` if it is specified.

### Scores & Rankings

```
challenge board dashboard   [-r ID] [--watch]
```
- rows: task-types
- columns: 
  - total number of tasks, 
  - of status PENDING
  - of status AC
  - of status WA
  - remaining tasks to claim (`total - (PENDING + OK + WA)`)


```
challenge board leaderboard [-r ID] [--watch]
```
- rows: teams
- columns:
  - one per task-type: score
  - total score


## As Admin

TODO.

For setting up the challenge and rounds use json-files as inputs and outputs.

# Optional: Interactive UI

Textual interactive UI or React web-app.

TODO.

