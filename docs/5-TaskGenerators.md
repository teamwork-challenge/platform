# Task generators and validator API

Task generator is a set of HTTP handlers


## Authentication

All requests require a `X-API-Key` header for authorization.

Known secret keys are stored in AWS Secrets Manager.


### GET `/statements`

Run by the platform ones when round is created.

Output:
```json
{
	"v1": "Initial version of the statement",
	"v2": "More complicated version of the statement for the same generator. May be used to provide more complex tasks in later in the round, or in the next rounds",
    "v3": "Even more complicated version of the statement for the same generator. May be used to provide even more complex tasks in later in the round, or in the next rounds"
  
}
```

### POST `/gen`

Generates new task.

Input:
```json
{
  "challenge-id": "{challenge-id}",
  "team-id": "{team-id}",
  "round-id": "{round-id}",
  "task-id": "{task-id}",
  "progress": {
    "task-index": 0,
    "task-count": 100,
    "elapsed-time": 0,
    "total-time": 0
  },
  "task-settings": "complication1:20,complication2:50,complication3:60"
}
```

#### Task Settings

Is specific for each task generator and can be used to pass additional parameters to the task generator.
It can be used to control the complexity of the task, and moments, when the complexity should be increased.

In the example above `"complication1:20,complication2:50,complication3:60"` may be used by the generator to decide that 
the first tasks should be simple, but starting with the 20-th task a complication1 should be used to generate tasks, starting with 50 complication2 should be used also and so on.


Output:
```json
{
  "statement-version": "v1",
  "input": "task input visible to the team",
  "checker-hint": "secret value helpful for the validator, but not visible to the team"
}
```

### POST /check

Checks the correctness of the solution.

Input:
```json
{
	"input": "the same input, as in the task generator output",
	"checker-hint": "the same checker-hint, as in the task generator output",
	"answer": "answer provided by the team"
}
```

Output:
```json
{
    "status": "{AC|WA}",
    "score": 1.0,
    "error": "",
    "collaborative_scores": {
        "{other-task-id}": 1.0
    }
}

```

- score should be between 0.0 and 1.0. Use 1.0 for fully correct solutions.
Original task should be updated with the score from the `score` field, if it is higher than the current one. 
So several submissions for the same task should never decrease the score of the task.
- error is present for WA status only and visible for the team.
- `collaborative_scores` should be present only for collaborative tasks. 
In this case tasks with ids from `collaborative_scores` keys should be updated with the new score, if it is higher than the current one.
`other-task-id` should be stored in the original task as `related_task_ids` for debugging purposes.

## Collaborative tasks example

Sample task:
1. Generator generates a random flag (GUID).
2. Player should submit a flag generated for some other team and was not yet submitted earlier.
3. Player gets 0.5 score for submitting a flag of another team, and 1.0 score when another team submits its flag.

Scenario:
1. `/gen` generates GUID and save it along with `team-id` and `task-id` in its database as not submitted yet flag.
2. `/gen` returns generated GUID as a flag in the `input` field and `team-id` in the  `checker-hint` field.
3. `/check` searches submitted GUID in its database and checks:
   - if it belongs to the team other that `team-id` from the `checker-hint`.
   - if it was not submitted yet.
4. If all checks are passed, the submitted GUID is marked as submitted in the database. 
As a result `/check` returns 
   - status AC 
   - score 0.5
   - collaborative_scores with one entry: 
      - `task-id`, associated with the submitted GUID and score 1.0.
5. If some check is failed, it returns:
    - status WA
    - error — one of the following: 
      - "Is not a valid flag"
      - "Cannot submit your own flag"
      - "This flag was already submitted earlier"
6. Platform should update the task score for both tasks — submitted one and the one associated with the submitted GUID.
So, after submitting correct flag, team gets 0.5 score for their submission.
And after another team submits the same flag, they get the full 1.0 score for the task.
