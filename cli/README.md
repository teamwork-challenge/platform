# Teamwork Challenge: CLI Client

A command-line interface for interacting with the Teamwork Challenge platform.

## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:

```bash
cli> pip install -r requirements-dev.txt
```

## Usage

The CLI provides various commands for interacting with the Teamwork Challenge platform:
From the root directory, run:
```bash
platform> python -m cli.main [COMMAND] [SUBCOMMAND] [OPTIONS]
```

## Type checking

In the root directory:

```bash
platform> mypy back
```


### Global Options

- `--json`: Output in JSON format instead of human-readable text. This flag is available for all commands and returns the raw JSON data from the API.
- `-r, --round ID`: Specify the round ID (defaults to current round)


## Development

### Architecture

The CLI uses an `ApiClient` class to handle all communication with the backend API. This class is responsible for:

- Managing API keys (loading, saving, validating)
- Making HTTP requests to the API endpoints
- Handling errors and responses

All commands in the CLI follow the same pattern:

1. Get data from the API using the `ApiClient`
2. If the `--json` flag is set, return the raw JSON data
3. Otherwise, format the data for human-readable output using Rich

### Adding New Commands

To add new commands:

1. Add a new method to the `ApiClient` class in `api_client.py` to handle the API request
2. Add a new command function to `main.py` with the appropriate Typer decorators
3. Follow the pattern of getting data from the API, then either returning it as JSON or formatting it for human-readable output
4. To handle json output, use the pattern `if json: return print_as_json(data)`
