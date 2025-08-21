#!/usr/bin/env python3
import logging
import sys

from pathlib import Path
from cli.typers.board_app import board_app
from cli.typers.round_app import round_app
from cli.typers.task_app import task_app
from cli.typers.team_app import team_app
from cli.typers.challenge_app import challenge_app
from cli.typers.config_app import config_app
from cli.typers.submission_app import submission_app
import typer
from cli.typers.app_deps import api_client, console, ensure_logged_in, json_output_option

app = typer.Typer(help="Teamwork Challenge CLI", pretty_exceptions_short=True, pretty_exceptions_show_locals=False, no_args_is_help=True)
__all__ = ["app"]

# Root-level commands (auth):
@app.command()
def login(api_key: str) -> None:
    """Store an API key into the config file after successful login."""
    api_client.save_api_key(api_key)
    try:
        role = api_client.auth()
    except Exception:
        api_client.remove_api_key()
        raise
    console.print(f"[green]Successfully logged in with role {role} using API key: {api_key}[/green]")

@app.command()
def logout() -> None:
    """Remove an API key from the config file."""
    api_client.remove_api_key()
    console.print("[green]Successfully logged out[/green]")

# Sub-typers
app.add_typer(challenge_app, name="challenge")
app.add_typer(team_app, name="team")
app.add_typer(round_app, name="round")
app.add_typer(task_app, name="task")
app.add_typer(board_app, name="board")
app.add_typer(submission_app, name="submission")
app.add_typer(config_app, name="config")

if __name__ == "__main__":
    # Configure logging based on persisted config
    try:
        from cli.typers.app_deps import config_manager
        log_cfg = config_manager.get("log_levels") or {}
    except Exception:
        log_cfg = {}

    console_level = (log_cfg.get("console") or "CRITICAL").upper()
    file_level = (log_cfg.get("file") or "INFO").upper()

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    handlers: list[logging.Handler] = []
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level_map.get(console_level, logging.CRITICAL + 10))
    handlers.append(ch)

    # File handler
    log_path = Path.home() / ".challenge" / "challenge.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(level_map.get(file_level, logging.INFO))
    handlers.append(fh)

    logging.basicConfig(
        level=logging.DEBUG,  # master level low enough; handlers filter
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=handlers,
        force=True,
    )

    app()
