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

## Optional: Interactive UI

Textual interactive UI or React web-app.

TODO.

