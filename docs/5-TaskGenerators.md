# DRAFT: Task generators and validator API

Task generator is a set of HTTP handlers published as AWS Lambda.

It authorizates all requests with SECRET_KEY header.

### GET `/statements`

Run by the platform ones when round is created.

Output:
```json
{
	"v1": "...",
	"v2": "...",
}
```

### POST `/gen`

Generates new task.

Input:
```json
{
	"challenge": "{challenge-id}",
	"team": "{team-id}",
	"round": "{round-id}",
	"round-start-at": "",
	"round-duration": "",
	"task-settings": ""
}
```

Output:
```json
{
	"statement-version": "v1",
	"value": "100",
	"input": "",
	"checker-hint": ""
}
```

### POST /check

Checks the correctness of the solution.

Input:
```json
{
	"input": "",
	"checker-hint": "",
	"answer": ""
}
```

Output:
```json
[
	{
		"task-id": "",
		"status": "{AC|WA}",
		"score": 1.0,
		"error": ""
	}
]
```

- task-id is optional. It can be used to give score to other tasks of other teams.
- score is optional. It can be used to give partial score.
- error is present for WA status only.