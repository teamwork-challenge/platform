# Backend

## Authentication

All API calls must include a valid X-API-Key header.
Missing or invalid keys return 401 Unauthorized.
Authentication determines role (admin or player) and binds to a challenge/team context.

## Player endpoints

Team and auth:
```
GET  /auth                     # returns role ("ADMIN" or "PLAYER")
GET  /team                     # current team info (derived from API key)
PUT  /team                     # rename current team
```

Challenges and rounds:
```
GET  /challenges/{challenge_id}
GET  /challenges/{challenge_id}/rounds
GET  /challenges/{challenge_id}/rounds/{round_id}
```
Note: the server accepts the literal value `current` for challenge_id/round_id
in many places to resolve current context.

Tasks (scoped to challenge and round):
Base path: `/challenges/{challenge_id}/rounds/{round_id}`
```
GET  /challenges/{challenge_id}/rounds/{round_id}/tasks
      ?status=<pending|wa|ac>&task_type=<type>&since=<ISO-datetime>
POST /challenges/{challenge_id}/rounds/{round_id}/tasks         # claim a task
GET  /challenges/{challenge_id}/rounds/{round_id}/tasks/{task_id}
POST /challenges/{challenge_id}/rounds/{round_id}/submissions    # submit answer
```

## Admin endpoints

Challenges and rounds:
```
GET  /challenges                                   # list all challenges
PUT  /challenges/{challenge_id}                    # update a challenge
PUT  /challenges/{challenge_id}/rounds/{round_id}  # create/update a round
DELETE /challenges/{challenge_id}/rounds/{round_id}
```

Teams:
```
GET  /challenges/{challenge_id}/teams              # list teams in a challenge
POST /teams                                        # batch-create teams
```

## Notes
- Dashboard and leaderboard endpoints are not exposed in the current backend implementation.
- Some endpoints require an admin role; authorization is enforced by dependencies.

## Deadline handling

Submissions after a task-specific deadline score 0 but are still evaluated for status.
Claiming and submitting before round start or after round end return 403 Forbidden.

## Logging

Every task-related action — claim, submit, status update — should be captured in logs (implementation details may vary).

## Performance and rate limits

Target latency: under 1 s at P95. Apply reasonable rate limiting and scaling as needed.
