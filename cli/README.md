# Teamwork Challenge: CLI Client

A command-line interface for interacting with the Teamwork Challenge platform.

## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:

```bash
pip install typer rich
```

## Usage

The CLI provides various commands for interacting with the Teamwork Challenge platform:

```bash
python main.py [COMMAND] [SUBCOMMAND] [OPTIONS]
```

### Global Options

- `--json`: Output in JSON format instead of human-readable text
- `-r, --round ID`: Specify the round ID (defaults to current round)

### Authentication

```bash
# Login with your API key
python main.py login <API_KEY>

# Logout
python main.py logout

# Show your team information
python main.py whoami
```

### Team Management

```bash
# Show team information
python main.py team show

# Rename your team
python main.py team rename <NEW_NAME>
```

### Challenge and Round Information

```bash
# Show challenge information
python main.py show

# Show round information
python main.py round show [-r ID]

# List all rounds
python main.py round list
```

### Task Management

```bash
# Claim a new task
python main.py task claim [-t TYPE]

# Show task information
python main.py task show <TASK_ID>

# Show raw task input
python main.py task show-input <TASK_ID>

# Submit an answer for a task
python main.py task submit <TASK_ID> <ANSWER>
python main.py task submit <TASK_ID> --file <PATH>

# Show submitted answer
python main.py task show-answer <SUBMIT_ID>

# List tasks
python main.py task list [-s STATUS] [-t TYPE] [-r ID] [--since TIME] [--watch]
```

### Leaderboard and Dashboard

```bash
# Show dashboard with task statistics
python main.py board dashboard [-r ID] [--watch]

# Show leaderboard with team scores
python main.py board leaderboard [-r ID] [--watch]
```

## Example

See the `example.py` script for a complete workflow demonstration:

```bash
python example.py
```

## Development

This CLI is built using:

- [Typer](https://typer.tiangolo.com/) - For command-line interface
- [Rich](https://rich.readthedocs.io/) - For rich text and formatting in the terminal

To add new commands, modify the `main.py` file and add your command functions with the appropriate decorators.
