# Task Generators and Validator API

## Overview

Task generators are AWS Lambda microservices that create, validate, and score tasks. Each task type has its own generator that operates independently from the main platform via a defined API, providing:
- Isolation of task-specific logic
- Independent scaling
- Support for various task complexities
- Enhanced security

## Authentication

All requests require a `SECRET_KEY` header for authorization.

## Task Settings

Task settings are configured by admins at the round level and include:
- Generator URL
- Task Type Code
- Difficulty Parameters (1-5 scale)
- Scoring Rules (base points and decay method)
- Time Allocation

These settings are passed to the generator via the `task-settings` field in the `/gen` endpoint request.

## Statement Versions

Task generators support multiple statement versions for:
- Progressive disclosure of task details
- Different difficulty levels
- Adaptive learning
- Hint systems

The platform decides which version to show based on round configuration and team progress.

## API Endpoints

### GET `/statements`
Returns available statement versions.

```json
{
	"v1": "Basic task description",
	"v2": "Detailed description with examples",
	"v3": "Comprehensive description with hints"
}
```

### POST `/gen`
Generates a new task when claimed by a team.

Input:
```json
{
	"challenge": "challenge-123",
	"team": "team-456",
	"round": "round-789",
	"round-start-at": "2023-10-15T14:00:00Z",
	"round-duration": "14400",  // 4 hours in seconds
	"task-settings": {
		"type": "string_processing",
		"difficulty": 3,  // 1-5 scale
		"format": "json",
		"scoring": {
			"base": 100,
			"decay": "linear"  // "linear"|"none"
		}
	}
}
```

Output:
```json
{
	"statement-version": "v1",
	"value": 100,  // Base points
	"input": "{'array': [2, 8, 1, 9, 5], 'target': 10}",
	"checker-hint": [[0,1], [2,3]]  // Correct answer
}
```

### POST `/check`
Validates a solution and assigns a score.

Input:
```json
{
	"input": "{'array': [2, 8, 1, 9, 5], 'target': 10}",
	"checker-hint": [[0,1], [2,3]],
	"answer": "[[1, 2], [3, 4]]"  // Team's solution
}
```

Output:
```json
[
	{
		"task-id": "task-123",
		"status": "AC",  // AC (Accepted) or WA (Wrong Answer)
		"score": 100,
		"error": ""  // For WA status only
	}
]
```

