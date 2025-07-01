# Task generators and validator API

Task generator is a set of HTTP handlers published as AWS Lambda.


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
	"challenge": "{challenge-id}",
	"team": "{team-id}",
	"round": "{round-id}",
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
	"score": 100,
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
		"score": 100,
		"error": ""
	}
]
```

- task-id is optional. It can be used to give score to other tasks of other teams for non-typical collaborative tasks.
- score is optional. It can be used to give a partial score.
- error is present for WA status only.