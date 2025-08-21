# Command Line Client UI/UX

All commands respect the API key in `%USERPROFILE%/.challenge/config.json`.
If `--challenge`/`-c` or `--round`/`-r` is omitted, the server-side "current"
challenge/round is used when supported by the endpoint.

`--json` outputs machine-friendly JSON instead of human-readable text.

## Login

```
challenge login <API_KEY>            # store key into config after successful login
challenge logout
```

## Player commands

### Team

```
challenge team show
challenge team rename <NEW_NAME>     # allowed until first submission
```

List and batch-manage teams (admin role required on the server):
```
challenge team list [CHALLENGE_ID]
challenge team create <CHALLENGE_ID> <TEAMS_TSV>
```
Where TEAMS_TSV is a tab-separated file with header: `name\tmembers\tcaptain_contact`.

### Challenge and Rounds

```
challenge challenge list                         # admin-only on server
challenge challenge show [-c|--challenge-id ID]
challenge challenge update <CHALLENGE.hjson>     # admin-only on server

challenge round show [-c ID] [-r ID]
challenge round list [-c ID]
challenge round update <ROUND.hjson>             # admin-only on server
challenge round delete --challenge <ID> --round <ID> [--yes]  # admin-only on server
```

### Tasks

```
challenge task claim        [-t TYPE]
challenge task show <TASK_ID>                     # shows task and its submissions
challenge task show-input <TASK_ID>               # shows raw task input payload
challenge task submit <TASK_ID> <ANSWER|--file PATH>
challenge task show-answer <SUBMIT_ID>            # fetches submission info (client-side)

challenge task list         [-s STATUS] [-t TYPE] [-r ID] [--since TIME] [--watch]
```
List output includes columns:
- task-id
- type
- status
- score
- claimed-at
- last-attempt-at (for non-pending)
- solved-at (for AC status)

### Boards

```
challenge board dashboard   [-r ID] [--watch]
challenge board leaderboard [-r ID] [--watch]
```

### Config

```
challenge config log-level <file|console> <CRITICAL|DEBUG|INFO|WARNING|ERROR>
challenge config api-url <BASE_URL>
```
`api-url` stores the base server URL, e.g. `http://127.0.0.1:8088`.

## Notes
- Use `--json` with any command for machine-friendly output.
- Authentication and authorization are enforced server-side; some commands will
  work only if your API key has admin role.

