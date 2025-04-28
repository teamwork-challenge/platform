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
	...
}
```

### POST `/gen`

Generates new task.

Input:
```json
{
	challenge: "{challenge-id}",
	team: "{team-id}",
	round: "{round-id}",
	round-start-at: "",
	round-duration: "",
	task-settings: ""
}
```

Output:
```json
{
	statement-version: "v1",
	value: "100",
	input: "",
	checker-hint: ""
}
```

### POST /check

Checks the correctness of the solution.

Input:
```json
{
	input: "",
	checker-hint: "",
	answer: ""
}
```

Output:
```json
[
	{
		task-id: "", 			# optional
		status: {AC|WA},
		score: 1.0				# optional, 0..1, can be present for AC only, 1.0 - full score.
		error: ""				# present for WA only
	}
]
```

Note: Using task-id it may results in giving score to other tasks of other teams.